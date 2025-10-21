import json
import uuid
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.db import models

logger = logging.getLogger(__name__)

User = get_user_model()

class OrderTrackingConsumer(AsyncWebsocketConsumer):
    
    async def connect(self):
        try:
            self.order_id = self.scope['url_route']['kwargs']['order_id']
            self.user = self.scope['user']
            
            if self.user.is_anonymous:
                await self.close(code=4401)
                return
            
            # Use await with the sync_to_async function
            has_access = await self.has_order_access()
            if not has_access:
                await self.close(code=4403)
                return
            
            self.connection_id = str(uuid.uuid4())
            await self.register_connection()
            await self.accept()
            
            await self.channel_layer.group_add(f"order_{self.order_id}", self.channel_name)
            await self.send_initial_status()
            
            logger.info(f"Order tracking WebSocket connected: {self.connection_id}")
            
        except Exception as e:
            logger.error(f"Error in order tracking WebSocket connect: {str(e)}")
            await self.close(code=4400)
    
    async def disconnect(self, close_code):
        try:
            await self.channel_layer.group_discard(f"order_{self.order_id}", self.channel_name)
            await self.unregister_connection()
        except Exception as e:
            logger.error(f"Error in order tracking WebSocket disconnect: {str(e)}")
    
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ping':
                await self.send_pong()
            elif message_type == 'get_status':
                await self.send_current_status()
            else:
                await self.send_error("Unknown message type")
                
        except json.JSONDecodeError:
            await self.send_error("Invalid JSON format")
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {str(e)}")
            await self.send_error("Internal server error")
    
    async def send_message(self, event):
        try:
            await self.send(text_data=json.dumps(event['message']))
        except Exception as e:
            logger.error(f"Error sending WebSocket message: {str(e)}")
    
    async def order_update(self, event):
        await self.send_message(event)
    
    async def order_progress(self, event):
        await self.send_message(event)
    
    async def delivery_location(self, event):
        await self.send_message(event)
    
    # FIXED: Proper database_sync_to_async usage
    @database_sync_to_async
    def has_order_access(self):
        """Check if user has access to this order - SYNC FUNCTION"""
        try:
            from .models import Order, RestaurantStaff
            order = Order.objects.get(order_uuid=self.order_id)
            
            if self.user.user_type == 'customer' and order.customer.user == self.user:
                return True
            
            if self.user.user_type == 'owner' and order.restaurant.owner == self.user:
                return True
            
            if self.user.user_type == 'staff':
                return RestaurantStaff.objects.filter(
                    user=self.user,
                    restaurant=order.restaurant,
                    is_active=True
                ).exists()
            
            if self.user.user_type == 'admin':
                return True
            
            return False
            
        except ObjectDoesNotExist:
            return False
    
    @database_sync_to_async
    def register_connection(self):
        """Register WebSocket connection in database - SYNC FUNCTION"""
        from .services.websocket_services import WebSocketService
        
        groups = {'orders': [f"order_{self.order_id}"]}
        
        if self.user.user_type in ['owner', 'staff', 'admin']:
            try:
                from .models import Order
                order = Order.objects.get(order_uuid=self.order_id)
                groups['restaurants'] = [f"restaurant_{order.restaurant.restaurant_id}"]
            except ObjectDoesNotExist:
                pass
        
        WebSocketService.register_connection(
            user=self.user,
            connection_id=self.connection_id,
            connection_type=self.user.user_type,
            groups=groups,
            ip_address=self.get_client_ip(),
            user_agent=self.scope.get('headers', {}).get(b'user-agent', b'').decode()
        )
    
    @database_sync_to_async
    def unregister_connection(self):
        """Unregister WebSocket connection from database - SYNC FUNCTION"""
        from .services.websocket_services import WebSocketService
        WebSocketService.unregister_connection(self.connection_id)
    
    async def send_initial_status(self):
        """Send initial order status to client"""
        try:
            # Call the sync function with await
            await self._send_initial_status_sync()
        except Exception as e:
            logger.error(f"Error sending initial status: {str(e)}")
    
    @database_sync_to_async
    def _send_initial_status_sync(self):
        """Sync version of send_initial_status"""
        from .models import Order
        from .serializers import OrderSerializer
        
        order = Order.objects.select_related(
            'customer__user', 'restaurant', 'branch', 'delivery_address'
        ).prefetch_related('order_items', 'tracking_history').get(order_uuid=self.order_id)
        
        order_data = OrderSerializer(order).data
        
        # Send via WebSocket service
        from .services.websocket_services import WebSocketService
        WebSocketService.broadcast_to_user(
            self.user,
            'initial_status',
            {
                'order': order_data,
                'timestamp': timezone.now().isoformat()
            },
            exclude_connection_id=self.connection_id
        )
    
    async def send_current_status(self):
        """Send current order status"""
        try:
            await self._send_current_status_sync()
        except Exception as e:
            logger.error(f"Error sending current status: {str(e)}")
    
    @database_sync_to_async
    def _send_current_status_sync(self):
        """Sync version of send_current_status"""
        from .models import Order
        
        order = Order.objects.get(order_uuid=self.order_id)
        
        status_data = {
            'order_id': str(order.order_uuid),
            'status': order.status,
            'timestamp': timezone.now().isoformat()
        }
        
        from .services.websocket_services import WebSocketService
        WebSocketService.broadcast_to_user(
            self.user,
            'current_status',
            status_data,
            exclude_connection_id=self.connection_id
        )
    
    async def send_pong(self):
        await self.send(text_data=json.dumps({
            'type': 'pong',
            'timestamp': timezone.now().isoformat()
        }))
    
    async def send_error(self, message):
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message,
            'timestamp': timezone.now().isoformat()
        }))
    
    def get_client_ip(self):
        x_forwarded_for = self.scope.get('headers', {}).get(b'x-forwarded-for')
        if x_forwarded_for:
            return x_forwarded_for.decode().split(',')[0].strip()
        return self.scope.get('client', [None, None])[0]

