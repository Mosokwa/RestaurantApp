from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone


class Cuisine(models.Model):
    cuisine_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cuisines'
        ordering = ['name']

    def __str__(self):
        return self.name
    
class MenuCategory(models.Model):
    category_id = models.AutoField(primary_key=True)
    restaurant = models.ForeignKey(
        'api.Restaurant',
        on_delete=models.CASCADE,
        related_name='menu_categories'
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    display_color = models.CharField(max_length=7, default='#FF6B35')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'menu_categories'
        ordering = ['restaurant', 'display_order', 'name']
        unique_together = ['restaurant', 'name']
        verbose_name_plural = 'menu categories'
        indexes = [
            models.Index(fields=['is_featured']),
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.name}"

class MenuItem(models.Model):
    ITEM_TYPES = (
        ('main', 'Main Dish'),
        ('beverage', 'Beverage'),
        ('dessert', 'Dessert'),
        ('side', 'Side Dish'),
        ('combo', 'Combo Meal'),
    )
    
    item_id = models.AutoField(primary_key=True)
    category = models.ForeignKey(
        'api.MenuCategory',
        on_delete=models.CASCADE,
        related_name='menu_items'
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    item_type = models.CharField(max_length=20, choices=ITEM_TYPES, default='main')
    image = models.ImageField(upload_to='menu_items/', blank=True, null=True)
    is_vegetarian = models.BooleanField(default=False)
    is_vegan = models.BooleanField(default=False)
    is_gluten_free = models.BooleanField(default=False)
    is_spicy = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    calories = models.IntegerField(blank=True, null=True, validators=[MinValueValidator(0)])
    preparation_time = models.IntegerField(help_text="Preparation time in minutes", default=15)

    popularity_score = models.IntegerField(default=0)
    last_ordered = models.DateTimeField(null=True, blank=True)
    order_count = models.IntegerField(default=0)
    seasonal_boost = models.IntegerField(default=0)

    is_available = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'menu_items'
        ordering = ['category__display_order', 'display_order', 'name']
        indexes = [
            models.Index(fields=['is_available']),
            models.Index(fields=['item_type']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['popularity_score']),
            models.Index(fields=['last_ordered']),  # NEW INDEX
            models.Index(fields=['order_count']),   # NEW INDEX

        ]

    def __str__(self):
        return f"{self.category.restaurant.name} - {self.name}"

    @property
    def restaurant(self):
        return self.category.restaurant
    
    def increment_popularity(self, points=1):
        """Increment popularity score"""
        self.popularity_score += points
        self.save(update_fields=['popularity_score'])

    def update_popularity_metrics(self):
        """Update popularity metrics based on recent orders and ratings"""
        from django.db.models import Count
        from datetime import timedelta
        
        # Calculate recent orders (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_orders = self.order_items.filter(
            order__order_placed_at__gte=thirty_days_ago
        ).count()
        
        # Get average rating
        rating_stats = self.get_rating_stats()
        avg_rating = rating_stats.get('average_rating', 0) or 0
        
        # Calculate seasonal boost
        seasonal_boost = self.calculate_seasonal_boost()
        
        # Calculate popularity score
        self.popularity_score = self.calculate_popularity_score(
            order_count=self.order_count,
            recent_orders=recent_orders,
            avg_rating=avg_rating,
            seasonal_boost=seasonal_boost
        )
        
        self.save(update_fields=['popularity_score', 'seasonal_boost'])

    def calculate_popularity_score(self, order_count, recent_orders, avg_rating, seasonal_boost):
        """Calculate comprehensive popularity score"""
        score = (
            (order_count * 10) +                    # Base order count
            (recent_orders * 5) +                   # Recent orders bonus
            (avg_rating * 20) +                     # Rating influence
            (50 if self.is_featured else 0) +       # Featured item boost
            seasonal_boost -                        # Seasonal adjustments
            (100 if not self.is_available else 0)   # Penalty for unavailable
        )
        return max(0, score)  # Ensure non-negative

    def calculate_seasonal_boost(self):
        """Calculate seasonal boost based on current month and item type"""
        current_month = timezone.now().month
        
        # Seasonal mapping (customize based on your menu)
        seasonal_boosts = {
            # Summer boosts for cold items
            6: {'beverage': 30, 'dessert': 20},  # June
            7: {'beverage': 40, 'dessert': 25},  # July
            8: {'beverage': 35, 'dessert': 20},  # August
            
            # Winter boosts for warm items
            12: {'main': 25, 'beverage': 20},    # December
            1: {'main': 30, 'beverage': 25},     # January
            2: {'main': 25, 'beverage': 20},     # February
        }
        
        boost_config = seasonal_boosts.get(current_month, {})
        return boost_config.get(self.item_type, 0) + self.seasonal_boost

    def update_restaurant_popularity_metrics(self):
        """Update popularity metrics within restaurant context"""
        # Restaurant-specific calculations
        restaurant = self.category.restaurant
        
        # Calculate rank within restaurant
        restaurant_items = MenuItem.objects.filter(
            category__restaurant=restaurant
        ).order_by('-popularity_score')
        
        current_rank = list(restaurant_items).index(self) + 1 if self in list(restaurant_items) else None
        
        # Update metrics
        self.update_popularity_metrics()
        
        return {
            'restaurant_rank': current_rank,
            'total_restaurant_items': restaurant_items.count(),
            'popularity_score': self.popularity_score
        }
    
    def update_rating_stats(self):
        """Update rating statistics for the menu item"""
        from django.db.models import Avg, Count
        from decimal import Decimal
        
        aggregates = self.ratings.aggregate(
            total_ratings=Count('dish_rating_id'),
            avg_rating=Avg('rating'),
            avg_taste=Avg('taste'),
            avg_portion=Avg('portion_size'),
            avg_value=Avg('value')
        )
        
        # Get rating distribution
        distribution = self.ratings.values('rating').annotate(
            count=Count('dish_rating_id')
        ).order_by('rating')
        
        rating_distribution = {str(i): 0 for i in range(1, 6)}
        for item in distribution:
            rating_distribution[str(int(item['rating']))] = item['count']
        
        # Get tag frequencies
        all_tags = []
        for rating in self.ratings.filter(tags__len__gt=0):
            all_tags.extend(rating.tags)
        
        tag_frequencies = {}
        for tag in all_tags:
            tag_frequencies[tag] = tag_frequencies.get(tag, 0) + 1
        
        # Create or update aggregate
        from ..models import RatingAggregate
        aggregate, created = RatingAggregate.objects.get_or_create(
            content_type='menu_item',
            object_id=self.item_id
        )
        
        aggregate.total_ratings = aggregates['total_ratings'] or 0
        aggregate.average_rating = Decimal(str(aggregates['avg_rating'] or 0))
        aggregate.average_food_quality = Decimal(str(aggregates['avg_taste'] or 0))
        aggregate.average_service_quality = Decimal(str(aggregates['avg_portion'] or 0))
        aggregate.average_value = Decimal(str(aggregates['avg_value'] or 0))
        aggregate.rating_distribution = rating_distribution
        aggregate.tag_frequencies = tag_frequencies
        aggregate.save()

    def get_rating_stats(self):
        """Get comprehensive rating statistics for menu item"""
        from ..models import RatingAggregate
        try:
            aggregate = RatingAggregate.objects.get(
                content_type='menu_item',
                object_id=self.item_id
            )
            return {
                'total_ratings': aggregate.total_ratings,
                'average_rating': float(aggregate.average_rating),
                'rating_distribution': aggregate.rating_distribution,
                'tag_frequencies': aggregate.tag_frequencies,
                'detailed_averages': {
                    'taste': float(aggregate.average_food_quality),
                    'portion_size': float(aggregate.average_service_quality),
                    'value': float(aggregate.average_value)
                }
            }
        except RatingAggregate.DoesNotExist:
            return {
                'total_ratings': 0,
                'average_rating': 0.0,
                'rating_distribution': {},
                'tag_frequencies': {},
                'detailed_averages': {}
            }

    def get_user_rating(self, user):
        """Get a specific user's rating for this menu item"""
        from ..models import DishRating
        if hasattr(user, 'customer_profile'):
            try:
                rating = DishRating.objects.get(
                    menu_item=self,
                    customer=user.customer_profile
                )
                return rating
            except DishRating.DoesNotExist:
                return None
        return None


class PopularitySnapshot(models.Model):
    """Track daily popularity scores for trend analysis"""
    snapshot_id = models.AutoField(primary_key=True)
    menu_item = models.ForeignKey(
        'MenuItem',
        on_delete=models.CASCADE,
        related_name='popularity_snapshots'
    )
    score = models.IntegerField()
    order_count = models.IntegerField()
    rank = models.IntegerField()  # Rank within restaurant
    date_recorded = models.DateField(auto_now_add=True)
    
    class Meta:
        db_table = 'popularity_snapshots'
        ordering = ['-date_recorded', 'rank']
        unique_together = ['menu_item', 'date_recorded']
        indexes = [
            models.Index(fields=['date_recorded', 'rank']),
            models.Index(fields=['menu_item', 'date_recorded']),
        ]

    def __str__(self):
        return f"{self.menu_item.name} - Score: {self.score} ({self.date_recorded})"

class ItemAssociation(models.Model):
    """Track items frequently bought together"""
    association_id = models.AutoField(primary_key=True)
    source_item = models.ForeignKey(
        'MenuItem',
        on_delete=models.CASCADE,
        related_name='associated_items'
    )
    target_item = models.ForeignKey(
        'MenuItem',
        on_delete=models.CASCADE,
        related_name='reverse_associations'
    )
    confidence = models.DecimalField(max_digits=5, decimal_places=4, default=0.0)
    support = models.IntegerField(default=0)  # Number of co-occurrences
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'item_associations'
        unique_together = ['source_item', 'target_item']
        ordering = ['-confidence']
        indexes = [
            models.Index(fields=['source_item', 'confidence']),
            models.Index(fields=['target_item', 'confidence']),
        ]

    def __str__(self):
        return f"{self.source_item.name} → {self.target_item.name} ({self.confidence})"


class ItemModifierGroup(models.Model):
    modifier_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    is_required = models.BooleanField(default=False)
    min_selections = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    max_selections = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'item_modifier_groups'
        ordering = ['name']

    def __str__(self):
        return self.name

class ItemModifier(models.Model):
    item_modifier_id = models.AutoField(primary_key=True)
    modifier_group = models.ForeignKey(
        'ItemModifierGroup',
        on_delete=models.CASCADE,
        related_name='modifiers'
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    price_modifier = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00,
        validators=[MinValueValidator(0)]
    )
    is_available = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'item_modifiers'
        ordering = ['modifier_group', 'display_order', 'name']

    def __str__(self):
        return f"{self.modifier_group.name} - {self.name}"

class MenuItemModifier(models.Model):
    menu_item = models.ForeignKey('api.MenuItem', on_delete=models.CASCADE)
    modifier_group = models.ForeignKey('api.ItemModifierGroup', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'menu_item_modifiers'
        unique_together = ['menu_item', 'modifier_group']
        ordering = ['modifier_group__name']

    def __str__(self):
        return f"{self.menu_item.name} - {self.modifier_group.name}"

class SpecialOffer(models.Model):
    OFFER_TYPES = (
        ('percentage', 'Percentage Discount'),
        ('fixed', 'Fixed Amount Discount'),
        ('bogo', 'Buy One Get One'),
        ('combo', 'Combo Deal'),
    )
    
    offer_id = models.AutoField(primary_key=True)
    restaurant = models.ForeignKey(
        'api.Restaurant',
        on_delete=models.CASCADE,
        related_name='special_offers'
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    offer_type = models.CharField(max_length=20, choices=OFFER_TYPES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    image = models.ImageField(upload_to='special_offers/', blank=True, null=True)  # NEW: Visual for carousel
    applicable_items = models.ManyToManyField('api.MenuItem', blank=True, related_name='special_offers')
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0)])
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    valid_days = models.JSONField(
        default=list, 
        blank=True,
        help_text="Leave empty for all days. Example: ['monday', 'tuesday']"
    )
    display_priority = models.IntegerField(default=0)  # NEW: Order in carousel (higher = first)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)  # NEW: Highlight on homepage
    max_usage = models.IntegerField(default=0, help_text="0 for unlimited")
    max_usage_per_user = models.IntegerField(default=0)  # NEW: 0 = unlimited
    current_usage = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        db_table = 'special_offers'
        ordering = ['-display_priority', '-valid_from', 'restaurant']
        indexes = [
            models.Index(fields=['is_active', 'is_featured']),
            models.Index(fields=['valid_from', 'valid_until']),
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.title}"
    
    def is_valid_for_day(self):
        """Check if offer is valid for current day (for day-specific offers)"""
        now = timezone.now()
        current_day = now.strftime('%A').lower()
        
        # If no specific days set, offer is valid every day
        if not self.valid_days:
            return True
            
        return current_day in self.valid_days

    def is_valid(self):
        """Enhanced validation including day-specific checks"""
        now = timezone.now()
        
        # Basic validation
        basic_valid = (self.is_active and 
                      self.valid_from <= now <= self.valid_until and
                      (self.max_usage == 0 or self.current_usage < self.max_usage))
        
        # Day-specific validation
        day_valid = self.is_valid_for_day()
        
        return basic_valid and day_valid
    
    def can_user_use(self, user):
        """Check if user can use this offer based on usage limits"""
        if self.max_usage_per_user == 0:
            return True
        
        if not hasattr(user, 'customer_profile'):
            return False
        
        from .ratingsandreviews_models import OfferUsage
        user_usage_count = OfferUsage.objects.filter(
            offer=self,
            customer=user.customer_profile,
            is_successful=True
        ).count()
        
        return user_usage_count < self.max_usage_per_user

    def get_user_usage_count(self, user):
        """Get how many times a user has used this offer"""
        if not hasattr(user, 'customer_profile'):
            return 0
        
        from .ratingsandreviews_models import OfferUsage
        return OfferUsage.objects.filter(
            offer=self,
            customer=user.customer_profile,
            is_successful=True
        ).count()
    
    def get_valid_days_display(self):
        """Get human-readable valid days"""
        if not self.valid_days:
            return "Every day"
        
        day_names = {
            'monday': 'Monday',
            'tuesday': 'Tuesday', 
            'wednesday': 'Wednesday',
            'thursday': 'Thursday',
            'friday': 'Friday',
            'saturday': 'Saturday',
            'sunday': 'Sunday'
        }
        
        display_days = [day_names.get(day, day) for day in self.valid_days]
        return ", ".join(display_days)

    def get_next_valid_day(self):
        """Get the next day when this offer will be valid"""
        if not self.valid_days:
            return "Available every day"
        
        from datetime import datetime, timedelta
        now = timezone.now()
        current_day = now.strftime('%A').lower()
        
        days_of_week = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        
        # Find next valid day
        current_index = days_of_week.index(current_day)
        for i in range(1, 8):  # Check next 7 days
            next_day_index = (current_index + i) % 7
            next_day = days_of_week[next_day_index]
            if next_day in self.valid_days:
                days_until = i
                if days_until == 1:
                    return "Tomorrow"
                else:
                    return f"This {next_day.capitalize()}"  # "This Tuesday"
        
        return "Not available soon"
