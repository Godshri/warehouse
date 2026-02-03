from django.urls import include, path
from rest_framework.routers import DefaultRouter

from equipment.views import EquipmentCategoryViewSet, EquipmentViewSet, LocationViewSet
from inventory.views import InventorySessionViewSet
from notifications.views import NotificationViewSet, OverdueView
from operations.views import IssueView, OperationViewSet, ReturnView, ScanView
from reports.views import ReportView, StatsView
from users.views import UserViewSet

router = DefaultRouter()
router.register('users', UserViewSet, basename='users')
router.register('equipment', EquipmentViewSet, basename='equipment')
router.register('categories', EquipmentCategoryViewSet, basename='categories')
router.register('locations', LocationViewSet, basename='locations')
router.register('operations', OperationViewSet, basename='operations')
router.register('inventory', InventorySessionViewSet, basename='inventory')
router.register('notifications', NotificationViewSet, basename='notifications')

urlpatterns = [
    path('', include(router.urls)),
    path('scan/', ScanView.as_view(), name='scan'),
    path('operations/issue/', IssueView.as_view(), name='operations-issue'),
    path('operations/return/', ReturnView.as_view(), name='operations-return'),
    path('reports/', ReportView.as_view(), name='reports'),
    path('stats/', StatsView.as_view(), name='stats'),
    path('notifications/overdue/', OverdueView.as_view(), name='notifications-overdue'),
]
