from rest_framework import serializers
from ..models import Notification, NotificationPreference, LiveOrderTracking, PushNotificationLog, PushNotificationDevice, WebSocketConnection


class NotificationSerializer(serializers.ModelSerializer):
    notification_id = serializers.UUIDField(read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'notification_id', 'type', 'type_display', 'priority', 'priority_display',
            'title', 'message', 'image_url', 'action_url', 'action_text', 'data',
            'order', 'restaurant', 'is_read', 'is_sent',
            'sent_via_websocket', 'sent_via_push', 'sent_via_email',
            'scheduled_for', 'expires_at', 'created_at', 'read_at', 'sent_at'
        ]
        read_only_fields = [
            'notification_id', 'created_at', 'read_at', 'sent_at',
            'is_sent', 'sent_via_websocket', 'sent_via_push', 'sent_via_email'
        ]

class NotificationPreferenceSerializer(serializers.ModelSerializer):
    preference_id = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = NotificationPreference
        fields = [
            'preference_id',
            'enable_websocket', 'enable_push', 'enable_email', 'enable_sms',
            'order_updates', 'promotional_offers', 'reservation_reminders',
            'review_responses', 'system_announcements', 'loyalty_updates',
            'delivery_updates', 'security_alerts',
            'quiet_hours_enabled', 'quiet_hours_start', 'quiet_hours_end',
            'max_daily_notifications',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['preference_id', 'created_at', 'updated_at']

class LiveOrderTrackingSerializer(serializers.ModelSerializer):
    order_uuid = serializers.UUIDField(source='order.order_uuid', read_only=True)
    order_status = serializers.CharField(source='order.status', read_only=True)
    
    class Meta:
        model = LiveOrderTracking
        fields = [
            'order_uuid', 'order_status',
            'current_latitude', 'current_longitude', 'location_updated_at',
            'delivery_person', 'delivery_person_name', 'delivery_person_phone',
            'estimated_preparation_completion', 'estimated_delivery_completion',
            'preparation_progress', 'delivery_progress',
            'last_websocket_update', 'update_count',
            'created_at', 'updated_at'
        ]

class PushNotificationDeviceSerializer(serializers.ModelSerializer):
    """Serializer for PushNotificationDevice model"""
    
    device_id = serializers.IntegerField(read_only=True)
    platform_display = serializers.CharField(source='get_platform_display', read_only=True)
    
    class Meta:
        model = PushNotificationDevice
        fields = [
            'device_id', 'platform', 'platform_display', 'device_token',
            'device_model', 'app_version', 'fcm_token', 'apns_token',
            'is_active', 'last_active', 'created_at'
        ]
        read_only_fields = ['device_id', 'last_active', 'created_at']
    
    def validate_platform(self, value):
        """Validate platform value"""
        valid_platforms = ['ios', 'android', 'web']
        if value not in valid_platforms:
            raise serializers.ValidationError(f"Platform must be one of: {', '.join(valid_platforms)}")
        return value
    
    def validate_device_token(self, value):
        """Validate device token format"""
        if not value or len(value) < 10:
            raise serializers.ValidationError("Device token must be at least 10 characters long")
        return value

class PushNotificationLogSerializer(serializers.ModelSerializer):
    """Serializer for PushNotificationLog model"""
    
    log_id = serializers.IntegerField(read_only=True)
    device_platform = serializers.CharField(source='device.platform', read_only=True)
    notification_title = serializers.CharField(source='notification.title', read_only=True)
    
    class Meta:
        model = PushNotificationLog
        fields = [
            'log_id', 'notification', 'notification_title', 'device', 'device_platform',
            'success', 'error_message', 'response_data', 'sent_at'
        ]
        read_only_fields = ['log_id', 'sent_at']

class WebSocketConnectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebSocketConnection
        fields = [
            'connection_id', 'user', 'connection_type', 'customer_group',
            'restaurant_groups', 'order_groups', 'is_active', 'ip_address',
            'user_agent', 'connected_at', 'last_activity', 'disconnected_at'
        ]
        read_only_fields = ['connection_id', 'connected_at', 'last_activity']