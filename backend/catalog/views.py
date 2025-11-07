from rest_framework import viewsets, filters
import logging
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models.deletion import ProtectedError
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action

from .models import Category, Brand, Product, Promotion
from .serializers import (
    CategorySerializer,
    BrandSerializer,
    ProductSerializer,
    PromotionSerializer,
)
from drf_spectacular.utils import extend_schema_view, extend_schema
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes


@extend_schema_view(
    list=extend_schema(tags=["catalog"], summary="Listar categorias"),
    retrieve=extend_schema(tags=["catalog"], summary="Detalhar categoria"),
    create=extend_schema(tags=["catalog"], summary="Criar categoria"),
    update=extend_schema(tags=["catalog"], summary="Atualizar categoria"),
    partial_update=extend_schema(tags=["catalog"], summary="AtualizaÃ§Ã£o parcial de categoria"),
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

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            self.perform_destroy(instance)
        except ProtectedError as exc:
            blocked = []
            try:
                for obj in exc.protected_objects:
                    blocked.append(
                        {
                            "repr": str(obj),
                            "model": obj._meta.label,
                            "id": getattr(obj, "uuid", getattr(obj, "pk", None)),
                        }
                    )
            except Exception:
                pass
            return Response(
                {
                    "detail": "Cannot delete category because other resources reference it.",
                    "blocked": blocked,
                },
                status=status.HTTP_409_CONFLICT,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    list=extend_schema(tags=["catalog"], summary="Listar marcas"),
    retrieve=extend_schema(tags=["catalog"], summary="Detalhar marca"),
    create=extend_schema(tags=["catalog"], summary="Criar marca"),
    update=extend_schema(tags=["catalog"], summary="Atualizar marca"),
    partial_update=extend_schema(tags=["catalog"], summary="AtualizaÃ§Ã£o parcial de marca"),
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

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            self.perform_destroy(instance)
        except ProtectedError as exc:
            blocked = []
            try:
                for obj in exc.protected_objects:
                    blocked.append(
                        {
                            "repr": str(obj),
                            "model": obj._meta.label,
                            "id": getattr(obj, "uuid", getattr(obj, "pk", None)),
                        }
                    )
            except Exception:
                pass
            return Response(
                {
                    "detail": "Cannot delete brand because other resources reference it.",
                    "blocked": blocked,
                },
                status=status.HTTP_409_CONFLICT,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    list=extend_schema(tags=["catalog"], summary="Listar produtos"),
    retrieve=extend_schema(tags=["catalog"], summary="Detalhar produto"),
    create=extend_schema(tags=["catalog"], summary="Criar produto"),
    update=extend_schema(tags=["catalog"], summary="Atualizar produto"),
    partial_update=extend_schema(tags=["catalog"], summary="AtualizaÃ§Ã£o parcial de produto"),
    destroy=extend_schema(tags=["catalog"], summary="Excluir produto"),
)
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related("category", "brand").all().order_by("name")
    serializer_class = ProductSerializer
    lookup_field = "uuid"
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {"brand": ["exact"], "category": ["exact"], "active": ["exact"], "needs_review": ["exact"], "created_at": ["gte", "lte"], "updated_at": ["gte", "lte"]}
    search_fields = ["name", "description", "sku", "barcode"]
    ordering_fields = ["name", "sale_price", "created_at", "updated_at"]

    @extend_schema(
        tags=["catalog"],
        summary="Itens para revisar preÃ§o",
        parameters=[
            OpenApiParameter(name="threshold", type=OpenApiTypes.NUMBER, required=False, description="Limite percentual (ex.: 0.05 para 5%)"),
            OpenApiParameter(name="limit", type=OpenApiTypes.INT, required=False, description="MÃ¡ximo de itens"),
        ],
    )
    @action(detail=False, methods=["get"], url_path="price-review")
    def price_review(self, request):
        from decimal import Decimal
        from django.conf import settings as s
        from core.pricing import apply_rounding

        try:
            threshold = Decimal(str(request.query_params.get("threshold", s.PRICE_REVIEW_THRESHOLD)))
        except Exception:
            threshold = Decimal(str(getattr(s, "PRICE_REVIEW_THRESHOLD", 0.05)))
        # Paginação e filtros (compatível com lista de produtos)
        try:
            default_page_size = int(getattr(s, "REST_FRAMEWORK", {}).get("PAGE_SIZE", 20))
        except Exception:
            default_page_size = 20
        try:
            page = max(1, int(request.query_params.get("page", 1)))
        except Exception:
            page = 1
        try:
            page_size = int(request.query_params.get("page_size", request.query_params.get("limit", default_page_size)))
            if page_size <= 0:
                page_size = default_page_size
        except Exception:
            page_size = default_page_size
        search = (request.query_params.get("search", "") or "").strip()
        ordering = (request.query_params.get("ordering", "-price_diff_pct") or "").strip()

        results = []
        qs = self.get_queryset()
        basis = getattr(s, "PRICE_COST_BASIS", "last")
        rounding = getattr(s, "PRICE_ROUNDING", "none")
        for p in qs.iterator(chunk_size=500):
            try:
                last_cost = Decimal(str(p.last_cost_price)) if p.last_cost_price is not None else None
                avg_cost = Decimal(str(p.avg_cost_price)) if p.avg_cost_price is not None else None
                # custo efetivo
                if basis == "last" and last_cost is not None:
                    pricing_cost = last_cost
                elif basis == "average" and avg_cost is not None:
                    pricing_cost = avg_cost
                else:
                    pricing_cost = Decimal(str(p.cost_price or 0))

                # preÃ§o sugerido
                margin = Decimal(str(p.margin or 0))
                if margin == 0:
                    suggested = Decimal("0.00")
                else:
                    base = pricing_cost + (pricing_cost * (margin / Decimal("100")))
                    suggested = apply_rounding(base, rounding)

                price_diff_pct = None
                if p.sale_price and p.sale_price != 0:
                    price_diff_pct = (Decimal(str(suggested)) - Decimal(str(p.sale_price))) / Decimal(str(p.sale_price))

                cost_diff_pct = None
                if last_cost is not None and avg_cost is not None and avg_cost != 0:
                    cost_diff_pct = (last_cost - avg_cost) / avg_cost

                # regra de alerta
                flag = False
                if price_diff_pct is not None and abs(price_diff_pct) >= threshold:
                    flag = True
                if not flag and cost_diff_pct is not None and abs(cost_diff_pct) >= threshold:
                    flag = True
                # incluir sempre produtos marcados manualmente ou com preÃ§o/margem zerados
                if not flag and getattr(p, 'needs_review', False):
                    flag = True
                if not flag and (Decimal(str(p.sale_price or 0)) == 0 or Decimal(str(p.margin or 0)) == 0):
                    flag = True
                if not flag:
                    continue

                results.append({
                    "id": p.id,
                    "uuid": str(p.uuid),
                    "name": p.name,
                    "sku": p.sku,
                    "margin": float(Decimal(str(p.margin or 0))),
                    "sale_price": float(Decimal(str(p.sale_price or 0))),
                    "suggested_sale_price": float(Decimal(str(suggested))),
                    "pricing_cost": float(Decimal(str(pricing_cost))),
                    "last_cost_price": float(last_cost) if last_cost is not None else None,
                    "avg_cost_price": float(avg_cost) if avg_cost is not None else None,
                    "price_diff_pct": float(price_diff_pct) if price_diff_pct is not None else None,
                    "cost_diff_pct": float(cost_diff_pct) if cost_diff_pct is not None else None,
                    "basis": basis,
                })
            except Exception:
                # Fallback: incluir item bÃ¡sico se marcado ou sem preÃ§o/margem
                try:
                    from decimal import Decimal as _D
                    minimal_flag = getattr(p, 'needs_review', False) or _D(str(p.margin or 0)) == 0 or _D(str(p.sale_price or 0)) == 0
                except Exception:
                    minimal_flag = True
                if minimal_flag:
                    try:
                        results.append({
                            "id": p.id,
                            "uuid": str(p.uuid),
                            "name": p.name,
                            "sku": p.sku,
                            "margin": None,
                            "sale_price": None,
                            "suggested_sale_price": None,
                            "pricing_cost": None,
                            "last_cost_price": None,
                            "avg_cost_price": None,
                            "price_diff_pct": None,
                            "cost_diff_pct": None,
                            "basis": basis,
                        })
                    except Exception:
                        pass

        # Search filter (name or SKU)
        if search:
            sterm = search.lower()
            results = [r for r in results if (r.get("name") or "").lower().find(sterm) >= 0 or (r.get("sku") or "").lower().find(sterm) >= 0]

        # Ordering
        if ordering:
            reverse = ordering.startswith("-")
            key = ordering[1:] if reverse else ordering
            allowed = {"name", "sku", "sale_price", "suggested_sale_price", "pricing_cost", "price_diff_pct", "cost_diff_pct"}
            if key in allowed:
                def _sort_key(x):
                    v = x.get(key)
                    return (v is None, v)
                results = sorted(results, key=_sort_key, reverse=reverse)

        # Manual pagination (DRF-like)
        total = len(results)
        start = (page - 1) * page_size
        end = start + page_size
        page_items = results[start:end]

        def _build_url(pageno):
            try:
                from urllib.parse import urlencode
                params = request.query_params.copy().dict()
                params["page"] = pageno
                params["page_size"] = page_size
                base = request.build_absolute_uri(request.path)
                return f"{base}?{urlencode(params)}"
            except Exception:
                return None

        next_url = _build_url(page + 1) if end < total else None
        prev_url = _build_url(page - 1) if start > 0 else None

        return Response({
            "count": total,
            "next": next_url,
            "previous": prev_url,
            "results": page_items,
            "threshold": float(threshold),
        })

    @extend_schema(
        tags=["catalog"],
        summary="Marcar produto como revisado",
        parameters=[OpenApiParameter(name="value", type=OpenApiTypes.BOOL, required=False, description="Define a flag needs_review (default False)")],
    )
    @action(detail=True, methods=["patch", "post"], url_path="mark-reviewed")
    def mark_reviewed(self, request, *args, **kwargs):
        product = self.get_object()
        val = request.data.get("value")
        value = False
        if isinstance(val, bool):
            value = val
        elif isinstance(val, str):
            value = val.strip().lower() in ("1", "true", "yes", "y")
        product.needs_review = value
        product.save(update_fields=["needs_review", "updated_at"])
        logger = logging.getLogger("catalog")
        try:
            logger.info("[price_review] product id=%s sku=%s set needs_review=%s", product.id, product.sku, value)
        except Exception:
            pass
        return Response(ProductSerializer(product).data)


@extend_schema_view(
    list=extend_schema(tags=["catalog"], summary="Listar promoÃ§Ãµes"),
    retrieve=extend_schema(tags=["catalog"], summary="Detalhar promoÃ§Ã£o"),
    create=extend_schema(tags=["catalog"], summary="Criar promoÃ§Ã£o"),
    update=extend_schema(tags=["catalog"], summary="Atualizar promoÃ§Ã£o"),
    partial_update=extend_schema(tags=["catalog"], summary="AtualizaÃ§Ã£o parcial de promoÃ§Ã£o"),
    destroy=extend_schema(tags=["catalog"], summary="Excluir promoÃ§Ã£o"),
)
class PromotionViewSet(viewsets.ModelViewSet):
    queryset = Promotion.objects.select_related("product").all().order_by("-created_at")
    serializer_class = PromotionSerializer
    lookup_field = "uuid"
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = {"product": ["exact"], "active": ["exact"], "start_date": ["gte", "lte"], "end_date": ["gte", "lte"], "created_at": ["gte", "lte"]}
    ordering_fields = ["created_at", "updated_at", "start_date", "end_date"]


