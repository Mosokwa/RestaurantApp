from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

class OfferUsage(models.Model):
    """
    Track special offer usage by customers
    """
    usage_id = models.AutoField(primary_key=True)
    offer = models.ForeignKey(
        'api.SpecialOffer',
        on_delete=models.CASCADE,
        related_name='usages'
    )
    customer = models.ForeignKey(
        'api.Customer',
        on_delete=models.CASCADE,
        related_name='offer_usages'
    )
    order = models.ForeignKey(
        'api.Order',
        on_delete=models.CASCADE,
        related_name='offer_usages',
        null=True,
        blank=True
    )
    
    # Usage details
    discount_applied = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    original_order_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    final_order_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    
    # Metadata
    is_successful = models.BooleanField(default=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    redeemed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'offer_usages'
        ordering = ['-applied_at']
        indexes = [
            models.Index(fields=['offer', 'customer']),
            models.Index(fields=['customer', 'applied_at']),
            models.Index(fields=['offer', 'applied_at']),
        ]
        unique_together = ['offer', 'order']

    def __str__(self):
        return f"Offer usage by {self.customer.user.username}"

    def save(self, *args, **kwargs):
        if not self.pk and self.is_successful:
            self.offer.current_usage += 1
            self.offer.save(update_fields=['current_usage'])
        super().save(*args, **kwargs)

class RestaurantReview(models.Model):
    REVIEW_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('reported', 'Reported'),
    )
    
    review_id = models.AutoField(primary_key=True)
    restaurant = models.ForeignKey(
        'api.Restaurant',
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    customer = models.ForeignKey(
        'api.Customer',
        on_delete=models.CASCADE,
        related_name='restaurant_reviews'
    )
    order = models.ForeignKey(
        'api.Order',
        on_delete=models.CASCADE,
        related_name='reviews',
        null=True,
        blank=True
    )
    
    # Rating details
    overall_rating = models.DecimalField(
        max_digits=2, 
        decimal_places=1, 
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    food_quality = models.DecimalField(
        max_digits=2, 
        decimal_places=1, 
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True
    )
    service_quality = models.DecimalField(
        max_digits=2, 
        decimal_places=1, 
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True
    )
    ambiance = models.DecimalField(
        max_digits=2, 
        decimal_places=1, 
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True
    )
    value_for_money = models.DecimalField(
        max_digits=2, 
        decimal_places=1, 
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True
    )
    
    # Review content
    title = models.CharField(max_length=200)
    comment = models.TextField()
    photos = models.JSONField(default=list, blank=True)  # Store photo URLs
    video_url = models.URLField(blank=True, null=True)
    
    # Review metadata
    helpful_count = models.IntegerField(default=0)
    status = models.CharField(max_length=10, choices=REVIEW_STATUS_CHOICES, default='pending')
    is_verified_purchase = models.BooleanField(default=False)
    is_owner_response_enabled = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'restaurant_reviews'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['restaurant', 'status']),
            models.Index(fields=['customer', 'created_at']),
            models.Index(fields=['overall_rating']),
            models.Index(fields=['created_at']),
        ]
        unique_together = ['restaurant', 'customer', 'order']

    def __str__(self):
        return f"Review for {self.restaurant.name} by {self.customer.user.username}"

    def save(self, *args, **kwargs):
        # Auto-approve reviews if restaurant has auto-approval enabled
        if self.status == 'pending' and hasattr(self.restaurant, 'review_settings'):
            if self.restaurant.review_settings.auto_approve_reviews:
                self.status = 'approved'
                self.approved_at = timezone.now()
        
        # Mark as verified if review is linked to an order
        if self.order and not self.is_verified_purchase:
            self.is_verified_purchase = True
            
        super().save(*args, **kwargs)
        
        # Update restaurant rating
        if self.status == 'approved':
            self.restaurant.update_rating(float(self.overall_rating))

class DishReview(models.Model):
    REVIEW_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    
    dish_review_id = models.AutoField(primary_key=True)
    menu_item = models.ForeignKey(
        'api.MenuItem',
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    customer = models.ForeignKey(
        'api.Customer',
        on_delete=models.CASCADE,
        related_name='dish_reviews'
    )
    order = models.ForeignKey(
        'api.Order',
        on_delete=models.CASCADE,
        related_name='dish_reviews',
        null=True,
        blank=True
    )
    
    # Rating
    rating = models.DecimalField(
        max_digits=2, 
        decimal_places=1, 
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    
    # Review content
    comment = models.TextField()
    photos = models.JSONField(default=list, blank=True)
    
    # Additional metrics
    taste_rating = models.DecimalField(
        max_digits=2, 
        decimal_places=1, 
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True
    )
    portion_size_rating = models.DecimalField(
        max_digits=2, 
        decimal_places=1, 
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True
    )
    value_rating = models.DecimalField(
        max_digits=2, 
        decimal_places=1, 
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True
    )
    
    # Metadata
    helpful_count = models.IntegerField(default=0)
    status = models.CharField(max_length=10, choices=REVIEW_STATUS_CHOICES, default='pending')
    is_verified_purchase = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'dish_reviews'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['menu_item', 'status']),
            models.Index(fields=['customer', 'created_at']),
            models.Index(fields=['rating']),
        ]
        unique_together = ['menu_item', 'customer', 'order']

    def __str__(self):
        return f"Review for {self.menu_item.name} by {self.customer.user.username}"

