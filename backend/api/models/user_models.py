from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator


class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('customer', 'Customer'),
        ('owner', 'Restaurant Owner'),
        ('staff', 'Restaurant Staff'),
        ('admin', 'Administrator'),
    )
    
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='customer')
    email=models.EmailField(unique=True, db_index=True)
    phone_number = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$', 'Enter a valid phone number.')]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    verification_code = models.CharField(max_length=10, blank=True, null=True)
    verification_code_expires = models.DateTimeField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    # Social authentication fields
    social_auth_provider = models.CharField(max_length=20, blank=True, null=True)
    social_auth_uid = models.CharField(max_length=255, blank=True, null=True)

    # Owner-specific fields
    is_restaurant_owner = models.BooleanField(default=False)
    owned_restaurants = models.ManyToManyField(
        'api.Restaurant', 
        through='RestaurantOwnership',
        related_name='owners',
        blank=True
    )

    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['user_type']),
            models.Index(fields=['created_at']),
            models.Index(fields=['social_auth_provider', 'social_auth_uid']),
            models.Index(fields=['is_restaurant_owner']),
        ]

    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"
    
    def save(self, *args, **kwargs):
        # Automatically set is_restaurant_owner based on user_type
        if self.user_type == 'owner':
            self.is_restaurant_owner = True
        super().save(*args, **kwargs)
    
class Customer(models.Model):
    customer_id = models.AutoField(primary_key=True)
    user = models.OneToOneField(
        'api.User', 
        on_delete=models.CASCADE, 
        related_name='customer_profile'
    )
    date_of_birth = models.DateField(null=True, blank=True)
    loyalty_points = models.IntegerField(default=0)
    dietary_preferences = models.JSONField(default=dict, blank=True)  # {'vegetarian': True, 'gluten_free': False}
    favorite_cuisines = models.ManyToManyField('api.Cuisine', blank=True)
    favorite_restaurants = models.ManyToManyField('api.Restaurant', blank=True, related_name='favorited_by')
    newsletter_subscribed = models.BooleanField(default=True)
    marketing_emails = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'customers'
        ordering = ['-created_at']

    def __str__(self):
        return f"Customer: {self.user.get_full_name() or self.user.username}"

    @property
    def email(self):
        return self.user.email

    @property
    def phone_number(self):
        return self.user.phone_number

    def add_loyalty_points(self, points):
        """Add loyalty points to customer"""
        self.loyalty_points += points
        self.save()

    def get_dietary_restrictions(self):
        """Get active dietary restrictions"""
        return [pref for pref, active in self.dietary_preferences.items() if active]
    

class RestaurantStaff(models.Model):
    ROLE_CHOICES = (
        ('owner', 'Owner'),
        ('manager', 'Manager'),
        ('chef', 'Chef'),
        ('cashier', 'Cashier'),
        ('waiter', 'Waiter'),
        ('delivery', 'Delivery Driver'),
        ('other', 'Other Staff'),
    )

    PERMISSION_LEVEL_CHOICES = (
        ('owner', 'Owner'),
        ('manager', 'Manager'),
        ('kitchen', 'Kitchen Staff'),
        ('delivery', 'Delivery Staff'),
        ('cashier', 'Cashier'),
    )
    
    staff_id = models.AutoField(primary_key=True)
    user = models.OneToOneField(
        'api.User', 
        on_delete=models.CASCADE, 
        related_name='staff_profile'
    )
    restaurant = models.ForeignKey(
        'api.Restaurant', 
        on_delete=models.CASCADE, 
        related_name='staff_members'
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    permission_level = models.CharField(max_length=20, choices=PERMISSION_LEVEL_CHOICES, default='cashier')

    # Branch access control
    branch_access = models.ManyToManyField(
        'api.Branch', 
        related_name='authorized_staff',
        blank=True
    )

    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    hire_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    can_manage_orders = models.BooleanField(default=False)
    can_manage_menu = models.BooleanField(default=False)
    can_manage_staff = models.BooleanField(default=False)
    can_view_reports = models.BooleanField(default=False)
    can_manage_finances = models.BooleanField(default=False)
    can_manage_reservations = models.BooleanField(default=False)

    shifts = models.JSONField(default=dict, blank=True)  # {'monday': ['09:00-17:00'], ...}
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'restaurant_staff'
        unique_together = ['user', 'restaurant']
        ordering = ['-hire_date']

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_role_display()} at {self.restaurant.name}"
    
    def save(self, *args, **kwargs):
        # Set permissions based on role
        self.set_permissions_by_role()
        super().save(*args, **kwargs)

    def set_permissions_by_role(self):
        """Automatically set permissions based on role"""
        role_permissions = {
            'owner': {
                'can_manage_orders': True,
                'can_manage_menu': True,
                'can_manage_staff': True,
                'can_view_reports': True,
                'can_manage_finances': True,
                'can_manage_reservations': True,
                'permission_level': 'owner'
            },
            'manager': {
                'can_manage_orders': True,
                'can_manage_menu': True,
                'can_manage_staff': True,
                'can_view_reports': True,
                'can_manage_finances': False,
                'can_manage_reservations': True,
                'permission_level': 'manager'
            },
            'chef': {
                'can_manage_orders': True,
                'can_manage_menu': False,
                'can_manage_staff': False,
                'can_view_reports': False,
                'can_manage_finances': False,
                'can_manage_reservations': False,
                'permission_level': 'kitchen'
            },
            'cashier': {
                'can_manage_orders': True,
                'can_manage_menu': False,
                'can_manage_staff': False,
                'can_view_reports': False,
                'can_manage_finances': False,
                'can_manage_reservations': False,
                'permission_level': 'cashier'
            },
            'delivery': {
                'can_manage_orders': False,
                'can_manage_menu': False,
                'can_manage_staff': False,
                'can_view_reports': False,
                'can_manage_finances': False,
                'can_manage_reservations': False,
                'permission_level': 'delivery'
            }
        }
        
        if self.role in role_permissions:
            permissions = role_permissions[self.role]
            for perm, value in permissions.items():
                setattr(self, perm, value)

    @property
    def is_manager(self):
        return self.role == 'manager'

    @property
    def is_chef(self):
        return self.role == 'chef'

    @property
    def can_access_kitchen(self):
        return self.role in ['chef', 'manager', 'owner']

    @property
    def can_process_payments(self):
        return self.role in ['cashier', 'manager', 'owner']
    
    def has_branch_access(self, branch):
        """Check if staff has access to specific branch"""
        if not self.branch_access.exists():
            return True  # No restrictions = access to all branches
        return self.branch_access.filter(pk=branch.pk).exists()

    def activate(self):
        """Activate staff member"""
        self.is_active = True
        self.save()

    def deactivate(self):
        """Deactivate staff member"""
        self.is_active = False
        self.save()


class RestaurantOwnership(models.Model):
    """Through model for restaurant ownership with additional fields"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    restaurant = models.ForeignKey('api.Restaurant', on_delete=models.CASCADE)
    is_primary_owner = models.BooleanField(default=False)
    ownership_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=100.00)
    joined_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'restaurant_ownership'
        unique_together = ['user', 'restaurant']