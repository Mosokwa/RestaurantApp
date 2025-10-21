from __future__ import absolute_import, unicode_literals
from celery import shared_task
from django.core.management import call_command
from django.utils import timezone
from datetime import timedelta
from logging import getLogger

logger = getLogger(__name__)

@shared_task
def update_popularity_scores_task():
    """Celery task to update popularity scores"""
    try:
        call_command('update_popularity_scores')
        return "Popularity scores updated successfully"
    except Exception as e:
        return f"Error updating popularity scores: {str(e)}"

@shared_task
def update_user_preferences_task():
    """Celery task to update all user preferences"""
    from .recommendation_engine import RecommendationEngine
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    engine = RecommendationEngine()
    
    updated_count = 0
    for user in User.objects.filter(is_active=True):
        try:
            engine.calculate_user_preferences(user)
            updated_count += 1
        except Exception as e:
            print(f"Error updating preferences for user {user.id}: {e}")
    
    return f"Updated preferences for {updated_count} users"

@shared_task
def cleanup_old_recommendations_task():
    """Clean up expired recommendations"""
    from .models import Recommendation
    
    expired_count = Recommendation.objects.filter(
        expires_at__lt=timezone.now()
    ).update(is_active=False)
    
    # Delete very old recommendations (older than 30 days)
    old_date = timezone.now() - timedelta(days=30)
    deleted_count = Recommendation.objects.filter(
        generated_at__lt=old_date
    ).delete()[0]
    
    return f"Deactivated {expired_count} expired recommendations, deleted {deleted_count} old records"

@shared_task
def calculate_item_associations_task():
    """Calculate item associations based on order history"""
    from .models import Order, MenuItem, ItemAssociation
    from django.db.models import Count
    
    # This is a more sophisticated version that analyzes all orders
    orders = Order.objects.filter(status='delivered').prefetch_related('order_items')
    
    for order in orders:
        items_in_order = list(order.order_items.values_list('menu_item', flat=True))
        
        # Create associations between all items in this order
        for i, item_a_id in enumerate(items_in_order):
            for item_b_id in items_in_order[i+1:]:
                # Update or create association
                association, created = ItemAssociation.objects.get_or_create(
                    source_item_id=item_a_id,
                    target_item_id=item_b_id,
                    defaults={'support': 1, 'confidence': 0.1}
                )
                
                if not created:
                    association.support += 1
                    association.save()
    
    return "Item associations calculated successfully"

# ========== NEW TASKS - REAL-TIME SYNC & MONITORING ==========

@shared_task
def periodic_pos_menu_sync():
    """
    NEW: Periodic POS menu synchronization
    INTEGRATES WITH: Your existing POSConnection.sync_menu_items()
    """
    try:
        from .models import POSConnection
        
        active_connections = POSConnection.objects.filter(
            is_active=True, 
            auto_sync_menu=True,
            sync_status='connected'
        ).select_related('restaurant')
        
        synced_count = 0
        for connection in active_connections:
            try:
                # Use your existing sync method
                success, result = connection.sync_menu_items()
                if success:
                    synced_count += 1
                    logger.info(f"Menu sync successful for {connection.restaurant.name}")
                    
                    # NEW: Broadcast real-time update
                    from .services.websocket_services import WebSocketService
                    WebSocketService.broadcast_to_restaurant(
                        connection.restaurant_id,
                        'pos_sync_complete',
                        {'sync_type': 'menu', 'result': result}
                    )
                else:
                    logger.error(f"Menu sync failed for {connection.restaurant.name}")
                    
            except Exception as e:
                logger.error(f"Menu sync error for {connection.restaurant.name}: {str(e)}")
        
        return f"POS menu sync completed: {synced_count} successful"
        
    except Exception as e:
        logger.error(f"Periodic POS menu sync failed: {str(e)}")
        return f"POS menu sync failed: {str(e)}"

@shared_task
def periodic_pos_inventory_sync():
    """
    NEW: Periodic POS inventory synchronization  
    INTEGRATES WITH: Your existing POSConnection.sync_inventory()
    """
    try:
        from .models import POSConnection
        
        active_connections = POSConnection.objects.filter(
            is_active=True, 
            auto_sync_inventory=True,
            sync_status='connected'
        ).select_related('restaurant')
        
        synced_count = 0
        for connection in active_connections:
            try:
                # Use your existing sync method
                success, result = connection.sync_inventory()
                if success:
                    synced_count += 1
                    logger.info(f"Inventory sync successful for {connection.restaurant.name}")
                    
                    # NEW: Broadcast real-time update
                    from .services.websocket_services import WebSocketService
                    WebSocketService.broadcast_to_restaurant(
                        connection.restaurant_id,
                        'pos_sync_complete', 
                        {'sync_type': 'inventory', 'result': result}
                    )
                else:
                    logger.error(f"Inventory sync failed for {connection.restaurant.name}")
                    
            except Exception as e:
                logger.error(f"Inventory sync error for {connection.restaurant.name}: {str(e)}")
        
        return f"POS inventory sync completed: {synced_count} successful"
        
    except Exception as e:
        logger.error(f"Periodic POS inventory sync failed: {str(e)}")
        return f"POS inventory sync failed: {str(e)}"

