# services/realtime_tracking_service.py
import asyncio
import json
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class RealtimeTrackingService:
    """Service for managing real-time tracking updates - FULLY IMPLEMENTED"""
    
    @staticmethod
    def broadcast_order_update(order, update_type, data):
        """Broadcast order update to connected clients"""
        channel_layer = get_channel_layer()
        
        async_to_sync(channel_layer.group_send)(
            f"order_{order.order_uuid}",
            {
                'type': 'order_update',
                'update_type': update_type,
                'order_uuid': str(order.order_uuid),
                'data': data,
                'timestamp': timezone.now().isoformat()
            }
        )
    
    @staticmethod
    def broadcast_kitchen_status(restaurant_id, status_data):
        """Broadcast kitchen status to restaurant staff"""
        channel_layer = get_channel_layer()
        
        async_to_sync(channel_layer.group_send)(
            f"restaurant_{restaurant_id}",
            {
                'type': 'kitchen_status',
                'restaurant_id': restaurant_id,
                'status_data': status_data,
                'timestamp': timezone.now().isoformat()
            }
        )
    
    @staticmethod
    def broadcast_station_update(station, update_type, data):
        """Broadcast station-specific updates"""
        channel_layer = get_channel_layer()
        
        async_to_sync(channel_layer.group_send)(
            f"kitchen_{station.restaurant_id}",
            {
                'type': 'station_update',
                'station_id': station.station_id,
                'update_type': update_type,
                'data': data,
                'timestamp': timezone.now().isoformat()
            }
        )
    
    @staticmethod
    def notify_pos_sync_complete(connection, sync_type, result):
        """Notify when POS sync completes"""
        channel_layer = get_channel_layer()
        
        async_to_sync(channel_layer.group_send)(
            f"restaurant_{connection.restaurant_id}",
            {
                'type': 'pos_sync_complete',
                'connection_id': connection.connection_id,
                'sync_type': sync_type,
                'result': result,
                'timestamp': timezone.now().isoformat()
            }
        )
    
    @staticmethod
    def broadcast_table_status(layout, table_number, status):
        """Broadcast table status changes"""
        channel_layer = get_channel_layer()
        
        async_to_sync(channel_layer.group_send)(
            f"restaurant_{layout.restaurant_id}",
            {
                'type': 'table_status_update',
                'layout_id': layout.layout_id,
                'table_number': table_number,
                'status': status,
                'timestamp': timezone.now().isoformat()
            }
        )

class POSWebhookProcessor:
    """Process POS webhooks and broadcast real-time updates"""
    
    def __init__(self, connection):
        self.connection = connection
        self.realtime_service = RealtimeTrackingService()
    
    def process_and_broadcast_order_update(self, webhook_data):
        """Process order webhook and broadcast real-time update"""
        from ..services.webhook_services import WebhookService
        
        webhook_service = WebhookService(self.connection)
        success = webhook_service.process_order_webhook(webhook_data)
        
        if success:
            # Extract order information from webhook
            order_data = self._extract_order_data(webhook_data)
            if order_data:
                self.realtime_service.broadcast_order_update(
                    order_data['order'],
                    'pos_sync',
                    {'pos_status': order_data['pos_status']}
                )
        
        return success
    
    def process_and_broadcast_inventory_update(self, webhook_data):
        """Process inventory webhook and broadcast real-time update"""
        from ..services.webhook_services import WebhookService
        
        webhook_service = WebhookService(self.connection)
        success = webhook_service.process_inventory_webhook(webhook_data)
        
        if success:
            # Broadcast inventory update to restaurant
            self.realtime_service.broadcast_kitchen_status(
                self.connection.restaurant_id,
                {'type': 'inventory_updated', 'timestamp': timezone.now().isoformat()}
            )
        
        return success
    
    def _extract_order_data(self, webhook_data):
        """Extract order data from webhook payload"""
        from ..models import OrderPOSInfo
        
        try:
            if self.connection.pos_type == 'square':
                for event in webhook_data.get('data', []):
                    if event['type'] == 'order.updated':
                        order_data = event['data']['object']['order']
                        pos_order_id = order_data['id']
                        
                        order_pos_info = OrderPOSInfo.objects.get(pos_order_id=pos_order_id)
                        return {
                            'order': order_pos_info.order,
                            'pos_status': order_data.get('state')
                        }
            
            elif self.connection.pos_type == 'toast':
                order_data = webhook_data.get('payload', {})
                pos_order_id = order_data.get('id')
                
                order_pos_info = OrderPOSInfo.objects.get(pos_order_id=pos_order_id)
                return {
                    'order': order_pos_info.order,
                    'pos_status': order_data.get('status')
                }
        
        except (OrderPOSInfo.DoesNotExist, KeyError) as e:
            logger.error(f"Error extracting order data: {str(e)}")
        
        return None