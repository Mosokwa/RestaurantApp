from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotificationViewSet,NotificationPreferenceViewSet, PushDeviceViewSet, InventoryViewSet

router = DefaultRouter()
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'notification-preferences', NotificationPreferenceViewSet, basename='notification-preference')
router.register(r'push-devices', PushDeviceViewSet, basename='push-device')


urlpatterns = [
    path('', include(router.urls)),
    path('inventory/update-stock/', InventoryViewSet.as_view({'post': 'update_stock'}), name='inventory-update-stock'),
    path('inventory/low-stock/', InventoryViewSet.as_view({'get': 'low_stock'}), name='inventory-low-stock'),
]