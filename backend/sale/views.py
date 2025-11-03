from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema_view, extend_schema

from .models import Order, OrderItem, confirm_order, cancel_order
from .serializers import OrderSerializer, OrderItemSerializer, AddItemSerializer, OrderActionSerializer


@extend_schema_view(
    list=extend_schema(tags=["sale"], summary="Listar pedidos"),
    retrieve=extend_schema(tags=["sale"], summary="Detalhar pedido"),
    create=extend_schema(tags=["sale"], summary="Criar pedido"),
)
class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.select_related("seller", "customer").all().order_by("-created_at")
    serializer_class = OrderSerializer
    lookup_field = "uuid"
    from rest_framework import filters as drf_filters
    from django_filters.rest_framework import DjangoFilterBackend
    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter, drf_filters.OrderingFilter]
    filterset_fields = {"status": ["exact"], "seller": ["exact"], "customer": ["exact"], "created_at": ["gte", "lte"], "updated_at": ["gte", "lte"]}
    search_fields = ["uuid"]
    ordering_fields = ["created_at", "updated_at", "total"]

    @extend_schema(responses={200: OrderItemSerializer(many=True)}, tags=["sale"], summary="Listar itens do pedido")
    @action(detail=True, methods=["get"], url_path="items")
    def list_items(self, request, *args, **kwargs):
        order = self.get_object()
        qs = order.items.all().order_by("-created_at")
        return Response(OrderItemSerializer(qs, many=True).data)

    @extend_schema(request=AddItemSerializer, responses={201: OrderItemSerializer}, tags=["sale"], summary="Adicionar item")
    @action(detail=True, methods=["post"], url_path="add-item")
    def add_item(self, request, *args, **kwargs):
        order = self.get_object()
        if order.status != "DRAFT":
            return Response({"detail": "Pedido não está em rascunho."}, status=status.HTTP_400_BAD_REQUEST)
        ser = AddItemSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        item = OrderItem(
            order=order,
            product=ser.validated_data["product"],
            quantity=ser.validated_data["quantity"],
            unit_price=ser.validated_data["unit_price"],
            discount_percent=ser.validated_data.get("discount_percent", 0),
        )
        item.save()
        return Response(OrderItemSerializer(item).data, status=status.HTTP_201_CREATED)

    @extend_schema(request=OrderItemSerializer, responses={200: OrderItemSerializer}, tags=["sale"], summary="Obter/atualizar/excluir item do pedido")
    @action(detail=True, methods=["get", "patch", "put", "delete"], url_path=r"items/(?P<item_id>[^/.]+)")
    def item(self, request, *args, **kwargs):
        order = self.get_object()
        try:
            item_id = kwargs.get("item_id")
            item = order.items.get(uuid=item_id)
        except OrderItem.DoesNotExist:
            if request.method.lower() == "delete":
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response({"detail": "Item nao encontrado"}, status=status.HTTP_404_NOT_FOUND)
        if order.status != "DRAFT" and request.method.lower() in {"patch", "put", "delete"}:
            return Response({"detail": "Pedido nao esta em rascunho."}, status=status.HTTP_400_BAD_REQUEST)
        if request.method.lower() == "get":
            return Response(OrderItemSerializer(item).data)
        if request.method.lower() in {"patch", "put"}:
            partial = request.method.lower() == "patch"
            ser = OrderItemSerializer(item, data=request.data, partial=partial)
            ser.is_valid(raise_exception=True)
            ser.save()
            return Response(ser.data)
        # delete
        item.delete()
        order.recalc_totals()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(request=OrderActionSerializer, tags=["sale"], summary="Confirmar ou cancelar pedido")
    @action(detail=True, methods=["post"], url_path="action")
    def perform_action(self, request, *args, **kwargs):
        order = self.get_object()
        action_name = request.data.get("action")
        if action_name == "confirm":
            from django.core.exceptions import ValidationError
            try:
                confirm_order(order)
            except ValidationError as e:
                return Response({"detail": e.messages[0] if hasattr(e, 'messages') else str(e)}, status=status.HTTP_400_BAD_REQUEST)
        elif action_name == "cancel":
            cancel_order(order)
        else:
            return Response({"detail": "Ação inválida."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(OrderSerializer(order).data)
