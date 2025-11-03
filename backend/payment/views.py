from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncMonth
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema_view, extend_schema
from django.conf import settings
import os
import datetime

from .models import PaymentMethod, Receivable, PaymentEvent, CardBrand, CardFeeTier
from .serializers import PaymentMethodSerializer, ReceivableSerializer, SettleSerializer, CardBrandSerializer, CardFeeTierSerializer
import logging
logger = logging.getLogger("payment")


@extend_schema_view(
    list=extend_schema(tags=["payment"], summary="Listar métodos de pagamento"),
    retrieve=extend_schema(tags=["payment"], summary="Detalhar método"),
    create=extend_schema(tags=["payment"], summary="Criar método"),
    update=extend_schema(tags=["payment"], summary="Atualizar método"),
    partial_update=extend_schema(tags=["payment"], summary="Atualização parcial de método"),
)
class PaymentMethodViewSet(viewsets.ModelViewSet):
    queryset = PaymentMethod.objects.all().order_by("name")
    serializer_class = PaymentMethodSerializer
    lookup_field = "uuid"
    from django_filters.rest_framework import DjangoFilterBackend
    from rest_framework import filters as drf_filters
    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter, drf_filters.OrderingFilter]
    filterset_fields = {"type": ["exact"], "created_at": ["gte", "lte"], "updated_at": ["gte", "lte"]}
    search_fields = ["name", "code"]
    ordering_fields = ["name", "created_at", "updated_at"]


@extend_schema_view(
    list=extend_schema(tags=["payment"], summary="Listar recebíveis"),
    retrieve=extend_schema(tags=["payment"], summary="Detalhar recebível"),
    create=extend_schema(tags=["payment"], summary="Criar recebível"),
)
class ReceivableViewSet(viewsets.ModelViewSet):
    queryset = Receivable.objects.select_related("method").all().order_by("-created_at")
    serializer_class = ReceivableSerializer
    lookup_field = "uuid"
    from django_filters.rest_framework import DjangoFilterBackend
    from rest_framework import filters as drf_filters
    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter, drf_filters.OrderingFilter]
    filterset_fields = {
        "method": ["exact"],
        "status": ["exact"],
        "due_date": ["gte", "lte"],
        "created_at": ["gte", "lte"],
        "updated_at": ["gte", "lte"],
    }
    search_fields = ["reference", "external_id"]
    ordering_fields = ["created_at", "due_date", "amount", "updated_at"]

    @extend_schema(request=SettleSerializer, tags=["payment"], summary="Baixar/ Liquidar recebível")
    @action(detail=True, methods=["post"], url_path="settle")
    def settle(self, request, pk=None):
        r = self.get_object()
        ser = SettleSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        # Idempotência por external_id de evento
        if data.get("external_id"):
            if PaymentEvent.objects.filter(external_id=data["external_id"]).exists():
                logger.info("[payment] duplicate settle ignored receivable=%s external_id=%s", r.id, data["external_id"]) 
                return Response({"detail": "Evento já processado."}, status=status.HTTP_200_OK)
        evt = PaymentEvent.objects.create(
            receivable=r,
            amount=data["amount"],
            fee_amount=data.get("fee_amount") or 0,
            paid_date=data["paid_date"],
            external_id=data.get("external_id") or None,
            metadata=data.get("metadata") or {},
        )
        evt.apply()
        logger.info("[payment] settled receivable=%s amount=%s fee=%s external_id=%s", r.id, data["amount"], data.get("fee_amount") or 0, data.get("external_id") or "")
        return Response(ReceivableSerializer(r).data)

    @extend_schema(tags=["payment"], summary="Resumo de recebíveis")
    @action(detail=False, methods=["get"], url_path="summary")
    def summary(self, request):
        method = request.query_params.get("method")
        ref = request.query_params.get("date")
        try:
            ref_date = datetime.date.fromisoformat(ref) if ref else datetime.date.today()
        except Exception:
            return Response({"detail": "Data inválida."}, status=status.HTTP_400_BAD_REQUEST)

        qs = Receivable.objects.select_related("method")
        if method:
            qs = qs.filter(method_id=method)

        total = qs.aggregate(count=Count("id"), value=Sum("amount"))
        by_status_qs = qs.values("status").annotate(count=Count("id"), value=Sum("amount")).order_by("status")
        by_status = {row["status"]: {"count": row["count"], "value": row["value"] or 0} for row in by_status_qs}

        overdue = qs.filter(due_date__lt=ref_date, status__in=["PENDENTE", "ATRASADO"]).aggregate(
            count=Count("id"), value=Sum("amount")
        )

        in_7 = qs.filter(due_date__gte=ref_date, due_date__lte=ref_date + datetime.timedelta(days=7)).aggregate(
            count=Count("id"), value=Sum("amount")
        )
        in_30 = qs.filter(due_date__gt=ref_date + datetime.timedelta(days=7), due_date__lte=ref_date + datetime.timedelta(days=30)).aggregate(
            count=Count("id"), value=Sum("amount")
        )

        six_months_ahead = ref_date + datetime.timedelta(days=31 * 6)
        monthly_qs = (
            qs.filter(due_date__gte=ref_date, due_date__lt=six_months_ahead)
            .annotate(month=TruncMonth("due_date"))
            .values("month")
            .annotate(count=Count("id"), value=Sum("amount"))
            .order_by("month")
        )
        monthly_next = [
            {"month": row["month"].strftime("%Y-%m"), "count": row["count"], "value": row["value"] or 0}
            for row in monthly_qs
        ]

        return Response(
            {
                "total": {"count": total.get("count") or 0, "value": total.get("value") or 0},
                "by_status": by_status,
                "overdue": {"count": overdue.get("count") or 0, "value": overdue.get("value") or 0},
                "upcoming": {
                    "7d": {"count": in_7.get("count") or 0, "value": in_7.get("value") or 0},
                    "30d": {"count": in_30.get("count") or 0, "value": in_30.get("value") or 0},
                },
                "monthly_next": monthly_next,
            }
        )


