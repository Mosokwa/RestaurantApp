import logging
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone

logger = logging.getLogger(__name__)

class WebSocketService:
    """
    NEW: Comprehensive WebSocket service for real-time communication
    INTEGRATES WITH: Your existing WebSocketConnection model and consumers
    """
    
    @staticmethod
    def register_connection(user, connection_id, connection_type, groups, ip_address=None, user_agent=None):
        """
        NEW: Enhanced connection registration with real-time groups
        """
        try:
            from ..models import WebSocketConnection
            
            # Deactivate existing connections for this user/type
            WebSocketConnection.objects.filter(
                user=user, 
                connection_type=connection_type,
                is_active=True
            ).update(is_active=False, disconnected_at=timezone.now())
            
            # Create new connection
            connection = WebSocketConnection.objects.create(
                user=user,
                connection_id=connection_id,
                connection_type=connection_type,
                customer_group=f"customer_{user.id}" if user.user_type == 'customer' else None,
                restaurant_groups=groups.get('restaurants', []),
                order_groups=groups.get('orders', []),
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            logger.info(f"WebSocket connection registered: {connection_id} for user {user.username}")
            return connection
            
        except Exception as e:
            logger.error(f"Error registering WebSocket connection: {str(e)}")
            return None
    
    @staticmethod
    def broadcast_to_restaurant(restaurant_id, message_type, data):
        """
        NEW: Broadcast to all connections in a restaurant
        """
        try:
            channel_layer = get_channel_layer()
            
            message = {
                'type': message_type,
                'data': data,
                'timestamp': timezone.now().isoformat()
            }
            
            async_to_sync(channel_layer.group_send)(
                f"restaurant_{restaurant_id}",
                {
                    'type': 'send_message',
                    'message': message
                }
            )
            
            logger.debug(f"Broadcast to restaurant {restaurant_id}: {message_type}")
            return True
            
        except Exception as e:
            logger.error(f"Error broadcasting to restaurant {restaurant_id}: {str(e)}")
            return False
    
    @staticmethod
    def broadcast_to_order(order_id, message_type, data):
        """
        NEW: Broadcast to all connections following an order
        """
        try:
            channel_layer = get_channel_layer()
            
            message = {
                'type': message_type,
                'data': data,
                'timestamp': timezone.now().isoformat()
            }
            
            async_to_sync(channel_layer.group_send)(
                f"order_{order_id}",
                {
                    'type': 'send_message',
                    'message': message
                }
            )
            
            logger.debug(f"Broadcast to order {order_id}: {message_type}")
            return True
            
        except Exception as e:
            logger.error(f"Error broadcasting to order {order_id}: {str(e)}")
            return False
    
    @staticmethod
    def broadcast_to_kitchen(restaurant_id, message_type, data):
        """
        NEW: Broadcast to kitchen management channel
        """
        try:
            channel_layer = get_channel_layer()
            
            message = {
                'type': message_type,
                'data': data,
                'timestamp': timezone.now().isoformat()
            }
            
            async_to_sync(channel_layer.group_send)(
                f"kitchen_{restaurant_id}",
                {
                    'type': 'send_message',
                    'message': message
                }
            )
            
            logger.debug(f"Broadcast to kitchen {restaurant_id}: {message_type}")
            return True
            
        except Exception as e:
            logger.error(f"Error broadcasting to kitchen {restaurant_id}: {str(e)}")
            return False
    
    @staticmethod
    def broadcast_to_pos_sync(restaurant_id, message_type, data):
        """
        NEW: Broadcast to POS synchronization channel
        """
        try:
            channel_layer = get_channel_layer()
            
            message = {
                'type': message_type,
                'data': data,
                'timestamp': timezone.now().isoformat()
            }
            
            async_to_sync(channel_layer.group_send)(
                f"pos_sync_{restaurant_id}",
                {
                    'type': 'send_message',
                    'message': message
                }
            )
            
            logger.debug(f"Broadcast to POS sync {restaurant_id}: {message_type}")
            return True
            
        except Exception as e:
            logger.error(f"Error broadcasting to POS sync {restaurant_id}: {str(e)}")
            return False
    
    @staticmethod
    def broadcast_to_table_management(restaurant_id, message_type, data):
        """
        NEW: Broadcast to table management channel
        """
        try:
            channel_layer = get_channel_layer()
            
            message = {
                'type': message_type,
                'data': data,
                'timestamp': timezone.now().isoformat()
            }
            
            async_to_sync(channel_layer.group_send)(
                f"tables_{restaurant_id}",
                {
                    'type': 'send_message',
                    'message': message
                }
            )
            
            logger.debug(f"Broadcast to tables {restaurant_id}: {message_type}")
            return True
            
        except Exception as e:
            logger.error(f"Error broadcasting to tables {restaurant_id}: {str(e)}")
            return False
    
    @staticmethod
    def broadcast_to_admin(message_type, data):
        """
        NEW: Broadcast to admin channel
        """
        try:
            channel_layer = get_channel_layer()
            
            message = {
                'type': message_type,
                'data': data,
                'timestamp': timezone.now().isoformat()
            }
            
            async_to_sync(channel_layer.group_send)(
                "admin_dashboard",
                {
                    'type': 'send_message',
                    'message': message
                }
            )
            
            logger.debug(f"Broadcast to admin: {message_type}")
            return True
            
        except Exception as e:
            logger.error(f"Error broadcasting to admin: {str(e)}")
            return False