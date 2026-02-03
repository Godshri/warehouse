from rest_framework import serializers

from .models import InventorySession


class InventorySessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventorySession
        fields = ('id', 'location', 'started_at', 'finished_at', 'created_by', 'result')
        read_only_fields = ('id', 'started_at', 'finished_at', 'created_by', 'result')


class InventoryScanSerializer(serializers.Serializer):
    equipment_id = serializers.UUIDField()

