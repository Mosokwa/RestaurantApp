from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.shortcuts import get_object_or_404
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
import logging

logger = logging.getLogger(__name__)
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
    ViewSet for restaurant homepage data
    URL: /api/routes/restaurant-homepage/{restaurant_id}/homepage/
    """
    permission_classes = [AllowAny]
    
    @action(detail=True, methods=['get'], url_path='homepage')
    def homepage(self, request, pk=None):
        """Get comprehensive homepage data for a restaurant"""
        try:
            from ..models import Restaurant, MenuCategory, MenuItem, SpecialOffer
            
            # Fetch restaurant - using status='active' instead of is_active
            restaurant = get_object_or_404(Restaurant, restaurant_id=pk, status='active')
            
            # Get branch for address info (first active branch)
            branch = restaurant.branches.filter(is_active=True).first()
            address = branch.address if branch else None
            
            # Build response data
            response_data = {
                'restaurant': {
                    'restaurant_id': restaurant.restaurant_id,
                    'name': restaurant.name,
                    'description': restaurant.description or '',
                    'story_description': restaurant.story_description or '',
                    'logo': restaurant.logo.url if restaurant.logo else None,
                    'banner_image': restaurant.banner_image.url if restaurant.banner_image else None,
                    'gallery_images': restaurant.gallery_images or [],
                    'amenities': restaurant.amenities or [],
                    'phone_number': restaurant.phone_number,
                    'email': restaurant.email,
                    'website': restaurant.website or '',
                    'overall_rating': float(restaurant.overall_rating),
                    'total_reviews': restaurant.total_reviews,
                    'is_featured': restaurant.is_featured,
                    'is_verified': restaurant.is_verified,
                    'reservation_enabled': restaurant.reservation_enabled,
                    'status': restaurant.status,
                    'contact_info': {
                        'phone': restaurant.phone_number,
                        'email': restaurant.email,
                        'website': restaurant.website or '',
                        'address': str(address) if address else None
                    },
                    'cuisines': [
                        {'cuisine_id': c.cuisine_id, 'name': c.name} 
                        for c in restaurant.cuisines.all()
                    ],
                },
                'special_offers': [],
                'menu_preview': {
                    'featured_categories': [],
                    'popular_items': []
                },
                'reservation_info': {
                    'has_reservations': restaurant.reservation_enabled,
                    'party_size_limits': {
                        'min': restaurant.min_party_size,
                        'max': restaurant.max_party_size
                    },
                    'deposit_required': restaurant.deposit_required,
                    'deposit_amount': float(restaurant.deposit_amount) if restaurant.deposit_required else 0,
                    'requires_confirmation': restaurant.requires_confirmation
                },
                'reviews_preview': {
                    'average_rating': float(restaurant.overall_rating),
                    'total_reviews': restaurant.total_reviews,
                    'rating_breakdown': {}
                },
                'loyalty_info': {
                    'enabled': False
                },
                'operational_info': {
                    'is_open_now': self._check_if_open(restaurant),
                    'current_wait_time': self._calculate_wait_time(restaurant)
                }
            }
            
            # Get featured categories (using is_active field from MenuCategory)
            try:
                featured_categories = MenuCategory.objects.filter(
                    restaurant=restaurant,
                    is_active=True,
                    is_featured=True
                ).order_by('display_order')[:5]
                
                response_data['menu_preview']['featured_categories'] = [
                    {
                        'category_id': cat.category_id,
                        'name': cat.name,
                        'description': cat.description or '',
                        'display_order': cat.display_order,
                        'is_featured': cat.is_featured,
                        'item_count': cat.menu_items.filter(is_available=True).count()
                    }
                    for cat in featured_categories
                ]
            except Exception as e:
                logger.warning(f"Error fetching categories: {str(e)}")
            
            # Get popular items (using is_available field from MenuItem)
            try:
                popular_items = MenuItem.objects.filter(
                    category__restaurant=restaurant,
                    is_available=True
                ).order_by('-popularity_score')[:6]
                
                response_data['menu_preview']['popular_items'] = [
                    {
                        'item_id': item.item_id,
                        'name': item.name,
                        'description': item.description or '',
                        'price': float(item.price),
                        'image': item.image.url if item.image else None,
                        'popularity_score': item.popularity_score,
                        'preparation_time': item.preparation_time,
                        'is_vegetarian': item.is_vegetarian,
                        'is_vegan': item.is_vegan,
                        'is_gluten_free': item.is_gluten_free,
                        'is_spicy': item.is_spicy,
                        'is_available': item.is_available,
                        'is_featured': item.is_featured,
                    }
                    for item in popular_items
                ]
            except Exception as e:
                logger.warning(f"Error fetching popular items: {str(e)}")
            
            # Get special offers
            try:
                now = timezone.now()
                offers = SpecialOffer.objects.filter(
                    restaurant=restaurant,
                    is_active=True,
                    valid_from__lte=now,
                    valid_until__gte=now
                ).order_by('-display_priority', '-created_at')[:5]
                
                response_data['special_offers'] = [
                    {
                        'offer_id': offer.offer_id,
                        'title': offer.title,
                        'description': offer.description or '',
                        'offer_type': offer.offer_type,
                        'discount_value': float(offer.discount_value),
                        'min_order_amount': float(offer.min_order_amount),
                        'image': offer.image.url if offer.image else None,
                        'is_featured': offer.is_featured,
                    }
                    for offer in offers
                ]
            except Exception as e:
                logger.warning(f"Error fetching offers: {str(e)}")
            
            # Get loyalty info
            try:
                from ..models import RestaurantLoyaltySettings
                loyalty_settings = RestaurantLoyaltySettings.objects.filter(
                    restaurant=restaurant,
                    is_loyalty_enabled=True
                ).select_related('program').first()
                
                if loyalty_settings and loyalty_settings.is_loyalty_active():
                    response_data['loyalty_info'] = {
                        'enabled': True,
                        'points_per_dollar': float(loyalty_settings.effective_points_rate),
                        'signup_bonus': loyalty_settings.effective_signup_bonus,
                        'minimum_order_amount': float(loyalty_settings.minimum_order_amount_for_points),
                        'allow_point_redemption': loyalty_settings.allow_point_redemption,
                        'allow_reward_redemption': loyalty_settings.allow_reward_redemption
                    }
            except Exception as e:
                logger.warning(f"Error fetching loyalty settings: {str(e)}")
            
            # Cache the response for 5 minutes
            cache_key = f"restaurant_homepage_{pk}"
            cache.set(cache_key, response_data, 300)
            
            return Response(response_data)
            
        except Restaurant.DoesNotExist:
            return Response(
                {'error': 'Restaurant not found', 'detail': f'No restaurant found with id {pk}'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error in restaurant homepage view: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Failed to load homepage data', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _check_if_open(self, restaurant):
        """Check if restaurant is currently open based on branches' operating hours"""
        try:
            now = timezone.now()
            current_day = now.strftime('%A').lower()
            current_time = now.strftime('%H:%M')
            
            for branch in restaurant.branches.filter(is_active=True):
                hours = branch.operating_hours or {}
                day_hours = hours.get(current_day, {})
                open_time = day_hours.get('open', '')
                close_time = day_hours.get('close', '')
                
                if open_time and close_time and open_time <= current_time <= close_time:
                    return True
            return False
        except Exception:
            return True  # Default to open if can't determine
    
    def _calculate_wait_time(self, restaurant):
        """Calculate estimated wait time based on restaurant activity"""
        try:
            from ..models import Order
            # Count recent active orders
            active_orders = Order.objects.filter(
                restaurant=restaurant,
                status__in=['confirmed', 'preparing']
            ).count()
            
            if active_orders > 10:
                return 45
            elif active_orders > 5:
                return 30
            elif active_orders > 0:
                return 15
            return None
        except Exception:
            return None