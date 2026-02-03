from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from equipment.models import Equipment, EquipmentCategory, Location
from inventory.models import InventorySession
from notifications.models import Notification
from operations.models import Operation


class Command(BaseCommand):
    help = 'Load demo data for Smart Warehouse.'

    def handle(self, *args, **options):
        User = get_user_model()

        admin, _ = User.objects.get_or_create(
            username='admin',
            defaults={'role': 'admin', 'is_staff': True, 'is_superuser': True, 'is_active': True},
        )
        admin.role = 'admin'
        admin.is_staff = True
        admin.is_superuser = True
        admin.is_active = True
        admin.set_password('demo1234')
        admin.save()

        storekeeper, _ = User.objects.get_or_create(
            username='storekeeper',
            defaults={'role': 'storekeeper', 'is_active': True},
        )
        storekeeper.role = 'storekeeper'
        storekeeper.is_active = True
        storekeeper.set_password('demo1234')
        storekeeper.save()

        worker, _ = User.objects.get_or_create(
            username='worker',
            defaults={'role': 'worker', 'is_active': True},
        )
        worker.role = 'worker'
        worker.is_active = True
        worker.set_password('demo1234')
        worker.save()

        observer, _ = User.objects.get_or_create(
            username='observer',
            defaults={'role': 'observer', 'is_active': True},
        )
        observer.role = 'observer'
        observer.is_active = True
        observer.set_password('demo1234')
        observer.save()

        tools, _ = EquipmentCategory.objects.get_or_create(name='Инструменты')
        machines, _ = EquipmentCategory.objects.get_or_create(name='Станки')
        consumables, _ = EquipmentCategory.objects.get_or_create(name='Расходники')

        warehouse, _ = Location.objects.get_or_create(name='Главный склад')
        room_a, _ = Location.objects.get_or_create(name='Цех A', parent=warehouse)
        room_b, _ = Location.objects.get_or_create(name='Цех B', parent=warehouse)

        drill, _ = Equipment.objects.get_or_create(
            name='Дрель аккумуляторная',
            defaults={
                'category': tools,
                'location': room_a,
                'status': Equipment.Status.IN_STOCK,
            },
        )
        saw, _ = Equipment.objects.get_or_create(
            name='Циркулярная пила',
            defaults={
                'category': tools,
                'location': room_b,
                'status': Equipment.Status.IN_STOCK,
            },
        )
        lathe, _ = Equipment.objects.get_or_create(
            name='Токарный станок',
            defaults={
                'category': machines,
                'location': warehouse,
                'status': Equipment.Status.IN_STOCK,
            },
        )
        gloves, _ = Equipment.objects.get_or_create(
            name='Перчатки защитные',
            defaults={
                'category': consumables,
                'location': warehouse,
                'status': Equipment.Status.IN_STOCK,
            },
        )

        issue_time = timezone.now() - timedelta(days=2)
        due_time = timezone.now() - timedelta(hours=4)
        drill.status = Equipment.Status.ISSUED
        drill.responsible_user = worker
        drill.save(update_fields=['status', 'responsible_user', 'updated_at'])
        Operation.objects.get_or_create(
            equipment=drill,
            action_type=Operation.ActionType.ISSUE,
            user=storekeeper,
            target_user=worker,
            location_from=room_a,
            defaults={'notes': 'Выдача на смену', 'due_at': due_time},
        )

        lathe.status = Equipment.Status.IN_REPAIR
        lathe.save(update_fields=['status', 'updated_at'])
        Operation.objects.get_or_create(
            equipment=lathe,
            action_type=Operation.ActionType.REPAIR,
            user=storekeeper,
            location_from=warehouse,
            notes='Плановый ремонт',
        )

        Notification.objects.get_or_create(
            user=admin,
            kind=Notification.Kind.OVERDUE,
            title='Просрочен возврат',
            defaults={'message': f'Оборудование {drill.name} не возвращено вовремя.'},
        )

        inventory = InventorySession.objects.create(
            location=warehouse,
            created_by=storekeeper,
            result={'scanned': [str(saw.id), str(gloves.id)]},
        )
        inventory.finished_at = timezone.now()
        inventory.result = {
            'scanned': [str(saw.id), str(gloves.id)],
            'missing': [str(drill.id)],
            'extra': [],
        }
        inventory.save(update_fields=['finished_at', 'result'])

        self.stdout.write(self.style.SUCCESS('Demo data loaded.'))
