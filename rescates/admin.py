from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin

from .models import AssignmentHistory, RescueAssignment, RescueTeam, Victim


@admin.register(RescueTeam)
class RescueTeamAdmin(GISModelAdmin):
    list_display = ("code", "name", "operational_status", "specialty", "vehicle_available")
    list_filter = ("operational_status", "specialty", "vehicle_available")
    search_fields = ("code", "name", "institution")


@admin.register(RescueAssignment)
class RescueAssignmentAdmin(admin.ModelAdmin):
    list_display = ("alert", "team", "status", "assigned_at", "assigned_by")
    list_filter = ("status",)
    search_fields = ("alert__public_tracking_code", "team__code", "team__name")
    readonly_fields = ("assigned_at",)


@admin.register(AssignmentHistory)
class AssignmentHistoryAdmin(admin.ModelAdmin):
    list_display = ("assignment", "old_status", "new_status", "changed_by", "created_at")
    readonly_fields = ("created_at",)


@admin.register(Victim)
class VictimAdmin(admin.ModelAdmin):
    list_display = ("first_names", "last_names", "alert", "rescue_status", "health_status")
    list_filter = ("rescue_status",)
    search_fields = ("first_names", "last_names", "identification_number", "alert__public_tracking_code")
