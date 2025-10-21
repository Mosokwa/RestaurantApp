from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from ..models import Cuisine, MenuCategory, MenuItem, ItemModifierGroup, ItemModifier, MenuItemModifier, SpecialOffer, PopularitySnapshot, ItemAssociation

class CuisineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cuisine
        fields = ['cuisine_id', 'name', 'description', 'is_active', 'created_at']
        read_only_fields = ['cuisine_id', 'created_at']

class ItemModifierSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemModifier
        fields = [
            'item_modifier_id', 'modifier_group', 'name', 'description',
            'price_modifier', 'is_available', 'display_order', 'created_at'
        ]
        read_only_fields = ['item_modifier_id', 'created_at']

class ItemModifierGroupSerializer(serializers.ModelSerializer):
    modifiers = ItemModifierSerializer(many=True, read_only=True)
    
    class Meta:
        model = ItemModifierGroup
        fields = [
            'modifier_id', 'name', 'description', 'is_required',
            'min_selections', 'max_selections', 'modifiers', 'created_at'
        ]
        read_only_fields = ['modifier_id', 'created_at']

class MenuItemModifierSerializer(serializers.ModelSerializer):
    modifier_group_name = serializers.CharField(source='modifier_group.name', read_only=True)
    
    class Meta:
        model = MenuItemModifier
        fields = ['menu_item', 'modifier_group', 'modifier_group_name', 'created_at']
        read_only_fields = ['created_at']

class MenuItemSerializer(serializers.ModelSerializer):
    """Enhanced serializer with popularity and recommendation data"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    restaurant_name = serializers.CharField(source='category.restaurant.name', read_only=True)
    restaurant_id = serializers.IntegerField(source='category.restaurant.restaurant_id', read_only=True)
    modifier_groups = serializers.SerializerMethodField()
    dietary_info = serializers.SerializerMethodField()
    rating_stats = serializers.SerializerMethodField()
    user_rating = serializers.SerializerMethodField()
    
    # ========== NEW POPULARITY FIELDS ==========
    popularity_metrics = serializers.SerializerMethodField()
    restaurant_rank = serializers.SerializerMethodField()
    trend_data = serializers.SerializerMethodField()
    frequently_bought_together = serializers.SerializerMethodField()
    # ========== END NEW POPULARITY FIELDS ==========
    
    class Meta:
        model = MenuItem
        fields = [
            'item_id', 'category', 'category_name', 'restaurant_name', 'restaurant_id', 'name',
            'description', 'price', 'item_type', 'image', 'is_vegetarian',
            'is_vegan', 'is_gluten_free', 'is_spicy', 'calories', 'preparation_time',
            'is_available', 'display_order', 'modifier_groups', 'dietary_info',
            'created_at', 'updated_at', 'rating_stats', 'user_rating',
            # New popularity fields
            'popularity_metrics', 'restaurant_rank', 'trend_data', 'frequently_bought_together'
        ]
        read_only_fields = ['item_id', 'created_at', 'updated_at']
    
    def get_modifier_groups(self, obj):
        modifier_groups = obj.menuitemmodifier_set.select_related('modifier_group').prefetch_related('modifier_group__modifiers')
        return MenuItemModifierSerializer(modifier_groups, many=True).data
    
    def get_dietary_info(self, obj):
        return {
            'vegetarian': obj.is_vegetarian,
            'vegan': obj.is_vegan,
            'gluten_free': obj.is_gluten_free,
            'spicy': obj.is_spicy
        }
    
    def get_rating_stats(self, obj):
        return obj.get_rating_stats()
    
    def get_user_rating(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            user_rating = obj.get_user_rating(request.user)
            return user_rating.rating if user_rating else None
        return None
    
    # ========== NEW POPULARITY METHODS ==========
    def get_popularity_metrics(self, obj):
        """Get comprehensive popularity metrics"""
        return {
            'popularity_score': obj.popularity_score,
            'order_count': obj.order_count,
            'last_ordered': obj.last_ordered,
            'seasonal_boost': obj.seasonal_boost,
            'is_featured': obj.is_featured,
            'preparation_time': obj.preparation_time
        }
    
    def get_restaurant_rank(self, obj):
        """Get item's rank within its restaurant"""
        try:
            restaurant_items = MenuItem.objects.filter(
                category__restaurant=obj.category.restaurant
            ).order_by('-popularity_score')
            
            rank = list(restaurant_items).index(obj) + 1
            total_items = restaurant_items.count()
            
            return {
                'rank': rank,
                'total_items': total_items,
                'percentile': round((1 - (rank / total_items)) * 100, 1) if total_items > 0 else 0
            }
        except (ValueError, IndexError):
            return {
                'rank': None,
                'total_items': 0,
                'percentile': 0
            }
    
    def get_trend_data(self, obj):
        """Get trend data from popularity snapshots"""
        from django.utils import timezone
        from datetime import timedelta
        
        # Get snapshots from last 30 days
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        snapshots = PopularitySnapshot.objects.filter(
            menu_item=obj,
            date_recorded__gte=thirty_days_ago
        ).order_by('date_recorded')
        
        if snapshots.count() < 2:
            return {
                'trend': 'stable',
                'growth_rate': 0,
                'data_points': snapshots.count()
            }
        
        # Calculate trend
        first_score = snapshots.first().score
        last_score = snapshots.last().score
        growth_rate = ((last_score - first_score) / first_score * 100) if first_score > 0 else 0
        
        if growth_rate > 10:
            trend = 'rising'
        elif growth_rate < -10:
            trend = 'falling'
        else:
            trend = 'stable'
        
        return {
            'trend': trend,
            'growth_rate': round(growth_rate, 1),
            'data_points': snapshots.count(),
            'score_history': [
                {'date': snapshot.date_recorded.isoformat(), 'score': snapshot.score}
                for snapshot in snapshots
            ]
        }
    
    def get_frequently_bought_together(self, obj):
        """Get items frequently bought together with this item"""
        associations = ItemAssociation.objects.filter(
            source_item=obj,
            confidence__gte=0.1  # Minimum confidence threshold
        ).select_related('target_item').order_by('-confidence')[:5]
        
        return [
            {
                'item_id': assoc.target_item.item_id,
                'name': assoc.target_item.name,
                'price': assoc.target_item.price,
                'confidence': float(assoc.confidence),
                'support': assoc.support
            }
            for assoc in associations
        ]
    # ========== END NEW POPULARITY METHODS ==========

