from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone

class GroupOrder(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    )
    
    group_id = models.AutoField(primary_key=True)
    organizer = models.ForeignKey(
        'api.Customer',
        on_delete=models.CASCADE,
        related_name='organized_group_orders'
    )
    restaurant = models.ForeignKey(
        'api.Restaurant',
        on_delete=models.CASCADE,
        related_name='group_orders'
    )
    
    # Group order details
    name = models.CharField(max_length=255, help_text="Name for this group order")
    description = models.TextField(blank=True, null=True)
    share_code = models.CharField(max_length=20, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Settings
    allow_anyone_to_join = models.BooleanField(default=True)
    max_participants = models.IntegerField(null=True, blank=True)
    order_deadline = models.DateTimeField()
    estimated_delivery_time = models.DateTimeField(null=True, blank=True)
    
    # Totals
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'group_orders'
        ordering = ['-created_at']

    def __str__(self):
        return f"Group Order: {self.name} - {self.restaurant.name}"

    def save(self, *args, **kwargs):
        if not self.share_code:
            self.share_code = self._generate_share_code()
        super().save(*args, **kwargs)
    
    def _generate_share_code(self):
        import random
        import string
        code = ''.join(random.choices(string.ascii_uppercase, k=6))
        while GroupOrder.objects.filter(share_code=code).exists():
            code = ''.join(random.choices(string.ascii_uppercase, k=6))
        return code
    
    def is_joinable(self):
        """Check if group order can be joined"""
        now = timezone.now()
        return (self.status == 'active' and
                now <= self.order_deadline and
                (self.max_participants is None or 
                 self.participants.count() < self.max_participants))
    
    def update_totals(self):
        """Update group order totals from all participant orders"""
        from decimal import Decimal
        
        self.subtotal = Decimal('0')
        for participant in self.participants.all():
            if participant.order:
                self.subtotal += Decimal(str(participant.order.subtotal))
        
        # Apply group discounts or calculate final total
        self.total_amount = self.subtotal
        self.save()

class GroupOrderParticipant(models.Model):
    participant_id = models.AutoField(primary_key=True)
    group_order = models.ForeignKey(
        GroupOrder,
        on_delete=models.CASCADE,
        related_name='participants'
    )
    customer = models.ForeignKey(
        'api.Customer',
        on_delete=models.CASCADE,
        related_name='group_order_participations'
    )
    order = models.OneToOneField(
        'api.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='group_order_participation'
    )
    
    # Participant details
    display_name = models.CharField(max_length=100)
    is_organizer = models.BooleanField(default=False)
    
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'group_order_participants'
        unique_together = ['group_order', 'customer']

    def __str__(self):
        return f"{self.display_name} - {self.group_order.name}"

class ScheduledOrder(models.Model):
    SCHEDULE_TYPES = (
        ('once', 'One Time'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    )
    
    schedule_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(
        'api.Customer',
        on_delete=models.CASCADE,
        related_name='scheduled_orders'
    )
    restaurant = models.ForeignKey(
        'api.Restaurant',
        on_delete=models.CASCADE,
        related_name='scheduled_orders'
    )
    
    # Schedule details
    schedule_type = models.CharField(max_length=20, choices=SCHEDULE_TYPES, default='once')
    scheduled_for = models.DateTimeField()
    timezone = models.CharField(max_length=50, default='UTC')
    
    # Order template (what to order)
    order_template = models.ForeignKey(
        'OrderTemplate',
        on_delete=models.CASCADE,
        related_name='scheduled_orders'
    )
    
    # Recurrence settings
    recurrence_end = models.DateTimeField(null=True, blank=True)
    recurrence_days = models.JSONField(default=list, blank=True)  # For weekly: [0,2,4] for Mon, Wed, Fri
    
    # Status
    is_active = models.BooleanField(default=True)
    last_processed = models.DateTimeField(null=True, blank=True)
    next_occurrence = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'scheduled_orders'
        ordering = ['scheduled_for']

    def __str__(self):
        return f"Scheduled Order - {self.customer.user.email} - {self.scheduled_for}"

    def save(self, *args, **kwargs):
        # Calculate next occurrence
        if self.is_active and not self.next_occurrence:
            self.next_occurrence = self._calculate_next_occurrence()
        super().save(*args, **kwargs)
    
    def _calculate_next_occurrence(self):
        now = timezone.now()
        if self.schedule_type == 'once':
            return self.scheduled_for if self.scheduled_for > now else None
        elif self.schedule_type == 'daily':
            # Find next occurrence after now
            next_time = self.scheduled_for
            while next_time <= now:
                next_time += timezone.timedelta(days=1)
            return next_time
        # Implement weekly/monthly logic as needed
        return self.scheduled_for

class OrderTemplate(models.Model):
    template_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(
        'api.Customer',
        on_delete=models.CASCADE,
        related_name='order_templates'
    )
    restaurant = models.ForeignKey(
        'api.Restaurant',
        on_delete=models.CASCADE,
        related_name='order_templates'
    )
    
    # Template details
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    
    # Order configuration
    order_type = models.CharField(max_length=20, choices=(
        ('delivery', 'Delivery'),
        ('pickup', 'Pickup'),
        ('dine_in', 'Dine-in'),
    ), default='delivery')
    
    delivery_address = models.ForeignKey(
        'api.Address',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    special_instructions = models.TextField(blank=True, null=True)
    
    # Items configuration (stored as JSON for flexibility)
    items_configuration = models.JSONField(default=dict)
    
    is_active = models.BooleanField(default=True)
    usage_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'order_templates'
        ordering = ['-usage_count', '-created_at']

    def __str__(self):
        return f"{self.name} - {self.restaurant.name}"

    def create_order_from_template(self):
        """Create a new order based on this template"""
        from ..models import Order, OrderItem, OrderItemModifier, MenuItem
        from decimal import Decimal
        
        # Create the order
        order = Order.objects.create(
            customer=self.customer,
            restaurant=self.restaurant,
            order_type=self.order_type,
            delivery_address=self.delivery_address,
            special_instructions=self.special_instructions
        )
        
        # Add items from configuration
        subtotal = Decimal('0')
        for item_config in self.items_configuration.get('items', []):
            try:
                menu_item = MenuItem.objects.get(
                    pk=item_config['menu_item_id'],
                    is_available=True
                )
                
                order_item = OrderItem.objects.create(
                    order=order,
                    menu_item=menu_item,
                    quantity=item_config['quantity'],
                    unit_price=menu_item.price,
                    special_instructions=item_config.get('special_instructions', '')
                )
                
                subtotal += Decimal(str(order_item.total_price))
                
                # Add modifiers if any
                for modifier_config in item_config.get('modifiers', []):
                    OrderItemModifier.objects.create(
                        order_item=order_item,
                        item_modifier_id=modifier_config['modifier_id'],
                        quantity=modifier_config.get('quantity', 1),
                        unit_price=modifier_config.get('price_modifier', 0)
                    )
                
            except MenuItem.DoesNotExist:
                continue
        
        # Update order totals
        order.subtotal = subtotal
        order.tax_amount = subtotal * Decimal('0.1')  # Example tax
        order.delivery_fee = Decimal('5.00') if order.order_type == 'delivery' else Decimal('0')
        order.total_amount = order.subtotal + order.tax_amount + order.delivery_fee
        order.save()
        
        # Update usage count
        self.usage_count += 1
        self.save()
        
        return order

class BulkOrder(models.Model):
    BULK_ORDER_TYPES = (
        ('corporate', 'Corporate Event'),
        ('catering', 'Catering'),
        ('party', 'Party/Group'),
        ('other', 'Other'),
    )
    
    bulk_order_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(
        'api.Customer',
        on_delete=models.CASCADE,
        related_name='bulk_orders'
    )
    restaurant = models.ForeignKey(
        'api.Restaurant',
        on_delete=models.CASCADE,
        related_name='bulk_orders'
    )
    
    # Event details
    event_type = models.CharField(max_length=20, choices=BULK_ORDER_TYPES)
    event_name = models.CharField(max_length=255)
    event_description = models.TextField(blank=True, null=True)
    event_date = models.DateTimeField()
    number_of_guests = models.IntegerField(validators=[MinValueValidator(1)])
    
    # Contact information
    contact_person = models.CharField(max_length=255)
    contact_phone = models.CharField(max_length=20)
    contact_email = models.EmailField()
    
    # Delivery/Setup details
    delivery_address = models.ForeignKey(
        'api.Address',
        on_delete=models.CASCADE,
        related_name='bulk_orders'
    )
    setup_requirements = models.TextField(blank=True, null=True)
    special_instructions = models.TextField(blank=True, null=True)
    
    # Pricing
    estimated_amount = models.DecimalField(max_digits=12, decimal_places=2)
    deposit_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    final_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=(
        ('inquiry', 'Inquiry'),
        ('quoted', 'Quoted'),
        ('confirmed', 'Confirmed'),
        ('preparing', 'Preparing'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ), default='inquiry')
    
    # Admin notes
    admin_notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bulk_orders'
        ordering = ['-created_at']

    def __str__(self):
        return f"Bulk Order: {self.event_name} - {self.restaurant.name}"

class BulkOrderItem(models.Model):
    bulk_item_id = models.AutoField(primary_key=True)
    bulk_order = models.ForeignKey(
        BulkOrder,
        on_delete=models.CASCADE,
        related_name='items'
    )
    menu_item = models.ForeignKey(
        'api.MenuItem',
        on_delete=models.CASCADE,
        related_name='bulk_order_items'
    )
    
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    special_instructions = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'bulk_order_items'

    def __str__(self):
        return f"{self.quantity}x {self.menu_item.name} - {self.bulk_order.event_name}"

    def save(self, *args, **kwargs):
        self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)