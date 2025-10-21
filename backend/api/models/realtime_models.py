import uuid
from django.db import models
from django.utils import timezone

class WebSocketConnection(models.Model):
    CONNECTION_TYPES = (
        ('customer', 'Customer'),
        ('restaurant_staff', 'Restaurant Staff'),
        ('delivery', 'Delivery Personnel'),
        ('admin', 'Administrator'),
    )
    
    connection_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='websocket_connections')
    connection_type = models.CharField(max_length=20, choices=CONNECTION_TYPES)
    customer_group = models.CharField(max_length=255, blank=True, null=True)
    restaurant_groups = models.JSONField(default=list, blank=True)
    order_groups = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    connected_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    disconnected_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'websocket_connections'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['is_active', 'last_activity']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.connection_type} - {self.connection_id}"
    
    def disconnect(self):
        self.is_active = False
        self.disconnected_at = timezone.now()
        self.save()

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('order_status', 'Order Status Update'),
        ('promotional', 'Promotional Offer'),
        ('reservation', 'Reservation Reminder'),
        ('review_response', 'Review Response'),
        ('system', 'System Announcement'),
        ('loyalty', 'Loyalty Program'),
        ('delivery', 'Delivery Update'),
        ('security', 'Security Alert'),
    )
    
    PRIORITY_LEVELS = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )
    
    notification_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')
    title = models.CharField(max_length=255)
    message = models.TextField()
    image_url = models.URLField(blank=True, null=True)
    action_url = models.CharField(max_length=500, blank=True, null=True)
    action_text = models.CharField(max_length=100, blank=True, null=True)
    data = models.JSONField(default=dict, blank=True)
    order = models.ForeignKey('Order', on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    restaurant = models.ForeignKey('Restaurant', on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    is_read = models.BooleanField(default=False)
    is_sent = models.BooleanField(default=False)
    sent_via_websocket = models.BooleanField(default=False)
    sent_via_push = models.BooleanField(default=False)
    sent_via_email = models.BooleanField(default=False)
    scheduled_for = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['type', 'created_at']),
            models.Index(fields=['order']),
            models.Index(fields=['restaurant']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()
    
    def mark_as_sent(self, method='websocket'):
        self.is_sent = True
        self.sent_at = timezone.now()
        if method == 'websocket':
            self.sent_via_websocket = True
        elif method == 'push':
            self.sent_via_push = True
        elif method == 'email':
            self.sent_via_email = True
        self.save()

class NotificationPreference(models.Model):
    preference_id = models.AutoField(primary_key=True)
    user = models.OneToOneField('User', on_delete=models.CASCADE, related_name='notification_preferences')
    enable_websocket = models.BooleanField(default=True)
    enable_push = models.BooleanField(default=True)
    enable_email = models.BooleanField(default=True)
    enable_sms = models.BooleanField(default=False)
    order_updates = models.BooleanField(default=True)
    promotional_offers = models.BooleanField(default=True)
    reservation_reminders = models.BooleanField(default=True)
    review_responses = models.BooleanField(default=True)
    system_announcements = models.BooleanField(default=True)
    loyalty_updates = models.BooleanField(default=True)
    delivery_updates = models.BooleanField(default=True)
    security_alerts = models.BooleanField(default=True)
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_hours_start = models.TimeField(default='22:00')
    quiet_hours_end = models.TimeField(default='08:00')
    max_daily_notifications = models.IntegerField(default=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notification_preferences'
    
    def __str__(self):
        return f"Notification Preferences - {self.user.username}"

class LiveOrderTracking(models.Model):
    tracking_id = models.AutoField(primary_key=True)
    order = models.OneToOneField('Order', on_delete=models.CASCADE, related_name='live_tracking')
    current_latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    current_longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    location_updated_at = models.DateTimeField(null=True, blank=True)
    delivery_person = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True, related_name='delivery_orders')
    delivery_person_name = models.CharField(max_length=255, blank=True, null=True)
    delivery_person_phone = models.CharField(max_length=20, blank=True, null=True)
    estimated_preparation_completion = models.DateTimeField(null=True, blank=True)
    estimated_delivery_completion = models.DateTimeField(null=True, blank=True)
    preparation_progress = models.IntegerField(default=0, help_text="Percentage 0-100")
    delivery_progress = models.IntegerField(default=0, help_text="Percentage 0-100")
    last_websocket_update = models.DateTimeField(null=True, blank=True)
    update_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'live_order_tracking'
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['delivery_person']),
        ]
    
    def __str__(self):
        return f"Live Tracking - Order #{self.order.order_uuid}"

# Signal to create notification preferences when user is created
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender='api.User')
def create_notification_preferences(sender, instance, created, **kwargs):
    if created:
        NotificationPreference.objects.create(user=instance)


class RealTimeInventory(models.Model):
    """
    Real-time inventory tracking for menu items across branches
    """
    inventory_id = models.AutoField(primary_key=True)
    menu_item = models.ForeignKey('MenuItem', on_delete=models.CASCADE, related_name='inventory')
    branch = models.ForeignKey('Branch', on_delete=models.CASCADE, related_name='inventory')
    
    # Inventory levels
    current_stock = models.IntegerField(default=0)
    low_stock_threshold = models.IntegerField(default=10)
    out_of_stock_threshold = models.IntegerField(default=0)
    
    # Real-time updates
    last_updated = models.DateTimeField(auto_now=True)
    last_restocked = models.DateTimeField(null=True, blank=True)
    
    # Auto-restock settings
    auto_restock_enabled = models.BooleanField(default=False)
    restock_quantity = models.IntegerField(default=0)
    restock_threshold = models.IntegerField(default=5)
    
    class Meta:
        db_table = 'real_time_inventory'
        unique_together = ['menu_item', 'branch']
        indexes = [
            models.Index(fields=['branch', 'current_stock']),
            models.Index(fields=['menu_item', 'current_stock']),
        ]
    
    def __str__(self):
        return f"{self.menu_item.name} - {self.branch.address.city} - Stock: {self.current_stock}"
    
    @property
    def is_low_stock(self):
        return self.current_stock <= self.low_stock_threshold
    
    @property
    def is_out_of_stock(self):
        return self.current_stock <= self.out_of_stock_threshold
    
    @property
    def needs_restock(self):
        return self.auto_restock_enabled and self.current_stock <= self.restock_threshold

class InventoryAlert(models.Model):
    """
    Track inventory alerts and notifications
    """
    ALERT_TYPES = (
        ('low_stock', 'Low Stock'),
        ('out_of_stock', 'Out of Stock'),
        ('restocked', 'Restocked'),
    )
    
    alert_id = models.AutoField(primary_key=True)
    inventory = models.ForeignKey(RealTimeInventory, on_delete=models.CASCADE, related_name='alerts')
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    message = models.TextField()
    previous_stock = models.IntegerField()
    current_stock = models.IntegerField()
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'inventory_alerts'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_alert_type_display()} - {self.inventory.menu_item.name}"

# Signal to create inventory records when menu items are created
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender='api.MenuItem')
def create_inventory_records(sender, instance, created, **kwargs):
    if created:
        from ..models import Branch
        branches = Branch.objects.filter(restaurant=instance.category.restaurant)
        for branch in branches:
            RealTimeInventory.objects.create(
                menu_item=instance,
                branch=branch,
                current_stock=0,
                low_stock_threshold=10
            )