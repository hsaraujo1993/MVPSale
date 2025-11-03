import datetime
from django.core.management.base import BaseCommand
from purchase.models import PurchaseInstallment


class Command(BaseCommand):
    help = "Reprocessa parcelas, marcando como ATRASADO se vencidas e pendentes"

    def add_arguments(self, parser):
        parser.add_argument("--date", dest="date", help="Data de referência YYYY-MM-DD (opcional)")

    def handle(self, *args, **options):
        ref_str = options.get("date")
        if ref_str:
            try:
                ref_date = datetime.date.fromisoformat(ref_str)
            except Exception:
                self.stderr.write(self.style.ERROR("Data inválida. Use YYYY-MM-DD."))
                return
        else:
            ref_date = datetime.date.today()

        qs = PurchaseInstallment.objects.filter(status="PENDENTE", due_date__lt=ref_date)
        count = qs.update(status="ATRASADO")
        self.stdout.write(self.style.SUCCESS(f"Parcelas marcadas ATRASADO: {count}"))

