import uuid

from django.conf import settings
from django.db import models


class EquipmentCategory(models.Model):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)

    def __str__(self) -> str:
        return self.name


class Location(models.Model):
    name = models.CharField(max_length=120)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='children')
    description = models.TextField(blank=True)

    class Meta:
        unique_together = ('name', 'parent')

    def __str__(self) -> str:
        return self.name


class Equipment(models.Model):
    class Status(models.TextChoices):
        IN_STOCK = 'in_stock', 'На складе'
        ISSUED = 'issued', 'Выдано'
        IN_REPAIR = 'in_repair', 'В ремонте'
        WRITTEN_OFF = 'written_off', 'Списано'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    category = models.ForeignKey(EquipmentCategory, null=True, blank=True, on_delete=models.SET_NULL)
    description = models.TextField(blank=True)
    location = models.ForeignKey(Location, null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.IN_STOCK)
    responsible_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='responsible_equipment',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f'{self.name} ({self.id})'

    @property
    def qr_payload(self) -> str:
        return str(self.id)


class EquipmentPhoto(models.Model):
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='equipment_photos/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f'Photo for {self.equipment_id}'
