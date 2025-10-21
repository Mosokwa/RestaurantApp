from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from ..models import (
    MultiRestaurantLoyaltyProgram, CustomerLoyalty, Reward, PointsTransaction, RewardRedemption, Restaurant, RestaurantLoyaltySettings
)

class MultiRestaurantLoyaltyProgramSerializer(serializers.ModelSerializer):
    participating_restaurants_count = serializers.SerializerMethodField()
    program_type_display = serializers.CharField(source='get_program_type_display', read_only=True)
    
    class Meta:
        model = MultiRestaurantLoyaltyProgram
        fields = [
            'program_id', 'name', 'program_type', 'program_type_display', 'is_active',
            'default_points_per_dollar', 'global_signup_bonus_points', 'global_referral_bonus_points',
            'bronze_min_points', 'silver_min_points', 'gold_min_points', 'platinum_min_points',
            'participating_restaurants', 'participating_restaurants_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['program_id', 'created_at', 'updated_at']
    
    def get_participating_restaurants_count(self, obj):
        if obj.program_type == 'global':
            return "All Restaurants"
        return obj.participating_restaurants.count()

class CustomerLoyaltySerializer(serializers.ModelSerializer):
    customer_email = serializers.CharField(source='customer.user.email', read_only=True)
    customer_name = serializers.CharField(source='customer.user.get_full_name', read_only=True)
    program_name = serializers.CharField(source='program.name', read_only=True)
    program_type = serializers.CharField(source='program.program_type', read_only=True)
    tier_benefits = serializers.SerializerMethodField()
    restaurant_stats_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomerLoyalty
        fields = [
            'loyalty_id', 'customer', 'customer_email', 'customer_name',
            'program', 'program_name', 'program_type', 'current_points', 'lifetime_points',
            'tier', 'referral_code', 'referred_by', 'total_orders', 'total_spent',
            'restaurant_stats', 'restaurant_stats_summary', 'tier_benefits',
            'joined_at', 'tier_updated_at'
        ]
        read_only_fields = [
            'loyalty_id', 'current_points', 'lifetime_points', 'tier',
            'referral_code', 'total_orders', 'total_spent', 'joined_at',
            'tier_updated_at'
        ]
    
    def get_tier_benefits(self, obj):
        restaurant = self.context.get('restaurant')
        return obj.get_tier_benefits(restaurant)
    
    def get_restaurant_stats_summary(self, obj):
        """Provide a summary of restaurant statistics"""
        return {
            'total_restaurants': len(obj.restaurant_stats),
            'active_restaurants': len([stats for stats in obj.restaurant_stats.values() if stats['orders'] > 0]),
            'most_visited': self._get_most_visited_restaurant(obj.restaurant_stats)
        }
    
    def _get_most_visited_restaurant(self, restaurant_stats):
        if not restaurant_stats:
            return None
        
        most_visited = max(restaurant_stats.items(), key=lambda x: x[1]['orders'])
        return {
            'restaurant_id': most_visited[0],
            'restaurant_name': most_visited[1].get('restaurant_name', 'Unknown'),
            'orders': most_visited[1]['orders'],
            'total_spent': most_visited[1]['spent']
        }

class PointsTransactionSerializer(serializers.ModelSerializer):
    order_uuid = serializers.CharField(source='order.order_uuid', read_only=True, allow_null=True)
    reward_name = serializers.CharField(source='reward.name', read_only=True, allow_null=True)
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True, allow_null=True)
    program_name = serializers.CharField(source='customer_loyalty.program.name', read_only=True)
    
    class Meta:
        model = PointsTransaction
        fields = [
            'transaction_id', 'customer_loyalty', 'points', 'transaction_type', 'reason',
            'order', 'order_uuid', 'reward', 'reward_name', 'restaurant', 'restaurant_name',
            'program_name', 'transaction_date', 'expires_at', 'is_active'
        ]
        read_only_fields = ['transaction_id', 'transaction_date']

