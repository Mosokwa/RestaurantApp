from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from ..models import DISH_RATING_TAGS, RESTAURANT_RATING_TAGS, DishRating, DishReview, RestaurantRating, RestaurantReview, RestaurantReviewSettings, ReviewHelpfulVote, ReviewReport, ReviewResponse, Order, OrderItem

class RestaurantReviewSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.user.get_full_name', read_only=True)
    customer_username = serializers.CharField(source='customer.user.username', read_only=True)
    customer_avatar = serializers.SerializerMethodField()
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    order_uuid = serializers.CharField(source='order.order_uuid', read_only=True)
    response = serializers.SerializerMethodField()
    user_has_voted = serializers.SerializerMethodField()
    user_vote_type = serializers.SerializerMethodField()
    
    class Meta:
        model = RestaurantReview
        fields = [
            'review_id', 'restaurant', 'restaurant_name', 'customer', 'customer_name',
            'customer_username', 'customer_avatar', 'order', 'order_uuid',
            'overall_rating', 'food_quality', 'service_quality', 'ambiance',
            'value_for_money', 'title', 'comment', 'photos', 'video_url',
            'helpful_count', 'status', 'is_verified_purchase', 'response',
            'user_has_voted', 'user_vote_type', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'review_id', 'helpful_count', 'status', 'is_verified_purchase',
            'created_at', 'updated_at'
        ]
    
    def get_customer_avatar(self, obj):
        # You can implement avatar logic here
        return None
    
    def get_response(self, obj):
        if hasattr(obj, 'response') and obj.response.is_public:
            return ReviewResponseSerializer(obj.response).data
        return None
    
    def get_user_has_voted(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if hasattr(request.user, 'customer_profile'):
                return obj.helpful_votes.filter(customer=request.user.customer_profile).exists()
        return False
    
    def get_user_vote_type(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if hasattr(request.user, 'customer_profile'):
                vote = obj.helpful_votes.filter(customer=request.user.customer_profile).first()
                return vote.is_helpful if vote else None
        return None
    
    def validate(self, data):
        # Ensure customer has ordered from this restaurant to review
        request = self.context.get('request')
        restaurant = data.get('restaurant')
        
        if request and hasattr(request.user, 'customer_profile'):
            customer = request.user.customer_profile
            has_ordered = Order.objects.filter(
                customer=customer,
                restaurant=restaurant,
                status='delivered'
            ).exists()
            
            if not has_ordered:
                raise ValidationError("You must have ordered from this restaurant to leave a review")
        
        return data
    
    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request.user, 'customer_profile'):
            validated_data['customer'] = request.user.customer_profile
        
        return super().create(validated_data)

class DishReviewSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.user.get_full_name', read_only=True)
    customer_username = serializers.CharField(source='customer.user.username', read_only=True)
    menu_item_name = serializers.CharField(source='menu_item.name', read_only=True)
    restaurant_name = serializers.CharField(source='menu_item.category.restaurant.name', read_only=True)
    
    class Meta:
        model = DishReview
        fields = [
            'dish_review_id', 'menu_item', 'menu_item_name', 'restaurant_name',
            'customer', 'customer_name', 'customer_username', 'order', 'rating',
            'comment', 'photos', 'taste_rating', 'portion_size_rating',
            'value_rating', 'helpful_count', 'status', 'is_verified_purchase',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'dish_review_id', 'helpful_count', 'status', 'is_verified_purchase',
            'created_at', 'updated_at'
        ]
    
    def validate(self, data):
        request = self.context.get('request')
        menu_item = data.get('menu_item')
        
        if request and hasattr(request.user, 'customer_profile'):
            customer = request.user.customer_profile
            has_ordered = OrderItem.objects.filter(
                order__customer=customer,
                menu_item=menu_item,
                order__status='delivered'
            ).exists()
            
            if not has_ordered:
                raise ValidationError("You must have ordered this menu item to leave a review")
        
        return data
    
    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request.user, 'customer_profile'):
            validated_data['customer'] = request.user.customer_profile
        
        return super().create(validated_data)

