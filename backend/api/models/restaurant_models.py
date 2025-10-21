from django.db import models
from datetime import timedelta
from django.core.validators import RegexValidator
from django.utils import timezone


class Restaurant(models.Model):
    RESTAURANT_STATUS = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('pending', 'Pending Approval'),
        ('suspended', 'Suspended'),
    )
    
    restaurant_id = models.AutoField(primary_key=True)
    owner = models.ForeignKey(
        'api.User', 
        on_delete=models.CASCADE, 
        related_name='restaurants',
        limit_choices_to={'user_type': 'owner'}
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    story_description = models.TextField(blank=True, null=True)
    cuisines = models.ManyToManyField('Cuisine', related_name='restaurants', blank=True)
    logo = models.ImageField(upload_to='restaurant_logos/', blank=True, null=True)
    banner_image = models.ImageField(upload_to='restaurant_banners/', blank=True, null=True)
    gallery_images = models.JSONField(default=list, blank=True)  # NEW: URLs for additional images
    amenities = models.JSONField(default=list, blank=True)  # NEW: ['WiFi', 'Parking', 'Outdoor Seating', 'Live Music']
    phone_number = models.CharField(
        max_length=20,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$', 'Enter a valid phone number.')]
    )
    email = models.EmailField()
    website = models.URLField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=RESTAURANT_STATUS, default='pending')
    is_featured = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    reservation_enabled = models.BooleanField(
        default=False,
        help_text="Enable table reservations for this restaurant"
    )
    overall_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_reviews = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # RESERVATION-SPECIFIC SETTINGS (NEW)
    reservation_lead_time_hours = models.IntegerField(default=2)
    reservation_max_days_ahead = models.IntegerField(default=30)
    max_party_size = models.IntegerField(default=20)
    min_party_size = models.IntegerField(default=1)
    reservation_duration_options = models.JSONField(
        default=list,
        help_text="Available duration options in minutes, e.g., [60, 90, 120]"
    )
    requires_confirmation = models.BooleanField(default=False)
    cancellation_policy_hours = models.IntegerField(default=24)
    deposit_required = models.BooleanField(default=False)
    deposit_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    time_slot_interval = models.IntegerField(default=15, help_text="Time slot interval in minutes")
    allow_same_day_reservations = models.BooleanField(default=True)
    require_phone_verification = models.BooleanField(default=False)
    auto_assign_tables = models.BooleanField(default=True)
    reservation_notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'restaurants'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'is_featured']),
            models.Index(fields=['overall_rating', 'total_reviews']),
            models.Index(fields=['created_at']),
            models.Index(fields=['reservation_enabled', 'status']),
        ]

    def __str__(self):
        return self.name

    def update_rating(self, new_rating):
        """Update overall rating when new review is added"""
        from decimal import Decimal
        
        # Get all approved reviews
        approved_reviews = self.reviews.filter(status='approved')
        total_reviews = approved_reviews.count()
        
        if total_reviews > 0:
            # Calculate new average
            total_rating = sum([float(review.overall_rating) for review in approved_reviews])
            self.overall_rating = Decimal(str(round(total_rating / total_reviews, 2)))
        else:
            self.overall_rating = Decimal('0.00')
        
        self.total_reviews = total_reviews
        self.save()

    def get_rating_breakdown(self):
        """Get rating breakdown for the restaurant"""
        from django.db.models import Count, Avg
        
        breakdown = self.reviews.filter(status='approved').aggregate(
            total_reviews=Count('review_id'),
            average_rating=Avg('overall_rating'),
            average_food_quality=Avg('food_quality'),
            average_service_quality=Avg('service_quality'),
            average_ambiance=Avg('ambiance'),
            average_value=Avg('value_for_money')
        )
        
        # Get rating distribution
        distribution = self.reviews.filter(status='approved').values('overall_rating').annotate(
            count=Count('review_id')
        ).order_by('overall_rating')
        
        return {
            'breakdown': breakdown,
            'distribution': list(distribution)
        }
    
    def update_rating_stats(self):
        """Update rating statistics for the restaurant"""
        from django.db.models import Avg, Count
        from decimal import Decimal
        from ..models import RatingAggregate
        
        # Calculate averages
        aggregates = self.ratings.aggregate(
            total_ratings=Count('rating_id'),
            avg_overall=Avg('overall_rating'),
            avg_food=Avg('food_quality'),
            avg_service=Avg('service_quality'),
            avg_ambiance=Avg('ambiance'),
            avg_value=Avg('value_for_money')
        )
        
        # Get rating distribution
        distribution = self.ratings.values('overall_rating').annotate(
            count=Count('rating_id')
        ).order_by('overall_rating')
        
        rating_distribution = {str(i): 0 for i in range(1, 6)}
        for item in distribution:
            rating_distribution[str(int(item['overall_rating']))] = item['count']
        
        # Get tag frequencies
        all_tags = []
        for rating in self.ratings.filter(tags__len__gt=0):
            all_tags.extend(rating.tags)
        
        tag_frequencies = {}
        for tag in all_tags:
            tag_frequencies[tag] = tag_frequencies.get(tag, 0) + 1
        
        # Create or update aggregate
        aggregate, created = RatingAggregate.objects.get_or_create(
            content_type='restaurant',
            object_id=self.restaurant_id
        )
        
        aggregate.total_ratings = aggregates['total_ratings'] or 0
        aggregate.average_rating = Decimal(str(aggregates['avg_overall'] or 0))
        aggregate.average_food_quality = Decimal(str(aggregates['avg_food'] or 0))
        aggregate.average_service_quality = Decimal(str(aggregates['avg_service'] or 0))
        aggregate.average_ambiance = Decimal(str(aggregates['avg_ambiance'] or 0))
        aggregate.average_value = Decimal(str(aggregates['avg_value'] or 0))
        aggregate.rating_distribution = rating_distribution
        aggregate.tag_frequencies = tag_frequencies
        aggregate.save()
        
        # Update main restaurant rating
        self.overall_rating = aggregate.average_rating
        self.total_reviews = aggregate.total_ratings  # Using total_ratings as review count
        self.save()

    def get_rating_stats(self):
        """Get comprehensive rating statistics"""
        from ..models import RatingAggregate
        try:
            aggregate = RatingAggregate.objects.get(
                content_type='restaurant',
                object_id=self.restaurant_id
            )
            return {
                'total_ratings': aggregate.total_ratings,
                'average_rating': float(aggregate.average_rating),
                'rating_distribution': aggregate.rating_distribution,
                'tag_frequencies': aggregate.tag_frequencies,
                'detailed_averages': {
                    'food_quality': float(aggregate.average_food_quality),
                    'service_quality': float(aggregate.average_service_quality),
                    'ambiance': float(aggregate.average_ambiance),
                    'value_for_money': float(aggregate.average_value)
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
        """Get a specific user's rating for this restaurant"""
        from ..models import RestaurantRating
        if hasattr(user, 'customer_profile'):
            try:
                rating = RestaurantRating.objects.get(
                    restaurant=self,
                    customer=user.customer_profile
                )
                return rating
            except RestaurantRating.DoesNotExist:
                return None
        return None
    
    def get_featured_categories(self):
        """Get featured categories for homepage preview"""
        return self.menu_categories.filter(is_featured=True).order_by('display_order')[:5]

    def get_featured_items(self):
        """Get featured menu items for homepage"""
        from .menu_models import MenuItem
        return MenuItem.objects.filter(
            category__restaurant=self,
            is_featured=True,
            is_available=True
        ).order_by('-popularity_score')[:10]

    def add_gallery_image(self, image_url):
        """Add image to gallery"""
        if image_url not in self.gallery_images:
            self.gallery_images.append(image_url)
            self.save()

    def remove_gallery_image(self, image_url):
        """Remove image from gallery"""
        if image_url in self.gallery_images:
            self.gallery_images.remove(image_url)
            self.save()

    def get_available_durations(self):
        """Get available duration options or default"""
        return self.reservation_duration_options or [60, 90, 120]

    def can_accept_reservation(self, party_size, reservation_datetime):
        """Check if restaurant can accept this reservation based on its rules"""
        from django.utils import timezone
        
        if not self.reservation_enabled:
            return False, "Reservations are not enabled for this restaurant"
        
        if party_size > self.max_party_size:
            return False, f"Maximum party size is {self.max_party_size}"
        
        if party_size < self.min_party_size:
            return False, f"Minimum party size is {self.min_party_size}"
        
        # Check lead time
        if not self.allow_same_day_reservations:
            min_date = timezone.now().date() + timedelta(days=1)
            if reservation_datetime.date() < min_date:
                return False, "Same-day reservations are not allowed"
        
        min_datetime = timezone.now() + timedelta(hours=self.reservation_lead_time_hours)
        if reservation_datetime < min_datetime:
            return False, f"Reservations must be made at least {self.reservation_lead_time_hours} hours in advance"
        
        # Check max days ahead
        max_date = timezone.now().date() + timedelta(days=self.reservation_max_days_ahead)
        if reservation_datetime.date() > max_date:
            return False, f"Reservations can only be made up to {self.reservation_max_days_ahead} days in advance"
        
        return True, "Valid reservation"

class Branch(models.Model):
    branch_id = models.AutoField(primary_key=True)
    restaurant = models.ForeignKey(
        'api.Restaurant', 
        on_delete=models.CASCADE, 
        related_name='branches'
    )
    address = models.OneToOneField('api.Address', on_delete=models.CASCADE)
    phone_number = models.CharField(
        max_length=20,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$', 'Enter a valid phone number.')],
        blank=True,
        null=True
    )
    operating_hours = models.JSONField(default=dict)  # {'monday': {'open': '09:00', 'close': '22:00'}, ...}
    is_active = models.BooleanField(default=True)
    is_main_branch = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'branches'
        ordering = ['restaurant', '-is_main_branch']
        verbose_name_plural = 'branches'

    def __str__(self):
        return f"{self.restaurant.name} - {self.address.city}"

    def is_open_now(self):
        """Check if branch is currently open"""
        now = timezone.now()
        current_day = now.strftime('%A').lower()
        current_time = now.strftime('%H:%M')
        
        hours = self.operating_hours.get(current_day, {})
        return hours.get('open', '00:00') <= current_time <= hours.get('close', '23:59')

class Address(models.Model):
    address_id = models.AutoField(primary_key=True)
    street_address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='USA')
    latitude = models.DecimalField(max_digits=10, decimal_places=8, blank=True, null=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'addresses'
        indexes = [
            models.Index(fields=['city', 'state']),
            models.Index(fields=['postal_code']),
        ]

    def __str__(self):
        return f"{self.street_address}, {self.city}, {self.country}"