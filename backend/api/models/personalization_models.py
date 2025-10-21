from django.db import models
from django.utils import timezone


class UserBehavior(models.Model):
    """
    Track user interactions with restaurants and menu items
    """
    BEHAVIOR_TYPES = (
        ('view', 'View'),
        ('order', 'Order'),
        ('favorite', 'Favorite'),
        ('rating', 'Rating'),
        ('search', 'Search'),
    )
    
    behavior_id = models.AutoField(primary_key=True)
    user = models.ForeignKey('api.User', on_delete=models.CASCADE, related_name='behaviors')
    restaurant = models.ForeignKey('api.Restaurant', on_delete=models.CASCADE, null=True, blank=True)
    menu_item = models.ForeignKey('api.MenuItem', on_delete=models.CASCADE, null=True, blank=True)
    behavior_type = models.CharField(max_length=20, choices=BEHAVIOR_TYPES)
    value = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # For ratings, order value, etc.
    metadata = models.JSONField(default=dict, blank=True)  # Additional context like location, time, etc.
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_behaviors'
        indexes = [
            models.Index(fields=['user', 'behavior_type']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['behavior_type', 'created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_behavior_type_display()} - {self.created_at}"
    


class UserPreference(models.Model):
    """
    Store calculated user preferences for cuisines, price ranges, etc.
    """
    preference_id = models.AutoField(primary_key=True)
    user = models.OneToOneField('api.User', on_delete=models.CASCADE, related_name='preferences')
    
    # Cuisine preferences (weighted scores)
    cuisine_scores = models.JSONField(default=dict, blank=True)  # {'italian': 0.8, 'mexican': 0.6}
    
    # Dietary preferences
    dietary_weights = models.JSONField(default=dict, blank=True)  # {'vegetarian': 0.9, 'vegan': 0.3}
    
    # Price range preferences
    price_preferences = models.JSONField(default=dict, blank=True)  # {'min': 10, 'max': 50, 'preferred': 25}
    
    # Location preferences
    preferred_locations = models.JSONField(default=list, blank=True)  # ['downtown', 'midtown']
    
    # Restaurant type preferences
    restaurant_type_scores = models.JSONField(default=dict, blank=True)  # {'fine_dining': 0.7, 'fast_food': 0.2}
    
    # Behavioral metrics
    avg_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    order_frequency_days = models.IntegerField(default=0)  # Average days between orders
    preferred_order_times = models.JSONField(default=dict, blank=True)  # {'lunch': 0.6, 'dinner': 0.8}
    
    last_calculated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_preferences'
    
    def __str__(self):
        return f"Preferences - {self.user.username}"

class Recommendation(models.Model):
    """
    Store generated recommendations for users
    """
    RECOMMENDATION_TYPES = (
        ('personalized', 'Personalized'),
        ('trending', 'Trending'),
        ('similar', 'Similar Items'),
        ('collaborative', 'Collaborative Filtering'),
        ('seasonal', 'Seasonal'),
    )
    
    recommendation_id = models.AutoField(primary_key=True)
    user = models.ForeignKey('api.User', on_delete=models.CASCADE, related_name='recommendations')
    recommendation_type = models.CharField(max_length=20, choices=RECOMMENDATION_TYPES)
    
    # Recommended items
    recommended_restaurants = models.ManyToManyField('api.Restaurant', blank=True)
    recommended_menu_items = models.ManyToManyField('api.MenuItem', blank=True)
    
    # Scores and metadata
    scores = models.JSONField(default=dict, blank=True)  # Item scores and reasoning
    algorithm_metadata = models.JSONField(default=dict, blank=True)  # Algorithm parameters and version
    
    # Expiration and freshness
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField()
    generated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'recommendations'
        indexes = [
            models.Index(fields=['user', 'recommendation_type']),
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['expires_at']),
        ]
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_recommendation_type_display()} - {self.generated_at}"
    
    def is_expired(self):
        return timezone.now() > self.expires_at

class SimilarityMatrix(models.Model):
    """
    Store precomputed similarity scores between items
    """
    matrix_id = models.AutoField(primary_key=True)
    matrix_type = models.CharField(max_length=50)  # 'menu_items', 'restaurants', 'cuisines'
    item_a_id = models.IntegerField()  # Generic ID reference
    item_b_id = models.IntegerField()  # Generic ID reference
    similarity_score = models.DecimalField(max_digits=5, decimal_places=4)
    calculation_method = models.CharField(max_length=100)
    metadata = models.JSONField(default=dict, blank=True)
    calculated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'similarity_matrix'
        unique_together = ['matrix_type', 'item_a_id', 'item_b_id']
        indexes = [
            models.Index(fields=['matrix_type', 'item_a_id']),
            models.Index(fields=['matrix_type', 'item_b_id']),
        ]
    
    def __str__(self):
        return f"{self.matrix_type}: {self.item_a_id} ~ {self.item_b_id} = {self.similarity_score}"