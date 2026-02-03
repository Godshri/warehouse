from django.conf import settings
from django.db import models

from equipment.models import Location


class InventorySession(models.Model):
    location = models.ForeignKey(Location, null=True, blank=True, on_delete=models.SET_NULL)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    result = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:
        return f'Inventory {self.id}'
