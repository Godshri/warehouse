from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from equipment.models import Equipment
from notifications.models import Notification
from .models import Operation
from .serializers import IssueSerializer, OperationSerializer, ReturnSerializer
from users.permissions import IsObserverOrAbove, IsStorekeeperOrAdmin

User = get_user_model()


class OperationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Operation.objects.select_related('equipment', 'user', 'target_user').all()
    serializer_class = OperationSerializer
    permission_classes = [IsObserverOrAbove]


class ScanView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        equipment_id = request.data.get('equipment_id') or request.data.get('qr_data')
        if not equipment_id:
            return Response({'detail': 'equipment_id or qr_data required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            equipment = Equipment.objects.get(id=equipment_id)
        except Equipment.DoesNotExist:
            return Response({'detail': 'Equipment not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response({
            'id': str(equipment.id),
            'name': equipment.name,
            'status': equipment.status,
            'location': equipment.location_id,
        })


class IssueView(APIView):
    permission_classes = [IsStorekeeperOrAdmin]

    @transaction.atomic
    def post(self, request):
        serializer = IssueSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            equipment = Equipment.objects.select_for_update().get(id=serializer.validated_data['equipment_id'])
        except Equipment.DoesNotExist:
            return Response({'detail': 'Equipment not found'}, status=status.HTTP_404_NOT_FOUND)
        try:
            target_user = User.objects.get(id=serializer.validated_data['target_user_id'])
        except User.DoesNotExist:
            return Response({'detail': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        equipment.status = Equipment.Status.ISSUED
        equipment.responsible_user = target_user
        equipment.save(update_fields=['status', 'responsible_user', 'updated_at'])
        operation = Operation.objects.create(
            equipment=equipment,
            action_type=Operation.ActionType.ISSUE,
            user=request.user,
            target_user=target_user,
            location_from=equipment.location,
            notes=serializer.validated_data.get('notes', ''),
            due_at=serializer.validated_data.get('due_at'),
        )
        return Response(OperationSerializer(operation).data, status=status.HTTP_201_CREATED)


class ReturnView(APIView):
    permission_classes = [IsStorekeeperOrAdmin]

    @transaction.atomic
    def post(self, request):
        serializer = ReturnSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            equipment = Equipment.objects.select_for_update().get(id=serializer.validated_data['equipment_id'])
        except Equipment.DoesNotExist:
            return Response({'detail': 'Equipment not found'}, status=status.HTTP_404_NOT_FOUND)
        condition = serializer.validated_data['condition']
        if condition == Operation.Condition.NEED_REPAIR:
            new_status = Equipment.Status.IN_REPAIR
        elif condition == Operation.Condition.DAMAGED:
            new_status = Equipment.Status.WRITTEN_OFF
        else:
            new_status = Equipment.Status.IN_STOCK
        equipment.status = new_status
        equipment.save(update_fields=['status', 'updated_at'])
        operation = Operation.objects.create(
            equipment=equipment,
            action_type=Operation.ActionType.RETURN,
            user=request.user,
            target_user=equipment.responsible_user,
            location_to=equipment.location,
            condition=condition,
            notes=serializer.validated_data.get('notes', ''),
        )
        if condition in {Operation.Condition.NEED_REPAIR, Operation.Condition.DAMAGED}:
            kind = Notification.Kind.REPAIR if condition == Operation.Condition.NEED_REPAIR else Notification.Kind.INFO
            title = f'Проблема с оборудованием: {equipment.name}'
            message = 'Требуется ремонт' if condition == Operation.Condition.NEED_REPAIR else 'Оборудование повреждено'
            for admin_user in User.objects.filter(role__in=['admin', 'storekeeper']):
                Notification.objects.create(
                    user=admin_user,
                    kind=kind,
                    title=title,
                    message=message,
                )
        if new_status != Equipment.Status.ISSUED:
            equipment.responsible_user = None
            equipment.save(update_fields=['responsible_user'])
        return Response(OperationSerializer(operation).data, status=status.HTTP_201_CREATED)
