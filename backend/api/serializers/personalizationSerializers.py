from rest_framework import serializers
from ..models import Recommendation, SimilarityMatrix, UserBehavior, UserPreference

class UserBehaviorSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    menu_item_name = serializers.CharField(source='menu_item.name', read_only=True)
    
    class Meta:
        model = UserBehavior
        fields = [
            'behavior_id', 'user', 'user_email', 'restaurant', 'restaurant_name',
            'menu_item', 'menu_item_name', 'behavior_type', 'value', 'metadata',
            'created_at'
        ]
        read_only_fields = ['behavior_id', 'created_at']

class UserPreferenceSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = UserPreference
        fields = [
            'preference_id', 'user', 'user_email', 'user_username', 'cuisine_scores',
            'dietary_weights', 'price_preferences', 'preferred_locations',
            'restaurant_type_scores', 'avg_order_value', 'order_frequency_days',
            'preferred_order_times', 'last_calculated', 'created_at'
        ]
        read_only_fields = ['preference_id', 'last_calculated', 'created_at']

class RecommendationSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    recommended_restaurant_names = serializers.SerializerMethodField()
    recommended_menu_item_names = serializers.SerializerMethodField()
    
    class Meta:
        model = Recommendation
        fields = [
            'recommendation_id', 'user', 'user_email', 'recommendation_type',
            'recommended_restaurants', 'recommended_restaurant_names',
            'recommended_menu_items', 'recommended_menu_item_names',
            'scores', 'algorithm_metadata', 'is_active', 'expires_at', 'generated_at'
        ]
        read_only_fields = ['recommendation_id', 'generated_at']
    
    def get_recommended_restaurant_names(self, obj):
        return [restaurant.name for restaurant in obj.recommended_restaurants.all()]
    
    def get_recommended_menu_item_names(self, obj):
        return [item.name for item in obj.recommended_menu_items.all()]

class SimilarityMatrixSerializer(serializers.ModelSerializer):
    class Meta:
        model = SimilarityMatrix
        fields = [
            'matrix_id', 'matrix_type', 'item_a_id', 'item_b_id',
            'similarity_score', 'calculation_method', 'metadata', 'calculated_at'
        ]
        read_only_fields = ['matrix_id', 'calculated_at']

# Recommendation response serializers
class RecommendedItemSerializer(serializers.Serializer):
    item_id = serializers.IntegerField()
    name = serializers.CharField()
    type = serializers.CharField()  # 'menu_item' or 'restaurant'
    description = serializers.CharField(required=False)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    image = serializers.URLField(required=False)
    restaurant_name = serializers.CharField(required=False)
    restaurant_id = serializers.IntegerField(required=False)
    score = serializers.FloatField()
    reasons = serializers.ListField(child=serializers.CharField())
    algorithms = serializers.ListField(child=serializers.CharField())
    distance_km = serializers.FloatField(required=False, allow_null=True)

class RecommendationResponseSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    recommendation_type = serializers.CharField()
    items = RecommendedItemSerializer(many=True)
    generated_at = serializers.DateTimeField()
    expires_at = serializers.DateTimeField()

class PreferenceUpdateSerializer(serializers.Serializer):
    cuisine_preferences = serializers.JSONField(required=False)
    dietary_preferences = serializers.JSONField(required=False)
    explicit_ratings = serializers.JSONField(required=False)  # {item_id: rating}

class TrendingRecommendationSerializer(serializers.Serializer):
    period = serializers.CharField()  # 'weekly', 'monthly'
    items = RecommendedItemSerializer(many=True)
    growth_metrics = serializers.JSONField()
