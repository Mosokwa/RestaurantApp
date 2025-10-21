from rest_framework import serializers
from ..models import RestaurantLoyaltySettings, Reward

class RestaurantLoyaltySettingsSerializer(serializers.ModelSerializer):
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    program_name = serializers.CharField(source='program.name', read_only=True)
    effective_points_rate = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    effective_signup_bonus = serializers.IntegerField(read_only=True)
    effective_referral_bonus = serializers.IntegerField(read_only=True)
    is_loyalty_active = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = RestaurantLoyaltySettings
        fields = [
            'settings_id', 'restaurant', 'restaurant_name', 'program', 'program_name',
            'is_loyalty_enabled', 'custom_points_per_dollar', 'effective_points_rate',
            'custom_signup_bonus_points', 'effective_signup_bonus',
            'custom_referral_bonus_points', 'effective_referral_bonus',
            'custom_tier_benefits', 'minimum_order_amount_for_points',
            'allow_point_redemption', 'allow_reward_redemption',
            'points_expiry_days', 'max_points_per_order', 'is_loyalty_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['settings_id', 'created_at', 'updated_at']
    
    def validate_custom_points_per_dollar(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError("Points per dollar must be greater than 0")
        return value
    
    def validate_minimum_order_amount_for_points(self, value):
        if value < 0:
            raise serializers.ValidationError("Minimum order amount cannot be negative")
        return value

class RestaurantLoyaltySettingsCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RestaurantLoyaltySettings
        fields = [
            'restaurant', 'program', 'is_loyalty_enabled', 'custom_points_per_dollar',
            'custom_signup_bonus_points', 'custom_referral_bonus_points',
            'minimum_order_amount_for_points', 'allow_point_redemption',
            'allow_reward_redemption', 'points_expiry_days', 'max_points_per_order'
        ]
    
    def validate_restaurant(self, value):
        request = self.context.get('request')
        if request and value.owner != request.user:
            raise serializers.ValidationError("You can only create settings for your own restaurants")
        return value

class RestaurantRewardSerializer(serializers.ModelSerializer):
    is_available = serializers.BooleanField(read_only=True)
    free_item_name = serializers.CharField(source='free_menu_item.name', read_only=True, allow_null=True)
    
    class Meta:
        model = Reward
        fields = [
            'reward_id', 'name', 'description', 'reward_type', 'points_required',
            'discount_percentage', 'discount_amount', 'free_menu_item', 'free_item_name',
            'is_active', 'stock_quantity', 'min_tier_required', 'is_available',
            'valid_from', 'valid_until', 'created_at', 'updated_at'
        ]
        read_only_fields = ['reward_id', 'created_at', 'updated_at']

class ToggleLoyaltySerializer(serializers.Serializer):
    is_loyalty_enabled = serializers.BooleanField(required=True)
    
    def update(self, instance, validated_data):
        instance.is_loyalty_enabled = validated_data.get('is_loyalty_enabled', instance.is_loyalty_enabled)
        instance.save()
        return instance