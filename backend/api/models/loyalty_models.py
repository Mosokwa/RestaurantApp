import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.core.exceptions import ValidationError

class MultiRestaurantLoyaltyProgram(models.Model):
    """
    Global loyalty program that supports multiple restaurants
    Each restaurant can have its own settings within the global program
    """
    PROGRAM_TYPES = (
        ('global', 'Global Program - All Restaurants'),
        ('franchise', 'Franchise Program - Restaurant Groups'),
        ('independent', 'Independent Program - Single Restaurant'),
    )
    
    program_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, default="Multi-Restaurant Loyalty Program")
    program_type = models.CharField(max_length=20, choices=PROGRAM_TYPES, default='global')
    is_active = models.BooleanField(default=True)
    
    # Global points configuration (can be overridden per restaurant)
    default_points_per_dollar = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)
    global_signup_bonus_points = models.IntegerField(default=100)
    global_referral_bonus_points = models.IntegerField(default=500)
    
    # Global tier configurations
    bronze_min_points = models.IntegerField(default=0)
    silver_min_points = models.IntegerField(default=1000)
    gold_min_points = models.IntegerField(default=5000)
    platinum_min_points = models.IntegerField(default=15000)
    
    # Program scope - which restaurants participate
    participating_restaurants = models.ManyToManyField(
        'api.Restaurant',
        related_name='loyalty_programs',
        blank=True,
        help_text="Restaurants participating in this program (empty for all restaurants)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'multi_restaurant_loyalty_programs'

    def __str__(self):
        return f"{self.name} ({self.get_program_type_display()})"

    def is_restaurant_participating(self, restaurant):
        """Check if a specific restaurant participates in this program"""
        if self.program_type == 'global':
            return True  # Global program includes all restaurants
        elif self.program_type == 'independent':
            return self.participating_restaurants.filter(pk=restaurant.pk).exists()
        else:  # franchise
            # For franchise programs, check if restaurant belongs to the same franchise group
            # This would require a franchise_group field on the Restaurant model
            return self.participating_restaurants.filter(pk=restaurant.pk).exists()

class RestaurantLoyaltySettings(models.Model):
    """
    Restaurant-specific loyalty program settings within the global program
    """
    settings_id = models.AutoField(primary_key=True)
    restaurant = models.OneToOneField(
        'api.Restaurant',
        on_delete=models.CASCADE,
        related_name='loyalty_settings'
    )
    program = models.ForeignKey(
        MultiRestaurantLoyaltyProgram,
        on_delete=models.CASCADE,
        related_name='restaurant_settings'
    )
    
    # Enable/disable loyalty for this specific restaurant
    is_loyalty_enabled = models.BooleanField(default=True)
    
    # Restaurant-specific points rates (override global settings)
    custom_points_per_dollar = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True,
        blank=True,
        help_text="Leave empty to use program default rate"
    )
    
    # Restaurant-specific bonuses
    custom_signup_bonus_points = models.IntegerField(null=True, blank=True)
    custom_referral_bonus_points = models.IntegerField(null=True, blank=True)
    
    # Restaurant-specific tier benefits
    custom_tier_benefits = models.JSONField(
        default=dict,
        blank=True,
        help_text="JSON structure for custom tier benefits for this restaurant"
    )
    
    # Restrictions
    minimum_order_amount_for_points = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)]
    )
    
    # Reward restrictions
    allow_point_redemption = models.BooleanField(default=True)
    allow_reward_redemption = models.BooleanField(default=True)
    
    # Restaurant-specific program rules
    points_expiry_days = models.IntegerField(default=365, help_text="Days before points expire")
    max_points_per_order = models.IntegerField(null=True, blank=True, help_text="Maximum points per order")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'restaurant_loyalty_settings'
        verbose_name_plural = 'restaurant loyalty settings'
        unique_together = ['restaurant', 'program']

    def __str__(self):
        return f"Loyalty Settings - {self.restaurant.name}"

    @property
    def effective_points_rate(self):
        """Get the effective points rate for this restaurant"""
        if self.custom_points_per_dollar is not None:
            return self.custom_points_per_dollar
        return self.program.default_points_per_dollar

    @property
    def effective_signup_bonus(self):
        """Get effective signup bonus for this restaurant"""
        if self.custom_signup_bonus_points is not None:
            return self.custom_signup_bonus_points
        return self.program.global_signup_bonus_points

    @property
    def effective_referral_bonus(self):
        """Get effective referral bonus for this restaurant"""
        if self.custom_referral_bonus_points is not None:
            return self.custom_referral_bonus_points
        return self.program.global_referral_bonus_points

    def is_loyalty_active(self):
        """Check if loyalty is fully active for this restaurant"""
        return (self.is_loyalty_enabled and 
                self.program.is_active and 
                self.program.is_restaurant_participating(self.restaurant))

