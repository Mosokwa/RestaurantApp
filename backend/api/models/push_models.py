from django.db import models
from django.utils import timezone

class PushNotificationDevice(models.Model):
    """
    Store push notification tokens for mobile devices
    """
    PLATFORMS = (
        ('ios', 'iOS'),
        ('android', 'Android'),
        ('web', 'Web'),
    )
    
    device_id = models.AutoField(primary_key=True)
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='push_devices')
    
    # Device information
    platform = models.CharField(max_length=10, choices=PLATFORMS)
    device_token = models.TextField(unique=True)
    device_model = models.CharField(max_length=100, blank=True, null=True)
    app_version = models.CharField(max_length=20, blank=True, null=True)
    
    # FCM/APNS specific
    fcm_token = models.TextField(blank=True, null=True)
    apns_token = models.TextField(blank=True, null=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    last_active = models.DateTimeField(auto_now=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'push_notification_devices'
        unique_together = ['user', 'device_token']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['platform', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.platform} - {self.device_token[:20]}..."

class PushNotificationLog(models.Model):
    """
    Log push notification delivery attempts
    """
    log_id = models.AutoField(primary_key=True)
    notification = models.ForeignKey('Notification', on_delete=models.CASCADE, related_name='push_logs')
    device = models.ForeignKey(PushNotificationDevice, on_delete=models.CASCADE)
    success = models.BooleanField(default=False)
    error_message = models.TextField(blank=True, null=True)
    response_data = models.JSONField(default=dict, blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'push_notification_logs'
        indexes = [
            models.Index(fields=['notification', 'success']),
            models.Index(fields=['sent_at']),
        ]
    
    def __str__(self):
        return f"Push to {self.device.platform} - {'Success' if self.success else 'Failed'}"