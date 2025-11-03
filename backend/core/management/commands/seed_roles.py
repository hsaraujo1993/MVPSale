from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group


ROLES = [
    "total",
    "leitura",
    "desconto",
    "fechamento",
]


class Command(BaseCommand):
    help = "Create initial roles/groups for the system"

    def handle(self, *args, **options):
        created = 0
        for name in ROLES:
            obj, was_created = Group.objects.get_or_create(name=name)
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f"Seeded roles. New groups created: {created}"))

