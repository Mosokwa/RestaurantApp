from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from ..models import Address, Restaurant, Branch, MenuItem

class RestaurantSerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    owner_email = serializers.CharField(source='owner.email', read_only=True)
    cuisine_names = serializers.SerializerMethodField()
    branch_count = serializers.SerializerMethodField()
    distance_km = serializers.SerializerMethodField()
    is_open = serializers.SerializerMethodField()
    rating_stats = serializers.SerializerMethodField()
    user_rating = serializers.SerializerMethodField()
    
    class Meta:
        model = Restaurant
        fields = [
            'restaurant_id', 'owner', 'owner_username', 'owner_email', 'name', 
            'description', 'cuisines', 'cuisine_names', 'logo', 'banner_image',
            'phone_number', 'email', 'website', 'status', 'is_featured', 
            'is_verified', 'overall_rating', 'total_reviews', 'branch_count',
            'distance_km', 'is_open', 'created_at', 'updated_at','rating_stats', 'user_rating'
        ]
        read_only_fields = ['restaurant_id', 'overall_rating', 'total_reviews', 'created_at', 'updated_at']
    
    def get_cuisine_names(self, obj):
        return [cuisine.name for cuisine in obj.cuisines.all()]
    
    def get_branch_count(self, obj):
        return obj.branches.count()
    
    def get_rating_stats(self, obj):
        return obj.get_rating_stats()
    
    def get_user_rating(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            user_rating = obj.get_user_rating(request.user)
            return user_rating.overall_rating if user_rating else None
        return None
    
    def get_distance_km(self, obj):
        """Calculate distance if user coordinates are provided in context"""
        request = self.context.get('request')
        if request and hasattr(request, 'query_params'):
            lat = request.query_params.get('lat')
            lng = request.query_params.get('lng')
            
            if lat and lng:
                try:
                    from ..search_utils import SearchUtils
                    distances = []
                    for branch in obj.branches.all():
                        if branch.address.latitude and branch.address.longitude:
                            dist = SearchUtils.calculate_distance(
                                float(lat), float(lng),
                                float(branch.address.latitude), float(branch.address.longitude)
                            )
                            if dist is not None:
                                distances.append(dist)
                    
                    if distances:
                        return round(min(distances), 2)
                except (ValueError, TypeError):
                    pass
        
        # Also check context for coordinates passed from views
        user_lat = self.context.get('user_latitude')
        user_lng = self.context.get('user_longitude')
        
        if user_lat is not None and user_lng is not None:
            try:
                from ..search_utils import SearchUtils
                distances = []
                for branch in obj.branches.all():
                    if branch.address.latitude and branch.address.longitude:
                        dist = SearchUtils.calculate_distance(
                            user_lat, user_lng,
                            float(branch.address.latitude), float(branch.address.longitude)
                        )
                        if dist is not None:
                            distances.append(dist)
                
                if distances:
                    return round(min(distances), 2)
            except (ValueError, TypeError):
                pass
        
        return None
    
    def get_is_open(self, obj):
        """Check if any branch is currently open"""
        return any(branch.is_open_now() for branch in obj.branches.all() if branch.is_active)
    
class BranchSerializer(serializers.ModelSerializer):
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    full_address = serializers.SerializerMethodField()
    is_open = serializers.SerializerMethodField()
    
    class Meta:
        model = Branch
        fields = [
            'branch_id', 'restaurant', 'restaurant_name', 'address', 'full_address',
            'phone_number', 'operating_hours', 'is_active', 'is_main_branch',
            'is_open', 'created_at', 'updated_at'
        ]
        read_only_fields = ['branch_id', 'created_at', 'updated_at']
    
    def get_full_address(self, obj):
        return str(obj.address)
    
    def get_is_open(self, obj):
        return obj.is_open_now()
    
class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            'address_id', 'street_address', 'city', 'state', 
            'postal_code', 'country', 'latitude', 'longitude', 'created_at'
        ]
        read_only_fields = ['address_id', 'created_at']
    
class RestaurantCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurant
        fields = [
            'restaurant_id','name', 'description', 'cuisines', 'phone_number', 'email',
            'website', 'status', 'is_featured'
        ]
        read_only_fields = ('restaurant_id',)
        extra_kwargs = {
            'cuisines': {'required': False}
        }
    
    def create(self, validated_data):
        # Set the owner from the request user
        cuisines_data = validated_data.pop('cuisines', [])
        request_user = self.context['request'].user

        if request_user.user_type != 'owner':
            raise ValidationError("Only restaurant owners can create restaurants")
        validated_data['owner'] = request_user
        restaurant = Restaurant.objects.create(**validated_data)

        if cuisines_data:
            restaurant.cuisines.set(cuisines_data)

        return restaurant

class BranchCreateSerializer(serializers.ModelSerializer):
    address_data = AddressSerializer(write_only=True)
    
    class Meta:
        model = Branch
        fields = [
            'restaurant', 'address_data', 'phone_number', 'operating_hours',
            'is_active', 'is_main_branch'
        ]
    

    def create(self, validated_data):
        address_data = validated_data.pop('address_data')
        address = Address.objects.create(**address_data)
        
        
        # Get restaurant from context
        restaurant = validated_data.pop('restaurant')
        if not restaurant:
            raise ValidationError("Restaurant is required")
        
        return Branch.objects.create(
            restaurant=restaurant,
            address=address,
            **validated_data
        )
    
    def update(self, instance, validated_data):
        address_data = validated_data.pop('address_data', None)
        if address_data:
            address_serializer = AddressSerializer(instance.address, data=address_data, partial=True)
            address_serializer.is_valid(raise_exception=True)
            address_serializer.save()
        
        return super().update(instance, validated_data)
    
