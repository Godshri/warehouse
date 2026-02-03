from django.conf import settings
from django.db import models

from equipment.models import Equipment, Location


class Operation(models.Model):
    class ActionType(models.TextChoices):
        ISSUE = 'issue', 'Выдача'
        RETURN = 'return', 'Возврат'
        MOVE = 'move', 'Перемещение'
        REPAIR = 'repair', 'Ремонт'
        WRITE_OFF = 'write_off', 'Списание'

    class Condition(models.TextChoices):
        OK = 'ok', 'Исправно'
        NEED_REPAIR = 'need_repair', 'Требует ремонта'
        DAMAGED = 'damaged', 'Повреждено'

    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='operations')
    action_type = models.CharField(max_length=32, choices=ActionType.choices)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='performed_operations')
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='received_operations',
    )
    location_from = models.ForeignKey(
        Location,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='operations_from',
    )
    location_to = models.ForeignKey(
        Location,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='operations_to',
    )
    condition = models.CharField(max_length=32, choices=Condition.choices, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    due_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f'{self.get_action_type_display()} - {self.equipment_id}'
