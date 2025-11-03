from rest_framework import viewsets, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend

from .models import Customer, Supplier, Seller
from .serializers import CustomerSerializer, SupplierSerializer, SellerSerializer
from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    OpenApiParameter,
    OpenApiExample,
    OpenApiResponse,
)
from drf_spectacular.types import OpenApiTypes


@extend_schema_view(
    list=extend_schema(tags=["people"], summary="Listar clientes"),
    retrieve=extend_schema(tags=["people"], summary="Detalhar cliente"),
    create=extend_schema(tags=["people"], summary="Criar cliente"),
    update=extend_schema(tags=["people"], summary="Atualizar cliente"),
    partial_update=extend_schema(tags=["people"], summary="Atualização parcial de cliente"),
    destroy=extend_schema(tags=["people"], summary="Excluir cliente"),
)
class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all().order_by("name")
    serializer_class = CustomerSerializer
    lookup_field = "uuid"
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {"cpf_cnpj": ["exact"], "city": ["exact"], "uf": ["exact"], "created_at": ["gte", "lte"], "updated_at": ["gte", "lte"]}
    search_fields = ["name", "email", "phone"]
    ordering_fields = ["name", "created_at", "updated_at"]

    def get_permissions(self):
        # Tornar a consulta de CEP pública
        if getattr(self, "action", None) == "cep_lookup":
            return [AllowAny()]
        return super().get_permissions()

    @extend_schema(
        tags=["people"],
        summary="Consultar CEP (Webmania/ViaCEP)",
        description=(
            "Consulta pública de CEP. Disponível sem autenticação em \n"
            "- GET /api/cep/?cep=05426-100 \n"
            "- GET /api/people/cep/?cep=05426-100 \n\n"
            "Exemplo de resposta (200):\\n"
            "{\\n"
            "  \"cep\": \"05426100\",\\n"
            "  \"address\": \"Avenida Brigadeiro Faria Lima\",\\n"
            "  \"neighborhood\": \"Pinheiros\",\\n"
            "  \"city\": \"São Paulo\",\\n"
            "  \"uf\": \"SP\"\\n"
            "}"
        ),
        parameters=[
            OpenApiParameter(
                name="cep",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=True,
                description="CEP a consultar. Pode conter hífen (ex.: 05426-100).",
            )
        ],
        responses={
            200: OpenApiResponse(
                description="Dados do CEP.",
                examples=[
                    OpenApiExample(
                        'Exemplo de sucesso',
                        value={
                            "cep": "05426100",
                            "address": "Avenida Brigadeiro Faria Lima",
                            "neighborhood": "Pinheiros",
                            "city": "São Paulo",
                            "uf": "SP",
                        },
                    )
                ],
            ),
            404: OpenApiResponse(
                description='CEP não encontrado',
                examples=[OpenApiExample('Não encontrado', value={"detail": "CEP não encontrado"})],
            ),
        },
    )
    @action(detail=False, methods=["get"], url_path="cep", permission_classes=[AllowAny])
    def cep_lookup(self, request):
        from .services.cep import fetch_cep, normalize_cep
        cep = request.query_params.get("cep")
        info = fetch_cep(cep)
        if not info:
            return Response({"detail": "CEP não encontrado"}, status=404)
        # Padroniza retorno
        return Response({
            "cep": normalize_cep(info.get("cep")),
            "address": info.get("address"),
            "neighborhood": info.get("neighborhood"),
            "city": info.get("city"),
            "uf": info.get("uf"),
        })


@extend_schema_view(
    list=extend_schema(tags=["people"], summary="Listar fornecedores"),
    retrieve=extend_schema(tags=["people"], summary="Detalhar fornecedor"),
    create=extend_schema(tags=["people"], summary="Criar fornecedor"),
    update=extend_schema(tags=["people"], summary="Atualizar fornecedor"),
    partial_update=extend_schema(tags=["people"], summary="Atualização parcial de fornecedor"),
    destroy=extend_schema(tags=["people"], summary="Excluir fornecedor"),
)
class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all().order_by("corporate_name")
    serializer_class = SupplierSerializer
    lookup_field = "uuid"
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {"cnpj": ["exact"], "city": ["exact"], "uf": ["exact"], "created_at": ["gte", "lte"], "updated_at": ["gte", "lte"]}
    search_fields = ["corporate_name", "email", "phone"]
    ordering_fields = ["corporate_name", "created_at", "updated_at"]


@extend_schema_view(
    list=extend_schema(tags=["people"], summary="Listar vendedores"),
    retrieve=extend_schema(tags=["people"], summary="Detalhar vendedor"),
    create=extend_schema(tags=["people"], summary="Criar vendedor"),
    update=extend_schema(tags=["people"], summary="Atualizar vendedor"),
    partial_update=extend_schema(tags=["people"], summary="Atualização parcial de vendedor"),
    destroy=extend_schema(tags=["people"], summary="Excluir vendedor"),
)
class SellerViewSet(viewsets.ModelViewSet):
    queryset = Seller.objects.select_related("user").all().order_by("name")
    serializer_class = SellerSerializer
    lookup_field = "uuid"
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {"access_level": ["exact"], "user": ["exact"], "created_at": ["gte", "lte"], "updated_at": ["gte", "lte"]}
    search_fields = ["name", "user__username", "user__email"]
    ordering_fields = ["name", "created_at", "updated_at"]

    @extend_schema(tags=["people"], summary="Garantir perfil de vendedor para o usuário atual")
    @action(detail=False, methods=["post"], url_path="ensure-me")
    def ensure_me(self, request):
        user = request.user
        if not user or not user.is_authenticated:
            return Response({"detail": "Autenticação requerida"}, status=401)
        seller, created = Seller.objects.get_or_create(
            user=user,
            defaults={"name": getattr(user, "username", str(user.pk)), "access_level": "desconto", "discount_max": 10},
        )
        return Response(SellerSerializer(seller).data, status=201 if created else 200)

from django.contrib.auth import get_user_model
from rest_framework import viewsets as drf_viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers as drf_serializers


class UserLiteSerializer(drf_serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ["id", "username", "email", "first_name", "last_name"]
        read_only_fields = ["id"]


@extend_schema_view(
    list=extend_schema(tags=["people"], summary="Listar usuários"),
    retrieve=extend_schema(tags=["people"], summary="Detalhar usuário"),
)
class UserViewSet(drf_viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        return get_user_model().objects.filter(is_superuser=False).order_by("username")
    serializer_class = UserLiteSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["patch"], url_path="me")
    def update_me(self, request):
        user = request.user
        if not user or not user.is_authenticated:
            return Response({"detail": "Autenticação requerida"}, status=401)
        data = request.data or {}
        allowed = {"first_name", "last_name", "email"}
        for field in allowed:
            if field in data:
                setattr(user, field, data.get(field))
        try:
            user.full_clean()
            user.save()
        except Exception as e:
            return Response({"detail": str(e)}, status=400)
        return Response(UserLiteSerializer(user).data)