class RewardSerializer(serializers.ModelSerializer):
    is_available = serializers.BooleanField(read_only=True)
    free_item_name = serializers.CharField(source='free_menu_item.name', read_only=True, allow_null=True)
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True, allow_null=True)
    program_name = serializers.CharField(source='program.name', read_only=True)
    applicable_restaurant_names = serializers.SerializerMethodField()
    
    class Meta:
        model = Reward
        fields = [
            'reward_id', 'program', 'program_name', 'restaurant', 'restaurant_name', 
            'name', 'description', 'reward_type', 'points_required', 'discount_percentage', 
            'discount_amount', 'free_menu_item', 'free_item_name', 'is_active', 
            'stock_quantity', 'redeemed_count', 'min_tier_required', 'is_available',
            'applicable_restaurants', 'applicable_restaurant_names',
            'valid_from', 'valid_until', 'created_at', 'updated_at'
        ]
        read_only_fields = ['reward_id', 'redeemed_count', 'created_at', 'updated_at']
    
    def get_applicable_restaurant_names(self, obj):
        return [restaurant.name for restaurant in obj.applicable_restaurants.all()]

class RewardRedemptionSerializer(serializers.ModelSerializer):
    reward_name = serializers.CharField(source='reward.name', read_only=True)
    customer_email = serializers.CharField(source='customer_loyalty.customer.user.email', read_only=True)
    customer_name = serializers.CharField(source='customer_loyalty.customer.user.get_full_name', read_only=True)
    redemption_code = serializers.CharField(read_only=True)
    voucher_code = serializers.CharField(source='discount_voucher.code', read_only=True, allow_null=True)
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    program_name = serializers.CharField(source='customer_loyalty.program.name', read_only=True)
    
    class Meta:
        model = RewardRedemption
        fields = [
            'redemption_id', 'customer_loyalty', 'customer_email', 'customer_name',
            'reward', 'reward_name', 'points_used', 'status', 'redemption_code', 
            'voucher_code', 'restaurant', 'restaurant_name', 'program_name',
            'discount_voucher', 'created_at', 'redeemed_at', 'expires_at'
        ]
        read_only_fields = [
            'redemption_id', 'points_used', 'redemption_code', 'created_at', 
            'redeemed_at', 'expires_at'
        ]

class PointsEarningSerializer(serializers.Serializer):
    order_id = serializers.IntegerField(required=True)
    points = serializers.IntegerField(required=True)
    reason = serializers.CharField(required=False, allow_blank=True)

class PointsRedemptionSerializer(serializers.Serializer):
    reward_id = serializers.IntegerField(required=True)
    restaurant_id = serializers.IntegerField(required=False, allow_null=True)
    
    def validate(self, data):
        reward_id = data['reward_id']
        restaurant_id = data.get('restaurant_id')
        
        try:
            reward = Reward.objects.get(pk=reward_id)
            if not reward.is_available():
                raise ValidationError("This reward is not available for redemption")
            
            if restaurant_id:
                try:
                    restaurant = Restaurant.objects.get(pk=restaurant_id)
                    if not reward.can_redeem_at_restaurant(restaurant):
                        raise ValidationError("This reward cannot be redeemed at the selected restaurant")
                    data['restaurant'] = restaurant
                except Restaurant.DoesNotExist:
                    raise ValidationError("Restaurant not found")
            
            data['reward'] = reward
        except Reward.DoesNotExist:
            raise ValidationError("Reward not found")
        return data

class ReferralSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        request = self.context.get('request')
        if request and value == request.user.email:
            raise ValidationError("You cannot refer yourself")
        return value

class ToggleLoyaltySerializer(serializers.Serializer):
    is_loyalty_enabled = serializers.BooleanField(required=True)
    
    def update(self, instance, validated_data):
        instance.is_loyalty_enabled = validated_data.get('is_loyalty_enabled', instance.is_loyalty_enabled)
        instance.save()
        return instance

class BulkToggleLoyaltySerializer(serializers.Serializer):
    restaurant_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True
    )
    enable = serializers.BooleanField(default=True)
    
    def validate_restaurant_ids(self, value):
        if not value:
            raise ValidationError("At least one restaurant ID is required")
        return value