class ReviewResponseSerializer(serializers.ModelSerializer):
    responder_name = serializers.CharField(source='responder.get_full_name', read_only=True)
    responder_username = serializers.CharField(source='responder.username', read_only=True)
    review_title = serializers.CharField(source='review.title', read_only=True)
    
    class Meta:
        model = ReviewResponse
        fields = [
            'response_id', 'review', 'review_title', 'responder', 'responder_name',
            'responder_username', 'comment', 'is_public', 'created_at', 'updated_at'
        ]
        read_only_fields = ['response_id', 'created_at', 'updated_at']
    
    def validate(self, data):
        request = self.context.get('request')
        review = data.get('review')
        
        # Check if user is restaurant owner or staff
        if request and review:
            restaurant = review.restaurant
            if not (request.user == restaurant.owner or 
                   restaurant.staff_members.filter(user=request.user).exists()):
                raise ValidationError("Only restaurant owners or staff can respond to reviews")
        
        # Check if response already exists
        if ReviewResponse.objects.filter(review=review).exists():
            raise ValidationError("A response already exists for this review")
        
        return data
    
    def create(self, validated_data):
        request = self.context.get('request')
        if request:
            validated_data['responder'] = request.user
        
        return super().create(validated_data)

class ReviewReportSerializer(serializers.ModelSerializer):
    reporter_name = serializers.CharField(source='reporter.get_full_name', read_only=True)
    review_title = serializers.CharField(source='review.title', read_only=True)
    restaurant_name = serializers.CharField(source='review.restaurant.name', read_only=True)
    
    class Meta:
        model = ReviewReport
        fields = [
            'report_id', 'review', 'review_title', 'restaurant_name', 'reporter',
            'reporter_name', 'reason', 'description', 'status', 'moderator_notes',
            'resolved_by', 'created_at', 'resolved_at'
        ]
        read_only_fields = [
            'report_id', 'status', 'moderator_notes', 'resolved_by',
            'created_at', 'resolved_at'
        ]
    
    def validate(self, data):
        request = self.context.get('request')
        review = data.get('review')
        
        # Check if user has already reported this review
        if request and ReviewReport.objects.filter(review=review, reporter=request.user).exists():
            raise ValidationError("You have already reported this review")
        
        return data
    
    def create(self, validated_data):
        request = self.context.get('request')
        if request:
            validated_data['reporter'] = request.user
        
        return super().create(validated_data)

class ReviewHelpfulVoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewHelpfulVote
        fields = ['vote_id', 'review', 'customer', 'is_helpful', 'created_at']
        read_only_fields = ['vote_id', 'customer', 'created_at']
    
    def validate(self, data):
        request = self.context.get('request')
        review = data.get('review')
        
        if request and hasattr(request.user, 'customer_profile'):
            customer = request.user.customer_profile
            if ReviewHelpfulVote.objects.filter(review=review, customer=customer).exists():
                raise ValidationError("You have already voted on this review")
        
        return data
    
    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request.user, 'customer_profile'):
            validated_data['customer'] = request.user.customer_profile
        
        return super().create(validated_data)

class RestaurantReviewSettingsSerializer(serializers.ModelSerializer):
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    
    class Meta:
        model = RestaurantReviewSettings
        fields = [
            'restaurant', 'restaurant_name', 'auto_approve_reviews',
            'allow_photo_reviews', 'allow_video_reviews', 'require_order_verification',
            'min_order_amount_for_review', 'notify_on_new_review',
            'notify_on_review_report', 'auto_response_enabled',
            'auto_response_message', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class ReviewAnalyticsSerializer(serializers.Serializer):
    total_reviews = serializers.IntegerField()
    average_rating = serializers.DecimalField(max_digits=3, decimal_places=2)
    rating_breakdown = serializers.JSONField()
    recent_reviews_count = serializers.IntegerField()
    response_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    reported_reviews_count = serializers.IntegerField()
    
    class Meta:
        fields = [
            'total_reviews', 'average_rating', 'rating_breakdown',
            'recent_reviews_count', 'response_rate', 'reported_reviews_count'
        ]

class RestaurantRatingSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.user.get_full_name', read_only=True)
    customer_username = serializers.CharField(source='customer.user.username', read_only=True)
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    order_uuid = serializers.CharField(source='order.order_uuid', read_only=True)
    
    class Meta:
        model = RestaurantRating
        fields = [
            'rating_id', 'restaurant', 'restaurant_name', 'customer', 'customer_name',
            'customer_username', 'order', 'order_uuid', 'overall_rating',
            'food_quality', 'service_quality', 'ambiance', 'value_for_money',
            'tags', 'is_verified_purchase', 'is_quick_rating', 'created_at', 'updated_at'
        ]
        read_only_fields = ['rating_id', 'is_verified_purchase', 'created_at', 'updated_at']
    
    def validate_tags(self, value):
        # Validate rating tags
        valid_tags = RESTAURANT_RATING_TAGS  # This should be imported from models
        for tag in value:
            if tag not in valid_tags:
                raise ValidationError(f"Invalid tag: {tag}. Valid tags are: {', '.join(valid_tags)}")
        return value
    
    def validate(self, data):
        # Ensure at least overall_rating is provided
        if not data.get('overall_rating'):
            raise ValidationError("Overall rating is required")
        
        # Validate rating ranges
        rating_fields = ['overall_rating', 'food_quality', 'service_quality', 'ambiance', 'value_for_money']
        for field in rating_fields:
            if data.get(field) and (data[field] < 1 or data[field] > 5):
                raise ValidationError(f"{field.replace('_', ' ').title()} must be between 1 and 5")
        
        return data
    
    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request.user, 'customer_profile'):
            validated_data['customer'] = request.user.customer_profile
        
        # Check if this is a quick rating (only overall_rating provided)
        detailed_ratings = any([
            validated_data.get('food_quality'),
            validated_data.get('service_quality'), 
            validated_data.get('ambiance'),
            validated_data.get('value_for_money'),
            validated_data.get('tags')
        ])
        validated_data['is_quick_rating'] = not detailed_ratings
        
        rating = super().create(validated_data)
        
        # Update restaurant rating stats
        rating.restaurant.update_rating_stats()
        
        return rating
    
    def update(self, instance, validated_data):
        rating = super().update(instance, validated_data)
        
        # Update restaurant rating stats
        rating.restaurant.update_rating_stats()
        
        return rating

class DishRatingSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.user.get_full_name', read_only=True)
    customer_username = serializers.CharField(source='customer.user.username', read_only=True)
    menu_item_name = serializers.CharField(source='menu_item.name', read_only=True)
    restaurant_name = serializers.CharField(source='menu_item.category.restaurant.name', read_only=True)
    
    class Meta:
        model = DishRating
        fields = [
            'dish_rating_id', 'menu_item', 'menu_item_name', 'restaurant_name',
            'customer', 'customer_name', 'customer_username', 'order', 'rating',
            'taste', 'portion_size', 'value', 'tags', 'is_verified_purchase',
            'is_quick_rating', 'created_at', 'updated_at'
        ]
        read_only_fields = ['dish_rating_id', 'is_verified_purchase', 'created_at', 'updated_at']
    
    def validate_tags(self, value):
        valid_tags = DISH_RATING_TAGS
        for tag in value:
            if tag not in valid_tags:
                raise ValidationError(f"Invalid tag: {tag}. Valid tags are: {', '.join(valid_tags)}")
        return value
    
    def validate(self, data):
        if not data.get('rating'):
            raise ValidationError("Rating is required")
        
        rating_fields = ['rating', 'taste', 'portion_size', 'value']
        for field in rating_fields:
            if data.get(field) and (data[field] < 1 or data[field] > 5):
                raise ValidationError(f"{field.replace('_', ' ').title()} must be between 1 and 5")
        
        return data
    
    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request.user, 'customer_profile'):
            validated_data['customer'] = request.user.customer_profile
        
        # Check if this is a quick rating
        detailed_ratings = any([
            validated_data.get('taste'),
            validated_data.get('portion_size'), 
            validated_data.get('value'),
            validated_data.get('tags')
        ])
        validated_data['is_quick_rating'] = not detailed_ratings
        
        rating = super().create(validated_data)
        
        # Update menu item rating stats
        rating.menu_item.update_rating_stats()
        
        return rating
    
    def update(self, instance, validated_data):
        rating = super().update(instance, validated_data)
        rating.menu_item.update_rating_stats()
        return rating

class QuickRatingSerializer(serializers.Serializer):
    """
    Serializer for quick ratings (just overall rating without details)
    """
    overall_rating = serializers.DecimalField(
        max_digits=2, 
        decimal_places=1, 
        min_value=1, 
        max_value=5
    )
    tags = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )
    
    def validate_tags(self, value):
        valid_tags = RESTAURANT_RATING_TAGS
        for tag in value:
            if tag not in valid_tags:
                raise ValidationError(f"Invalid tag: {tag}")
        return value

class RatingStatsSerializer(serializers.Serializer):
    total_ratings = serializers.IntegerField()
    average_rating = serializers.FloatField()
    rating_distribution = serializers.JSONField()
    tag_frequencies = serializers.JSONField()
    detailed_averages = serializers.JSONField()
    user_rating = serializers.DecimalField(
        max_digits=2, 
        decimal_places=1, 
        allow_null=True
    )

class BulkRatingSerializer(serializers.Serializer):
    """
    Serializer for bulk rating operations (rating multiple items at once)
    """
    restaurant_ratings = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        default=list
    )
    dish_ratings = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        default=list
    )
    
    def validate(self, data):
        if not data.get('restaurant_ratings') and not data.get('dish_ratings'):
            raise ValidationError("At least one rating must be provided")
        return data