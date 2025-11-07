from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0003_brand_uuid_category_uuid_product_uuid_promotion_uuid"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="last_cost_price",
            field=models.DecimalField(null=True, blank=True, max_digits=12, decimal_places=2),
        ),
        migrations.AddField(
            model_name="product",
            name="avg_cost_price",
            field=models.DecimalField(null=True, blank=True, max_digits=12, decimal_places=2),
        ),
    ]

