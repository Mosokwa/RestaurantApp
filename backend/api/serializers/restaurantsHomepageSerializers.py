from rest_framework import serializers
from ..models import Restaurant, MenuCategory, MenuItem, SpecialOffer
from ..serializers import RestaurantSerializer, SpecialOfferSerializer

class RestaurantHomepageSerializer(RestaurantSerializer):
    """Enhanced serializer for homepage restaurant listings"""
    featured_categories = serializers.SerializerMethodField()
    featured_items = serializers.SerializerMethodField()
    active_offers_count = serializers.SerializerMethodField()
    
    class Meta(RestaurantSerializer.Meta):
        fields = RestaurantSerializer.Meta.fields + [
            'story_description', 'amenities', 'gallery_images',
            'reservation_enabled', 'loyalty_enabled',
            'featured_categories', 'featured_items', 'active_offers_count'
        ]
    
    def get_featured_categories(self, obj):
        categories = obj.menu_categories.filter(is_featured=True).order_by('display_order')[:5]
        return MenuCategoryHomeSerializer(categories, many=True, context=self.context).data
    
    def get_featured_items(self, obj):
        items = MenuItem.objects.filter(
            category__restaurant=obj,
            is_featured=True,
            is_available=True
        ).order_by('-popularity_score')[:10]
        return FeaturedItemSerializer(items, many=True, context=self.context).data
    
    def get_active_offers_count(self, obj):
        return obj.special_offers.filter(is_active=True, is_featured=True).count()

class MenuCategoryHomeSerializer(serializers.ModelSerializer):
    """Simplified category serializer for homepage"""
    item_count = serializers.SerializerMethodField()
    featured_items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = MenuCategory
        fields = [
            'category_id', 'name', 'description', 'display_color',
            'item_count', 'featured_items_count', 'display_order', 'is_featured'
        ]
    
    def get_item_count(self, obj):
        return obj.menu_items.count()
    
    def get_featured_items_count(self, obj):
        return obj.menu_items.filter(is_featured=True).count()

class FeaturedItemSerializer(serializers.ModelSerializer):
    """Simplified item serializer for homepage featuring"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    preparation_time_display = serializers.SerializerMethodField()
    dietary_info = serializers.SerializerMethodField()
    
    class Meta:
        model = MenuItem
        fields = [
            'item_id', 'name', 'description', 'price', 'image', 'category_name',
            'restaurant_name', 'preparation_time', 'preparation_time_display',
            'is_vegetarian', 'is_vegan', 'is_gluten_free', 'is_spicy',
            'popularity_score', 'dietary_info', 'is_featured'
        ]
    
    def get_preparation_time_display(self, obj):
        if obj.preparation_time <= 15:
            return "Fast"
        elif obj.preparation_time <= 30:
            return "Medium"
        else:
            return "Slow"
    
    def get_dietary_info(self, obj):
        return {
            'vegetarian': obj.is_vegetarian,
            'vegan': obj.is_vegan,
            'gluten_free': obj.is_gluten_free,
            'spicy': obj.is_spicy
        }

class EnhancedSpecialOfferSerializer(SpecialOfferSerializer):
    """Enhanced offer serializer for homepage carousel"""
    restaurant_logo = serializers.ImageField(source='restaurant.logo', read_only=True)
    usage_remaining = serializers.SerializerMethodField()
    user_can_use = serializers.SerializerMethodField()
    user_usage_count = serializers.SerializerMethodField()
    valid_days_display = serializers.SerializerMethodField()
    next_valid_day = serializers.SerializerMethodField()
    is_valid_today = serializers.SerializerMethodField()
    
    class Meta(SpecialOfferSerializer.Meta):
        fields = SpecialOfferSerializer.Meta.fields + [
            'image', 'display_priority', 'is_featured',
            'max_usage_per_user', 'restaurant_logo', 'valid_days',
            'usage_remaining', 'user_can_use', 'user_usage_count',
            'valid_days_display', 'next_valid_day', 'is_valid_today'
        ]
    
    def get_usage_remaining(self, obj):
        if obj.max_usage == 0:
            return "Unlimited"
        return obj.max_usage - obj.current_usage
    
    def get_user_can_use(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated and hasattr(request.user, 'customer_profile'):
            return obj.can_user_use(request.user)
        return False
    
    def get_user_usage_count(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated and hasattr(request.user, 'customer_profile'):
            return obj.get_user_usage_count(request.user)
        return 0
    
    def get_valid_days_display(self, obj):
        return obj.get_valid_days_display()
    
    def get_next_valid_day(self, obj):
        return obj.get_next_valid_day()
    
    def get_is_valid_today(self, obj):
        return obj.is_valid_for_day()

class RestaurantGallerySerializer(serializers.ModelSerializer):
    """Serializer for managing restaurant gallery images"""
    class Meta:
        model = Restaurant
        fields = ['restaurant_id', 'gallery_images']
        read_only_fields = ['restaurant_id']
    
    def update(self, instance, validated_data):
        gallery_images = validated_data.get('gallery_images', [])
        if len(gallery_images) > 10:
            raise serializers.ValidationError("Maximum 10 gallery images allowed")
        instance.gallery_images = gallery_images
        instance.save()
        return instance