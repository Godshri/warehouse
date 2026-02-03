from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from equipment.models import Equipment
from operations.models import Operation
from users.permissions import IsStorekeeperOrAdmin
from .models import Notification
from .serializers import NotificationSerializer


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({'updated': count})


class OverdueView(APIView):
    permission_classes = [IsStorekeeperOrAdmin]

    def get(self, request):
        now = timezone.now()
        overdue_ops = Operation.objects.filter(
            action_type=Operation.ActionType.ISSUE,
            due_at__isnull=False,
            due_at__lt=now,
            equipment__status=Equipment.Status.ISSUED,
        ).select_related('equipment', 'target_user')
        data = []
        for op in overdue_ops:
            data.append({
                'equipment_id': str(op.equipment_id),
                'equipment_name': op.equipment.name,
                'target_user': op.target_user.username if op.target_user else '',
                'due_at': op.due_at.isoformat() if op.due_at else None,
            })
        return Response({'overdue': data}, status=status.HTTP_200_OK)
