from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("purchase", "0003_purchaseinstallment_uuid_purchaseinvoice_uuid_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="supplierproduct",
            name="last_cost",
            field=models.DecimalField(null=True, blank=True, max_digits=12, decimal_places=2),
        ),
        migrations.AddField(
            model_name="supplierproduct",
            name="last_purchase_date",
            field=models.DateField(null=True, blank=True),
        ),
    ]