class NotificationConsumer(AsyncWebsocketConsumer):
    
    async def connect(self):
        try:
            self.user = self.scope['user']
            
            if self.user.is_anonymous:
                await self.close(code=4401)
                return
            
            self.connection_id = str(uuid.uuid4())
            await self.register_connection()
            await self.accept()
            
            await self.channel_layer.group_add(f"customer_{self.user.id}", self.channel_name)
            await self.add_to_restaurant_groups()
            await self.send_unread_count()
            await self.send_recent_notifications()
            
            logger.info(f"Notification WebSocket connected: {self.connection_id}")
            
        except Exception as e:
            logger.error(f"Error in notification WebSocket connect: {str(e)}")
            await self.close(code=4400)
    
    async def disconnect(self, close_code):
        try:
            await self.channel_layer.group_discard(f"customer_{self.user.id}", self.channel_name)
            await self.remove_from_restaurant_groups()
            await self.unregister_connection()
        except Exception as e:
            logger.error(f"Error in notification WebSocket disconnect: {str(e)}")
    
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ping':
                await self.send_pong()
            elif message_type == 'mark_read':
                await self.handle_mark_read(data)
            elif message_type == 'mark_all_read':
                await self.handle_mark_all_read()
            elif message_type == 'get_notifications':
                await self.handle_get_notifications(data)
            else:
                await self.send_error("Unknown message type")
                
        except json.JSONDecodeError:
            await self.send_error("Invalid JSON format")
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {str(e)}")
            await self.send_error("Internal server error")
    
    async def send_message(self, event):
        try:
            await self.send(text_data=json.dumps(event['message']))
        except Exception as e:
            logger.error(f"Error sending WebSocket message: {str(e)}")
    
    async def notification(self, event):
        await self.send_message(event)
    
    @database_sync_to_async
    def register_connection(self):
        """Register WebSocket connection in database - SYNC FUNCTION"""
        from .services.websocket_services import WebSocketService
        
        groups = {'restaurants': self._get_restaurant_groups_sync()}
        
        WebSocketService.register_connection(
            user=self.user,
            connection_id=self.connection_id,
            connection_type=self.user.user_type,
            groups=groups,
            ip_address=self.get_client_ip(),
            user_agent=self.scope.get('headers', {}).get(b'user-agent', b'').decode()
        )
    
    def _get_restaurant_groups_sync(self):
        """Sync function to get restaurant groups"""
        if self.user.user_type not in ['owner', 'staff', 'admin']:
            return []
        
        restaurant_groups = []
        
        if self.user.user_type == 'owner':
            from .models import Restaurant
            owned_restaurants = Restaurant.objects.filter(owner=self.user)
            restaurant_groups.extend([f"restaurant_{r.restaurant_id}" for r in owned_restaurants])
        
        if self.user.user_type == 'staff':
            from .models import RestaurantStaff
            staff_assignments = RestaurantStaff.objects.filter(
                user=self.user,
                is_active=True
            ).select_related('restaurant')
            restaurant_groups.extend([f"restaurant_{a.restaurant.restaurant_id}" for a in staff_assignments])
        
        if self.user.user_type == 'admin':
            from .models import Restaurant
            all_restaurants = Restaurant.objects.all()
            restaurant_groups.extend([f"restaurant_{r.restaurant_id}" for r in all_restaurants])
        
        return restaurant_groups
    
    @database_sync_to_async
    def get_restaurant_groups(self):
        """Wrapper for sync function"""
        return self._get_restaurant_groups_sync()
    
    async def add_to_restaurant_groups(self):
        """Add connection to restaurant groups"""
        restaurant_groups = await self.get_restaurant_groups()
        for group in restaurant_groups:
            await self.channel_layer.group_add(group, self.channel_name)
    
    async def remove_from_restaurant_groups(self):
        """Remove connection from restaurant groups"""
        restaurant_groups = await self.get_restaurant_groups()
        for group in restaurant_groups:
            await self.channel_layer.group_discard(group, self.channel_name)
    
    @database_sync_to_async
    def unregister_connection(self):
        """Unregister WebSocket connection from database - SYNC FUNCTION"""
        from .services.websocket_services import WebSocketService
        WebSocketService.unregister_connection(self.connection_id)
    
    async def send_unread_count(self):
        """Send unread notifications count to client"""
        try:
            count = await self._get_unread_count_sync()
            await self.send(text_data=json.dumps({
                'type': 'unread_count',
                'data': {'count': count}
            }))
        except Exception as e:
            logger.error(f"Error sending unread count: {str(e)}")
    
    @database_sync_to_async
    def _get_unread_count_sync(self):
        """Sync function to get unread count"""
        from .models import Notification
        return Notification.objects.filter(user=self.user, is_read=False).count()
    
    async def send_recent_notifications(self):
        """Send recent notifications to client"""
        try:
            await self._send_recent_notifications_sync()
        except Exception as e:
            logger.error(f"Error sending recent notifications: {str(e)}")
    
    @database_sync_to_async
    def _send_recent_notifications_sync(self):
        """Sync function to send recent notifications"""
        from .models import Notification
        from .serializers import NotificationSerializer
        
        notifications = Notification.objects.filter(user=self.user).order_by('-created_at')[:10]
        serializer = NotificationSerializer(notifications, many=True)
        
        from .services.websocket_services import WebSocketService
        WebSocketService.broadcast_to_user(
            self.user,
            'recent_notifications',
            {'notifications': serializer.data},
            exclude_connection_id=self.connection_id
        )
    
    async def send_pong(self):
        await self.send(text_data=json.dumps({
            'type': 'pong',
            'timestamp': timezone.now().isoformat()
        }))
    
    async def send_error(self, message):
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message,
            'timestamp': timezone.now().isoformat()
        }))
    
    async def handle_mark_read(self, data):
        """Handle mark as read request"""
        try:
            await self._handle_mark_read_sync(data)
        except Exception as e:
            logger.error(f"Error marking notification as read: {str(e)}")
    
    @database_sync_to_async
    def _handle_mark_read_sync(self, data):
        """Sync function to handle mark read"""
        from .models import Notification
        
        notification_id = data.get('notification_id')
        if notification_id:
            try:
                notification = Notification.objects.get(notification_id=notification_id, user=self.user)
                notification.mark_as_read()
            except Notification.DoesNotExist:
                pass
    
    async def handle_mark_all_read(self):
        """Handle mark all as read request"""
        try:
            await self._handle_mark_all_read_sync()
            await self.send_unread_count()  # Send updated count
        except Exception as e:
            logger.error(f"Error marking all notifications as read: {str(e)}")
    
    @database_sync_to_async
    def _handle_mark_all_read_sync(self):
        """Sync function to handle mark all read"""
        from .models import Notification
        Notification.objects.filter(user=self.user, is_read=False).update(
            is_read=True, read_at=timezone.now()
        )
    
    async def handle_get_notifications(self, data):
        """Handle get notifications request"""
        try:
            await self._handle_get_notifications_sync(data)
        except Exception as e:
            logger.error(f"Error getting notifications: {str(e)}")
    
    @database_sync_to_async
    def _handle_get_notifications_sync(self, data):
        """Sync function to handle get notifications"""
        from .models import Notification
        from .serializers import NotificationSerializer
        
        limit = data.get('limit', 20)
        offset = data.get('offset', 0)
        
        notifications = Notification.objects.filter(user=self.user).order_by('-created_at')[offset:offset + limit]
        serializer = NotificationSerializer(notifications, many=True)
        
        from .services.websocket_services import WebSocketService
        WebSocketService.broadcast_to_user(
            self.user,
            'notifications_list',
            {
                'notifications': serializer.data,
                'has_more': notifications.count() == limit
            },
            exclude_connection_id=self.connection_id
        )
    
    def get_client_ip(self):
        x_forwarded_for = self.scope.get('headers', {}).get(b'x-forwarded-for')
        if x_forwarded_for:
            return x_forwarded_for.decode().split(',')[0].strip()
        return self.scope.get('client', [None, None])[0]

