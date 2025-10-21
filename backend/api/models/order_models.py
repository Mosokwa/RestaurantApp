from decimal import Decimal
import uuid
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.core.exceptions import ValidationError

class Order(models.Model):
    ORDER_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready for Pickup'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    )
    
    ORDER_TYPE_CHOICES = (
        ('delivery', 'Delivery'),
        ('pickup', 'Pickup'),
        ('dine_in', 'Dine-in'),
    )
    
    order_id = models.AutoField(primary_key=True)
    order_uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    customer = models.ForeignKey(
        'api.Customer',
        on_delete=models.CASCADE,
        related_name='orders'
    )
    restaurant = models.ForeignKey(
        'api.Restaurant',
        on_delete=models.CASCADE,
        related_name='orders'
    )
    branch = models.ForeignKey(
        'api.Branch',
        on_delete=models.CASCADE,
        related_name='orders',
        null=True,
        blank=True
    )
    
    # Order details
    order_type = models.CharField(max_length=20, choices=ORDER_TYPE_CHOICES, default='delivery')
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    special_instructions = models.TextField(blank=True, null=True)
    
    # Pricing
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0)])
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0)])
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0)])
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0)])
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0)])
    
    # Multi-restaurant loyalty tracking
    loyalty_points_earned = models.IntegerField(default=0, help_text="Points earned from this order")
    loyalty_points_awarded = models.BooleanField(default=False, help_text="Whether loyalty points have been awarded")
    loyalty_points_awarded_at = models.DateTimeField(null=True, blank=True, help_text="When loyalty points were awarded")
    loyalty_program_used = models.ForeignKey(
        'api.MultiRestaurantLoyaltyProgram',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        help_text="Which loyalty program was used for this order"
    )

    # Timestamps
    order_placed_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    preparation_started_at = models.DateTimeField(null=True, blank=True)
    ready_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    # Delivery information (for delivery orders)
    delivery_address = models.ForeignKey(
        'api.Address',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='delivery_orders'
    )
    estimated_delivery_time = models.DateTimeField(null=True, blank=True)
    
    # Table information (for dine-in orders)
    table_number = models.CharField(max_length=20, blank=True, null=True)

    applied_offers = models.ManyToManyField(
        'api.SpecialOffer',
        through='OfferUsage',
        related_name='orders_used',
        blank=True
    )
    
    class Meta:
        db_table = 'orders'
        ordering = ['-order_placed_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['order_placed_at']),
            models.Index(fields=['customer', 'order_placed_at']),
            models.Index(fields=['restaurant', 'order_placed_at']),
            models.Index(fields=['loyalty_points_awarded']),  # New index for loyalty queries
        ]

    def __str__(self):
        return f"Order #{self.order_uuid} - {self.customer.user.username}"

    def save(self, *args, **kwargs):
        # Convert all values to Decimal for consistent arithmetic
        from decimal import Decimal
        
        # Ensure all values are Decimal
        self.subtotal = Decimal(str(self.subtotal)) if self.subtotal else Decimal('0')
        self.tax_amount = Decimal(str(self.tax_amount)) if self.tax_amount else Decimal('0')
        self.delivery_fee = Decimal(str(self.delivery_fee)) if self.delivery_fee else Decimal('0')
        self.discount_amount = Decimal(str(self.discount_amount)) if self.discount_amount else Decimal('0')
        
        # Calculate total before saving
        self.total_amount = self.subtotal + self.tax_amount + self.delivery_fee - self.discount_amount
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new and self.status == 'pending':
            self.update_item_popularity()

    def update_item_popularity(self):
        """Update popularity scores for items in this order"""
        for order_item in self.order_items.all():
            order_item.menu_item.increment_popularity()
            
            # Update item associations
            self.update_item_associations(order_item.menu_item)

    def update_item_associations(self, current_item):
        """Update frequently-bought-together associations"""
        from api.models import ItemAssociation
        
        # Get all other items in this order
        other_items = self.order_items.exclude(
            menu_item=current_item
        ).values_list('menu_item', flat=True)
        
        for other_item_id in other_items:
            # Update or create association
            association, created = ItemAssociation.objects.get_or_create(
                source_item=current_item,
                target_item_id=other_item_id,
                defaults={'support': 1, 'confidence': 0.1}
            )
            
            if not created:
                association.support += 1
                # Simple confidence calculation (can be enhanced)
                total_orders = current_item.order_count
                association.confidence = association.support / max(1, total_orders)
                association.save()
    
    def update_status(self, new_status):
        """Update order status and set appropriate timestamps"""
        self.status = new_status
        now = timezone.now()
        
        if new_status == 'confirmed':
            self.confirmed_at = now
        elif new_status == 'preparing':
            self.preparation_started_at = now
        elif new_status == 'ready':
            self.ready_at = now
        elif new_status == 'delivered':
            self.delivered_at = now
        elif new_status == 'cancelled':
            self.cancelled_at = now
        
        self.save()

    def can_award_loyalty_points(self):
        """Check if this order is eligible for loyalty points across multiple restaurants"""
        return (self.status == 'delivered' and 
                not self.loyalty_points_awarded and 
                self.loyalty_points_earned == 0 and
                self.restaurant.loyalty_settings.exists())  # Restaurant must have loyalty configured

    def award_loyalty_points(self):
        """Award loyalty points for this order using multi-restaurant service"""
        from ..services.loyalty_services import MultiRestaurantLoyaltyService
        
        success, message = MultiRestaurantLoyaltyService.award_order_points(self)
        return success, message
    
    def create_live_tracking(self):
        """Create or get live tracking record"""
        from .realtime_models import LiveOrderTracking
        from django.utils import timezone
        from datetime import timedelta
        
        tracking, created = LiveOrderTracking.objects.get_or_create(
            order=self,
            defaults={
                'estimated_preparation_completion': self.calculate_estimated_preparation_time(),
                'estimated_delivery_completion': self.calculate_estimated_delivery_time()
            }
        )
        return tracking

    def update_status_with_realtime(self, new_status, updated_by=None, description=None):
        """Enhanced status update with real-time tracking"""
        from django.utils import timezone
        from .order_models import OrderTracking
        from ..services.websocket_services import WebSocketService
        from ..services.notification_service import NotificationService
        
        old_status = self.status
        
        # Update order status using existing method
        self.update_status(new_status)
        
        # Create traditional tracking record
        OrderTracking.objects.create(
            order=self,
            status=new_status,
            description=description or f"Order status changed from {old_status} to {new_status}",
            updated_by=updated_by
        )
        
        # REAL-TIME: Create live tracking if doesn't exist
        if not hasattr(self, 'live_tracking'):
            self.create_live_tracking()
        
        # REAL-TIME: Update progress based on status
        progress_updates = {
            'pending': (0, 0),
            'confirmed': (10, 0),
            'preparing': (50, 0),
            'ready': (80, 0),
            'out_for_delivery': (100, 30),
            'delivered': (100, 100),
            'cancelled': (0, 0),
            'refunded': (0, 0),
        }
        
        prep_progress, delivery_progress = progress_updates.get(new_status, (0, 0))
        
        # Update live tracking progress
        self.live_tracking.preparation_progress = prep_progress
        self.live_tracking.delivery_progress = delivery_progress
        self.live_tracking.save()
        
        # REAL-TIME: Broadcast update
        WebSocketService.broadcast_to_order(
            self.order_id,
            'order_update',
            {
                'order_id': str(self.order_uuid),
                'old_status': old_status,
                'new_status': new_status,
                'preparation_progress': prep_progress,
                'delivery_progress': delivery_progress,
                'timestamp': timezone.now().isoformat()
            }
        )
        
        # REAL-TIME: Send notification
        NotificationService.notify_order_status_update(self, old_status, new_status)

    def update_delivery_location(self, latitude, longitude, delivery_person=None):
        """Update delivery location with real-time tracking"""
        from ..services.websocket_services import WebSocketService
        
        # REAL-TIME: Create live tracking if doesn't exist
        if not hasattr(self, 'live_tracking'):
            self.create_live_tracking()
        
        # Update location
        self.live_tracking.current_latitude = latitude
        self.live_tracking.current_longitude = longitude
        self.live_tracking.location_updated_at = timezone.now()
        
        if delivery_person:
            self.live_tracking.delivery_person = delivery_person
            self.live_tracking.delivery_person_name = delivery_person.get_full_name() or delivery_person.username
            self.live_tracking.delivery_person_phone = delivery_person.phone_number
        
        self.live_tracking.save()
        
        # Broadcast location update
        WebSocketService.broadcast_to_order(
            self.order_id,
            'delivery_location',
            {
                'order_id': str(self.order_uuid),
                'current_latitude': float(latitude),
                'current_longitude': float(longitude),
                'delivery_person': self.live_tracking.delivery_person_name,
                'timestamp': timezone.now().isoformat()
            }
        )

    def calculate_estimated_preparation_time(self):
        """Calculate preparation time based on order items"""
        from django.utils import timezone
        from datetime import timedelta
        
        base_time = 15  # minutes
        if hasattr(self, 'order_items'):
            item_time = sum(item.menu_item.preparation_time for item in self.order_items.all())
            total_time = max(base_time, item_time)
        else:
            total_time = base_time
        
        return timezone.now() + timedelta(minutes=total_time)

    def calculate_estimated_delivery_time(self):
        """Calculate delivery time based on preparation time"""
        from datetime import timedelta
        prep_time = self.calculate_estimated_preparation_time()
        return prep_time + timedelta(minutes=25)  # Fixed delivery offset
    
    def apply_special_offer(self, offer, customer):
        """Apply special offer to order and record usage"""
        from decimal import Decimal
        from ..models.ratingsandreviews_models import OfferUsage
        
        if not offer.is_valid():
            raise ValidationError("Offer is no longer valid")
        
        if not offer.can_user_use(customer.user):
            raise ValidationError("You have reached the usage limit for this offer")
        
        if self.subtotal < offer.min_order_amount:
            raise ValidationError(f"Order subtotal must be at least {offer.min_order_amount}")
        
        discount_amount = self.calculate_offer_discount(offer)
        original_total = self.total_amount
        
        self.discount_amount += discount_amount
        self.total_amount = max(Decimal('0'), self.total_amount - discount_amount)
        self.save()
        
        # Record usage
        OfferUsage.objects.create(
            offer=offer,
            customer=customer,
            order=self,
            discount_applied=discount_amount,
            original_order_amount=original_total,
            final_order_amount=self.total_amount,
            is_successful=True,
            redeemed_at=timezone.now()
        )
        
        return discount_amount

    def calculate_offer_discount(self, offer):
        """Calculate discount based on offer type"""
        from decimal import Decimal
        if offer.offer_type == 'percentage':
            return (self.subtotal * offer.discount_value) / Decimal('100')
        elif offer.offer_type == 'fixed':
            return min(offer.discount_value, self.subtotal)
        return Decimal('0.00')
    
    def sync_to_pos(self):
        """Sync order to POS system"""
        if not hasattr(self, 'pos_info'):
            # Create POS info if it doesn't exist
            from .pos_integration_models import OrderPOSInfo
            OrderPOSInfo.objects.create(order=self)
        
        success, message = self.pos_info.sync_to_pos()
        
        if success and self.pos_info.pos_order_id:
            # Route order to kitchen stations
            from ..services.order_routing_service import OrderRoutingService
            routing_service = OrderRoutingService(self)
            routing_result = routing_service.route_order()
            
            # Update preparation timestamps
            self.pos_info.preparation_started_at = timezone.now()
            self.pos_info.save()
        
        return success, message
    
    def update_kitchen_status(self, item_id, status, station_id=None):
        """Update kitchen preparation status"""
        from .pos_integration_models import OrderItemPreparation
        
        try:
            order_item = self.order_items.get(order_item_id=item_id)
            prep_info = order_item.preparation_info
            
            if status == 'preparing':
                prep_info.preparation_status = 'preparing'
                prep_info.preparation_started_at = timezone.now()
            elif status == 'ready':
                prep_info.preparation_status = 'ready'
                prep_info.actual_completion_at = timezone.now()
            elif status == 'served':
                prep_info.preparation_status = 'served'
            
            if station_id:
                from .pos_integration_models import KitchenStation
                station = KitchenStation.objects.get(station_id=station_id)
                prep_info.assigned_station = station
            
            prep_info.save()
            
            # Check if all items are ready
            self._check_order_readiness()
            
            return True
            
        except OrderItemPreparation.DoesNotExist:
            return False
    
    def _check_order_readiness(self):
        """Check if all order items are ready"""
        if not self.order_items.filter(
            preparation_info__preparation_status__in=['pending', 'preparing']
        ).exists():
            # All items are ready or served
            self.pos_info.actual_ready_at = timezone.now()
            self.pos_info.save()
            
            if self.status == 'preparing':
                self.status = 'ready'
                self.save()
        

