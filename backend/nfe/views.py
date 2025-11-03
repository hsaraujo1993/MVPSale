from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema_view, extend_schema
from django.utils.crypto import get_random_string
from django.conf import settings
from django.http import HttpResponse

from .models import NFeInvoice, Company
from .serializers import NFeInvoiceSerializer
from rest_framework import viewsets as drf_viewsets, serializers
from .services.focusnfe import get_focus_config, FocusNFeClient
from sale.models import Order


@extend_schema_view(
    list=extend_schema(tags=["nfe"], summary="Listar NF-e"),
    retrieve=extend_schema(tags=["nfe"], summary="Detalhar NF-e"),
)
class NFeInvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = NFeInvoice.objects.select_related("order").all().order_by("-created_at")
    serializer_class = NFeInvoiceSerializer
    lookup_field = "uuid"
    from django_filters.rest_framework import DjangoFilterBackend
    from rest_framework import filters as drf_filters
    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter, drf_filters.OrderingFilter]
    filterset_fields = {"order": ["exact"], "company": ["exact"], "status": ["exact"], "created_at": ["gte", "lte"], "updated_at": ["gte", "lte"]}
    search_fields = ["ref", "chave"]
    ordering_fields = ["created_at", "updated_at"]

    @extend_schema(tags=["nfe"], summary="Emitir NF-e a partir do pedido")
    @action(detail=False, methods=["post"], url_path="from-order/(?P<order_id>[^/.]+)")
    def from_order(self, request, order_id=None):
        cfg = get_focus_config()
        if not cfg:
            return Response({"detail": "FOCUSNFE_API_TOKEN ausente. Configure o .env para emissão."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            order = Order.objects.get(uuid=order_id)
        except Order.DoesNotExist:
            return Response({"detail": "Pedido não encontrado."}, status=status.HTTP_404_NOT_FOUND)
        if order.status != "CONFIRMED":
            return Response({"detail": "Pedido deve estar CONFIRMED para emitir NF-e."}, status=status.HTTP_400_BAD_REQUEST)

        ref = f"ORD-{order.id}-{get_random_string(6)}"
        inv = NFeInvoice.objects.create(
            order=order,
            ref=ref,
            env="homolog" if "homolog" in settings.FOCUSNFE_BASE_URL else "prod",
            total=order.total,
            status="SUBMITTED",
        )
        # Try submission if configured
        client = FocusNFeClient(cfg)
        try:
            result = client.submit_from_order(order.id, ref)
            data = result.get("data", {})
            http_status = result.get("http_status")
            # Focus retorna status textual; apenas armazenamos resposta mínima
            inv.cStat = str(data.get("status_sefaz") or "")
            inv.xMotivo = data.get("mensagem_sefaz") or data.get("mensagem") or ""
            inv.chave = data.get("chave_nfe") or inv.chave
            inv.protocolo = data.get("numero_protocolo") or inv.protocolo
            if data.get("status") == "autorizado":
                inv.status = "AUTHORIZED"
                inv.danfe_url = data.get("link_danfe") or inv.danfe_url
            elif data.get("status") == "cancelado":
                inv.status = "CANCELED"
            elif data.get("status") == "rejeitado":
                inv.status = "REJECTED"
            else:
                inv.status = "SUBMITTED"
            inv.save()
        except Exception as exc:
            # Mantém como SUBMITTED e retorna detalhe de erro
            return Response({"invoice": NFeInvoiceSerializer(inv).data, "detail": str(exc)}, status=status.HTTP_202_ACCEPTED)

        return Response(NFeInvoiceSerializer(inv).data, status=status.HTTP_201_CREATED)

    @extend_schema(tags=["nfe"], summary="Cancelar NF-e")
    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        cfg = get_focus_config()
        if not cfg:
            return Response({"detail": "FOCUSNFE_API_TOKEN ausente. Configure o .env para cancelar."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            inv = NFeInvoice.objects.get(uuid=pk)
        except NFeInvoice.DoesNotExist:
            return Response({"detail": "NF-e não encontrada."}, status=status.HTTP_404_NOT_FOUND)
        motivo = request.data.get("motivo") or "Cancelamento solicitado via API"
        if not inv.chave:
            return Response({"detail": "NF-e sem chave para cancelamento."}, status=status.HTTP_400_BAD_REQUEST)
        client = FocusNFeClient(cfg)
        try:
            result = client.cancel(inv.chave, motivo)
            data = result.get("data", {})
            if data.get("status") == "cancelado":
                inv.status = "CANCELED"
                inv.save(update_fields=["status", "updated_at"])
            return Response({"provider": data, "invoice": NFeInvoiceSerializer(inv).data})
        except Exception as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = [
            "id","cnpj","ie","regime_tributario","razao_social","nome_fantasia",
            "logradouro","numero","bairro","cidade","uf","cep","created_at","updated_at"
        ]
        read_only_fields = ["id","created_at","updated_at"]


@extend_schema_view(
    list=extend_schema(tags=["nfe"], summary="Listar emitentes"),
    retrieve=extend_schema(tags=["nfe"], summary="Detalhar emitente"),
    create=extend_schema(tags=["nfe"], summary="Criar emitente"),
    update=extend_schema(tags=["nfe"], summary="Atualizar emitente"),
    partial_update=extend_schema(tags=["nfe"], summary="Atualizar parcialmente emitente"),
    destroy=extend_schema(tags=["nfe"], summary="Excluir emitente"),
)
class CompanyViewSet(drf_viewsets.ModelViewSet):
    queryset = Company.objects.all().order_by("razao_social")
    serializer_class = CompanySerializer

    @extend_schema(tags=["nfe"], summary="Atualizar status da NF-e com o provedor (Focus)")
    @action(detail=True, methods=["post"], url_path="refresh")
    def refresh(self, request, pk=None):
        cfg = get_focus_config()
        if not cfg:
            return Response({"detail": "FOCUSNFE_API_TOKEN ausente. Configure o .env para atualizar."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            inv = NFeInvoice.objects.get(uuid=pk)
        except NFeInvoice.DoesNotExist:
            return Response({"detail": "NF-e não encontrada."}, status=status.HTTP_404_NOT_FOUND)

        ident = inv.ref or inv.chave
        if not ident:
            return Response({"detail": "NF-e sem referência ou chave para consulta."}, status=status.HTTP_400_BAD_REQUEST)

        client = FocusNFeClient(cfg)
        try:
            result = client.get_status(ident)
            data = result.get("data", {})
            inv.cStat = str(data.get("status_sefaz") or "")
            inv.xMotivo = data.get("mensagem_sefaz") or data.get("mensagem") or inv.xMotivo
            inv.chave = data.get("chave_nfe") or inv.chave
            inv.protocolo = data.get("numero_protocolo") or inv.protocolo
            if data.get("status") == "autorizado":
                inv.status = "AUTHORIZED"
                inv.danfe_url = data.get("link_danfe") or inv.danfe_url
            elif data.get("status") == "cancelado":
                inv.status = "CANCELED"
            elif data.get("status") == "rejeitado":
                inv.status = "REJECTED"
            inv.save()
            return Response({"provider": data, "invoice": NFeInvoiceSerializer(inv).data})
        except Exception as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(tags=["nfe"], summary="Baixar XML autorizado da NF-e")
    @action(detail=True, methods=["get"], url_path="xml")
    def download_xml(self, request, pk=None):
        cfg = get_focus_config()
        if not cfg:
            return Response({"detail": "FOCUSNFE_API_TOKEN ausente."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            inv = NFeInvoice.objects.get(uuid=pk)
        except NFeInvoice.DoesNotExist:
            return Response({"detail": "NF-e não encontrada."}, status=status.HTTP_404_NOT_FOUND)
        if not inv.chave:
            return Response({"detail": "NF-e sem chave."}, status=status.HTTP_400_BAD_REQUEST)
        client = FocusNFeClient(cfg)
        result = client.get_xml(inv.chave)
        if result["http_status"] != 200:
            return Response({"detail": "Falha ao obter XML", "provider_status": result["http_status"]}, status=status.HTTP_400_BAD_REQUEST)
        content = result["content"]
        try:
            inv.xml = content.decode("utf-8", errors="ignore")
            inv.save(update_fields=["xml", "updated_at"])
        except Exception:
            pass
        resp = HttpResponse(content, content_type=result.get("content_type", "application/xml"))
        resp["Content-Disposition"] = f"attachment; filename=nota-{inv.chave}.xml"
        return resp

    @extend_schema(tags=["nfe"], summary="Baixar DANFE (PDF) da NF-e")
    @action(detail=True, methods=["get"], url_path="danfe")
    def download_danfe(self, request, pk=None):
        cfg = get_focus_config()
        if not cfg:
            return Response({"detail": "FOCUSNFE_API_TOKEN ausente."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            inv = NFeInvoice.objects.get(uuid=pk)
        except NFeInvoice.DoesNotExist:
            return Response({"detail": "NF-e não encontrada."}, status=status.HTTP_404_NOT_FOUND)
        if not inv.chave:
            return Response({"detail": "NF-e sem chave."}, status=status.HTTP_400_BAD_REQUEST)
        client = FocusNFeClient(cfg)
        result = client.get_danfe(inv.chave)
        if result["http_status"] != 200:
            return Response({"detail": "Falha ao obter DANFE", "provider_status": result["http_status"]}, status=status.HTTP_400_BAD_REQUEST)
        content = result["content"]
        resp = HttpResponse(content, content_type=result.get("content_type", "application/pdf"))
        resp["Content-Disposition"] = f"attachment; filename=danfe-{inv.chave}.pdf"
        return resp

