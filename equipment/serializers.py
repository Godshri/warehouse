from rest_framework import serializers

from .models import Equipment, EquipmentCategory, EquipmentPhoto, Location


class EquipmentCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentCategory
        fields = ('id', 'name', 'description')


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ('id', 'name', 'parent', 'description')


class EquipmentPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentPhoto
        fields = ('id', 'image', 'uploaded_at')
        read_only_fields = ('id', 'uploaded_at')


class EquipmentSerializer(serializers.ModelSerializer):
    photos = EquipmentPhotoSerializer(many=True, read_only=True)
    category_detail = EquipmentCategorySerializer(source='category', read_only=True)
    location_detail = LocationSerializer(source='location', read_only=True)

    class Meta:
        model = Equipment
        fields = (
            'id',
            'name',
            'category',
            'category_detail',
            'description',
            'location',
            'location_detail',
            'status',
            'responsible_user',
            'created_at',
            'updated_at',
            'photos',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')
