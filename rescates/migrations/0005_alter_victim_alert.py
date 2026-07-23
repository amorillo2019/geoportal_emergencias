from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("rescates", "0004_victim_location"),
    ]

    operations = [
        migrations.AlterField(
            model_name="victim",
            name="alert",
            field=models.ForeignKey(blank=True, null=True, on_delete=models.CASCADE, related_name="victims", to="alertas.alert"),
        ),
    ]
