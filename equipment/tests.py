from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

from .models import Equipment, EquipmentCategory

User = get_user_model()


class EquipmentTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='user', password='pass')
        self.client.force_authenticate(self.user)
        self.category = EquipmentCategory.objects.create(name='Станок')
        self.equipment = Equipment.objects.create(name='Токарный станок', category=self.category)

    def test_qr_endpoint(self):
        url = reverse('equipment-qr', kwargs={'pk': self.equipment.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/png')
