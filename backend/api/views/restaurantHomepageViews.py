from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import viewsets, status
from django.core.cache import cache
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from django.db.models import Count, Prefetch, Avg, Q, Case, When, IntegerField
from datetime import timedelta
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from ..models import Restaurant, MenuItem, Restaurant, MenuCategory, MenuItem, SpecialOffer, RestaurantReview, Table, RestaurantLoyaltySettings
from ..recommendation_engine import RecommendationEngine
from ..serializers import (
    MenuItemSerializer,
    RestaurantRecommendationResponseSerializer,
    TrendingItemsResponseSerializer, RestaurantHomepageSerializer, EnhancedSpecialOfferSerializer,
    MenuCategoryHomeSerializer, FeaturedItemSerializer
)

class RestaurantHomepageRecommendationsView(APIView):
    """
    API endpoint for restaurant-specific homepage recommendations
    """
    permission_classes = [AllowAny]
    
    def get(self, request, restaurant_id):
        """Get recommendations for a restaurant's homepage"""
        limit = int(request.query_params.get('limit', 12))
        current_item_id = request.query_params.get('current_item_id')
        
        engine = RecommendationEngine()
        
        kwargs = {}
        if current_item_id:
            kwargs['current_item_id'] = current_item_id
        
        # For anonymous users, pass None as user
        user = request.user if request.user.is_authenticated else None
        
        recommendations = engine.get_restaurant_homepage_recommendations(
            user, restaurant_id, limit=limit, **kwargs
        )
        
        # Serialize the recommendations using EnhancedMenuItemSerializer
        serialized_recommendations = self._serialize_recommendations(
            recommendations, request
        )
        
        # Group by recommendation type for organized display
        grouped_recommendations = self._group_by_type(serialized_recommendations)
        
        response_data = {
            'restaurant_id': restaurant_id,
            'recommendations': grouped_recommendations,
            'generated_at': timezone.now(),
            'total_recommendations': len(serialized_recommendations),
            'user_authenticated': request.user.is_authenticated
        }
        
        # Use the proper serializer for response
        serializer = RestaurantRecommendationResponseSerializer(response_data)
        return Response(serializer.data)
    
    def _serialize_recommendations(self, recommendations, request):
        """Serialize recommendation items using EnhancedMenuItemSerializer"""
        serialized = []
        
        for rec in recommendations:
            # Use EnhancedMenuItemSerializer for full popularity data
            item_data = MenuItemSerializer(
                rec['item'], 
                context={'request': request}
            ).data
            
            # Add recommendation metadata
            item_data.update({
                'recommendation_score': rec['score'],
                'recommendation_reason': rec['reason'],
                'recommendation_algorithm': rec['algorithm']
            })
            
            serialized.append(item_data)
        
        return serialized
    
    def _group_by_type(self, recommendations):
        """Group recommendations by type for organized display"""
        groups = {
            'popular_items': [],
            'similar_items': [], 
            'frequently_bought_together': [],
            'personalized_picks': []
        }
        
        algorithm_mapping = {
            'restaurant_popularity': 'popular_items',
            'restaurant_similarity': 'similar_items',
            'frequently_bought_together': 'frequently_bought_together',
            'restaurant_personalized': 'personalized_picks'
        }
        
        for rec in recommendations:
            group_key = algorithm_mapping.get(
                rec['recommendation_algorithm'], 
                'personalized_picks'
            )
            groups[group_key].append(rec)
        
        # Limit each group for balanced display
        for key in groups:
            groups[key] = groups[key][:4]  # Max 4 items per group
        
        return groups