class ReviewResponse(models.Model):
    response_id = models.AutoField(primary_key=True)
    review = models.OneToOneField(
        'api.RestaurantReview',
        on_delete=models.CASCADE,
        related_name='response'
    )
    responder = models.ForeignKey(
        'api.User',
        on_delete=models.CASCADE,
        related_name='review_responses'
    )
    
    # Response content
    comment = models.TextField()
    is_public = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'review_responses'
        ordering = ['-created_at']

    def __str__(self):
        return f"Response to review #{self.review.review_id} by {self.responder.username}"

class ReviewReport(models.Model):
    REPORT_REASON_CHOICES = (
        ('spam', 'Spam or misleading'),
        ('inappropriate', 'Inappropriate content'),
        ('fake', 'Fake review'),
        ('harassment', 'Harassment or bullying'),
        ('other', 'Other'),
    )
    
    REPORT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('under_review', 'Under Review'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    )
    
    report_id = models.AutoField(primary_key=True)
    review = models.ForeignKey(
        'api.RestaurantReview',
        on_delete=models.CASCADE,
        related_name='reports'
    )
    reporter = models.ForeignKey(
        'api.User',
        on_delete=models.CASCADE,
        related_name='review_reports'
    )
    
    # Report details
    reason = models.CharField(max_length=20, choices=REPORT_REASON_CHOICES)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=15, choices=REPORT_STATUS_CHOICES, default='pending')
    
    # Moderation
    moderator_notes = models.TextField(blank=True, null=True)
    resolved_by = models.ForeignKey(
        'api.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_reports'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'review_reports'
        ordering = ['-created_at']
        unique_together = ['review', 'reporter']

    def __str__(self):
        return f"Report on review #{self.review.review_id} by {self.reporter.username}"

class ReviewHelpfulVote(models.Model):
    vote_id = models.AutoField(primary_key=True)
    review = models.ForeignKey(
        'api.RestaurantReview',
        on_delete=models.CASCADE,
        related_name='helpful_votes'
    )
    customer = models.ForeignKey(
        'api.Customer',
        on_delete=models.CASCADE,
        related_name='review_votes'
    )
    is_helpful = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'review_helpful_votes'
        unique_together = ['review', 'customer']

    def __str__(self):
        return f"Vote on review #{self.review.review_id} by {self.customer.user.username}"

class RestaurantReviewSettings(models.Model):
    restaurant = models.OneToOneField(
        'api.Restaurant',
        on_delete=models.CASCADE,
        related_name='review_settings'
    )
    
    # Review settings
    auto_approve_reviews = models.BooleanField(default=True)
    allow_photo_reviews = models.BooleanField(default=True)
    allow_video_reviews = models.BooleanField(default=True)
    require_order_verification = models.BooleanField(default=True)
    min_order_amount_for_review = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00
    )
    
    # Notification settings
    notify_on_new_review = models.BooleanField(default=True)
    notify_on_review_report = models.BooleanField(default=True)
    
    # Response settings
    auto_response_enabled = models.BooleanField(default=False)
    auto_response_message = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'restaurant_review_settings'

    def __str__(self):
        return f"Review settings for {self.restaurant.name}"


from django.db.models.signals import post_save
from django.dispatch import receiver
# Signal to create review settings when restaurant is created
@receiver(post_save, sender='api.Restaurant')
def create_restaurant_review_settings(sender, instance, created, **kwargs):
    if created:
        RestaurantReviewSettings.objects.create(restaurant=instance)


