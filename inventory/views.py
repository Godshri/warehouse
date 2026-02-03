from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from equipment.models import Equipment
from .models import InventorySession
from .serializers import InventoryScanSerializer, InventorySessionSerializer
from users.permissions import IsStorekeeperOrAdmin


class InventorySessionViewSet(viewsets.ModelViewSet):
    queryset = InventorySession.objects.select_related('location', 'created_by').all()
    serializer_class = InventorySessionSerializer
    permission_classes = [IsStorekeeperOrAdmin]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, result={'scanned': []})

    @action(detail=True, methods=['post'])
    def scan(self, request, pk=None):
        session = self.get_object()
        serializer = InventoryScanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        scanned = session.result.get('scanned', [])
        equipment_id = str(serializer.validated_data['equipment_id'])
        if equipment_id not in scanned:
            scanned.append(equipment_id)
            session.result['scanned'] = scanned
            session.save(update_fields=['result'])
        return Response({'scanned_count': len(scanned)})

    @action(detail=True, methods=['post'])
    def finish(self, request, pk=None):
        session = self.get_object()
        scanned = set(session.result.get('scanned', []))
        expected_qs = Equipment.objects.all()
        if session.location_id:
            expected_qs = expected_qs.filter(location_id=session.location_id)
        expected = set(str(item.id) for item in expected_qs)
        missing = sorted(expected - scanned)
        extra = sorted(scanned - expected)
        session.result = {
            'scanned': sorted(scanned),
            'missing': missing,
            'extra': extra,
        }
        session.finished_at = timezone.now()
        session.save(update_fields=['result', 'finished_at'])
        return Response(session.result, status=status.HTTP_200_OK)
