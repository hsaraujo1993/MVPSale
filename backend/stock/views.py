from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema_view, extend_schema

from .models import Stock, StockMovement
from .serializers import StockSerializer, StockMovementSerializer


@extend_schema_view(
    list=extend_schema(tags=["stock"], summary="Listar estoque"),
    retrieve=extend_schema(tags=["stock"], summary="Detalhar estoque de produto"),
    update=extend_schema(tags=["stock"], summary="Atualizar mínimo/máximo"),
    partial_update=extend_schema(tags=["stock"], summary="Atualização parcial"),
)
class StockViewSet(viewsets.ModelViewSet):
    queryset = Stock.objects.select_related("product").all().order_by("-updated_at")
    serializer_class = StockSerializer
    lookup_field = "uuid"
    from rest_framework import filters as drf_filters
    filter_backends = [DjangoFilterBackend, drf_filters.OrderingFilter]
    filterset_fields = {"product": ["exact"], "product__uuid": ["exact"], "status": ["exact"], "created_at": ["gte", "lte"], "updated_at": ["gte", "lte"]}
    ordering_fields = ["updated_at", "created_at", "quantity_current"]


@extend_schema_view(
    list=extend_schema(tags=["stock"], summary="Listar movimentações"),
    create=extend_schema(tags=["stock"], summary="Criar movimentação de estoque"),
)
class StockMovementViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = StockMovement.objects.select_related("product").all().order_by("-created_at")
    serializer_class = StockMovementSerializer
    from rest_framework import filters as drf_filters
    filter_backends = [DjangoFilterBackend, drf_filters.OrderingFilter]
    filterset_fields = {"product": ["exact"], "type": ["exact"], "created_at": ["gte", "lte"]}
    ordering_fields = ["created_at", "quantity"]
