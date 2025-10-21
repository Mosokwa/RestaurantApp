from rest_framework import serializers
from ..models import Restaurant, MenuItem

class RestaurantSearchSerializer(serializers.ModelSerializer):
    """Enhanced serializer with new location features"""
    distance_km = serializers.FloatField(read_only=True)
    cuisine_names = serializers.SerializerMethodField()
    branch_count = serializers.SerializerMethodField()
    estimated_delivery_time = serializers.SerializerMethodField()
    is_open = serializers.SerializerMethodField()
    has_open_branch = serializers.SerializerMethodField()
    open_branches_count = serializers.IntegerField(read_only=True)
    location_priority = serializers.SerializerMethodField()
    
    class Meta:
        model = Restaurant
        fields = [
            'restaurant_id', 'name', 'description', 'cuisine_names', 'logo',
            'phone_number', 'email', 'overall_rating', 'total_reviews',
            'distance_km', 'branch_count', 'estimated_delivery_time',
            'is_open', 'has_open_branch', 'open_branches_count', 
            'location_priority', 'is_featured', 'is_verified', 'created_at'
        ]
    
    def get_cuisine_names(self, obj):
        return [cuisine.name for cuisine in obj.cuisines.all()]
    
    def get_branch_count(self, obj):
        return obj.branches.count()
    
    def get_estimated_delivery_time(self, obj):
        # Enhanced delivery time estimation based on distance
        distance = getattr(obj, 'distance_km', None)
        if distance:
            # Base prep time + travel time (assuming 30km/h average speed)
            base_prep_time = 25  # minutes
            travel_time = (distance / 30) * 60  # Convert to minutes
            return round(base_prep_time + travel_time)
        return 30  # Default fallback
    
    def get_is_open(self, obj):
        return any(branch.is_open_now() for branch in obj.branches.all() if branch.is_active)
    
    def get_has_open_branch(self, obj):
        return getattr(obj, 'has_open_branch', False)
    
    def get_location_priority(self, obj):
        """Calculate location priority for UI highlighting"""
        distance = getattr(obj, 'distance_km', None)
        if distance is None:
            return 'unknown'
        
        if distance <= 2:
            return 'very_near'
        elif distance <= 5:
            return 'near'
        elif distance <= 10:
            return 'moderate'
        elif distance <= 20:
            return 'far'
        else:
            return 'very_far'

class MenuItemSearchSerializer(serializers.ModelSerializer):
    """Serializer for menu item search results"""
    restaurant_name = serializers.CharField(source='category.restaurant.name')
    restaurant_id = serializers.IntegerField(source='category.restaurant.restaurant_id')
    restaurant_rating = serializers.DecimalField(
        source='category.restaurant.overall_rating', 
        max_digits=3, 
        decimal_places=2
    )
    category_name = serializers.CharField(source='category.name')
    distance_km = serializers.FloatField(read_only=True)
    
    class Meta:
        model = MenuItem
        fields = [
            'item_id', 'name', 'description', 'price', 'image',
            'restaurant_name', 'restaurant_id', 'restaurant_rating',
            'category_name', 'distance_km', 'is_vegetarian', 'is_vegan',
            'is_gluten_free', 'is_spicy', 'calories', 'preparation_time'
        ]

class SearchSuggestionSerializer(serializers.Serializer):
    """Serializer for search suggestions"""
    type = serializers.CharField()  # 'restaurant', 'menu_item', 'cuisine'
    name = serializers.CharField()
    id = serializers.IntegerField(required=False)
    restaurant_name = serializers.CharField(required=False)
    cuisine_name = serializers.CharField(required=False)

class SearchFilterSerializer(serializers.Serializer):
    """Serializer for search filters"""
    query = serializers.CharField(required=False)
    latitude = serializers.FloatField(required=False)
    longitude = serializers.FloatField(required=False)
    radius_km = serializers.FloatField(default=10)
    cuisine = serializers.CharField(required=False)
    min_rating = serializers.FloatField(min_value=0, max_value=5, required=False)
    price_range = serializers.ChoiceField(
        choices=[('$', 'Budget'), ('$$', 'Moderate'), ('$$$', 'Expensive'), ('$$$$', 'Premium')],
        required=False
    )
    dietary_preferences = serializers.MultipleChoiceField(
        choices=[
            ('vegetarian', 'Vegetarian'),
            ('vegan', 'Vegan'),
            ('gluten_free', 'Gluten Free'),
            ('spicy', 'Spicy')
        ],
        required=False
    )
    delivery_time_max = serializers.IntegerField(min_value=0, required=False)
    is_open_now = serializers.BooleanField(required=False)
    sort_by = serializers.ChoiceField(
        choices=[
            ('relevance', 'Relevance'),
            ('distance', 'Distance'),
            ('rating', 'Rating'),
            ('delivery_time', 'Delivery Time'),
            ('price_low', 'Price: Low to High'),
            ('price_high', 'Price: High to Low')
        ],
        default='relevance'
    )
    page = serializers.IntegerField(min_value=1, default=1)
    page_size = serializers.IntegerField(min_value=1, max_value=100, default=20)