class PaymentLogsView(viewsets.ViewSet):
    @extend_schema(tags=["payment"], summary="Últimos logs de pagamento")
    def list(self, request):
        try:
            limit = int(request.query_params.get("limit", 200))
        except ValueError:
            return Response({"detail": "limit inválido"}, status=status.HTTP_400_BAD_REQUEST)
        log_path = os.path.join(settings.BASE_DIR, "logs", "payment.log")
        if not os.path.exists(log_path):
            return Response({"lines": [], "path": log_path})
        try:
            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        tail = [ln.rstrip("\n") for ln in lines[-limit:]]
        return Response({"lines": tail, "path": log_path, "count": len(tail)})


@extend_schema_view(
    list=extend_schema(tags=["payment"], summary="Listar bandeiras"),
    retrieve=extend_schema(tags=["payment"], summary="Detalhar bandeira"),
    create=extend_schema(tags=["payment"], summary="Criar bandeira"),
    update=extend_schema(tags=["payment"], summary="Atualizar bandeira"),
    partial_update=extend_schema(tags=["payment"], summary="Atualização parcial de bandeira"),
    destroy=extend_schema(tags=["payment"], summary="Excluir bandeira"),
)
class CardBrandViewSet(viewsets.ModelViewSet):
    queryset = CardBrand.objects.all().order_by("name")
    serializer_class = CardBrandSerializer
    from django_filters.rest_framework import DjangoFilterBackend
    from rest_framework import filters as drf_filters
    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter, drf_filters.OrderingFilter]
    filterset_fields = {"active": ["exact"], "created_at": ["gte", "lte"], "updated_at": ["gte", "lte"]}
    search_fields = ["name"]
    ordering_fields = ["name", "created_at", "updated_at"]


@extend_schema_view(
    list=extend_schema(tags=["payment"], summary="Listar taxas de bandeira"),
    retrieve=extend_schema(tags=["payment"], summary="Detalhar taxa"),
    create=extend_schema(tags=["payment"], summary="Criar taxa"),
    update=extend_schema(tags=["payment"], summary="Atualizar taxa"),
    partial_update=extend_schema(tags=["payment"], summary="Atualização parcial de taxa"),
    destroy=extend_schema(tags=["payment"], summary="Excluir taxa"),
)
class CardFeeTierViewSet(viewsets.ModelViewSet):
    queryset = CardFeeTier.objects.select_related("brand").all().order_by("brand__name", "type", "installments_min")
    serializer_class = CardFeeTierSerializer
    from django_filters.rest_framework import DjangoFilterBackend
    from rest_framework import filters as drf_filters
    filter_backends = [DjangoFilterBackend, drf_filters.OrderingFilter]
    filterset_fields = {"brand": ["exact"], "type": ["exact"], "created_at": ["gte", "lte"], "updated_at": ["gte", "lte"]}
    ordering_fields = ["installments_min", "installments_max", "created_at", "updated_at"]
