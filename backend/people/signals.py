from django.contrib.auth.models import Group
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Seller


@receiver(post_save, sender=Seller)
def ensure_seller_group(sender, instance: Seller, created, **kwargs):
    try:
        group = Group.objects.get(name=instance.access_level)
    except Group.DoesNotExist:
        return
    user = instance.user
    # Remove from other seller groups to avoid conflicts
    for name in ["total", "leitura", "desconto", "fechamento"]:
        try:
            g = Group.objects.get(name=name)
            user.groups.remove(g)
        except Group.DoesNotExist:
            continue
    user.groups.add(group)
    user.save(update_fields=[])