class RestaurantPopularItemsView(APIView):
    """
    API endpoint for popular items in a restaurant (for restaurant homepage)
    """
    permission_classes = [AllowAny]
    
    def get(self, request, restaurant_id):
        """Get popular items for restaurant homepage"""
        limit = int(request.query_params.get('limit', 8))
        
        popular_items = MenuItem.objects.filter(
            category__restaurant_id=restaurant_id,
            is_available=True
        ).select_related('category', 'category__restaurant').order_by('-popularity_score', '-is_featured')[:limit]
        
        # Use EnhancedMenuItemSerializer for full popularity data
        serializer = MenuItemSerializer(
            popular_items, 
            many=True, 
            context={'request': request}
        )
        
        return Response({
            'restaurant_id': restaurant_id,
            'popular_items': serializer.data,
            'total_count': len(popular_items),
            'user_authenticated': request.user.is_authenticated
        })

class RestaurantSimilarItemsView(APIView):
    """
    API endpoint for similar items within a restaurant
    """
    permission_classes = [AllowAny]
    
    def get(self, request, restaurant_id, item_id):
        """Get similar items within the same restaurant"""
        limit = int(request.query_params.get('limit', 6))
        
        engine = RecommendationEngine()
        
        # For anonymous users, pass None as user
        user = request.user if request.user.is_authenticated else None
        
        similar_items = engine.get_restaurant_homepage_recommendations(
            user, 
            restaurant_id, 
            limit=limit,
            current_item_id=item_id,
            recommendation_types=['similar']
        )
        
        serialized_items = []
        for rec in similar_items:
            # Use EnhancedMenuItemSerializer for full data
            item_data = MenuItemSerializer(
                rec['item'],
                context={'request': request}
            ).data
            item_data['similarity_score'] = rec['score']
            serialized_items.append(item_data)
        
        return Response({
            'original_item_id': item_id,
            'similar_items': serialized_items,
            'user_authenticated': request.user.is_authenticated
        })

class RestaurantTrendingItemsView(APIView):
    """
    API endpoint for trending items within a restaurant
    """
    permission_classes = [AllowAny]
    
    def get(self, request, restaurant_id):
        """Get trending items in the restaurant"""
        limit = int(request.query_params.get('limit', 6))
        days = int(request.query_params.get('days', 7))
        
        # Calculate date range
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        comparison_start_date = start_date - timedelta(days=days)
        comparison_end_date = start_date - timedelta(days=1)
        
        # Get current period orders with growth calculation
        from django.db.models import Count, Q
        
        trending_data = []
        menu_items = MenuItem.objects.filter(
            category__restaurant_id=restaurant_id,
            is_available=True
        ).select_related('category', 'category__restaurant')
        
        for item in menu_items:
            # Get current period orders
            current_orders = item.order_items.filter(
                order__status='delivered',
                order__order_placed_at__range=[start_date, end_date]
            ).count()
            
            # Get previous period orders for comparison
            previous_orders = item.order_items.filter(
                order__status='delivered',
                order__order_placed_at__range=[comparison_start_date, comparison_end_date]
            ).count()
            
            if previous_orders > 0 and current_orders > previous_orders:
                growth_rate = (current_orders - previous_orders) / previous_orders
                if growth_rate > 0.1:  # At least 10% growth
                    trending_data.append({
                        'item': item,
                        'growth_rate': growth_rate,
                        'current_orders': current_orders,
                        'previous_orders': previous_orders
                    })
            elif previous_orders == 0 and current_orders >= 3:  # New trending item
                trending_data.append({
                    'item': item,
                    'growth_rate': 1.0,  # 100% growth for new items
                    'current_orders': current_orders,
                    'previous_orders': 0
                })
        
        # Sort by growth rate and limit
        trending_data.sort(key=lambda x: x['growth_rate'], reverse=True)
        trending_data = trending_data[:limit]
        
        # Serialize results using EnhancedMenuItemSerializer
        serialized_items = []
        for trend_data in trending_data:
            item_data = MenuItemSerializer(
                trend_data['item'],
                context={'request': request}
            ).data
            item_data.update({
                'growth_rate': trend_data['growth_rate'],
                'current_orders': trend_data['current_orders'],
                'previous_orders': trend_data['previous_orders'],
                'growth_percentage': f"+{int(trend_data['growth_rate'] * 100)}%"
            })
            serialized_items.append(item_data)
        
        response_data = {
            'restaurant_id': restaurant_id,
            'trending_items': serialized_items,
            'period_days': days,
            'user_authenticated': request.user.is_authenticated
        }
        
        # Use the proper serializer
        serializer = TrendingItemsResponseSerializer(response_data)
        return Response(serializer.data)
    

