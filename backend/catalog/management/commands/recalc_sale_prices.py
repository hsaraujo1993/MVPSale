from decimal import Decimal, ROUND_HALF_UP
from django.core.management.base import BaseCommand
from catalog.models import Product
from core.pricing import apply_rounding


class Command(BaseCommand):
    help = (
        "Recalcula o sale_price dos produtos. Por padrão, ajusta apenas os com margin=0 para sale_price=0. "
        "Use --all para recalcular todos com base em cost_price e margin."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--all",
            action="store_true",
            dest="all",
            help="Recalcular sale_price de todos os produtos (não apenas margin=0)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry",
            help="Apenas exibe o que seria alterado, sem salvar",
        )

    def handle(self, *args, **options):
        do_all = options.get("all")
        dry = options.get("dry")
        updated = 0

        if not do_all:
            qs = Product.objects.filter(margin=0).exclude(sale_price=0)
            total = qs.count()
            self.stdout.write(f"Encontrados {total} produtos com margin=0 e sale_price != 0")
            if not dry:
                updated = qs.update(sale_price=Decimal("0.00"))
                self.stdout.write(f"Atualizados {updated} produtos para sale_price=0")
            else:
                for p in qs.values("id", "uuid", "name", "sale_price")[:50]:
                    self.stdout.write(f"DRY-RUN id={p['id']} name={p['name']} sale_price_atual={p['sale_price']} -> 0.00")
                self.stdout.write("(Exibidos no máximo 50 itens em dry-run)")
            return

        # --all: recalcular todos com base na BASE DE CUSTO configurada (PRICE_COST_BASIS) + margin
        qs = Product.objects.all()
        total = qs.count()
        self.stdout.write(f"Recalculando sale_price de {total} produtos (--all)")
        from django.conf import settings as dj_settings
        basis = getattr(dj_settings, "PRICE_COST_BASIS", "last")
        for p in qs.iterator(chunk_size=500):
            # Seleciona a base de custo
            if basis == "last" and getattr(p, "last_cost_price", None) is not None:
                cost = Decimal(str(p.last_cost_price))
            elif basis == "average" and getattr(p, "avg_cost_price", None) is not None:
                cost = Decimal(str(p.avg_cost_price))
            else:
                cost = Decimal(str(p.cost_price or 0))
            margin = Decimal(str(p.margin or 0))
            if margin == 0:
                new_sale = Decimal("0.00")
            else:
                base = cost + (cost * (margin / Decimal("100")))
                from django.conf import settings as s
                new_sale = apply_rounding(Decimal(base), getattr(s, "PRICE_ROUNDING", "none"))
            if new_sale != p.sale_price:
                if not dry:
                    p.sale_price = new_sale
                    # Evita disparar clean() completo; apenas persiste o novo preço
                    p.save(update_fields=["sale_price", "updated_at"])  # save() já recalcula, mas confirmamos o valor
                updated += 1
        self.stdout.write(f"Produtos atualizados (ou que seriam, em dry-run): {updated}")
