from django.contrib import admin
from .models import RoomObjects, Alarm, AlarmSession

@admin.register(RoomObjects)
class RoomObjectAdmin(admin.ModelAdmin):
    list_display = ("emoji", "name", "category", "is_active")
    list_filter = ("category","is_active")
    search_fields = ("name",)

@admin.register(Alarm)
class AlarmAdmin(admin.ModelAdmin):
    list_display = ("label", "time", "is_active", "created_at")
    list_filter = ("is_active",)

@admin.register(AlarmSession)
class AlarmSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "alarm", "assigned_object", "status", "triggered_at", "solved_at")
    list_filter = ("status",)
    readonly_fields = ("id", "triggered_at", "solved_at", "ai_confidence", "ai_detected_label")
    