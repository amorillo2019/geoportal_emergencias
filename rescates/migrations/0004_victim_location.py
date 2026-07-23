from django.contrib.gis.db import models
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("rescates", "0003_victim_safe_place_victim_transfer_hospital_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="victim",
            name="location",
            field=models.PointField(blank=True, null=True, spatial_index=True, srid=4326, verbose_name="ubicacion de la victima"),
        ),
    ]
