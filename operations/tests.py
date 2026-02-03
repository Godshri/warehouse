from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

from equipment.models import Equipment, EquipmentCategory, Location
from operations.models import Operation

User = get_user_model()


class IssueReturnTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(username='admin', password='pass', role='admin')
        self.worker = User.objects.create_user(username='worker', password='pass', role='worker')
        self.client.force_authenticate(self.admin)
        self.category = EquipmentCategory.objects.create(name='Инструмент')
        self.location = Location.objects.create(name='Склад')
        self.equipment = Equipment.objects.create(
            name='Дрель',
            category=self.category,
            location=self.location,
        )

    def test_issue_and_return(self):
        issue_url = reverse('operations-issue')
        response = self.client.post(issue_url, {
            'equipment_id': str(self.equipment.id),
            'target_user_id': self.worker.id,
            'notes': 'Выдача на смену',
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.equipment.refresh_from_db()
        self.assertEqual(self.equipment.status, Equipment.Status.ISSUED)
        self.assertEqual(self.equipment.responsible_user_id, self.worker.id)

        return_url = reverse('operations-return')
        response = self.client.post(return_url, {
            'equipment_id': str(self.equipment.id),
            'condition': Operation.Condition.OK,
            'notes': 'Возврат',
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.equipment.refresh_from_db()
        self.assertEqual(self.equipment.status, Equipment.Status.IN_STOCK)
        self.assertIsNone(self.equipment.responsible_user)
