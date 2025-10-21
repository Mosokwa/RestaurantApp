import logging
import requests
import json
from django.conf import settings
from ..models import PushNotificationDevice, PushNotificationLog

logger = logging.getLogger(__name__)

class PushNotificationService:
    """
    Service for sending push notifications via FCM (Firebase) and APNS (Apple)
    """
    
    @staticmethod
    def send_push_notification(notification, devices=None):
        """Send push notification to user's devices"""
        try:
            if devices is None:
                devices = PushNotificationDevice.objects.filter(
                    user=notification.user,
                    is_active=True
                )
            
            if not devices.exists():
                return False
            
            success_count = 0
            for device in devices:
                try:
                    if device.platform == 'android':
                        success = PushNotificationService.send_fcm_notification(device, notification)
                    elif device.platform == 'ios':
                        success = PushNotificationService.send_apns_notification(device, notification)
                    else:
                        success = PushNotificationService.send_web_notification(device, notification)
                    
                    # Log the attempt
                    PushNotificationLog.objects.create(
                        notification=notification,
                        device=device,
                        success=success,
                        error_message="" if success else "Unknown error"
                    )
                    
                    if success:
                        success_count += 1
                        
                except Exception as e:
                    logger.error(f"Error sending push to device {device.device_id}: {str(e)}")
                    PushNotificationLog.objects.create(
                        notification=notification,
                        device=device,
                        success=False,
                        error_message=str(e)
                    )
            
            # Update notification sent status
            if success_count > 0:
                notification.sent_via_push = True
                notification.save(update_fields=['sent_via_push'])
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error in send_push_notification: {str(e)}")
            return False
    
    @staticmethod
    def send_fcm_notification(device, notification):
        """Send notification via Firebase Cloud Messaging (Android)"""
        try:
            if not device.fcm_token:
                return False
            
            # FCM payload
            payload = {
                'to': device.fcm_token,
                'notification': {
                    'title': notification.title,
                    'body': notification.message,
                    'image': notification.image_url,
                },
                'data': {
                    'action_url': notification.action_url or '',
                    'notification_id': str(notification.notification_id),
                    'type': notification.type,
                    'priority': notification.priority,
                    **notification.data
                },
                'android': {
                    'priority': 'high' if notification.priority in ['high', 'urgent'] else 'normal'
                },
                'apns': {
                    'payload': {
                        'aps': {
                            'content-available': 1,
                            'badge': 1,
                            'sound': 'default'
                        }
                    }
                }
            }
            
            # Send to FCM
            headers = {
                'Authorization': f'key={settings.FCM_SERVER_KEY}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                'https://fcm.googleapis.com/fcm/send',
                headers=headers,
                data=json.dumps(payload)
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('success', 0) == 1
            else:
                logger.error(f"FCM API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending FCM notification: {str(e)}")
            return False
    
    @staticmethod
    def send_apns_notification(device, notification):
        """Send notification via Apple Push Notification Service (iOS)"""
        try:
            if not device.apns_token:
                return False
            
            # APNS payload
            payload = {
                'aps': {
                    'alert': {
                        'title': notification.title,
                        'body': notification.message
                    },
                    'badge': 1,
                    'sound': 'default',
                    'content-available': 1
                },
                'notification_id': str(notification.notification_id),
                'type': notification.type,
                'action_url': notification.action_url,
                'data': notification.data
            }
            
            # In production, you'd use the actual APNS service
            # This is a simplified version
            logger.info(f"Would send APNS notification to {device.apns_token[:20]}...")
            
            # For now, simulate success
            return True
            
        except Exception as e:
            logger.error(f"Error sending APNS notification: {str(e)}")
            return False
    
    @staticmethod
    def send_web_notification(device, notification):
        """Send notification for web push"""
        try:
            # Web push implementation would go here
            # This typically involves Service Workers and browser push APIs
            logger.info(f"Would send web push notification to {device.device_token[:20]}...")
            
            # For now, simulate success
            return True
            
        except Exception as e:
            logger.error(f"Error sending web notification: {str(e)}")
            return False
    
    @staticmethod
    def register_device(user, platform, device_token, **kwargs):
        """Register a new push notification device"""
        try:
            device, created = PushNotificationDevice.objects.get_or_create(
                device_token=device_token,
                defaults={
                    'user': user,
                    'platform': platform,
                    'device_model': kwargs.get('device_model'),
                    'app_version': kwargs.get('app_version'),
                    'fcm_token': kwargs.get('fcm_token'),
                    'apns_token': kwargs.get('apns_token'),
                }
            )
            
            if not created:
                # Update existing device
                device.user = user
                device.platform = platform
                device.device_model = kwargs.get('device_model', device.device_model)
                device.app_version = kwargs.get('app_version', device.app_version)
                device.fcm_token = kwargs.get('fcm_token', device.fcm_token)
                device.apns_token = kwargs.get('apns_token', device.apns_token)
                device.is_active = True
                device.save()
            
            return device, created
            
        except Exception as e:
            logger.error(f"Error registering push device: {str(e)}")
            return None, False
    
    @staticmethod
    def unregister_device(device_token):
        """Unregister a push notification device"""
        try:
            deleted_count = PushNotificationDevice.objects.filter(device_token=device_token).delete()[0]
            return deleted_count > 0
        except Exception as e:
            logger.error(f"Error unregistering push device: {str(e)}")
            return False