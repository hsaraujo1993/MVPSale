from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0004_product_cost_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="needs_review",
            field=models.BooleanField(default=False),
        ),
    ]