class MenuCategorySerializer(serializers.ModelSerializer):
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    item_count = serializers.SerializerMethodField()
    items = MenuItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = MenuCategory
        fields = [
            'category_id', 'restaurant', 'restaurant_name', 'name', 'description',
            'display_order', 'is_active', 'item_count', 'items', 'created_at', 'updated_at'
        ]
        read_only_fields = ['category_id', 'created_at', 'updated_at']
    
    def get_item_count(self, obj):
        return obj.menu_items.count()
    
class SpecialOfferSerializer(serializers.ModelSerializer):
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    is_valid = serializers.BooleanField(read_only=True)
    applicable_item_names = serializers.SerializerMethodField()
    distance_km = serializers.SerializerMethodField()
    restaurant_is_open = serializers.SerializerMethodField()
    
    class Meta:
        model = SpecialOffer
        fields = [
            'offer_id', 'restaurant', 'restaurant_name', 'title', 'description',
            'offer_type', 'discount_value', 'applicable_items', 'applicable_item_names',
            'min_order_amount', 'valid_from', 'valid_until', 'is_active', 'is_valid',
            'distance_km', 'restaurant_is_open', 'max_usage', 'current_usage', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['offer_id', 'created_at', 'updated_at']
    
    def get_applicable_item_names(self, obj):
        return [item.name for item in obj.applicable_items.all()]
    
    def get_distance_km(self, obj):
        """Calculate distance for the restaurant offering this special"""
        request = self.context.get('request')
        if request and hasattr(request, 'query_params'):
            lat = request.query_params.get('lat')
            lng = request.query_params.get('lng')
            
            if lat and lng:
                try:
                    from ..search_utils import SearchUtils
                    distances = []
                    for branch in obj.restaurant.branches.all():
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
        
        user_lat = self.context.get('user_latitude')
        user_lng = self.context.get('user_longitude')
        
        if user_lat is not None and user_lng is not None:
            try:
                from ..search_utils import SearchUtils
                distances = []
                for branch in obj.restaurant.branches.all():
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
    
    def get_restaurant_is_open(self, obj):
        """Check if the restaurant is currently open"""
        return any(branch.is_open_now() for branch in obj.restaurant.branches.all() if branch.is_active)
    
class PopularitySnapshotSerializer(serializers.ModelSerializer):
    menu_item_name = serializers.CharField(source='menu_item.name', read_only=True)
    restaurant_name = serializers.CharField(source='menu_item.category.restaurant.name', read_only=True)
    date_recorded_display = serializers.SerializerMethodField()
    
    class Meta:
        model = PopularitySnapshot
        fields = [
            'snapshot_id', 'menu_item', 'menu_item_name', 'restaurant_name',
            'score', 'order_count', 'rank', 'date_recorded', 'date_recorded_display'
        ]
        read_only_fields = ['snapshot_id', 'date_recorded']
    
    def get_date_recorded_display(self, obj):
        return obj.date_recorded.strftime('%b %d, %Y')

class ItemAssociationSerializer(serializers.ModelSerializer):
    source_item_name = serializers.CharField(source='source_item.name', read_only=True)
    source_restaurant = serializers.CharField(source='source_item.category.restaurant.name', read_only=True)
    target_item_name = serializers.CharField(source='target_item.name', read_only=True)
    target_restaurant = serializers.CharField(source='target_item.category.restaurant.name', read_only=True)
    confidence_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = ItemAssociation
        fields = [
            'association_id', 'source_item', 'source_item_name', 'source_restaurant',
            'target_item', 'target_item_name', 'target_restaurant', 'confidence',
            'confidence_percentage', 'support', 'created_at', 'updated_at'
        ]
        read_only_fields = ['association_id', 'created_at', 'updated_at']
    
    def get_confidence_percentage(self, obj):
        return f"{float(obj.confidence) * 100:.1f}%"


class RestaurantRecommendationResponseSerializer(serializers.Serializer):
    """Serializer for restaurant homepage recommendation responses"""
    restaurant_id = serializers.IntegerField()
    recommendations = serializers.DictField()
    generated_at = serializers.DateTimeField()
    total_recommendations = serializers.IntegerField()
    user_authenticated = serializers.BooleanField()

class TrendingItemsResponseSerializer(serializers.Serializer):
    """Serializer for trending items response"""
    restaurant_id = serializers.IntegerField()
    trending_items = serializers.ListField()
    period_days = serializers.IntegerField()
    user_authenticated = serializers.BooleanField()