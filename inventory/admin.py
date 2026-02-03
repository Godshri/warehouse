from django.contrib import admin

from .models import InventorySession


@admin.register(InventorySession)
class InventorySessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'location', 'started_at', 'finished_at', 'created_by')
    list_filter = ('location', 'started_at')