class OrderItem(models.Model):
    order_item_id = models.AutoField(primary_key=True)
    order = models.ForeignKey(
        'api.Order',
        on_delete=models.CASCADE,
        related_name='order_items'
    )
    menu_item = models.ForeignKey(
        'api.MenuItem',
        on_delete=models.CASCADE,
        related_name='order_items'
    )
    
    # Item details
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    special_instructions = models.TextField(blank=True, null=True)
    
    # Calculated fields
    total_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    
    class Meta:
        db_table = 'order_items'
        ordering = ['order', 'order_item_id']

    def __str__(self):
        return f"{self.quantity}x {self.menu_item.name} - Order #{self.order.order_uuid}"

    def save(self, *args, **kwargs):
        from decimal import Decimal
        # Calculate total price before saving
        self.total_price = Decimal(str(self.unit_price)) * self.quantity
        super().save(*args, **kwargs)

class OrderItemModifier(models.Model):
    order_item_modifier_id = models.AutoField(primary_key=True)
    order_item = models.ForeignKey(
        'api.OrderItem',
        on_delete=models.CASCADE,
        related_name='modifiers'
    )
    item_modifier = models.ForeignKey(
        'api.ItemModifier',
        on_delete=models.CASCADE,
        related_name='order_modifiers'
    )
    
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    total_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])

    class Meta:
        db_table = 'order_item_modifiers'
        ordering = ['order_item', 'item_modifier']

    def __str__(self):
        return f"{self.item_modifier.name} - {self.order_item.menu_item.name}"

    def save(self, *args, **kwargs):
        from decimal import Decimal
        self.total_price = Decimal(str(self.unit_price)) * self.quantity
        super().save(*args, **kwargs)

