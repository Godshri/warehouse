from django.conf import settings
from django.db import models


class Notification(models.Model):
    class Kind(models.TextChoices):
        OVERDUE = 'overdue', 'Просроченный возврат'
        REPAIR = 'repair', 'Нужен ремонт'
        INFO = 'info', 'Информация'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    kind = models.CharField(max_length=32, choices=Kind.choices, default=Kind.INFO)
    title = models.CharField(max_length=200)
    message = models.TextField(blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f'{self.get_kind_display()}: {self.title}'
