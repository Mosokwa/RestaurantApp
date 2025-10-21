import logging
from django.utils import timezone
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)

class POSMenuSyncService:
    """
    NEW: POS menu synchronization service with real-time updates
    INTEGRATES WITH: Your existing POSConnection and WebSocket system
    """
    
    def __init__(self, connection):
        self.connection = connection
        self.channel_layer = get_channel_layer()
    
    def sync_menu(self):
        """NEW: Enhanced menu sync with real-time progress"""
        try:
            self._broadcast_sync_start('menu')
            
            # Use your existing POS service
            from .pos_services import POSServiceFactory
            pos_service = POSServiceFactory.get_service(self.connection.pos_type, self.connection)
            
            if not pos_service:
                raise Exception("POS service not available")
            
            # Perform sync
            success, result = pos_service.sync_menu_items()
            
            if success:
                self._broadcast_sync_complete('menu', result)
                return True, result
            else:
                self._broadcast_sync_error('menu', result.get('error', 'Unknown error'))
                return False, result
                
        except Exception as e:
            error_msg = f"Menu sync failed: {str(e)}"
            self._broadcast_sync_error('menu', error_msg)
            return False, {'error': error_msg}
    
    def _broadcast_sync_start(self, sync_type):
        """NEW: Broadcast sync start"""
        try:
            async_to_sync(self.channel_layer.group_send)(
                f"pos_sync_{self.connection.restaurant_id}",
                {
                    'type': 'sync_start',
                    'sync_type': sync_type,
                    'connection_id': self.connection.connection_id,
                    'timestamp': timezone.now().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Failed to broadcast sync start: {str(e)}")
    
    def _broadcast_sync_complete(self, sync_type, result):
        """NEW: Broadcast sync completion"""
        try:
            async_to_sync(self.channel_layer.group_send)(
                f"pos_sync_{self.connection.restaurant_id}",
                {
                    'type': 'sync_complete',
                    'sync_type': sync_type,
                    'connection_id': self.connection.connection_id,
                    'result': result,
                    'timestamp': timezone.now().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Failed to broadcast sync complete: {str(e)}")
    
    def _broadcast_sync_error(self, sync_type, error):
        """NEW: Broadcast sync error"""
        try:
            async_to_sync(self.channel_layer.group_send)(
                f"pos_sync_{self.connection.restaurant_id}",
                {
                    'type': 'sync_error',
                    'sync_type': sync_type,
                    'connection_id': self.connection.connection_id,
                    'error': error,
                    'timestamp': timezone.now().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Failed to broadcast sync error: {str(e)}")

class OrderSyncService:
    """
    NEW: Order synchronization service with real-time tracking
    INTEGRATES WITH: Your existing OrderPOSInfo and WebSocket system
    """
    
    def __init__(self, connection):
        self.connection = connection
        self.channel_layer = get_channel_layer()
    
    def sync_order_to_pos(self, order):
        """NEW: Sync order to POS with real-time updates"""
        try:
            self._broadcast_order_sync_start(order)
            
            from .pos_services import POSServiceFactory
            pos_service = POSServiceFactory.get_service(self.connection.pos_type, self.connection)
            
            if not pos_service:
                raise Exception("POS service not available")
            
            # Convert order data
            order_data = self._convert_order_to_sync_format(order)
            
            # Send to POS
            success, pos_order_id = pos_service.create_order(order_data)
            
            if success:
                self._broadcast_order_sync_complete(order, pos_order_id)
                return True, pos_order_id
            else:
                self._broadcast_order_sync_error(order, pos_order_id)
                return False, pos_order_id
                
        except Exception as e:
            error_msg = f"Order sync failed: {str(e)}"
            self._broadcast_order_sync_error(order, error_msg)
            return False, error_msg
    
    def _convert_order_to_sync_format(self, order):
        """NEW: Convert order to sync format"""
        order_data = {
            'order_id': str(order.order_uuid),
            'order_type': order.order_type,
            'total_amount': float(order.total_amount),
            'customer_info': {
                'name': order.customer.user.get_full_name(),
                'email': order.customer.user.email
            },
            'items': []
        }
        
        for item in order.order_items.all():
            item_data = {
                'item_id': item.menu_item.item_id,
                'name': item.menu_item.name,
                'quantity': item.quantity,
                'price': float(item.unit_price),
                'modifiers': []
            }
            
            for modifier in item.modifiers.all():
                item_data['modifiers'].append({
                    'modifier_id': modifier.item_modifier.item_modifier_id,
                    'name': modifier.item_modifier.name,
                    'price': float(modifier.unit_price)
                })
            
            order_data['items'].append(item_data)
        
        return order_data
    
    def _broadcast_order_sync_start(self, order):
        """NEW: Broadcast order sync start"""
        try:
            async_to_sync(self.channel_layer.group_send)(
                f"order_{order.order_id}",
                {
                    'type': 'order_sync_start',
                    'order_id': order.order_id,
                    'timestamp': timezone.now().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Failed to broadcast order sync start: {str(e)}")
    
    def _broadcast_order_sync_complete(self, order, pos_order_id):
        """NEW: Broadcast order sync completion"""
        try:
            async_to_sync(self.channel_layer.group_send)(
                f"order_{order.order_id}",
                {
                    'type': 'order_sync_complete',
                    'order_id': order.order_id,
                    'pos_order_id': pos_order_id,
                    'timestamp': timezone.now().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Failed to broadcast order sync complete: {str(e)}")
    
    def _broadcast_order_sync_error(self, order, error):
        """NEW: Broadcast order sync error"""
        try:
            async_to_sync(self.channel_layer.group_send)(
                f"order_{order.order_id}",
                {
                    'type': 'order_sync_error',
                    'order_id': order.order_id,
                    'error': error,
                    'timestamp': timezone.now().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Failed to broadcast order sync error: {str(e)}")

class InventorySyncService:
    """
    NEW: Inventory synchronization service with real-time alerts
    INTEGRATES WITH: Your existing RealTimeInventory and alert system
    """
    
    def __init__(self, connection):
        self.connection = connection
        self.channel_layer = get_channel_layer()
    
    def sync_inventory(self):
        """NEW: Enhanced inventory sync with real-time updates"""
        try:
            self._broadcast_sync_start('inventory')
            
            from .pos_services import POSServiceFactory
            pos_service = POSServiceFactory.get_service(self.connection.pos_type, self.connection)
            
            if not pos_service:
                raise Exception("POS service not available")
            
            # Perform sync
            success, result = pos_service.sync_inventory()
            
            if success:
                self._broadcast_sync_complete('inventory', result)
                return True, result
            else:
                self._broadcast_sync_error('inventory', result.get('error', 'Unknown error'))
                return False, result
                
        except Exception as e:
            error_msg = f"Inventory sync failed: {str(e)}"
            self._broadcast_sync_error('inventory', error_msg)
            return False, {'error': error_msg}
    
    def _broadcast_sync_start(self, sync_type):
        """NEW: Broadcast sync start"""
        try:
            async_to_sync(self.channel_layer.group_send)(
                f"pos_sync_{self.connection.restaurant_id}",
                {
                    'type': 'sync_start',
                    'sync_type': sync_type,
                    'connection_id': self.connection.connection_id,
                    'timestamp': timezone.now().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Failed to broadcast sync start: {str(e)}")
    
    def _broadcast_sync_complete(self, sync_type, result):
        """NEW: Broadcast sync completion"""
        try:
            async_to_sync(self.channel_layer.group_send)(
                f"pos_sync_{self.connection.restaurant_id}",
                {
                    'type': 'sync_complete',
                    'sync_type': sync_type,
                    'connection_id': self.connection.connection_id,
                    'result': result,
                    'timestamp': timezone.now().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Failed to broadcast sync complete: {str(e)}")
    
    def _broadcast_sync_error(self, sync_type, error):
        """NEW: Broadcast sync error"""
        try:
            async_to_sync(self.channel_layer.group_send)(
                f"pos_sync_{self.connection.restaurant_id}",
                {
                    'type': 'sync_error',
                    'sync_type': sync_type,
                    'connection_id': self.connection.connection_id,
                    'error': error,
                    'timestamp': timezone.now().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Failed to broadcast sync error: {str(e)}")