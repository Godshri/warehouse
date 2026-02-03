from django.contrib import admin

from .models import Operation


@admin.register(Operation)
class OperationAdmin(admin.ModelAdmin):
    list_display = ('equipment', 'action_type', 'user', 'target_user', 'timestamp')
    list_filter = ('action_type', 'timestamp')
    search_fields = ('equipment__name', 'equipment__id')
