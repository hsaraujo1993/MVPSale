from decimal import Decimal
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema_view, extend_schema

from .models import CashierSession, CashMovement
from .serializers import (
    CashierSessionSerializer,
    OpenSessionSerializer,
    CloseSessionSerializer,
    CashMovementSerializer,
)


def get_open_session() -> CashierSession | None:
    return CashierSession.objects.filter(status="OPEN").order_by("-opened_at").first()


@extend_schema_view(
    list=extend_schema(tags=["cashier"], summary="Listar sessões de caixa"),
    retrieve=extend_schema(tags=["cashier"], summary="Detalhar sessão"),
)
class CashierSessionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CashierSession.objects.all().order_by("-opened_at")
    serializer_class = CashierSessionSerializer
    lookup_field = "uuid"

    @extend_schema(request=OpenSessionSerializer, tags=["cashier"], summary="Abrir caixa")
    @action(detail=False, methods=["post"], url_path="open")
    def open(self, request):
        if get_open_session():
            return Response({"detail": "Já existe um caixa aberto."}, status=status.HTTP_400_BAD_REQUEST)
        ser = OpenSessionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        sess = CashierSession.objects.create(
            opened_by=request.user,
            opening_amount=ser.validated_data.get("opening_amount") or Decimal("0.00"),
            expected_amount=ser.validated_data.get("opening_amount") or Decimal("0.00"),
            notes=ser.validated_data.get("notes") or "",
        )
        return Response(CashierSessionSerializer(sess).data, status=status.HTTP_201_CREATED)

    @extend_schema(request=CloseSessionSerializer, tags=["cashier"], summary="Fechar caixa")
    @action(detail=True, methods=["post"], url_path="close")
    def close(self, request, pk=None):
        try:
            sess = CashierSession.objects.get(uuid=pk)
        except CashierSession.DoesNotExist:
            return Response({"detail": "Sessão não encontrada."}, status=status.HTTP_404_NOT_FOUND)
        if sess.status != "OPEN":
            return Response({"detail": "Sessão já está fechada."}, status=status.HTTP_400_BAD_REQUEST)
        ser = CloseSessionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        sess.closing_amount = ser.validated_data["closing_amount"]
        sess.difference = (sess.closing_amount or Decimal("0.00")) - (sess.expected_amount or Decimal("0.00"))
        sess.closed_by = request.user
        sess.closed_at = timezone.now()
        sess.status = "CLOSED"
        if ser.validated_data.get("notes"):
            sess.notes = ser.validated_data.get("notes")
        sess.save()
        return Response(CashierSessionSerializer(sess).data)

    @extend_schema(tags=["cashier"], summary="Sessão aberta atual")
    @action(detail=False, methods=["get"], url_path="current")
    def current(self, request):
        sess = get_open_session()
        if not sess:
            return Response({"detail": "Nenhum caixa aberto."}, status=status.HTTP_404_NOT_FOUND)
        return Response(CashierSessionSerializer(sess).data)

    @extend_schema(tags=["cashier"], summary="Resumo da sessão aberta atual")
    @action(detail=False, methods=["get"], url_path="current/summary")
    def current_summary(self, request):
        from django.db.models import Sum
        sess = get_open_session()
        if not sess:
            return Response({"detail": "Nenhum caixa aberto."}, status=status.HTTP_404_NOT_FOUND)
        inflow_qs = sess.movements.filter(type="INFLOW")
        outflow_qs = sess.movements.filter(type="OUTFLOW")
        inflow = inflow_qs.aggregate(total=Sum("amount")).get("total") or Decimal("0.00")
        outflow = outflow_qs.aggregate(total=Sum("amount")).get("total") or Decimal("0.00")
        expected = (sess.opening_amount or Decimal("0.00")) + inflow - outflow
        q = Decimal("0.00")
        inflow_s = str(inflow.quantize(Decimal("0.00")))
        outflow_s = str(outflow.quantize(Decimal("0.00")))
        expected_s = str(expected.quantize(Decimal("0.00")))
        # Breakdown by reason
        by_reason = {}
        br_qs = sess.movements.values("reason", "type").annotate(total=Sum("amount"))
        for row in br_qs:
            reason = row["reason"] or "(sem motivo)"
            if reason not in by_reason:
                by_reason[reason] = {"inflow": "0.00", "outflow": "0.00"}
            val = Decimal(row["total"]).quantize(Decimal("0.00"))
            if row["type"] == "INFLOW":
                by_reason[reason]["inflow"] = str(val)
            else:
                by_reason[reason]["outflow"] = str(val)
        return Response({
            "session_id": sess.id,
            "opened_at": sess.opened_at,
            "opened_by": sess.opened_by_id,
            "opening_amount": str((sess.opening_amount or Decimal("0.00")).quantize(Decimal("0.00"))),
            "inflow_total": inflow_s,
            "inflow_count": inflow_qs.count(),
            "outflow_total": outflow_s,
            "outflow_count": outflow_qs.count(),
            "expected_amount": expected_s,
            "balance": expected_s,
            "movements_count": sess.movements.count(),
            "by_reason": by_reason,
            "by_type": {
                "INFLOW": {"count": inflow_qs.count(), "total": inflow_s},
                "OUTFLOW": {"count": outflow_qs.count(), "total": outflow_s},
            },
        })

    @extend_schema(tags=["cashier"], summary="Resumo das últimas sessões fechadas")
    @action(detail=False, methods=["get"], url_path="history/summary")
    def history_summary(self, request):
        from django.db.models import Sum
        try:
            limit = int(request.query_params.get("limit", 5))
        except ValueError:
            limit = 5
        sessions = CashierSession.objects.filter(status="CLOSED")
        # Filters by user and date
        user_id = request.query_params.get("user") or request.query_params.get("opened_by")
        if user_id:
            try:
                uid = int(user_id)
                sessions = sessions.filter(opened_by_id=uid)
            except ValueError:
                pass
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        from datetime import datetime, timedelta
        if date_from:
            try:
                sessions = sessions.filter(closed_at__date__gte=datetime.fromisoformat(date_from).date())
            except Exception:
                pass
        if date_to:
            try:
                sessions = sessions.filter(closed_at__date__lte=datetime.fromisoformat(date_to).date())
            except Exception:
                pass
        sessions = sessions.order_by("-closed_at")[:limit]
        data = []
        for sess in sessions:
            inflow = sess.movements.filter(type="INFLOW").aggregate(total=Sum("amount")).get("total") or Decimal("0.00")
            outflow = sess.movements.filter(type="OUTFLOW").aggregate(total=Sum("amount")).get("total") or Decimal("0.00")
            expected = (sess.opening_amount or Decimal("0.00")) + inflow - outflow
            data.append({
                "session_id": sess.id,
                "opened_at": sess.opened_at,
                "closed_at": sess.closed_at,
                "opening_amount": str((sess.opening_amount or Decimal("0.00")).quantize(Decimal("0.00"))),
                "inflow_total": str(Decimal(inflow).quantize(Decimal("0.00"))),
                "outflow_total": str(Decimal(outflow).quantize(Decimal("0.00"))),
                "expected_amount": str(Decimal(expected).quantize(Decimal("0.00"))),
                "closing_amount": str((sess.closing_amount or Decimal("0.00")).quantize(Decimal("0.00"))) if sess.closing_amount is not None else None,
                "difference": str((sess.difference or Decimal("0.00")).quantize(Decimal("0.00"))),
            })
        return Response({"sessions": data, "count": len(data)})