# Simplified RestaurantDashboardConsumer for now
class RestaurantDashboardConsumer(AsyncWebsocketConsumer):
    
    async def connect(self):
        try:
            self.restaurant_id = self.scope['url_route']['kwargs']['restaurant_id']
            self.user = self.scope['user']
            
            if self.user.is_anonymous:
                await self.close(code=4401)
                return
            
            await self.accept()
            await self.channel_layer.group_add(f"restaurant_{self.restaurant_id}", self.channel_name)
            
            await self.send(text_data=json.dumps({
                'type': 'connected',
                'message': f'Connected to restaurant {self.restaurant_id} dashboard'
            }))
            
        except Exception as e:
            logger.error(f"Error in restaurant dashboard WebSocket connect: {str(e)}")
            await self.close(code=4400)
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(f"restaurant_{self.restaurant_id}", self.channel_name)
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        if data.get('type') == 'ping':
            await self.send_pong()
    
    async def send_message(self, event):
        await self.send(text_data=json.dumps(event['message']))
    
    async def order_update(self, event):
        await self.send_message(event)
    
    async def inventory_update(self, event):
        await self.send_message(event)
    
    async def send_pong(self):
        await self.send(text_data=json.dumps({
            'type': 'pong',
            'timestamp': timezone.now().isoformat()
        }))


class POSRealtimeConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time POS updates - FULLY IMPLEMENTED"""
    
    async def connect(self):
        user = await self.get_user()
        if not user or not user.is_authenticated:
            await self.close()
            return
        
        self.order_group_name = None
        self.restaurant_group_name = None
        self.kitchen_group_name = None
        
        await self.accept()
        logger.info("WebSocket connected")

    async def disconnect(self, close_code):
        if self.order_group_name:
            await self.channel_layer.group_discard(
                self.order_group_name,
                self.channel_name
            )
        if self.restaurant_group_name:
            await self.channel_layer.group_discard(
                self.restaurant_group_name,
                self.channel_name
            )
        if self.kitchen_group_name:
            await self.channel_layer.group_discard(
                self.kitchen_group_name,
                self.channel_name
            )
        logger.info("WebSocket disconnected")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'subscribe_order':
                await self.handle_order_subscription(data)
            elif message_type == 'subscribe_restaurant':
                await self.handle_restaurant_subscription(data)
            elif message_type == 'subscribe_kitchen':
                await self.handle_kitchen_subscription(data)
            elif message_type == 'kitchen_update':
                await self.handle_kitchen_update(data)
            elif message_type == 'order_status_update':
                await self.handle_order_status_update(data)
            elif message_type == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong', 'timestamp': timezone.now().isoformat()}))
            else:
                await self.send_error(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            await self.send_error("Invalid JSON format")
        except Exception as e:
            await self.send_error(f"Error processing message: {str(e)}")

    async def handle_order_subscription(self, data):
        order_uuid = data.get('order_uuid')
        if order_uuid:
            self.order_group_name = f'order_{order_uuid}'
            await self.channel_layer.group_add(
                self.order_group_name,
                self.channel_name
            )
            await self.send_success(f"Subscribed to order {order_uuid}")
            
            # Send current order status
            order_data = await self.get_order_data(order_uuid)
            if order_data:
                await self.send(text_data=json.dumps({
                    'type': 'order_status',
                    'order_data': order_data,
                    'timestamp': timezone.now().isoformat()
                }))

    async def handle_restaurant_subscription(self, data):
        restaurant_id = data.get('restaurant_id')
        if restaurant_id:
            self.restaurant_group_name = f'restaurant_{restaurant_id}'
            await self.channel_layer.group_add(
                self.restaurant_group_name,
                self.channel_name
            )
            await self.send_success(f"Subscribed to restaurant {restaurant_id}")

    async def handle_kitchen_subscription(self, data):
        restaurant_id = data.get('restaurant_id')
        if restaurant_id:
            self.kitchen_group_name = f'kitchen_{restaurant_id}'
            await self.channel_layer.group_add(
                self.kitchen_group_name,
                self.channel_name
            )
            await self.send_success(f"Subscribed to kitchen {restaurant_id}")
            
            # Send current kitchen status
            kitchen_status = await self.get_kitchen_status(restaurant_id)
            await self.send(text_data=json.dumps({
                'type': 'kitchen_status',
                'status': kitchen_status,
                'timestamp': timezone.now().isoformat()
            }))

    async def handle_kitchen_update(self, data):
        item_id = data.get('item_id')
        status = data.get('status')
        station_id = data.get('station_id')
        notes = data.get('notes', '')
        
        try:
            # Update item status in database
            success = await self.update_item_status(item_id, status, station_id, notes)
            
            if success:
                # Broadcast update to relevant groups
                await self.broadcast_kitchen_update(item_id, status, station_id, notes)
                await self.send_success(f"Item {item_id} status updated to {status}")
            else:
                await self.send_error(f"Failed to update item {item_id}")

        except Exception as e:
            await self.send_error(f"Failed to update kitchen status: {str(e)}")

    async def handle_order_status_update(self, data):
        order_uuid = data.get('order_uuid')
        status = data.get('status')
        
        try:
            success = await self.update_order_status(order_uuid, status)
            if success:
                await self.broadcast_order_status_update(order_uuid, status)
                await self.send_success(f"Order {order_uuid} status updated to {status}")
            else:
                await self.send_error(f"Failed to update order {order_uuid} status")

        except Exception as e:
            await self.send_error(f"Failed to update order status: {str(e)}")

    @database_sync_to_async
    def check_order_permission(self, order_uuid):
        """Check if user has permission to access this order"""
        from .models import Order
        from .permissions import IsRestaurantOwner, IsCustomer
        
        try:
            order = Order.objects.get(order_uuid=order_uuid)
            
            # Restaurant owners can access orders from their restaurants
            if self.user.user_type == 'owner':
                return order.restaurant.owner == self.user
            
            # Customers can access their own orders
            if self.user.user_type == 'customer':
                return order.customer.user == self.user
            
            # Staff can access orders from their restaurant
            if self.user.user_type == 'staff':
                from .models import RestaurantStaff
                return RestaurantStaff.objects.filter(
                    user=self.user,
                    restaurant=order.restaurant
                ).exists()
            
            return False
            
        except Order.DoesNotExist:
            return False

    @database_sync_to_async
    def get_order_data(self, order_uuid):
        from api.models import Order
        try:
            order = Order.objects.select_related(
                'pos_info', 'restaurant', 'branch'
            ).prefetch_related(
                'order_items__preparation_info__assigned_station',
                'order_items__menu_item'
            ).get(order_uuid=order_uuid)
            
            return {
                'order_uuid': str(order.order_uuid),
                'status': order.status,
                'total_amount': str(order.total_amount),
                'order_type': order.order_type,
                'table_number': order.pos_info.table_number if hasattr(order, 'pos_info') else None,
                'items': [
                    {
                        'item_id': item.order_item_id,
                        'name': item.menu_item.name,
                        'quantity': item.quantity,
                        'status': item.preparation_info.preparation_status if hasattr(item, 'preparation_info') else 'pending',
                        'station': item.preparation_info.assigned_station.name if hasattr(item, 'preparation_info') and item.preparation_info.assigned_station else None
                    }
                    for item in order.order_items.all()
                ],
                'estimated_ready_at': order.pos_info.estimated_ready_at.isoformat() if hasattr(order, 'pos_info') and order.pos_info.estimated_ready_at else None
            }
        except Order.DoesNotExist:
            return None

    @database_sync_to_async
    def get_kitchen_status(self, restaurant_id):
        from api.models import KitchenStation, OrderItemPreparation
        from django.utils import timezone
        
        stations = KitchenStation.objects.filter(restaurant_id=restaurant_id, is_available=True)
        
        status_data = {
            'stations': [],
            'active_orders': 0,
            'items_preparing': 0,
            'items_ready': 0
        }
        
        for station in stations:
            workload = station.get_current_workload()
            active_items = OrderItemPreparation.objects.filter(
                assigned_station=station,
                preparation_status__in=['preparing', 'pending']
            ).count()
            
            station_data = {
                'station_id': station.station_id,
                'name': station.name,
                'type': station.station_type,
                'workload': workload,
                'active_items': active_items,
                'assigned_staff': list(station.assigned_staff.values_list('user__username', flat=True))
            }
            status_data['stations'].append(station_data)
        
        status_data['active_orders'] = OrderItemPreparation.objects.filter(
            order_item__order__restaurant_id=restaurant_id,
            preparation_status__in=['pending', 'preparing']
        ).values('order_item__order').distinct().count()
        
        status_data['items_preparing'] = OrderItemPreparation.objects.filter(
            order_item__order__restaurant_id=restaurant_id,
            preparation_status='preparing'
        ).count()
        
        status_data['items_ready'] = OrderItemPreparation.objects.filter(
            order_item__order__restaurant_id=restaurant_id,
            preparation_status='ready'
        ).count()
        
        return status_data

    @database_sync_to_async
    def update_item_status(self, item_id, status, station_id, notes):
        from api.models import OrderItemPreparation, KitchenStation
        
        try:
            prep_info = OrderItemPreparation.objects.get(order_item_id=item_id)
            
            if status == 'started':
                prep_info.preparation_status = 'preparing'
                prep_info.preparation_started_at = timezone.now()
            elif status == 'ready':
                prep_info.preparation_status = 'ready'
                prep_info.actual_completion_at = timezone.now()
                prep_info.quality_notes = notes
            elif status == 'served':
                prep_info.preparation_status = 'served'
            elif status == 'cancelled':
                prep_info.preparation_status = 'cancelled'
            
            if station_id:
                try:
                    station = KitchenStation.objects.get(station_id=station_id)
                    prep_info.assigned_station = station
                except KitchenStation.DoesNotExist:
                    pass
            
            prep_info.save()
            
            # Check if all items in order are ready
            order_item = prep_info.order_item
            order = order_item.order
            self._check_order_readiness(order)
            
            return True
            
        except OrderItemPreparation.DoesNotExist:
            return False

    def _check_order_readiness(self, order):
        """Check if all order items are ready"""
        from api.models import OrderItemPreparation
        from django.utils import timezone
        
        if not order.order_items.filter(
            preparation_info__preparation_status__in=['pending', 'preparing']
        ).exists():
            # All items are ready or served
            if hasattr(order, 'pos_info'):
                order.pos_info.actual_ready_at = timezone.now()
                order.pos_info.save()
            
            if order.status == 'preparing':
                order.status = 'ready'
                order.save()

    @database_sync_to_async
    def update_order_status(self, order_uuid, status):
        from api.models import Order
        
        try:
            order = Order.objects.get(order_uuid=order_uuid)
            order.status = status
            order.save()
            
            # Sync to POS if connected
            if hasattr(order, 'pos_info'):
                order.pos_info.sync_to_pos()
            
            return True
            
        except Order.DoesNotExist:
            return False

    async def broadcast_kitchen_update(self, item_id, status, station_id, notes):
        order_info = await self.get_order_info_for_item(item_id)
        if order_info:
            # Broadcast to order group
            await self.channel_layer.group_send(
                f"order_{order_info['order_uuid']}",
                {
                    'type': 'kitchen_status_update',
                    'item_id': item_id,
                    'status': status,
                    'station_id': station_id,
                    'notes': notes,
                    'timestamp': timezone.now().isoformat()
                }
            )
            
            # Broadcast to restaurant group
            await self.channel_layer.group_send(
                f"restaurant_{order_info['restaurant_id']}",
                {
                    'type': 'kitchen_broadcast',
                    'item_id': item_id,
                    'order_uuid': order_info['order_uuid'],
                    'status': status,
                    'station_id': station_id,
                    'timestamp': timezone.now().isoformat()
                }
            )
            
            # Broadcast to kitchen group
            await self.channel_layer.group_send(
                f"kitchen_{order_info['restaurant_id']}",
                {
                    'type': 'item_status_update',
                    'item_id': item_id,
                    'order_uuid': order_info['order_uuid'],
                    'status': status,
                    'station_id': station_id,
                    'timestamp': timezone.now().isoformat()
                }
            )

    async def broadcast_order_status_update(self, order_uuid, status):
        order_info = await self.get_order_info(order_uuid)
        if order_info:
            await self.channel_layer.group_send(
                f"order_{order_uuid}",
                {
                    'type': 'order_status_update',
                    'order_uuid': order_uuid,
                    'status': status,
                    'timestamp': timezone.now().isoformat()
                }
            )
            
            await self.channel_layer.group_send(
                f"restaurant_{order_info['restaurant_id']}",
                {
                    'type': 'order_status_broadcast',
                    'order_uuid': order_uuid,
                    'status': status,
                    'timestamp': timezone.now().isoformat()
                }
            )

    @database_sync_to_async
    def get_order_info_for_item(self, item_id):
        from api.models import OrderItem
        
        try:
            order_item = OrderItem.objects.select_related('order').get(
                order_item_id=item_id
            )
            return {
                'order_uuid': str(order_item.order.order_uuid),
                'restaurant_id': order_item.order.restaurant_id
            }
        except OrderItem.DoesNotExist:
            return None

    @database_sync_to_async
    def get_order_info(self, order_uuid):
        from api.models import Order
        
        try:
            order = Order.objects.get(order_uuid=order_uuid)
            return {
                'restaurant_id': order.restaurant_id
            }
        except Order.DoesNotExist:
            return None

    # Handler methods for group messages
    async def kitchen_status_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'kitchen_status_update',
            'item_id': event['item_id'],
            'status': event['status'],
            'station_id': event['station_id'],
            'notes': event.get('notes', ''),
            'timestamp': event['timestamp']
        }))

    async def kitchen_broadcast(self, event):
        await self.send(text_data=json.dumps({
            'type': 'kitchen_broadcast',
            'item_id': event['item_id'],
            'order_uuid': event['order_uuid'],
            'status': event['status'],
            'station_id': event['station_id'],
            'timestamp': event['timestamp']
        }))

    async def item_status_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'item_status_update',
            'item_id': event['item_id'],
            'order_uuid': event['order_uuid'],
            'status': event['status'],
            'station_id': event['station_id'],
            'timestamp': event['timestamp']
        }))

    async def order_status_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'order_status_update',
            'order_uuid': event['order_uuid'],
            'status': event['status'],
            'timestamp': event['timestamp']
        }))

    async def order_status_broadcast(self, event):
        await self.send(text_data=json.dumps({
            'type': 'order_status_broadcast',
            'order_uuid': event['order_uuid'],
            'status': event['status'],
            'timestamp': event['timestamp']
        }))

    async def send_success(self, message):
        await self.send(text_data=json.dumps({
            'type': 'success',
            'message': message,
            'timestamp': timezone.now().isoformat()
        }))

    async def send_error(self, error):
        await self.send(text_data=json.dumps({
            'type': 'error',
            'error': error,
            'timestamp': timezone.now().isoformat()
        }))

class KitchenManagementConsumer(AsyncWebsocketConsumer):
    """
    NEW: Real-time kitchen order management
    PATH: /ws/kitchen/{restaurant_id}/management/
    """
    
    async def connect(self):
        self.restaurant_id = self.scope['url_route']['kwargs']['restaurant_id']
        self.room_group_name = f'kitchen_{self.restaurant_id}'
        
        user = await self.get_user()
        if not user or not await self.has_kitchen_access(user):
            await self.close()
            return
        
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        
        # Send current kitchen status
        await self.send_kitchen_status()
        
        logger.info(f"Kitchen management connected: {self.channel_name}")
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        logger.info(f"Kitchen management disconnected: {self.channel_name}")
    
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            action = data.get('action')
            
            if action == 'acknowledge_order':
                await self.handle_order_acknowledgement(data)
            elif action == 'update_item_status':
                await self.handle_item_status_update(data)
            elif action == 'assign_station':
                await self.handle_station_assignment(data)
            elif action == 'request_help':
                await self.handle_help_request(data)
                
        except Exception as e:
            logger.error(f"Kitchen management error: {str(e)}")
            await self.send_error(str(e))
    
    async def handle_order_acknowledgement(self, data):
        """NEW: Handle order acknowledgement from kitchen"""
        order_id = data['order_id']
        station_id = data.get('station_id')
        
        success = await self.acknowledge_order_in_db(order_id, station_id)
        
        if success:
            # Broadcast to kitchen and order tracking
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'order_acknowledged',
                    'order_id': order_id,
                    'station_id': station_id,
                    'timestamp': timezone.now().isoformat()
                }
            )
            
            from .services.websocket_services import WebSocketService
            WebSocketService.broadcast_to_order(
                order_id,
                'kitchen_acknowledged',
                {'order_id': order_id, 'station_id': station_id}
            )
    
    async def order_acknowledged(self, event):
        await self.send(text_data=json.dumps(event))
    
    async def item_status_updated(self, event):
        await self.send(text_data=json.dumps(event))
    
    async def station_assigned(self, event):
        await self.send(text_data=json.dumps(event))
    
    async def help_requested(self, event):
        await self.send(text_data=json.dumps(event))
    
    # Database methods...
    @database_sync_to_async
    def get_user(self):
        return self.scope.get('user')
    
    @database_sync_to_async
    def has_kitchen_access(self, user):
        from .models import RestaurantStaff
        return RestaurantStaff.objects.filter(
            user=user,
            restaurant_id=self.restaurant_id,
            is_active=True,
            role__in=['kitchen_staff', 'kitchen_manager', 'chef']
        ).exists()
    
    @database_sync_to_async
    def acknowledge_order_in_db(self, order_id, station_id):
        from .models import Order
        try:
            order = Order.objects.get(order_id=order_id, restaurant_id=self.restaurant_id)
            order.status = 'preparing'
            order.preparation_started_at = timezone.now()
            order.save()
            return True
        except Order.DoesNotExist:
            return False

class POSSynchronizationConsumer(AsyncWebsocketConsumer):
    """
    NEW: Real-time POS synchronization management
    PATH: /ws/pos/{restaurant_id}/sync/
    """
    
    async def connect(self):
        self.restaurant_id = self.scope['url_route']['kwargs']['restaurant_id']
        self.room_group_name = f'pos_sync_{self.restaurant_id}'
        
        user = await self.get_user()
        if not user or not await self.has_pos_access(user):
            await self.close()
            return
        
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        
        # Send current sync status
        await self.send_sync_status()
        
        logger.info(f"POS synchronization connected: {self.channel_name}")
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        logger.info(f"POS synchronization disconnected: {self.channel_name}")
    
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            action = data.get('action')
            
            if action == 'sync_menu':
                await self.handle_menu_sync(data)
            elif action == 'sync_inventory':
                await self.handle_inventory_sync(data)
            elif action == 'test_connection':
                await self.handle_connection_test(data)
                
        except Exception as e:
            logger.error(f"POS sync error: {str(e)}")
            await self.send_error(str(e))
    
    async def handle_menu_sync(self, data):
        """NEW: Handle manual menu sync request"""
        from .tasks import periodic_pos_menu_sync
        periodic_pos_menu_sync.delay()
        
        await self.send(text_data=json.dumps({
            'type': 'sync_initiated',
            'sync_type': 'menu',
            'timestamp': timezone.now().isoformat()
        }))
    
    async def sync_start(self, event):
        await self.send(text_data=json.dumps(event))
    
    async def sync_complete(self, event):
        await self.send(text_data=json.dumps(event))
    
    async def sync_error(self, event):
        await self.send(text_data=json.dumps(event))
    
    @database_sync_to_async
    def get_user(self):
        return self.scope.get('user')
    
    @database_sync_to_async
    def has_pos_access(self, user):
        from .models import RestaurantStaff
        return RestaurantStaff.objects.filter(
            user=user,
            restaurant_id=self.restaurant_id,
            is_active=True,
            role__in=['manager', 'pos_manager', 'admin']
        ).exists()
    
    @database_sync_to_async
    def send_sync_status(self):
        from .models import POSConnection, POSSyncLog
        from datetime import timedelta
        
        connections = POSConnection.objects.filter(restaurant_id=self.restaurant_id)
        connection_status = []
        
        for connection in connections:
            recent_logs = POSSyncLog.objects.filter(
                connection=connection,
                started_at__gte=timezone.now() - timedelta(hours=24)
            ).order_by('-started_at')[:5]
            
            connection_status.append({
                'connection_id': connection.connection_id,
                'name': connection.connection_name,
                'sync_status': connection.sync_status,
                'last_sync': connection.last_sync.isoformat() if connection.last_sync else None,
                'recent_logs': [
                    {
                        'sync_type': log.sync_type,
                        'status': log.status,
                        'started_at': log.started_at.isoformat()
                    }
                    for log in recent_logs
                ]
            })
        
        from .services.websocket_services import WebSocketService
        WebSocketService.broadcast_to_pos_sync(
            self.restaurant_id,
            'sync_status',
            {'connections': connection_status}
        )

class TableManagementConsumer(AsyncWebsocketConsumer):
    """
    NEW: Real-time table status management
    PATH: /ws/tables/{restaurant_id}/management/
    """
    
    async def connect(self):
        self.restaurant_id = self.scope['url_route']['kwargs']['restaurant_id']
        self.room_group_name = f'tables_{self.restaurant_id}'
        
        user = await self.get_user()
        if not user or not await self.has_table_access(user):
            await self.close()
            return
        
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        
        # Send current table status
        await self.send_table_status()
        
        logger.info(f"Table management connected: {self.channel_name}")
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        logger.info(f"Table management disconnected: {self.channel_name}")
    
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            action = data.get('action')
            
            if action == 'update_status':
                await self.handle_status_update(data)
            elif action == 'assign_customer':
                await self.handle_customer_assignment(data)
            elif action == 'request_clean':
                await self.handle_clean_request(data)
                
        except Exception as e:
            logger.error(f"Table management error: {str(e)}")
            await self.send_error(str(e))
    
    async def handle_status_update(self, data):
        """NEW: Handle table status update"""
        table_id = data['table_id']
        status = data['status']
        
        success = await self.update_table_status(table_id, status)
        
        if success:
            # Broadcast to table management and kitchen
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'table_status_updated',
                    'table_id': table_id,
                    'status': status,
                    'timestamp': timezone.now().isoformat()
                }
            )
    
    async def table_status_updated(self, event):
        await self.send(text_data=json.dumps(event))
    
    async def customer_assigned(self, event):
        await self.send(text_data=json.dumps(event))
    
    async def clean_requested(self, event):
        await self.send(text_data=json.dumps(event))
    
    @database_sync_to_async
    def get_user(self):
        return self.scope.get('user')
    
    @database_sync_to_async
    def has_table_access(self, user):
        from .models import RestaurantStaff
        return RestaurantStaff.objects.filter(
            user=user,
            restaurant_id=self.restaurant_id,
            is_active=True,
            role__in=['host', 'floor_manager', 'manager']
        ).exists()
    
    @database_sync_to_async
    def update_table_status(self, table_id, status):
        from .models import Table
        try:
            table = Table.objects.get(table_id=table_id, restaurant_id=self.restaurant_id)
            table.status = status
            table.save()
            return True
        except Table.DoesNotExist:
            return False
    
    @database_sync_to_async
    def send_table_status(self):
        from .models import Table
        
        tables = Table.objects.filter(restaurant_id=self.restaurant_id)
        table_status = [
            {
                'table_id': table.table_id,
                'table_number': table.table_number,
                'status': table.status,
                'capacity': table.capacity
            }
            for table in tables
        ]
        
        from .services.websocket_services import WebSocketService
        WebSocketService.broadcast_to_table_management(
            self.restaurant_id,
            'table_status',
            {'tables': table_status}
        )
