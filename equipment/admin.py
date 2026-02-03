from django.contrib import admin

from .models import Equipment, EquipmentCategory, EquipmentPhoto, Location


@admin.register(EquipmentCategory)
class EquipmentCategoryAdmin(admin.ModelAdmin):
    search_fields = ('name',)


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    list_display = ('name', 'parent')


class EquipmentPhotoInline(admin.TabularInline):
    model = EquipmentPhoto
    extra = 1


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'location', 'responsible_user')
    list_filter = ('status', 'category')
    search_fields = ('name', 'id')
    inlines = [EquipmentPhotoInline]
