from rest_framework import serializers

from .models import Operation


class OperationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Operation
        fields = (
            'id',
            'equipment',
            'action_type',
            'user',
            'target_user',
            'location_from',
            'location_to',
            'condition',
            'timestamp',
            'notes',
            'due_at',
        )
        read_only_fields = ('id', 'timestamp', 'user')


class IssueSerializer(serializers.Serializer):
    equipment_id = serializers.UUIDField()
    target_user_id = serializers.IntegerField()
    notes = serializers.CharField(required=False, allow_blank=True)
    due_at = serializers.DateTimeField(required=False, allow_null=True)


class ReturnSerializer(serializers.Serializer):
    equipment_id = serializers.UUIDField()
    condition = serializers.ChoiceField(choices=Operation.Condition.choices)
    notes = serializers.CharField(required=False, allow_blank=True)