class RestaurantRating(models.Model):
    """
    Standalone restaurant rating without requiring a full review
    """
    rating_id = models.AutoField(primary_key=True)
    restaurant = models.ForeignKey(
        'api.Restaurant',
        on_delete=models.CASCADE,
        related_name='ratings'
    )
    customer = models.ForeignKey(
        'api.Customer',
        on_delete=models.CASCADE,
        related_name='restaurant_ratings'
    )
    order = models.ForeignKey(
        'api.Order',
        on_delete=models.CASCADE,
        related_name='ratings',
        null=True,
        blank=True
    )
    
    # Core rating
    overall_rating = models.DecimalField(
        max_digits=2, 
        decimal_places=1, 
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    
    # Detailed rating categories (optional)
    food_quality = models.DecimalField(
        max_digits=2, 
        decimal_places=1, 
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True
    )
    service_quality = models.DecimalField(
        max_digits=2, 
        decimal_places=1, 
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True
    )
    ambiance = models.DecimalField(
        max_digits=2, 
        decimal_places=1, 
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True
    )
    value_for_money = models.DecimalField(
        max_digits=2, 
        decimal_places=1, 
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True
    )
    
    # Quick rating tags (for fast rating)
    tags = models.JSONField(default=list, blank=True)  # ['great_service', 'fast_delivery', etc.]
    
    # Metadata
    is_verified_purchase = models.BooleanField(default=False)
    is_quick_rating = models.BooleanField(default=False)  # Whether it's a quick rating without details
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'restaurant_ratings'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['restaurant', 'overall_rating']),
            models.Index(fields=['customer', 'created_at']),
            models.Index(fields=['overall_rating']),
        ]
        unique_together = ['restaurant', 'customer', 'order']

    def __str__(self):
        return f"Rating {self.overall_rating} for {self.restaurant.name} by {self.customer.user.username}"

    def save(self, *args, **kwargs):
        # Mark as verified if linked to an order
        if self.order and not self.is_verified_purchase:
            self.is_verified_purchase = True
            
        super().save(*args, **kwargs)
        
        # Update restaurant rating statistics
        self.restaurant.update_rating_stats()

class DishRating(models.Model):
    """
    Standalone dish rating without requiring a full review
    """
    dish_rating_id = models.AutoField(primary_key=True)
    menu_item = models.ForeignKey(
        'api.MenuItem',
        on_delete=models.CASCADE,
        related_name='ratings'
    )
    customer = models.ForeignKey(
        'api.Customer',
        on_delete=models.CASCADE,
        related_name='dish_ratings'
    )
    order = models.ForeignKey(
        'api.Order',
        on_delete=models.CASCADE,
        related_name='dish_ratings',
        null=True,
        blank=True
    )
    
    # Core rating
    rating = models.DecimalField(
        max_digits=2, 
        decimal_places=1, 
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    
    # Detailed ratings (optional)
    taste = models.DecimalField(
        max_digits=2, 
        decimal_places=1, 
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True
    )
    portion_size = models.DecimalField(
        max_digits=2, 
        decimal_places=1, 
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True
    )
    value = models.DecimalField(
        max_digits=2, 
        decimal_places=1, 
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True
    )
    
    # Quick tags
    tags = models.JSONField(default=list, blank=True)  # ['spicy', 'fresh', 'generous_portion', etc.]
    
    # Metadata
    is_verified_purchase = models.BooleanField(default=False)
    is_quick_rating = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'dish_ratings'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['menu_item', 'rating']),
            models.Index(fields=['customer', 'created_at']),
        ]
        unique_together = ['menu_item', 'customer', 'order']

    def __str__(self):
        return f"Rating {self.rating} for {self.menu_item.name} by {self.customer.user.username}"

    def save(self, *args, **kwargs):
        if self.order and not self.is_verified_purchase:
            self.is_verified_purchase = True
            
        super().save(*args, **kwargs)
        
        # Update menu item rating statistics
        self.menu_item.update_rating_stats()

class RatingAggregate(models.Model):
    """
    Pre-calculated rating aggregates for better performance
    """
    aggregate_id = models.AutoField(primary_key=True)
    content_type = models.CharField(max_length=20)  # 'restaurant' or 'menu_item'
    object_id = models.IntegerField()  # ID of the restaurant or menu item
    
    # Aggregate statistics
    total_ratings = models.IntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    rating_distribution = models.JSONField(default=dict)  # {1: 5, 2: 3, 3: 10, 4: 20, 5: 15}
    
    # Detailed aggregates
    average_food_quality = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    average_service_quality = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    average_ambiance = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    average_value = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    
    # Tag frequencies
    tag_frequencies = models.JSONField(default=dict)
    
    last_calculated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'rating_aggregates'
        unique_together = ['content_type', 'object_id']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        return f"Aggregate for {self.content_type} #{self.object_id}"


# Common rating tags
RESTAURANT_RATING_TAGS = [
    'great_service', 'fast_delivery', 'friendly_staff', 'clean_environment',
    'good_ambiance', 'good_value', 'quick_preparation', 'accurate_order',
    'fresh_ingredients', 'generous_portions', 'comfortable_seating',
    'good_presentation', 'varied_menu', 'healthy_options'
]

DISH_RATING_TAGS = [
    'delicious', 'spicy', 'fresh', 'flavorful', 'tender', 'crispy',
    'creamy', 'savory', 'sweet', 'aromatic', 'generous_portion',
    'well_presented', 'hot', 'authentic', 'unique', 'comfort_food'
]