class CustomerLoyalty(models.Model):
    """
    Customer loyalty profile that works across multiple restaurants
    """
    TIER_CHOICES = (
        ('bronze', 'Bronze'),
        ('silver', 'Silver'),
        ('gold', 'Gold'),
        ('platinum', 'Platinum'),
    )
    
    loyalty_id = models.AutoField(primary_key=True)
    customer = models.OneToOneField(
        'api.Customer',
        on_delete=models.CASCADE,
        related_name='loyalty_profile'
    )
    program = models.ForeignKey(
        MultiRestaurantLoyaltyProgram,
        on_delete=models.CASCADE,
        related_name='customers'
    )
    
    # Global points and tier (across all restaurants in the program)
    current_points = models.IntegerField(default=0)
    lifetime_points = models.IntegerField(default=0)
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='bronze')
    
    # Cross-restaurant statistics
    total_orders = models.IntegerField(default=0)
    total_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # Restaurant-specific statistics (JSON field for flexibility)
    restaurant_stats = models.JSONField(
        default=dict,
        blank=True,
        help_text="Statistics per restaurant: {restaurant_id: {orders: X, spent: Y, last_order: date}}"
    )
    
    # Referral information (works across all restaurants)
    referral_code = models.CharField(max_length=20, unique=True, blank=True)
    referred_by = models.ForeignKey(
        'api.Customer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='referrals'
    )
    
    # Timestamps
    joined_at = models.DateTimeField(auto_now_add=True)
    tier_updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'customer_loyalty'
        verbose_name_plural = 'customer loyalties'
        indexes = [
            models.Index(fields=['customer', 'program']),
            models.Index(fields=['tier']),
            models.Index(fields=['current_points']),
        ]

    def __str__(self):
        return f"{self.customer.user.email} - {self.tier} - {self.program.name}"

    def save(self, *args, **kwargs):
        # Generate referral code if not exists
        if not self.referral_code:
            self.referral_code = self._generate_referral_code()
    
        # Track tier changes for email notifications
        old_tier = None
        if self.pk:
            try:
                old_instance = CustomerLoyalty.objects.get(pk=self.pk)
                old_tier = old_instance.tier
            except CustomerLoyalty.DoesNotExist:
                pass
        
        self._update_tier()
        
        super().save(*args, **kwargs)
    
        # Send tier upgrade email if tier changed
        if old_tier and old_tier != self.tier:
            from ..services.loyalty_email_service import EmailService
            new_benefits = self.get_tier_benefits()
            EmailService.send_tier_upgrade_email(self, old_tier, self.tier, new_benefits)
    
    def _generate_referral_code(self):
        import random
        import string
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        while CustomerLoyalty.objects.filter(referral_code=code).exists():
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        return code
    
    def _update_tier(self):
        program = self.program
        if self.current_points >= program.platinum_min_points:
            new_tier = 'platinum'
        elif self.current_points >= program.gold_min_points:
            new_tier = 'gold'
        elif self.current_points >= program.silver_min_points:
            new_tier = 'silver'
        else:
            new_tier = 'bronze'
        
        if new_tier != self.tier:
            self.tier = new_tier
            self.tier_updated_at = timezone.now()
    
    def update_restaurant_stats(self, restaurant, order_amount):
        """Update statistics for a specific restaurant"""
        restaurant_id = str(restaurant.restaurant_id)
        
        if restaurant_id not in self.restaurant_stats:
            self.restaurant_stats[restaurant_id] = {
                'orders': 0,
                'spent': '0.00',
                'last_order': timezone.now().isoformat(),
                'restaurant_name': restaurant.name
            }
        
        stats = self.restaurant_stats[restaurant_id]
        stats['orders'] += 1
        stats['spent'] = str(float(stats['spent']) + float(order_amount))
        stats['last_order'] = timezone.now().isoformat()
        
        self.save()
    
    def get_restaurant_stats(self, restaurant):
        """Get statistics for a specific restaurant"""
        restaurant_id = str(restaurant.restaurant_id)
        return self.restaurant_stats.get(restaurant_id, {
            'orders': 0,
            'spent': '0.00',
            'last_order': None,
            'restaurant_name': restaurant.name
        })
    
    def add_points(self, points, reason="", order=None, restaurant=None):
        """Add points to customer's account with restaurant validation"""
        from django.db import transaction
        
        try:
            # Validate restaurant loyalty settings if provided
            if restaurant:
                try:
                    loyalty_settings = restaurant.loyalty_settings.get(program=self.program)
                    if not loyalty_settings.is_loyalty_active():
                        return False, "Loyalty program is disabled for this restaurant"
                    
                    # Check minimum order amount
                    if (order and 
                        loyalty_settings.minimum_order_amount_for_points > 0 and 
                        order.subtotal < loyalty_settings.minimum_order_amount_for_points):
                        return False, f"Order amount below minimum for points (${loyalty_settings.minimum_order_amount_for_points})"
                    
                    # Check max points per order
                    if (loyalty_settings.max_points_per_order and 
                        points > loyalty_settings.max_points_per_order):
                        points = loyalty_settings.max_points_per_order
                        reason += f" (capped at {points} points)"
                
                except RestaurantLoyaltySettings.DoesNotExist:
                    return False, "This restaurant is not configured for the loyalty program"
            
            with transaction.atomic():
                # Update points
                self.current_points += points
                self.lifetime_points += points
                
                # Update restaurant stats if applicable
                if restaurant and order:
                    self.update_restaurant_stats(restaurant, order.subtotal)
                    self.total_orders += 1
                    self.total_spent += order.subtotal
                
                self.save()
                
                # Create transaction record
                PointsTransaction.objects.create(
                    customer_loyalty=self,
                    points=points,
                    transaction_type='earned',
                    reason=reason,
                    order=order,
                    restaurant=restaurant
                )
            
            return True, "Points added successfully"
        
        except Exception as e:
            return False, f"Error adding points: {str(e)}"

    def get_tier_benefits(self, restaurant=None):
        """Get benefits for current tier, with restaurant-specific overrides"""
        base_benefits = {
            'bronze': {
                'discount_rate': 0,
                'priority_support': False,
                'free_delivery': False,
                'birthday_reward': True,
            },
            'silver': {
                'discount_rate': 5,
                'priority_support': False,
                'free_delivery': True,
                'birthday_reward': True,
            },
            'gold': {
                'discount_rate': 10,
                'priority_support': True,
                'free_delivery': True,
                'birthday_reward': True,
                'early_access': True,
            },
            'platinum': {
                'discount_rate': 15,
                'priority_support': True,
                'free_delivery': True,
                'birthday_reward': True,
                'early_access': True,
                'exclusive_events': True,
            }
        }
        
        benefits = base_benefits.get(self.tier, {}).copy()
        
        # Apply restaurant-specific overrides if available
        if restaurant:
            try:
                loyalty_settings = restaurant.loyalty_settings.get(program=self.program)
                if loyalty_settings.custom_tier_benefits:
                    custom_benefits = loyalty_settings.custom_tier_benefits.get(self.tier, {})
                    benefits.update(custom_benefits)
            except RestaurantLoyaltySettings.DoesNotExist:
                pass
        
        return benefits

