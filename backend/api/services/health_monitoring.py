import logging
import time
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import connection
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)

class HealthMonitoringService:
    """
    NEW: Comprehensive system health monitoring
    INTEGRATES WITH: Your existing models and WebSocket system
    """
    
    def __init__(self):
        self.channel_layer = get_channel_layer()
    
    def check_system_health(self, restaurant_id=None):
        """
        NEW: Perform comprehensive system health check
        """
        health_report = {
            'timestamp': timezone.now().isoformat(),
            'overall_status': 'healthy',
            'components': {},
            'alerts': []
        }
        
        # Check database health
        db_health = self._check_database_health()
        health_report['components']['database'] = db_health
        
        # Check WebSocket connections
        ws_health = self._check_websocket_health(restaurant_id)
        health_report['components']['websocket'] = ws_health
        
        # Check POS connections
        pos_health = self._check_pos_health(restaurant_id)
        health_report['components']['pos'] = pos_health
        
        # Check synchronization status
        sync_health = self._check_sync_health(restaurant_id)
        health_report['components']['synchronization'] = sync_health
        
        # Determine overall status
        if any(comp['status'] == 'critical' for comp in health_report['components'].values()):
            health_report['overall_status'] = 'critical'
        elif any(comp['status'] == 'warning' for comp in health_report['components'].values()):
            health_report['overall_status'] = 'warning'
        
        # Broadcast health status
        self._broadcast_health_status(restaurant_id, health_report)
        
        return health_report
    
    def _check_database_health(self):
        """
        NEW: Check database connection and performance
        """
        try:
            start_time = time.time()
            
            # Test database connection using your existing connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            
            response_time = (time.time() - start_time) * 1000
            
            status = 'healthy'
            if response_time > 1000:
                status = 'warning'
            elif response_time > 5000:
                status = 'critical'
            
            return {
                'status': status,
                'response_time_ms': round(response_time, 2),
                'details': 'Database connection successful'
            }
            
        except Exception as e:
            return {
                'status': 'critical',
                'error': str(e),
                'details': 'Database connection failed'
            }
    
    def _check_websocket_health(self, restaurant_id):
        """
        NEW: Check WebSocket connections health
        INTEGRATES WITH: Your existing WebSocketConnection model
        """
        try:
            from ..models import WebSocketConnection
            
            # Count active connections
            active_connections = WebSocketConnection.objects.filter(is_active=True)
            
            if restaurant_id:
                active_connections = active_connections.filter(
                    restaurant_groups__contains=[f"restaurant_{restaurant_id}"]
                )
            
            connection_count = active_connections.count()
            
            # Check connection age
            old_connections = active_connections.filter(
                last_activity__lt=timezone.now() - timedelta(hours=1)
            )
            stale_count = old_connections.count()
            
            status = 'healthy'
            if stale_count > connection_count * 0.5:
                status = 'warning'
            elif connection_count == 0:
                status = 'critical'
            
            return {
                'status': status,
                'active_connections': connection_count,
                'stale_connections': stale_count,
                'details': f'{connection_count} active WebSocket connections'
            }
            
        except Exception as e:
            return {
                'status': 'critical',
                'error': str(e),
                'details': 'WebSocket health check failed'
            }
    
    def _check_pos_health(self, restaurant_id):
        """
        NEW: Check POS connections health
        INTEGRATES WITH: Your existing POSConnection model
        """
        try:
            from ..models import POSConnection
            
            pos_connections = POSConnection.objects.filter(is_active=True)
            
            if restaurant_id:
                pos_connections = pos_connections.filter(restaurant_id=restaurant_id)
            
            healthy_connections = 0
            total_connections = pos_connections.count()
            
            for connection in pos_connections:
                if connection.sync_status == 'connected' and connection.last_error is None:
                    healthy_connections += 1
            
            status = 'healthy'
            if healthy_connections == 0 and total_connections > 0:
                status = 'critical'
            elif healthy_connections < total_connections:
                status = 'warning'
            
            return {
                'status': status,
                'total_connections': total_connections,
                'healthy_connections': healthy_connections,
                'details': f'{healthy_connections}/{total_connections} healthy POS connections'
            }
            
        except Exception as e:
            return {
                'status': 'critical',
                'error': str(e),
                'details': 'POS health check failed'
            }
    
    def _check_sync_health(self, restaurant_id):
        """
        NEW: Check synchronization health
        INTEGRATES WITH: Your existing POSSyncLog model
        """
        try:
            from ..models import POSSyncLog
            
            # Check recent sync logs
            recent_syncs = POSSyncLog.objects.filter(
                started_at__gte=timezone.now() - timedelta(hours=1)
            )
            
            if restaurant_id:
                recent_syncs = recent_syncs.filter(connection__restaurant_id=restaurant_id)
            
            total_syncs = recent_syncs.count()
            failed_syncs = recent_syncs.filter(status='failed').count()
            
            failure_rate = (failed_syncs / total_syncs) if total_syncs > 0 else 0
            
            status = 'healthy'
            if failure_rate > 0.1:
                status = 'warning'
            elif failure_rate > 0.3:
                status = 'critical'
            elif total_syncs == 0:
                status = 'warning'
            
            return {
                'status': status,
                'total_syncs': total_syncs,
                'failed_syncs': failed_syncs,
                'failure_rate': round(failure_rate * 100, 2),
                'details': f'Sync failure rate: {failure_rate * 100:.2f}%'
            }
            
        except Exception as e:
            return {
                'status': 'critical',
                'error': str(e),
                'details': 'Sync health check failed'
            }
    
    def _broadcast_health_status(self, restaurant_id, health_report):
        """
        NEW: Broadcast health status to relevant channels
        INTEGRATES WITH: Your WebSocket service
        """
        try:
            from .websocket_services import WebSocketService
            
            if restaurant_id:
                WebSocketService.broadcast_to_restaurant(
                    restaurant_id,
                    'health_update',
                    health_report
                )
            
            # Always broadcast to admin
            WebSocketService.broadcast_to_admin('health_update', health_report)
            
        except Exception as e:
            logger.error(f"Failed to broadcast health status: {str(e)}")

class AlertService:
    """
    NEW: Service for managing health alerts
    INTEGRATES WITH: Your existing notification system
    """
    
    @staticmethod
    def create_alert(alert_type, severity, message, restaurant_id=None, component=None):
        """
        NEW: Create a new health alert
        """
        alert = {
            'type': alert_type,
            'severity': severity,
            'message': message,
            'restaurant_id': restaurant_id,
            'component': component,
            'timestamp': timezone.now().isoformat(),
            'is_acknowledged': False
        }
        
        # Log alert
        logger.warning(f"ALERT [{severity.upper()}] {alert_type}: {message}")
        
        # Broadcast alert
        AlertService._broadcast_alert(alert)
        
        return alert
    
    @staticmethod
    def _broadcast_alert(alert):
        """
        NEW: Broadcast alert to relevant channels
        """
        try:
            from .websocket_services import WebSocketService
            
            # Broadcast to restaurant-specific channel if applicable
            if alert['restaurant_id']:
                WebSocketService.broadcast_to_restaurant(
                    alert['restaurant_id'],
                    'alert_created',
                    {'alert': alert}
                )
            
            # Broadcast to admin channel
            WebSocketService.broadcast_to_admin('alert_created', {'alert': alert})
            
        except Exception as e:
            logger.error(f"Failed to broadcast alert: {str(e)}")