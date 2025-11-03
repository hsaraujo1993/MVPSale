from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from .serializers import NFeImportSerializer, PurchaseInvoiceSerializer
from .services.nfe_import import import_nfe_xml
from .models import PurchaseInstallment, PurchaseInvoice
import datetime
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncMonth


class NFeImportView(APIView):
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    @extend_schema(request=NFeImportSerializer, responses={200: None}, tags=["purchase"], summary="Importar XML de NFe")
    def post(self, request):
        xml_text = request.data.get("xml_text")
        if not xml_text and "xml" in request.FILES:
            xml_file = request.FILES["xml"]
            xml_text = xml_file.read().decode("utf-8", errors="ignore")
        if not xml_text:
            return Response({"detail": "Informe xml_text ou arquivo xml."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = import_nfe_xml(xml_text)
            return Response({"status": "ok", **result}, status=status.HTTP_201_CREATED)
        except Exception as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


class ReprocessInstallmentsView(APIView):
    @extend_schema(tags=["purchase"], summary="Reprocessar parcelas para marcar atrasos")
    def post(self, request):
        ref = request.data.get("date")
        try:
            ref_date = datetime.date.fromisoformat(ref) if ref else datetime.date.today()
        except Exception:
            return Response({"detail": "Data inválida. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

        qs = PurchaseInstallment.objects.filter(status="PENDENTE", due_date__lt=ref_date)
        count = qs.update(status="ATRASADO")
        return Response({"updated": count, "reference_date": str(ref_date)}, status=status.HTTP_200_OK)


class InstallmentSummaryView(APIView):
    @extend_schema(tags=["purchase"], summary="Resumo de parcelas por status e por fornecedor")
    def get(self, request):
        supplier_id = request.query_params.get("supplier")
        ref = request.query_params.get("date")
        try:
            ref_date = datetime.date.fromisoformat(ref) if ref else datetime.date.today()
        except Exception:
            return Response({"detail": "Data inválida. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

        qs = PurchaseInstallment.objects.select_related("invoice", "invoice__supplier")
        if supplier_id:
            qs = qs.filter(invoice__supplier_id=supplier_id)

        # Totais gerais
        agg = qs.aggregate(total_value=Sum("value"))
        total_value = agg.get("total_value") or 0
        total_count = qs.count()

        # Por status
        by_status_qs = qs.values("status").annotate(count=Count("id"), total_value=Sum("value")).order_by("status")
        by_status = {row["status"]: {"count": row["count"], "value": row["total_value"] or 0} for row in by_status_qs}

        # Em atraso
        overdue = qs.filter(due_date__lt=ref_date).aggregate(count=Count("id"), value=Sum("value"))
        overdue_count = overdue.get("count") or 0
        overdue_value = overdue.get("value") or 0

        # Por fornecedor (se não filtrado)
        suppliers = []
        supplier_group_qs = (
            qs.values("invoice__supplier_id", "invoice__supplier__corporate_name")
            .annotate(
                count=Count("id"),
                total_value=Sum("value"),
                overdue_count=Count("id", filter=Q(due_date__lt=ref_date)),
                overdue_value=Sum("value", filter=Q(due_date__lt=ref_date)),
            )
            .order_by("invoice__supplier__corporate_name")
        )
        for row in supplier_group_qs:
            suppliers.append(
                {
                    "supplier_id": row["invoice__supplier_id"],
                    "supplier_name": row["invoice__supplier__corporate_name"],
                    "count": row["count"],
                    "value": row["total_value"] or 0,
                    "overdue_count": row["overdue_count"] or 0,
                    "overdue_value": row["overdue_value"] or 0,
                }
            )

        # Upcoming windows (pending only)
        in_7 = qs.filter(status="PENDENTE", due_date__gte=ref_date, due_date__lte=ref_date + datetime.timedelta(days=7)).aggregate(
            count=Count("id"), value=Sum("value")
        )
        in_30 = qs.filter(status="PENDENTE", due_date__gt=ref_date + datetime.timedelta(days=7), due_date__lte=ref_date + datetime.timedelta(days=30)).aggregate(
            count=Count("id"), value=Sum("value")
        )

        # Overdue aging buckets by due_date
        overdue_1_7 = qs.filter(due_date__lt=ref_date, due_date__gte=ref_date - datetime.timedelta(days=7)).aggregate(
            count=Count("id"), value=Sum("value")
        )
        overdue_8_30 = qs.filter(due_date__lt=ref_date - datetime.timedelta(days=7), due_date__gte=ref_date - datetime.timedelta(days=30)).aggregate(
            count=Count("id"), value=Sum("value")
        )
        overdue_gt_30 = qs.filter(due_date__lt=ref_date - datetime.timedelta(days=30)).aggregate(
            count=Count("id"), value=Sum("value")
        )

        # Monthly totals for next 6 months (including current month)
        six_months_ahead = ref_date + datetime.timedelta(days=31 * 6)
        monthly_qs = (
            qs.filter(due_date__gte=ref_date, due_date__lt=six_months_ahead)
            .annotate(month=TruncMonth("due_date"))
            .values("month")
            .annotate(count=Count("id"), value=Sum("value"))
            .order_by("month")
        )
        monthly_next = [
            {"month": row["month"].strftime("%Y-%m"), "count": row["count"], "value": row["value"] or 0}
            for row in monthly_qs
        ]

        return Response(
            {
                "total": {"count": total_count, "value": total_value},
                "by_status": by_status,
                "overdue": {"count": overdue_count, "value": overdue_value},
                "suppliers": suppliers,
                "upcoming": {
                    "7d": {"count": in_7.get("count") or 0, "value": in_7.get("value") or 0},
                    "30d": {"count": in_30.get("count") or 0, "value": in_30.get("value") or 0},
                },
                "overdue_buckets": {
                    "1-7": {"count": overdue_1_7.get("count") or 0, "value": overdue_1_7.get("value") or 0},
                    "8-30": {"count": overdue_8_30.get("count") or 0, "value": overdue_8_30.get("value") or 0},
                    ">30": {"count": overdue_gt_30.get("count") or 0, "value": overdue_gt_30.get("value") or 0},
                },
                "monthly_next": monthly_next,
            }
        )

from rest_framework import viewsets, status
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters as drf_filters
from drf_spectacular.utils import extend_schema_view, extend_schema
from rest_framework.response import Response


@extend_schema_view(
    list=extend_schema(tags=["purchase"], summary="Listar notas de fornecedores"),
    retrieve=extend_schema(tags=["purchase"], summary="Detalhar nota de fornecedor"),
)
class PurchaseInvoiceViewSet(viewsets.ModelViewSet):
    queryset = PurchaseInvoice.objects.select_related('supplier').all().order_by('-created_at')
    serializer_class = PurchaseInvoiceSerializer
    lookup_field = 'uuid'
    http_method_names = ['get', 'delete', 'head', 'options']
    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter, drf_filters.OrderingFilter]
    filterset_fields = {"supplier": ["exact"], "issue_date": ["gte", "lte"], "created_at": ["gte", "lte"]}
    search_fields = ["number", "series", "supplier__corporate_name"]
    ordering_fields = ["created_at", "issue_date", "total_value"]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            from .serializers import PurchaseInvoiceDetailSerializer
            return PurchaseInvoiceDetailSerializer
        return super().get_serializer_class()

    @extend_schema(tags=["purchase"], summary="Detalhar nota de fornecedor")
    def retrieve(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = self.get_serializer(obj)
        data = serializer.data
        try:
            from .services.nfe_import import extract_items
            data = dict(data)
            data["items"] = extract_items(obj.xml)
        except Exception:
            pass
        return Response(data)
