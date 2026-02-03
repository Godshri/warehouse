from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Администратор'
        STOREKEEPER = 'storekeeper', 'Кладовщик'
        WORKER = 'worker', 'Работник'
        OBSERVER = 'observer', 'Наблюдатель'

    role = models.CharField(max_length=32, choices=Role.choices, default=Role.WORKER)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f'{self.username} ({self.get_role_display()})'