class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('cancelled', 'Cancelled'),
    )
    
    PAYMENT_METHOD_CHOICES = (
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('paypal', 'PayPal'),
        ('stripe', 'Stripe'),
        ('cash', 'Cash on Delivery'),
        ('mobile_wallet', 'Mobile Wallet'),
    )
    
    payment_id = models.AutoField(primary_key=True)
    order = models.OneToOneField(
        'api.Order',
        on_delete=models.CASCADE,
        related_name='payment'
    )
    
    # Payment details
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    
    # Payment processing information
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    payment_gateway_response = models.JSONField(blank=True, null=True)
    
    # Timestamps
    payment_initiated_at = models.DateTimeField(auto_now_add=True)
    payment_completed_at = models.DateTimeField(null=True, blank=True)
    payment_failed_at = models.DateTimeField(null=True, blank=True)
    
    # Refund information
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0)])
    refund_reason = models.TextField(blank=True, null=True)
    refunded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'payments'
        ordering = ['-payment_initiated_at']
        indexes = [
            models.Index(fields=['payment_status']),
            models.Index(fields=['transaction_id']),
        ]

    def __str__(self):
        return f"Payment #{self.transaction_id or self.payment_id} - {self.amount}"

class OrderTracking(models.Model):
    tracking_id = models.AutoField(primary_key=True)
    order = models.ForeignKey(
        'api.Order',
        on_delete=models.CASCADE,
        related_name='tracking_history'
    )
    
    # Tracking information
    status = models.CharField(max_length=20, choices=Order.ORDER_STATUS_CHOICES)
    description = models.TextField(blank=True, null=True)
    
    # Staff who updated the status
    updated_by = models.ForeignKey(
        'api.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='order_updates'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'order_tracking'
        ordering = ['order', '-created_at']
        verbose_name_plural = 'order tracking'

    def __str__(self):
        return f"Order #{self.order.order_uuid} - {self.status} at {self.created_at}"

class Cart(models.Model):
    cart_id = models.AutoField(primary_key=True)
    customer = models.OneToOneField(
        'api.Customer',
        on_delete=models.CASCADE,
        related_name='cart'
    )
    
    restaurant = models.ForeignKey(
        'api.Restaurant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='carts'
    )

    applied_offers = models.ManyToManyField(
        'api.SpecialOffer',
        related_name='carts',
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'carts'
        ordering = ['-updated_at']

    def __str__(self):
        return f"Cart - {self.customer.user.username}"

    @property
    def total_items(self):
        return self.cart_items.count()
    
    @property
    def subtotal(self):
        from decimal import Decimal
        total = Decimal('0')
        for item in self.cart_items.all():
            total += Decimal(str(item.total_price))
        return total
    
    def get_restaurant(self):
        """Dynamically determine restaurant from items"""
        if self.restaurant:
            return self.restaurant
        if self.cart_items.exists():
            first_item = self.cart_items.first()
            return first_item.menu_item.category.restaurant
        return None

    def clean(self):
        """Validate that all items belong to the same restaurant"""
        if self.cart_items.exists():
            restaurants = set()
            for item in self.cart_items.all():
                restaurants.add(item.menu_item.category.restaurant)
            
            if len(restaurants) > 1:
                raise ValidationError("All cart items must belong to the same restaurant")
            
            if self.restaurant and self.restaurant not in restaurants:
                raise ValidationError("Cart restaurant must match item restaurants")
            
    @property
    def discount_amount(self):
        """Calculate total discount from applied offers"""
        from decimal import Decimal
        total_discount = Decimal('0')
        
        for offer in self.applied_offers.all():
            if offer.is_valid():
                discount = self.calculate_offer_discount(offer)
                total_discount += discount
        
        return total_discount
    
    @property
    def total_with_discount(self):
        """Calculate total with discounts applied"""
        return max(Decimal('0'), self.subtotal - self.discount_amount)
    
    def calculate_offer_discount(self, offer):
        """Calculate discount for a specific offer in cart"""
        from decimal import Decimal
        
        if not offer.is_valid():
            return Decimal('0.00')
        
        if offer.offer_type == 'percentage':
            return (self.subtotal * offer.discount_value) / Decimal('100')
        elif offer.offer_type == 'fixed':
            return min(offer.discount_value, self.subtotal)
        return Decimal('0.00')
    
    def apply_offer(self, offer, customer):
        """Apply special offer to cart with day validation"""
        if not offer.is_valid():
            # Provide specific reason why offer is invalid
            if not offer.is_active:
                raise ValidationError("Offer is no longer active")
            elif not offer.is_valid_for_day():
                raise ValidationError(f"This offer is only available on {offer.get_valid_days_display()}")
            elif offer.max_usage > 0 and offer.current_usage >= offer.max_usage:
                raise ValidationError("This offer has reached its usage limit")
            else:
                raise ValidationError("Offer is no longer valid")
        
        if not offer.can_user_use(customer.user):
            raise ValidationError("You have reached the usage limit for this offer")
        
        if self.subtotal < offer.min_order_amount:
            raise ValidationError(f"Cart subtotal must be at least {offer.min_order_amount}")
        
        # Check applicable items if offer is item-specific
        if offer.applicable_items.exists():
            cart_item_ids = set(self.cart_items.values_list('menu_item_id', flat=True))
            applicable_item_ids = set(offer.applicable_items.values_list('item_id', flat=True))
            
            if not cart_item_ids.intersection(applicable_item_ids):
                raise ValidationError("No applicable items in cart for this offer")
        
        self.applied_offers.add(offer)
        self.save()
        return True
    
    def remove_offer(self, offer):
        """Remove special offer from cart"""
        self.applied_offers.remove(offer)
        self.save()
        return True
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

class CartItem(models.Model):
    cart_item_id = models.AutoField(primary_key=True)
    cart = models.ForeignKey(
        'api.Cart',
        on_delete=models.CASCADE,
        related_name='cart_items'
    )
    menu_item = models.ForeignKey(
        'api.MenuItem',
        on_delete=models.CASCADE,
        related_name='cart_items'
    )
    
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    total_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    special_instructions = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cart_items'
        ordering = ['cart', '-created_at']
        unique_together = ['cart', 'menu_item']

    def __str__(self):
        return f"{self.quantity}x {self.menu_item.name} - Cart #{self.cart.cart_id}"

    def save(self, *args, **kwargs):
        from decimal import Decimal
        # Calculate total price before saving
        self.total_price = Decimal(str(self.unit_price)) * self.quantity
        super().save(*args, **kwargs)

class CartItemModifier(models.Model):
    cart_item_modifier_id = models.AutoField(primary_key=True)
    cart_item = models.ForeignKey(
        'api.CartItem',
        on_delete=models.CASCADE,
        related_name='modifiers'
    )
    item_modifier = models.ForeignKey(
        'api.ItemModifier',
        on_delete=models.CASCADE,
        related_name='cart_modifiers'
    )
    
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    total_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])

    class Meta:
        db_table = 'cart_item_modifiers'
        ordering = ['cart_item', 'item_modifier']
        unique_together = ['cart_item', 'item_modifier']

    def __str__(self):
        return f"{self.item_modifier.name} - {self.cart_item.menu_item.name}"

    def save(self, *args, **kwargs):
        from decimal import Decimal
        self.total_price = Decimal(str(self.unit_price)) * self.quantity
        super().save(*args, **kwargs)