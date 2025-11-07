from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from decimal import Decimal

from catalog.models import Category, Brand, Product


class Command(BaseCommand):
    help = "Cria dados de demonstração para a tela de Revisão de Preço e imprime evidências"

    def handle(self, *args, **options):
        User = get_user_model()

        cat, _ = Category.objects.get_or_create(name="Demo Categoria")
        brand, _ = Brand.objects.get_or_create(name="Demo Marca")

        # Produto 1: Δ Preço (sale_price propositalmente diferente do sugerido)
        p1, created = Product.objects.get_or_create(
            sku="DEMO-PRICE", defaults=dict(
                name="Produto Delta Preco",
                category=cat,
                brand=brand,
                cost_price=Decimal("100.00"),
                margin=Decimal("30.00"),
                sale_price=Decimal("0.00"),  # será recalculado no save()
                last_cost_price=Decimal("100.00"),
                avg_cost_price=Decimal("80.00"),
                active=True,
            )
        )
        if not created:
            # Atualiza base de custo/margem
            p1.name = "Produto Delta Preco"
            p1.cost_price = Decimal("100.00")
            p1.margin = Decimal("30.00")
            p1.last_cost_price = Decimal("100.00")
            p1.avg_cost_price = Decimal("80.00")
            p1.active = True
            p1.save()
        # Após o save, sale_price = 130.00; força divergência para evidência de Δ Preço
        Product.objects.filter(pk=p1.pk).update(sale_price=Decimal("120.00"))
        p1.refresh_from_db()

        # Produto 2: Δ Custo (last_cost != avg_cost)
        p2, created = Product.objects.get_or_create(
            sku="DEMO-COST", defaults=dict(
                name="Produto Delta Custo",
                category=cat,
                brand=brand,
                cost_price=Decimal("100.00"),
                margin=Decimal("20.00"),
                sale_price=Decimal("0.00"),
                last_cost_price=Decimal("120.00"),
                avg_cost_price=Decimal("100.00"),
                active=True,
            )
        )
        if not created:
            p2.name = "Produto Delta Custo"
            p2.cost_price = Decimal("100.00")
            p2.margin = Decimal("20.00")
            p2.last_cost_price = Decimal("120.00")
            p2.avg_cost_price = Decimal("100.00")
            p2.active = True
            p2.save()

        # Produto 3: Revisão manual (needs_review=True)
        p3, created = Product.objects.get_or_create(
            sku="DEMO-MANUAL", defaults=dict(
                name="Produto Revisão Manual",
                category=cat,
                brand=brand,
                cost_price=Decimal("50.00"),
                margin=Decimal("0.00"),
                sale_price=Decimal("0.00"),
                last_cost_price=Decimal("50.00"),
                avg_cost_price=Decimal("50.00"),
                active=True,
            )
        )
        # Marca manualmente como pendente
        Product.objects.filter(pk=p3.pk).update(needs_review=True)
        p3.refresh_from_db()

        # Evidências: calcula os diffs como feito no endpoint
        def _pricing_cost(prod):
            # Base padrão: 'last' (ver settings)
            return Decimal(str(prod.last_cost_price or prod.cost_price))

        def _suggested(prod):
            cost = _pricing_cost(prod)
            margin = Decimal(str(prod.margin or 0))
            if margin == 0:
                return Decimal("0.00")
            return (cost + cost * (margin / Decimal("100"))).quantize(Decimal("0.01"))

        def _pct(a, b):
            if b in (None, 0, Decimal("0")):
                return None
            return (Decimal(str(a)) - Decimal(str(b))) / Decimal(str(b))

        data = []
        for prod in (p1, p2, p3):
            suggested = _suggested(prod)
            price_diff = _pct(suggested, prod.sale_price)
            cost_diff = None
            if prod.last_cost_price is not None and prod.avg_cost_price not in (None, Decimal("0")):
                cost_diff = _pct(prod.last_cost_price, prod.avg_cost_price)
            data.append(dict(
                sku=prod.sku,
                name=prod.name,
                pricing_cost=str(_pricing_cost(prod)),
                margin=str(prod.margin),
                sale_price=str(prod.sale_price),
                suggested_sale_price=str(suggested),
                price_diff_pct=f"{(price_diff*100):.1f}%" if price_diff is not None else None,
                cost_diff_pct=f"{(cost_diff*100):.1f}%" if cost_diff is not None else None,
                needs_review=prod.needs_review,
            ))

        self.stdout.write(self.style.SUCCESS("Evidências locais (cálculo direto):"))
        for item in data:
            self.stdout.write(str(item))

        # Evidências via endpoint (sem servidor): usa APIClient com JWT
        try:
            from rest_framework.test import APIClient

            user, _ = User.objects.get_or_create(username="demo")
            user.set_password("demo1234")
            user.is_staff = True
            user.save()

            client = APIClient()
            token_resp = client.post("/api/token/", {"username": "demo", "password": "demo1234"}, format="json")
            access = token_resp.json().get("access")
            client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
            resp = client.get("/api/v1/catalog/products/price-review/?ordering=-price_diff_pct&page_size=5")
            self.stdout.write(self.style.SUCCESS("\nEvidências via endpoint /api/v1/catalog/products/price-review/:"))
            self.stdout.write(f"status={resp.status_code}")
            self.stdout.write(str(resp.json()))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Falha ao chamar endpoint de evidência: {e}"))
