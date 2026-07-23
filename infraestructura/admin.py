from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin

from .models import (
    AffectedBuilding, AdministrativeSector, BlockedRoadSegment,
    EmergencyZone, Hospital, Road, Shelter,
)


for model in (
    Hospital, Shelter, Road, BlockedRoadSegment,
    AffectedBuilding, EmergencyZone, AdministrativeSector,
):
    admin.site.register(model, GISModelAdmin)