@shared_task
def sync_single_order_to_pos(order_id):
    """
    NEW: Sync single order to POS with real-time tracking
    INTEGRATES WITH: Your existing OrderPOSInfo.sync_to_pos()
    """
    try:
        from .models import Order
        
        order = Order.objects.select_related('restaurant').get(order_id=order_id)
        
        # NEW: Broadcast sync start
        from .services.websocket_services import WebSocketService
        WebSocketService.broadcast_to_order(
            order.order_id,
            'pos_sync_start',
            {'order_id': order_id}
        )
        
        if hasattr(order, 'pos_info'):
            # Use your existing sync method
            success, message = order.pos_info.sync_to_pos()
            
            if success:
                logger.info(f"Order {order_id} synced to POS successfully")
                
                # NEW: Broadcast success
                WebSocketService.broadcast_to_order(
                    order.order_id,
                    'pos_sync_complete',
                    {'order_id': order_id, 'pos_order_id': order.pos_info.pos_order_id}
                )
                return f"Order {order_id} synced to POS"
            else:
                logger.error(f"Order {order_id} POS sync failed: {message}")
                
                # NEW: Broadcast failure
                WebSocketService.broadcast_to_order(
                    order.order_id, 
                    'pos_sync_error',
                    {'order_id': order_id, 'error': message}
                )
                return f"Order {order_id} sync failed: {message}"
        else:
            logger.warning(f"Order {order_id} has no POS info")
            return f"Order {order_id} has no POS info"
            
    except Order.DoesNotExist:
        logger.error(f"Order {order_id} not found for POS sync")
        return f"Order {order_id} not found"
    except Exception as e:
        logger.error(f"Order sync failed for {order_id}: {str(e)}")
        return f"Order sync failed: {str(e)}"

@shared_task
def run_system_health_check():
    """
    NEW: Comprehensive system health monitoring
    INTEGRATES WITH: Your existing models and services
    """
    try:
        from .services.health_monitoring import HealthMonitoringService
        
        monitor = HealthMonitoringService()
        health_report = monitor.check_system_health()
        
        # NEW: Broadcast health status
        from .services.websocket_services import WebSocketService
        WebSocketService.broadcast_to_admin(
            'system_health_update',
            health_report
        )
        
        logger.info(f"System health check completed: {health_report['overall_status']}")
        return f"Health check: {health_report['overall_status']}"
        
    except Exception as e:
        logger.error(f"Health monitoring failed: {str(e)}")
        return f"Health monitoring failed: {str(e)}"

@shared_task
def resolve_data_conflicts():
    """
    NEW: Automated data conflict resolution
    INTEGRATES WITH: Your existing models and business logic
    """
    try:
        from .services.conflict_resolution import ConflictResolutionService
        
        resolver = ConflictResolutionService()
        results = resolver.detect_and_resolve_all_conflicts()
        
        logger.info(f"Conflict resolution completed: {results}")
        return f"Resolved {results['resolved']} conflicts, {results['remaining']} remaining"
        
    except Exception as e:
        logger.error(f"Conflict resolution failed: {str(e)}")
        return f"Conflict resolution failed: {str(e)}"

@shared_task  
def cleanup_old_websocket_connections():
    """
    NEW: Clean up stale WebSocket connections
    INTEGRATES WITH: Your existing WebSocketConnection model
    """
    try:
        from .models import WebSocketConnection
        
        cutoff_time = timezone.now() - timedelta(hours=24)
        old_connections = WebSocketConnection.objects.filter(
            last_activity__lt=cutoff_time,
            is_active=True
        )
        
        count = old_connections.count()
        old_connections.update(is_active=False, disconnected_at=timezone.now())
        
        logger.info(f"Cleaned up {count} old WebSocket connections")
        return f"Cleaned up {count} old connections"
        
    except Exception as e:
        logger.error(f"WebSocket cleanup failed: {str(e)}")
        return f"WebSocket cleanup failed: {str(e)}"