class PointsTransaction(models.Model):
    """
    Track all loyalty points transactions (earnings and redemptions)
    """
    TRANSACTION_TYPES = (
        ('earned', 'Points Earned'),
        ('redeemed', 'Points Redeemed'),
        ('adjusted', 'Points Adjusted'),
        ('expired', 'Points Expired'),
        ('signup_bonus', 'Signup Bonus'),
        ('referral_bonus', 'Referral Bonus'),
    )
    
    transaction_id = models.AutoField(primary_key=True)
    customer_loyalty = models.ForeignKey(
        CustomerLoyalty,
        on_delete=models.CASCADE,
        related_name='points_transactions'
    )
    
    # Transaction details
    points = models.IntegerField(help_text="Positive for earned, negative for redeemed")
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    reason = models.TextField(blank=True, null=True)
    
    # Related objects
    order = models.ForeignKey(
        'api.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='loyalty_points_transactions'
    )
    reward = models.ForeignKey(
        'Reward',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='points_transactions'
    )
    restaurant = models.ForeignKey(
        'api.Restaurant',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='points_transactions'
    )
    
    # Metadata
    transaction_date = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True, help_text="When these points will expire")
    is_active = models.BooleanField(default=True, help_text="Whether these points are still active/valid")
    
    class Meta:
        db_table = 'points_transactions'
        ordering = ['-transaction_date']
        indexes = [
            models.Index(fields=['customer_loyalty', 'transaction_date']),
            models.Index(fields=['order']),
            models.Index(fields=['restaurant']),
        ]

    def __str__(self):
        sign = "+" if self.points > 0 else ""
        return f"{self.customer_loyalty.customer.user.email} - {sign}{self.points} points - {self.transaction_type}"

    def save(self, *args, **kwargs):
        # Set expiration date for earned points (e.g., 1 year from transaction)
        if self.points > 0 and not self.expires_at and self.transaction_type in ['earned', 'signup_bonus', 'referral_bonus']:
            self.expires_at = timezone.now() + timezone.timedelta(days=365)
        super().save(*args, **kwargs)

