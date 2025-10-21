from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from ..models import Notification, NotificationPreference, PushNotificationDevice
from ..serializers import NotificationSerializer, NotificationPreferenceSerializer, PushNotificationDeviceSerializer
from ..services.inventory_service import InventoryService
from ..services.push_service import PushNotificationService

class NotificationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'unread_count': count})
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        updated = self.get_queryset().filter(is_read=False).update(
            is_read=True, read_at=timezone.now()
        )
        return Response({'marked_read': updated})
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notification = self.get_queryset().get(notification_id=pk)
        notification.mark_as_read()
        return Response({'status': 'marked as read'})

class NotificationPreferenceViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationPreferenceSerializer
    
    def get_queryset(self):
        return NotificationPreference.objects.filter(user=self.request.user)
    
    def get_object(self):
        obj, created = NotificationPreference.objects.get_or_create(user=self.request.user)
        return obj
    

class InventoryViewSet(viewsets.ViewSet):
    """HTTP API for inventory management"""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def update_stock(self, request):
        """Update inventory stock level"""
        menu_item_id = request.data.get('menu_item_id')
        branch_id = request.data.get('branch_id')
        new_quantity = request.data.get('quantity')
        reason = request.data.get('reason', '')
        
        if not all([menu_item_id, branch_id, new_quantity is not None]):
            return Response(
                {'error': 'menu_item_id, branch_id, and quantity are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            inventory = InventoryService.update_inventory(
                menu_item_id, branch_id, int(new_quantity), reason, request.user
            )
            
            if inventory:
                return Response({
                    'message': 'Inventory updated successfully',
                    'inventory_id': inventory.inventory_id,
                    'current_stock': inventory.current_stock,
                    'is_low_stock': inventory.is_low_stock,
                    'is_out_of_stock': inventory.is_out_of_stock
                })
            else:
                return Response(
                    {'error': 'Inventory record not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
                
        except Exception as e:
            return Response(
                {'error': f'Failed to update inventory: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Get low stock items for user's restaurants"""
        restaurant_id = request.query_params.get('restaurant_id')
        branch_id = request.query_params.get('branch_id')
        
        try:
            if branch_id:
                inventory_items = InventoryService.get_branch_inventory(branch_id, low_stock_only=True)
            elif restaurant_id:
                inventory_items = InventoryService.get_restaurant_inventory(restaurant_id, low_stock_only=True)
            else:
                return Response(
                    {'error': 'restaurant_id or branch_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            low_stock_data = []
            for item in inventory_items:
                low_stock_data.append({
                    'inventory_id': item.inventory_id,
                    'menu_item_id': item.menu_item.item_id,
                    'menu_item_name': item.menu_item.name,
                    'branch_id': item.branch.branch_id,
                    'branch_name': f"{item.branch.restaurant.name} - {item.branch.address.city}",
                    'current_stock': item.current_stock,
                    'low_stock_threshold': item.low_stock_threshold,
                    'is_out_of_stock': item.is_out_of_stock
                })
            
            return Response({'low_stock_items': low_stock_data})
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get low stock items: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class PushDeviceViewSet(viewsets.ModelViewSet):
    """HTTP API for push notification devices"""
    permission_classes = [IsAuthenticated]
    serializer_class = PushNotificationDeviceSerializer
    
    def get_queryset(self):
        return PushNotificationDevice.objects.filter(user=self.request.user, is_active=True)
    
    def create(self, request, *args, **kwargs):
        """Register a push notification device"""
        platform = request.data.get('platform')
        device_token = request.data.get('device_token')
        
        if not platform or not device_token:
            return Response(
                {'error': 'platform and device_token are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        device, created = PushNotificationService.register_device(
            request.user,
            platform,
            device_token,
            device_model=request.data.get('device_model'),
            app_version=request.data.get('app_version'),
            fcm_token=request.data.get('fcm_token'),
            apns_token=request.data.get('apns_token'),
        )
        
        if device:
            serializer = self.get_serializer(device)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
            )
        else:
            return Response(
                {'error': 'Failed to register device'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def unregister(self, request):
        """Unregister a push notification device"""
        device_token = request.data.get('device_token')
        
        if not device_token:
            return Response(
                {'error': 'device_token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        success = PushNotificationService.unregister_device(device_token)
        
        return Response({'unregistered': success})