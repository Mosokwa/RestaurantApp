import logging
from django.utils import timezone
from ..models import Notification
from .websocket_services import WebSocketService

logger = logging.getLogger(__name__)

class NotificationService:
    
    @staticmethod
    def create_notification(user, notification_type, title, message, **kwargs):
        try:
            notification = Notification.objects.create(
                user=user,
                type=notification_type,
                title=title,
                message=message,
                image_url=kwargs.get('image_url'),
                action_url=kwargs.get('action_url'),
                action_text=kwargs.get('action_text'),
                data=kwargs.get('data', {}),
                order=kwargs.get('order'),
                restaurant=kwargs.get('restaurant'),
                priority=kwargs.get('priority', 'medium'),
                scheduled_for=kwargs.get('scheduled_for'),
                expires_at=kwargs.get('expires_at')
            )
            
            if not notification.scheduled_for or notification.scheduled_for <= timezone.now():
                NotificationService.send_notification(notification)
            
            return notification
            
        except Exception as e:
            logger.error(f"Error creating notification: {str(e)}")
            return None
    
    @staticmethod
    def send_notification(notification):
        try:
            preferences = notification.user.notification_preferences
            
            if not preferences.can_receive_notification(notification.type, 'websocket'):
                return False
            
            if preferences.enable_websocket:
                NotificationService.send_websocket_notification(notification)
            
            notification.mark_as_sent('websocket')
            return True
            
        except Exception as e:
            logger.error(f"Error sending notification {notification.notification_id}: {str(e)}")
            return False
    
    @staticmethod
    def send_websocket_notification(notification):
        try:
            message_data = {
                'notification_id': str(notification.notification_id),
                'type': notification.type,
                'title': notification.title,
                'message': notification.message,
                'image_url': notification.image_url,
                'action_url': notification.action_url,
                'action_text': notification.action_text,
                'data': notification.data,
                'priority': notification.priority,
                'created_at': notification.created_at.isoformat(),
                'is_read': notification.is_read
            }
            
            WebSocketService.broadcast_to_user(
                notification.user,
                'notification',
                message_data
            )
            
            notification.sent_via_websocket = True
            notification.save(update_fields=['sent_via_websocket'])
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending WebSocket notification: {str(e)}")
            return False
    
    @staticmethod
    def notify_order_status_update(order, old_status, new_status):
        try:
            customer = order.customer.user
            restaurant_name = order.restaurant.name
            status_display = dict(order.ORDER_STATUS_CHOICES).get(new_status, new_status)
            
            title = f"Order Status Updated"
            message = f"Your order from {restaurant_name} is now {status_display}"
            
            notification = NotificationService.create_notification(
                user=customer,
                notification_type='order_status',
                title=title,
                message=message,
                order=order,
                restaurant=order.restaurant,
                action_url=f"/orders/{order.order_uuid}",
                action_text="View Order",
                data={
                    'order_id': str(order.order_uuid),
                    'old_status': old_status,
                    'new_status': new_status,
                    'restaurant_name': restaurant_name
                }
            )
            
            return notification
            
        except Exception as e:
            logger.error(f"Error sending order status notification: {str(e)}")
            return None
        
    @staticmethod
    def send_notification(notification):
        """Enhanced to include push notifications"""
        try:
            preferences = notification.user.notification_preferences
            
            if not preferences.can_receive_notification(notification.type, 'websocket'):
                return False
            
            # Check quiet hours
            if preferences.is_quiet_hours() and notification.priority not in ['high', 'urgent']:
                logger.debug(f"Quiet hours active, skipping notification: {notification.notification_id}")
                return False
            
            # Send via WebSocket
            if preferences.enable_websocket:
                NotificationService.send_websocket_notification(notification)
            
            # Send via push notification
            if preferences.enable_push:
                from .push_service import PushNotificationService
                PushNotificationService.send_push_notification(notification)
            
            # Send via email
            if preferences.enable_email:
                NotificationService.send_email_notification(notification)
            
            notification.mark_as_sent('websocket')
            return True
            
        except Exception as e:
            logger.error(f"Error sending notification {notification.notification_id}: {str(e)}")
            return False