@extend_schema_view(
    list=extend_schema(tags=["cashier"], summary="Listar movimentos"),
    create=extend_schema(tags=["cashier"], summary="Criar movimento"),
)
class CashMovementViewSet(viewsets.ModelViewSet):
    queryset = CashMovement.objects.select_related("session").all().order_by("-created_at")
    serializer_class = CashMovementSerializer
    lookup_field = "uuid"

    def get_queryset(self):
        qs = super().get_queryset()
        qp = getattr(self, "request", None).query_params if getattr(self, "request", None) else {}
        mv_type = qp.get("type")
        if mv_type in ("INFLOW", "OUTFLOW"):
            qs = qs.filter(type=mv_type)
        reason = qp.get("reason")
        if reason:
            qs = qs.filter(reason__icontains=reason)
        # Optional date filters
        date_from = qp.get("date_from")
        date_to = qp.get("date_to")
        from datetime import datetime
        if date_from:
            try:
                qs = qs.filter(created_at__date__gte=datetime.fromisoformat(date_from).date())
            except Exception:
                pass
        if date_to:
            try:
                qs = qs.filter(created_at__date__lte=datetime.fromisoformat(date_to).date())
            except Exception:
                pass
        # Ordering
        order_by = qp.get("order_by", "created_at")
        if order_by not in ("created_at", "amount"):
            order_by = "created_at"
        order_dir = qp.get("order", "desc").lower()
        prefix = "-" if order_dir != "asc" else ""
        qs = qs.order_by(f"{prefix}{order_by}")
        return qs

    def create(self, request, *args, **kwargs):
        # Default to current open session if not specified
        data = request.data.copy()
        if not data.get("session"):
            sess = get_open_session()
            if not sess:
                return Response({"detail": "Nenhum caixa aberto."}, status=status.HTTP_400_BAD_REQUEST)
            data["session"] = sess.id
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        # Update expected amount on session
        sess = CashierSession.objects.get(pk=serializer.data["session"]) if isinstance(serializer.data["session"], int) else None
        if not sess:
            sess = get_open_session()
        if sess:
            inflow = Decimal("0.00")
            outflow = Decimal("0.00")
            for mv in sess.movements.all():
                if mv.type == "INFLOW":
                    inflow += mv.amount
                else:
                    outflow += mv.amount
            sess.expected_amount = (sess.opening_amount or Decimal("0.00")) + inflow - outflow
            sess.save(update_fields=["expected_amount", "updated_at"])
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