class RestaurantPopularitySerializer(serializers.ModelSerializer):
    """Serializer for restaurant popularity and recommendation data"""
    popular_items = serializers.SerializerMethodField()
    trending_items = serializers.SerializerMethodField()
    popularity_metrics = serializers.SerializerMethodField()
    
    class Meta:
        model = Restaurant
        fields = [
            'restaurant_id', 'name', 'overall_rating', 'total_reviews',
            'popular_items', 'trending_items', 'popularity_metrics'
        ]
        read_only_fields = ['restaurant_id', 'name', 'overall_rating', 'total_reviews']
    
    def get_popular_items(self, obj):
        """Get popular items for this restaurant"""
        popular_items = MenuItem.objects.filter(
            category__restaurant=obj,
            is_available=True
        ).order_by('-popularity_score')[:8]
        
        from .menuSerializers import EnhancedMenuItemSerializer
        return EnhancedMenuItemSerializer(
            popular_items, 
            many=True,
            context=self.context
        ).data
    
    def get_trending_items(self, obj):
        """Get trending items for this restaurant"""
        from datetime import timedelta
        from django.utils import timezone
        from django.db.models import Count
        
        # Items with significant growth in last 7 days
        seven_days_ago = timezone.now() - timedelta(days=7)
        
        trending_items = MenuItem.objects.filter(
            category__restaurant=obj,
            order_items__order__order_placed_at__gte=seven_days_ago,
            is_available=True
        ).annotate(
            recent_orders=Count('order_items')
        ).order_by('-recent_orders')[:6]
        
        from .menuSerializers import MenuItemSerializer
        return MenuItemSerializer(
            trending_items, 
            many=True,
            context=self.context
        ).data
    
    def get_popularity_metrics(self, obj):
        """Get restaurant-level popularity metrics"""
        total_items = MenuItem.objects.filter(category__restaurant=obj).count()
        available_items = MenuItem.objects.filter(category__restaurant=obj, is_available=True).count()
        featured_items = MenuItem.objects.filter(category__restaurant=obj, is_featured=True).count()
        
        # Average popularity score
        avg_popularity = MenuItem.objects.filter(
            category__restaurant=obj
        ).aggregate(avg_popularity=serializers.Avg('popularity_score'))['avg_popularity'] or 0
        
        return {
            'total_menu_items': total_items,
            'available_items': available_items,
            'featured_items': featured_items,
            'availability_rate': round((available_items / total_items * 100), 1) if total_items > 0 else 0,
            'average_popularity_score': round(avg_popularity, 1),
            'popularity_tier': self._get_popularity_tier(avg_popularity)
        }
    
    def _get_popularity_tier(self, score):
        """Convert popularity score to tier"""
        if score >= 500:
            return 'very_high'
        elif score >= 300:
            return 'high'
        elif score >= 150:
            return 'medium'
        elif score >= 50:
            return 'low'
        else:
            return 'very_low'

class RestaurantPopSearchSerializer(serializers.ModelSerializer):
    """Enhanced serializer for restaurant search with popularity data"""
    cuisine_names = serializers.SerializerMethodField()
    branch_count = serializers.SerializerMethodField()
    distance_km = serializers.SerializerMethodField()
    is_open = serializers.SerializerMethodField()
    popularity_score = serializers.SerializerMethodField()
    recommended_items = serializers.SerializerMethodField()
    
    class Meta:
        model = Restaurant
        fields = [
            'restaurant_id', 'name', 'description', 'cuisine_names', 'logo',
            'overall_rating', 'total_reviews', 'branch_count', 'distance_km',
            'is_open', 'popularity_score', 'recommended_items', 'is_featured',
            'is_verified', 'created_at'
        ]
        read_only_fields = ['restaurant_id', 'created_at']
    
    def get_cuisine_names(self, obj):
        return [cuisine.name for cuisine in obj.cuisines.all()]
    
    def get_branch_count(self, obj):
        return obj.branches.count()
    
    def get_distance_km(self, obj):
        """Calculate distance if coordinates provided"""
        request = self.context.get('request')
        if request and hasattr(request, 'query_params'):
            lat = request.query_params.get('lat')
            lng = request.query_params.get('lng')
            
            if lat and lng:
                try:
                    from ..search_utils import SearchUtils
                    distances = []
                    for branch in obj.branches.all():
                        if branch.address.latitude and branch.address.longitude:
                            dist = SearchUtils.calculate_distance(
                                float(lat), float(lng),
                                float(branch.address.latitude), float(branch.address.longitude)
                            )
                            if dist is not None:
                                distances.append(dist)
                    
                    if distances:
                        return round(min(distances), 2)
                except (ValueError, TypeError):
                    pass
        return None
    
    def get_is_open(self, obj):
        """Check if any branch is currently open"""
        return any(branch.is_open_now() for branch in obj.branches.all() if branch.is_active)
    
    def get_popularity_score(self, obj):
        """Calculate restaurant popularity score based on menu items"""
        from django.db.models import Avg
        result = MenuItem.objects.filter(
            category__restaurant=obj
        ).aggregate(avg_popularity=Avg('popularity_score'))
        
        return round(result['avg_popularity'] or 0, 1)
    
    def get_recommended_items(self, obj):
        """Get a few recommended items from this restaurant"""
        recommended_items = MenuItem.objects.filter(
            category__restaurant=obj,
            is_available=True,
            popularity_score__gte=100  # Only reasonably popular items
        ).order_by('-popularity_score')[:3]
        
        return [
            {
                'item_id': item.item_id,
                'name': item.name,
                'price': item.price,
                'image': item.image.url if item.image else None
            }
            for item in recommended_items
        ]