class Reward(models.Model):
    REWARD_TYPES = (
        ('discount', 'Discount'),
        ('free_item', 'Free Item'),
        ('free_delivery', 'Free Delivery'),
        ('voucher', 'Gift Voucher'),
    )
    
    reward_id = models.AutoField(primary_key=True)
    program = models.ForeignKey(
        MultiRestaurantLoyaltyProgram,
        on_delete=models.CASCADE,
        related_name='rewards'
    )
    
    # Restaurant-specific rewards (null means global reward)
    restaurant = models.ForeignKey(
        'api.Restaurant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='loyalty_rewards'
    )
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    reward_type = models.CharField(max_length=20, choices=REWARD_TYPES)
    
    # Reward value
    points_required = models.IntegerField(validators=[MinValueValidator(1)])
    discount_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    discount_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0)]
    )
    free_menu_item = models.ForeignKey(
        'api.MenuItem',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    # Availability
    is_active = models.BooleanField(default=True)
    stock_quantity = models.IntegerField(default=0)  # 0 for unlimited
    redeemed_count = models.IntegerField(default=0)
    
    # Tier restrictions
    min_tier_required = models.CharField(
        max_length=20,
        choices=CustomerLoyalty.TIER_CHOICES,
        default='bronze'
    )
    
    # Restaurant restrictions
    applicable_restaurants = models.ManyToManyField(
        'api.Restaurant',
        blank=True,
        related_name='applicable_rewards',
        help_text="Restaurants where this reward can be used (empty for all)"
    )
    
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'rewards'
        ordering = ['points_required']
        indexes = [
            models.Index(fields=['is_active', 'valid_from', 'valid_until']),
            models.Index(fields=['min_tier_required']),
        ]

    def __str__(self):
        scope = f" - {self.restaurant.name}" if self.restaurant else " (Global)"
        return f"{self.name}{scope} ({self.points_required} points)"

    def is_available(self, restaurant=None):
        """Check if reward is available for redemption at specific restaurant"""
        now = timezone.now()
        
        # Basic availability check
        if not (self.is_active and
                self.valid_from <= now and
                (not self.valid_until or now <= self.valid_until) and
                (self.stock_quantity == 0 or self.redeemed_count < self.stock_quantity)):
            return False
        
        # Restaurant-specific checks
        if restaurant:
            # Check if reward is restricted to specific restaurants
            if self.applicable_restaurants.exists() and not self.applicable_restaurants.filter(pk=restaurant.pk).exists():
                return False
            
            # Check restaurant loyalty settings
            try:
                loyalty_settings = restaurant.loyalty_settings
                if not loyalty_settings.allow_reward_redemption:
                    return False
            except RestaurantLoyaltySettings.DoesNotExist:
                pass  # No settings, allow by default
        
        return True

    def can_redeem_at_restaurant(self, restaurant):
        """Check if this reward can be redeemed at specific restaurant"""
        if self.restaurant and self.restaurant != restaurant:
            return False
        
        if self.applicable_restaurants.exists() and not self.applicable_restaurants.filter(pk=restaurant.pk).exists():
            return False
        
        return True

class RewardRedemption(models.Model):
    REDEMPTION_STATUS = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    )
    
    redemption_id = models.AutoField(primary_key=True)
    customer_loyalty = models.ForeignKey(
        CustomerLoyalty,
        on_delete=models.CASCADE,
        related_name='reward_redemptions'
    )
    reward = models.ForeignKey(
        Reward,
        on_delete=models.CASCADE,
        related_name='redemptions'
    )
    
    points_used = models.IntegerField()
    status = models.CharField(max_length=20, choices=REDEMPTION_STATUS, default='pending')
    
    # Restaurant where reward is being redeemed
    restaurant = models.ForeignKey(
        'api.Restaurant',
        on_delete=models.CASCADE,
        related_name='reward_redemptions'
    )
    
    # Redemption code for discounts/free items
    redemption_code = models.CharField(max_length=20, unique=True)
    
    # For discount rewards
    discount_voucher = models.OneToOneField(
        'DiscountVoucher',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='redemption'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    redeemed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'reward_redemptions'
        indexes = [
            models.Index(fields=['redemption_code']),
            models.Index(fields=['status', 'expires_at']),
        ]

    def __str__(self):
        return f"{self.customer_loyalty.customer.user.email} - {self.reward.name}"

    def save(self, *args, **kwargs):
        if not self.redemption_code:
            self.redemption_code = self._generate_redemption_code()
        super().save(*args, **kwargs)
    
    def _generate_redemption_code(self):
        import random
        import string
        code = 'RWD-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        while RewardRedemption.objects.filter(redemption_code=code).exists():
            code = 'RWD-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        return code

class DiscountVoucher(models.Model):
    voucher_id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=20, unique=True)
    
    # Restaurant restriction
    restaurant = models.ForeignKey(
        'api.Restaurant',
        on_delete=models.CASCADE,
        related_name='loyalty_vouchers',
        null=True,
        blank=True
    )
    
    discount_type = models.CharField(max_length=20, choices=(
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ))
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    max_discount_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    
    is_used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)
    
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField()
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'discount_vouchers'
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_used', 'valid_until']),
        ]

    def __str__(self):
        return self.code

    def is_valid(self, restaurant=None):
        """Check if voucher is valid for specific restaurant"""
        now = timezone.now()
        
        if (self.is_used or 
            self.valid_from > now or 
            self.valid_until < now):
            return False
        
        # Check restaurant restriction
        if self.restaurant and restaurant and self.restaurant != restaurant:
            return False