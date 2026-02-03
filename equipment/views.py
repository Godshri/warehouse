import io

import qrcode
from PIL import Image
from django.http import HttpResponse
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Equipment, EquipmentCategory, Location
from .serializers import EquipmentCategorySerializer, EquipmentSerializer, LocationSerializer
from users.permissions import ReadOnlyOrStorekeeper


class EquipmentCategoryViewSet(viewsets.ModelViewSet):
    queryset = EquipmentCategory.objects.all().order_by('name')
    serializer_class = EquipmentCategorySerializer
    permission_classes = [ReadOnlyOrStorekeeper]


class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all().order_by('name')
    serializer_class = LocationSerializer
    permission_classes = [ReadOnlyOrStorekeeper]


class EquipmentViewSet(viewsets.ModelViewSet):
    queryset = Equipment.objects.select_related('category', 'location', 'responsible_user').all()
    serializer_class = EquipmentSerializer
    permission_classes = [ReadOnlyOrStorekeeper]

    @action(detail=True, methods=['get'])
    def qr(self, request, pk=None):
        equipment = self.get_object()
        img = qrcode.make(equipment.qr_payload)
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return HttpResponse(buffer.read(), content_type='image/png')

    @action(detail=False, methods=['get'])
    def qr_bulk(self, request):
        ids = request.query_params.getlist('ids')
        queryset = self.get_queryset()
        if ids:
            queryset = queryset.filter(id__in=ids)
        images = []
        for equipment in queryset:
            img = qrcode.make(equipment.qr_payload)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            images.append(img)
        if not images:
            return Response({'detail': 'No equipment found'}, status=404)
        buffer = io.BytesIO()
        first, rest = images[0], images[1:]
        first.save(buffer, format='PDF', save_all=True, append_images=rest)
        buffer.seek(0)
        response = HttpResponse(buffer.read(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="equipment_qr.pdf"'
        return response
