from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin

from .models import Alert, AlertHistory


class AlertHistoryInline(admin.TabularInline):
    model = AlertHistory
    extra = 0
    readonly_fields = ("changed_by", "change_type", "old_value", "new_value", "note", "created_at")
    can_delete = False


@admin.register(Alert)
class AlertAdmin(GISModelAdmin):
    inlines = (AlertHistoryInline,)
    list_display = (
        "public_tracking_code", "emergency_type", "priority", "status",
        "created_at", "point",
    )
    list_filter = ("status", "priority", "emergency_type", "building_condition")
    search_fields = ("public_tracking_code", "person_name", "phone", "email")
    readonly_fields = ("public_tracking_code", "point", "created_at", "last_updated")
