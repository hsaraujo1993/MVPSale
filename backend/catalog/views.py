from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend

from .models import Category, Brand, Product, Promotion
from .serializers import (
    CategorySerializer,
    BrandSerializer,
    ProductSerializer,
    PromotionSerializer,
)
from drf_spectacular.utils import extend_schema_view, extend_schema


@extend_schema_view(
    list=extend_schema(tags=["catalog"], summary="Listar categorias"),
    retrieve=extend_schema(tags=["catalog"], summary="Detalhar categoria"),
    create=extend_schema(tags=["catalog"], summary="Criar categoria"),
    update=extend_schema(tags=["catalog"], summary="Atualizar categoria"),
    partial_update=extend_schema(tags=["catalog"], summary="Atualização parcial de categoria"),
    destroy=extend_schema(tags=["catalog"], summary="Excluir categoria"),
)
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by("name")
    serializer_class = CategorySerializer
    lookup_field = "uuid"
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        "active": ["exact"],
        "created_at": ["gte", "lte"],
        "updated_at": ["gte", "lte"],
    }
    search_fields = ["name", "slug"]
    ordering_fields = ["name", "created_at", "updated_at"]


@extend_schema_view(
    list=extend_schema(tags=["catalog"], summary="Listar marcas"),
    retrieve=extend_schema(tags=["catalog"], summary="Detalhar marca"),
    create=extend_schema(tags=["catalog"], summary="Criar marca"),
    update=extend_schema(tags=["catalog"], summary="Atualizar marca"),
    partial_update=extend_schema(tags=["catalog"], summary="Atualização parcial de marca"),
    destroy=extend_schema(tags=["catalog"], summary="Excluir marca"),
)
class BrandViewSet(viewsets.ModelViewSet):
    queryset = Brand.objects.all().order_by("name")
    serializer_class = BrandSerializer
    lookup_field = "uuid"
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        "active": ["exact"],
        "created_at": ["gte", "lte"],
        "updated_at": ["gte", "lte"],
    }
    search_fields = ["name"]
    ordering_fields = ["name", "created_at", "updated_at"]


@extend_schema_view(
    list=extend_schema(tags=["catalog"], summary="Listar produtos"),
    retrieve=extend_schema(tags=["catalog"], summary="Detalhar produto"),
    create=extend_schema(tags=["catalog"], summary="Criar produto"),
    update=extend_schema(tags=["catalog"], summary="Atualizar produto"),
    partial_update=extend_schema(tags=["catalog"], summary="Atualização parcial de produto"),
    destroy=extend_schema(tags=["catalog"], summary="Excluir produto"),
)
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related("category", "brand").all().order_by("name")
    serializer_class = ProductSerializer
    lookup_field = "uuid"
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {"brand": ["exact"], "category": ["exact"], "active": ["exact"], "created_at": ["gte", "lte"], "updated_at": ["gte", "lte"]}
    search_fields = ["name", "description", "sku", "barcode"]
    ordering_fields = ["name", "sale_price", "created_at", "updated_at"]


@extend_schema_view(
    list=extend_schema(tags=["catalog"], summary="Listar promoções"),
    retrieve=extend_schema(tags=["catalog"], summary="Detalhar promoção"),
    create=extend_schema(tags=["catalog"], summary="Criar promoção"),
    update=extend_schema(tags=["catalog"], summary="Atualizar promoção"),
    partial_update=extend_schema(tags=["catalog"], summary="Atualização parcial de promoção"),
    destroy=extend_schema(tags=["catalog"], summary="Excluir promoção"),
)
class PromotionViewSet(viewsets.ModelViewSet):
    queryset = Promotion.objects.select_related("product").all().order_by("-created_at")
    serializer_class = PromotionSerializer
    lookup_field = "uuid"
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = {"product": ["exact"], "active": ["exact"], "start_date": ["gte", "lte"], "end_date": ["gte", "lte"], "created_at": ["gte", "lte"]}
    ordering_fields = ["created_at", "updated_at", "start_date", "end_date"]