class RestaurantHomepageViewSet(viewsets.ViewSet):
    """
    Optimized homepage endpoint for restaurant data
    """
    
    @method_decorator(cache_page(60 * 5))  # Cache for 5 minutes
    @action(detail=True, methods=['get'], url_path='homepage')
    def homepage(self, request, pk=None):
        """
        Get comprehensive homepage data for a restaurant in a single optimized query
        """
        try:
            restaurant = self.get_optimized_restaurant_data(pk)
            if not restaurant:
                raise NotFound("Restaurant not found")
            
            # Build response data with optimized queries
            response_data = self.build_homepage_response(restaurant, request)
            
            return Response(response_data)
            
        except Exception as e:
            return Response(
                {"error": "Failed to load homepage data", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get_optimized_restaurant_data(self, restaurant_id):
        """
        Single optimized query to fetch all restaurant data with related objects
        """
        # Main restaurant query with all necessary prefetches
        restaurant = Restaurant.objects.filter(
            restaurant_id=restaurant_id,
            status='active'
        ).select_related(
            'owner'
        ).prefetch_related(
            # Branches with addresses
            Prefetch(
                'branches',
                queryset=Restaurant.branches.field.related_model.objects.select_related(
                    'address'
                ).filter(is_active=True)
            ),
            # Cuisines
            'cuisines',
            # Menu categories with featured items
            Prefetch(
                'menu_categories',
                queryset=MenuCategory.objects.filter(
                    is_active=True
                ).prefetch_related(
                    Prefetch(
                        'menu_items',
                        queryset=MenuItem.objects.filter(
                            is_available=True
                        ).order_by('-popularity_score')[:8]  # Limit items per category
                    )
                ).order_by('display_order')
            ),
            # Special offers
            Prefetch(
                'special_offers',
                queryset=SpecialOffer.objects.filter(
                    is_active=True,
                    is_featured=True
                ).prefetch_related('applicable_items')[:10]  # Limit offers
            ),
            # Review settings
            Prefetch(
                'review_settings',
                queryset=Restaurant.review_settings.field.related_model.objects.all()
            ),
            # Loyalty settings
            Prefetch(
                'loyalty_settings',
                queryset=RestaurantLoyaltySettings.objects.select_related('program')
            )
        ).annotate(
            # Annotate with calculated fields
            featured_items_count=Count(
                'menu_categories__menu_items',
                filter=Q(menu_categories__menu_items__is_featured=True) & 
                       Q(menu_categories__menu_items__is_available=True)
            ),
            active_offers_count=Count(
                'special_offers',
                filter=Q(special_offers__is_active=True)
            ),
            open_branches_count=Count(
                'branches',
                filter=Q(branches__is_active=True)
            )
        ).first()
        
        return restaurant
    
    def build_homepage_response(self, restaurant, request):
        """
        Build comprehensive homepage response with optimized data loading
        """
        # Use cache for expensive operations
        cache_key = f"restaurant_homepage_{restaurant.restaurant_id}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        response_data = {
            "restaurant": self.get_restaurant_basic_info(restaurant),
            "special_offers": self.get_special_offers_data(restaurant, request),
            "menu_preview": self.get_menu_preview_data(restaurant, request),
            "reservation_info": self.get_reservation_info(restaurant),
            "reviews_preview": self.get_reviews_preview_data(restaurant),
            "loyalty_info": self.get_loyalty_info(restaurant),
            "operational_info": self.get_operational_info(restaurant)
        }
        
        # Cache the complete response
        cache.set(cache_key, response_data, 300)  # 5 minutes cache
        
        return response_data
    
    def get_restaurant_basic_info(self, restaurant):
        """
        Extract basic restaurant information
        """
        main_branch = restaurant.branches.filter(is_main_branch=True).first()
        any_branch = restaurant.branches.first()
        
        return {
            "id": restaurant.restaurant_id,
            "name": restaurant.name,
            "description": restaurant.description,
            "story_description": restaurant.story_description,
            "logo": restaurant.logo.url if restaurant.logo else None,
            "banner_image": restaurant.banner_image.url if restaurant.banner_image else None,
            "gallery_images": restaurant.gallery_images[:5],  # Limit gallery images
            "amenities": restaurant.amenities,
            "overall_rating": float(restaurant.overall_rating),
            "total_reviews": restaurant.total_reviews,
            "delivery_time": self.calculate_delivery_time(restaurant),
            "reservation_enabled": restaurant.reservation_enabled,
            "loyalty_enabled": self.has_loyalty_enabled(restaurant),
            "operating_hours": main_branch.operating_hours if main_branch else {},
            "contact_info": {
                "phone": restaurant.phone_number,
                "email": restaurant.email,
                "website": restaurant.website,
                "address": str(any_branch.address) if any_branch else None
            },
            "is_featured": restaurant.is_featured,
            "is_verified": restaurant.is_verified
        }
    
    def get_special_offers_data(self, restaurant, request):
        """
        Get active special offers with user-specific context
        """
        offers = list(restaurant.special_offers.all())
        
        return EnhancedSpecialOfferSerializer(
            offers,
            many=True,
            context={'request': request}
        ).data
    
    def get_menu_preview_data(self, restaurant, request):
        """
        Get optimized menu preview data
        """
        # Get featured categories with their items
        featured_categories = restaurant.menu_categories.filter(
            is_featured=True
        )[:5]  # Limit to 5 featured categories
        
        categories_data = MenuCategoryHomeSerializer(
            featured_categories,
            many=True,
            context={'request': request}
        ).data
        
        # Get popular items across all categories (top 6)
        popular_items = MenuItem.objects.filter(
            category__restaurant=restaurant,
            is_available=True
        ).order_by('-popularity_score')[:6]
        
        popular_items_data = FeaturedItemSerializer(
            popular_items,
            many=True,
            context={'request': request}
        ).data
        
        return {
            "featured_categories": categories_data,
            "popular_items": popular_items_data,
            "total_categories": restaurant.menu_categories.count(),
            "total_items": MenuItem.objects.filter(
                category__restaurant=restaurant,
                is_available=True
            ).count()
        }
    
    def get_reservation_info(self, restaurant):
        """
        Get reservation availability information
        """
        if not restaurant.reservation_enabled:
            return {"has_reservations": False}
        
        # Check table availability for today
        from django.utils import timezone
        from datetime import datetime, timedelta
        
        today = timezone.now().date()
        available_tables = Table.objects.filter(
            restaurant=restaurant,
            is_available=True
        ).exists()
        
        # Get next available time slots (simplified - in production, use proper slot finding)
        next_slots = self.find_next_available_slots(restaurant, today)
        
        return {
            "has_reservations": True,
            "next_available_slots": next_slots,
            "party_size_limits": {
                "min": restaurant.min_party_size,
                "max": restaurant.max_party_size
            },
            "today_availability": available_tables and len(next_slots) > 0,
            "requires_confirmation": restaurant.requires_confirmation,
            "deposit_required": restaurant.deposit_required,
            "deposit_amount": float(restaurant.deposit_amount) if restaurant.deposit_required else 0
        }
    
    def get_reviews_preview_data(self, restaurant):
        """
        Get reviews summary and featured reviews
        """
        # Get rating breakdown from aggregate if available
        rating_stats = restaurant.get_rating_stats()
        
        # Get featured reviews (verified purchases with photos)
        featured_reviews = RestaurantReview.objects.filter(
            restaurant=restaurant,
            status='approved',
            is_verified_purchase=True
        ).select_related(
            'customer__user'
        ).prefetch_related(
            'response'
        ).order_by('-helpful_count', '-created_at')[:3]
        
        featured_reviews_data = []
        for review in featured_reviews:
            featured_reviews_data.append({
                "id": review.review_id,
                "customer_name": review.customer.user.get_full_name() or review.customer.user.username,
                "rating": float(review.overall_rating),
                "comment": review.comment,
                "created_at": review.created_at,
                "photos": review.photos[:2],  # Limit photos
                "helpful_count": review.helpful_count,
                "owner_response": review.response.comment if hasattr(review, 'response') else None
            })
        
        return {
            "average_rating": rating_stats.get('average_rating', 0),
            "total_reviews": rating_stats.get('total_ratings', 0),
            "rating_breakdown": rating_stats.get('rating_distribution', {}),
            "featured_reviews": featured_reviews_data
        }
    
    def get_loyalty_info(self, restaurant):
        """
        Get loyalty program information
        """
        try:
            loyalty_settings = restaurant.loyalty_settings.get(
                program__is_active=True
            )
            
            if not loyalty_settings.is_loyalty_active():
                return {"enabled": False}
            
            return {
                "enabled": True,
                "points_per_dollar": float(loyalty_settings.effective_points_rate),
                "signup_bonus": loyalty_settings.effective_signup_bonus,
                "minimum_order_amount": float(loyalty_settings.minimum_order_amount_for_points),
                "allow_point_redemption": loyalty_settings.allow_point_redemption,
                "allow_reward_redemption": loyalty_settings.allow_reward_redemption
            }
            
        except RestaurantLoyaltySettings.DoesNotExist:
            return {"enabled": False}
    
    def get_operational_info(self, restaurant):
        """
        Get current operational status
        """
        open_branches = [
            branch for branch in restaurant.branches.all() 
            if branch.is_active and branch.is_open_now()
        ]
        
        return {
            "is_open_now": len(open_branches) > 0,
            "open_branches_count": len(open_branches),
            "delivery_available": any(
                branch.operating_hours for branch in open_branches
            ),
            "pickup_available": True,  # Assuming always available if open
            "current_wait_time": self.calculate_current_wait_time(restaurant)
        }
    
    # Helper methods
    def calculate_delivery_time(self, restaurant):
        """
        Calculate estimated delivery time based on restaurant data
        """
        # Simple calculation - in production, use more sophisticated logic
        base_time = 30  # minutes
        popularity_factor = min(restaurant.total_reviews / 100, 20)  # Add up to 20 min for popular restaurants
        return base_time + popularity_factor
    
    def has_loyalty_enabled(self, restaurant):
        """
        Check if loyalty is enabled for this restaurant
        """
        try:
            return restaurant.loyalty_settings.get(
                program__is_active=True
            ).is_loyalty_active()
        except RestaurantLoyaltySettings.DoesNotExist:
            return False
    
    def find_next_available_slots(self, restaurant, date):
        """
        Find next available reservation slots (simplified implementation)
        """
        # This is a simplified version - in production, implement proper slot finding
        from datetime import datetime, timedelta
        
        slots = []
        current_time = datetime.now()
        
        # Generate sample slots for the next 2 hours
        for i in range(1, 5):
            slot_time = current_time + timedelta(hours=i)
            # Round to nearest 15 minutes
            minutes = (slot_time.minute // 15) * 15
            slot_time = slot_time.replace(minute=minutes, second=0, microsecond=0)
            
            slots.append(slot_time.isoformat())
            
            if len(slots) >= 3:  # Return max 3 slots
                break
        
        return slots
    
    def calculate_current_wait_time(self, restaurant):
        """
        Calculate current wait time based on restaurant activity
        """
        # Simple calculation - in production, use order queue data
        base_prep_time = 15
        busy_factor = min(restaurant.total_reviews / 50, 15)  # Add up to 15 min for busy restaurants
        return base_prep_time + busy_factor