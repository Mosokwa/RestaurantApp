from datetime import timedelta
import logging
import json
from django.utils import timezone
from rest_framework import viewsets, status
from api.recommendation_engine import RecommendationEngine
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from ..models import Recommendation, Order, UserBehavior, UserPreference, Restaurant, MenuItem
from ..serializers import (
    PreferenceUpdateSerializer, RecommendationResponseSerializer, TrendingRecommendationSerializer, UserBehaviorSerializer, UserPreferenceSerializer
)

logger = logging.getLogger(__name__)

class UserBehaviorViewSet(viewsets.ModelViewSet):
    """
    API endpoint for tracking user behaviors
    """
    serializer_class = UserBehaviorSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return UserBehavior.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class UserPreferenceView(APIView):
    """
    API endpoint for user preferences
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get user preferences"""
        try:
            preferences = UserPreference.objects.get(user=request.user)
            serializer = UserPreferenceSerializer(preferences)
            return Response(serializer.data)
        except UserPreference.DoesNotExist:
            # Calculate preferences if they don't exist
            engine = RecommendationEngine()
            preferences = engine.calculate_user_preferences(request.user)
            serializer = UserPreferenceSerializer(preferences)
            return Response(serializer.data)
    
    def post(self, request):
        """Update user preferences (manual overrides)"""
        serializer = PreferenceUpdateSerializer(data=request.data)
        
        if serializer.is_valid():
            preferences, created = UserPreference.objects.get_or_create(user=request.user)
            
            # Update explicit preferences
            if 'cuisine_preferences' in serializer.validated_data:
                preferences.cuisine_scores.update(serializer.validated_data['cuisine_preferences'])
            
            if 'dietary_preferences' in serializer.validated_data:
                preferences.dietary_weights.update(serializer.validated_data['dietary_preferences'])
            
            preferences.save()
            
            # Log this as explicit preference behavior
            UserBehavior.objects.create(
                user=request.user,
                behavior_type='rating',
                value=5.0,  # High weight for explicit preferences
                metadata={'type': 'explicit_preference_update', 'data': serializer.validated_data}
            )
            
            return Response({'status': 'preferences_updated'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class PersonalizedRecommendationView(APIView):
    """
    Get personalized restaurant recommendations based on user behavior
    Uses the existing UserBehavior model to generate recommendations
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            user = request.user
            limit = int(request.query_params.get('limit', 20))
            
            # Get location from query params if available
            location_context = {
                'lat': request.query_params.get('lat'),
                'lng': request.query_params.get('lng'),
                'city': request.query_params.get('city')
            }
            
            # Get recommendations
            recommendations = self._get_personalized_recommendations(user, limit)
            
            # Serialize with proper context - FIX: Pass request parameter
            serialized_items = self._serialize_recommendations(
                recommendations, 
                request,  # Pass the entire request object
                location_context
            )
            
            return Response({
                'recommendations': serialized_items,
                'total': len(serialized_items),
                'based_on': self._get_recommendation_basis(user)
            })
            
        except Exception as e:
            logger.error(f"Error getting personalized recommendations: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Failed to get recommendations'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_personalized_recommendations(self, user, limit):
        """Get personalized recommendations based on user behavior history"""
        from django.db.models import Count, Q, OuterRef, Subquery
        from ..models import Restaurant, UserBehavior
        
        # Get user's behavior history (last 100 interactions)
        user_behaviors = UserBehavior.objects.filter(
            user=user
        ).select_related('restaurant', 'menu_item').order_by('-created_at')[:100]
        
        if not user_behaviors.exists():
            # No history - return popular restaurants
            return Restaurant.objects.filter(
                status='active',
                is_verified=True
            ).order_by('-overall_rating', '-total_reviews')[:limit]
        
        # Extract preferences from behavior
        viewed_restaurants = set()
        ordered_restaurants = set()
        favorite_restaurants = set()
        cuisine_preferences = {}
        
        for behavior in user_behaviors:
            if behavior.restaurant:
                if behavior.behavior_type == 'view':
                    viewed_restaurants.add(behavior.restaurant.restaurant_id)
                elif behavior.behavior_type == 'order':
                    ordered_restaurants.add(behavior.restaurant.restaurant_id)
                elif behavior.behavior_type == 'favorite':
                    favorite_restaurants.add(behavior.restaurant.restaurant_id)
                
                # Track cuisine preferences from viewed/ordered restaurants
                for cuisine in behavior.restaurant.cuisines.all():
                    cuisine_preferences[cuisine.cuisine_id] = (
                        cuisine_preferences.get(cuisine.cuisine_id, 0) + 1
                    )
        
        # Build recommendation query
        queryset = Restaurant.objects.filter(
            status='active',
            is_verified=True
        ).exclude(
            restaurant_id__in=viewed_restaurants  # Don't recommend already viewed
        )
        
        # Prioritize based on user preferences
        if cuisine_preferences:
            # Get top cuisines
            top_cuisines = sorted(
                cuisine_preferences.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5]
            cuisine_ids = [c[0] for c in top_cuisines]
            
            # Annotate with matching cuisine count
            from django.db.models import Count, Case, When, IntegerField
            
            queryset = queryset.annotate(
                matching_cuisines=Count(
                    Case(
                        When(cuisines__cuisine_id__in=cuisine_ids, then=1),
                        output_field=IntegerField()
                    )
                ),
                preference_score=Count(
                    Case(
                        When(cuisines__cuisine_id__in=cuisine_ids, then=1),
                        output_field=IntegerField()
                    )
                ) * 2 +  # Weighted by cuisine match
                Case(
                    When(restaurant_id__in=favorite_restaurants, then=10),
                    default=0,
                    output_field=IntegerField()
                ) +  # Favorites get +10
                Case(
                    When(restaurant_id__in=ordered_restaurants, then=5),
                    default=0,
                    output_field=IntegerField()
                )  # Ordered from get +5
            ).order_by('-preference_score', '-overall_rating')
        else:
            # Default to popular restaurants
            queryset = queryset.order_by('-overall_rating', '-total_reviews')
        
        return queryset[:limit]
    
    def _serialize_recommendations(self, recommendations, request, location_context):
        """Serialize recommendations with user context"""
        from ..serializers import RestaurantSerializer
        
        result = []
        for restaurant in recommendations:
            # Pass request in serializer context
            serializer = RestaurantSerializer(
                restaurant, 
                context={'request': request}
            )
            data = serializer.data
            
            # Add recommendation reason
            data['recommendation_reason'] = self._get_recommendation_reason(
                restaurant, request.user
            )
            
            # Add distance if location provided
            if location_context.get('lat') and location_context.get('lng'):
                from ..search_utils import SearchUtils
                distances = []
                for branch in restaurant.branches.all():
                    if (branch.address and branch.address.latitude and 
                        branch.address.longitude):
                        dist = SearchUtils.calculate_distance(
                            float(location_context['lat']),
                            float(location_context['lng']),
                            float(branch.address.latitude),
                            float(branch.address.longitude)
                        )
                        if dist:
                            distances.append(dist)
                
                if distances:
                    data['distance_km'] = round(min(distances), 2)
            
            result.append(data)
        
        return result
    
    def _get_recommendation_reason(self, restaurant, user):
        """Generate human-readable reason for recommendation"""
        from ..models import UserBehavior
        
        # Check if based on favorite
        if UserBehavior.objects.filter(
            user=user,
            restaurant=restaurant,
            behavior_type='favorite'
        ).exists():
            return "Based on your favorites"
        
        # Check if based on cuisine preference
        recent_cuisines = UserBehavior.objects.filter(
            user=user,
            behavior_type__in=['view', 'order']
        ).exclude(
            restaurant__isnull=True
        ).values_list('restaurant__cuisines__name', flat=True).distinct()[:3]
        
        matching_cuisines = restaurant.cuisines.filter(
            name__in=recent_cuisines
        ).values_list('name', flat=True)
        
        if matching_cuisines:
            return f"Because you like {', '.join(matching_cuisines[:2])}"
        
        # Check if popular
        if restaurant.total_reviews > 100 and restaurant.overall_rating > 4.5:
            return "Highly rated in your area"
        
        return "Recommended for you"
    
    def _get_recommendation_basis(self, user):
        """Get explanation of how recommendations were generated"""
        from ..models import UserBehavior
        
        recent_count = UserBehavior.objects.filter(
            user=user
        ).count()
        
        if recent_count > 10:
            return f"Based on your {recent_count} interactions"
        elif recent_count > 0:
            return "Based on your recent activity"
        else:
            return "Based on popular restaurants in your area"

class TrendingRecommendationView(APIView):
    """
    API endpoint for trending recommendations
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get trending recommendations"""
        limit = int(request.query_params.get('limit', 10))
        period = request.query_params.get('period', 'weekly')
        location_context = self._get_location_context(request)
        
        engine = RecommendationEngine()
        recommendations = engine.get_trending_recommendations(
            request.user, limit, location_context
        )
        
        # Convert to serializable format
        serialized_items = self._serialize_recommendations(recommendations, request.user, location_context)
        
        response_data = {
            'period': period,
            'items': serialized_items,
            'growth_metrics': self._calculate_growth_metrics(recommendations)
        }
        
        serializer = TrendingRecommendationSerializer(response_data)
        return Response(serializer.data)
    
    def _get_location_context(self, request):
        """Extract location context (same as personalized view)"""
        # Implementation similar to PersonalizedRecommendationView
        location_context = {}
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        
        if lat and lng:
            try:
                location_context['latitude'] = float(lat)
                location_context['longitude'] = float(lng)
            except (ValueError, TypeError):
                pass
        
        return location_context
    
    def _serialize_recommendations(self, recommendations, user, location_context, request):
        """Convert recommendation objects to serializable format"""
        # Implementation similar to PersonalizedRecommendationView
        serialized_items = []
        
        for rec in recommendations:
            item_data = {
                'item_id': rec['item'].item_id,
                'name': rec['item'].name,
                'type': rec['type'],
                'description': rec['item'].description,
                'price': rec['item'].price,
                'restaurant_name': rec['item'].category.restaurant.name,
                'restaurant_id': rec['item'].category.restaurant.restaurant_id,
                'score': rec['score'],
                'reasons': [rec.get('reason', 'Trending item')],
                'algorithms': [rec.get('algorithm', 'trending')],
            }
            
            if rec['item'].image:
                item_data['image'] = request.build_absolute_uri(rec['item'].image.url)
            
            serialized_items.append(item_data)
        
        return serialized_items
    
    def _calculate_growth_metrics(self, recommendations):
        """Calculate overall growth metrics for trending items"""
        if not recommendations:
            return {}
        
        avg_growth = sum(rec['score'] for rec in recommendations) / len(recommendations)
        max_growth = max(rec['score'] for rec in recommendations)
        
        return {
            'average_growth_rate': avg_growth,
            'max_growth_rate': max_growth,
            'total_trending_items': len(recommendations)
        }
    
class SimilarItemsView(APIView):
    """
    API endpoint for getting items similar to a specific item
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, item_id):
        """Get items similar to the specified item"""
        item_type = request.query_params.get('type', 'menu_item')
        limit = int(request.query_params.get('limit', 5))
        
        engine = RecommendationEngine()
        
        if item_type == 'menu_item':
            similar_items = engine.get_similar_items(item_id, item_type, limit)
            
            # Serialize the results
            serialized_items = []
            for item_data in similar_items:
                item = item_data['item']
                serialized_items.append({
                    'item_id': item.item_id,
                    'name': item.name,
                    'description': item.description,
                    'price': float(item.price),
                    'restaurant_name': item.category.restaurant.name,
                    'restaurant_id': item.category.restaurant.restaurant_id,
                    'similarity_score': float(item_data['similarity']),
                    'image': request.build_absolute_uri(item.image.url) if item.image else None
                })
            
            return Response({
                'original_item_id': item_id,
                'similar_items': serialized_items
            })
        
        return Response({'error': 'Only menu_item type is currently supported'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
class TrackUserBehaviorView(APIView):
    """
    Track user interactions for personalization
    Maps frontend events to the UserBehavior model structure
    """
    permission_classes = [IsAuthenticated]  # Most tracking requires auth
    
    # Mapping from frontend event types to model behavior_type
    EVENT_TYPE_MAPPING = {
        'page_view': 'view',
        'restaurant_view': 'view',
        'restaurant_click': 'view',
        'menu_item_view': 'view',
        'search': 'search',
        'filter_apply': 'search',
        'order_placed': 'order',
        'add_to_favorites': 'favorite',
        'remove_from_favorites': 'favorite',
        'rating_submitted': 'rating'
    }
    
    def post(self, request):
        """
        Expected payload can be flexible - we'll map it to our model
        """
        try:
            data = request.data
            user = request.user
            
            # Get the frontend event type
            frontend_event = data.get('event_type')
            if not frontend_event:
                return Response(
                    {'error': 'event_type is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Map to model behavior_type
            behavior_type = self.EVENT_TYPE_MAPPING.get(frontend_event)
            if not behavior_type:
                logger.warning(f"Unmapped event type: {frontend_event}")
                behavior_type = 'view'  # Default to view
            
            # Handle restaurant reference
            restaurant = None
            restaurant_id = data.get('restaurant_id') or data.get('restaurantId')
            if restaurant_id:
                try:
                    restaurant = Restaurant.objects.get(restaurant_id=restaurant_id)
                except Restaurant.DoesNotExist:
                    logger.warning(f"Restaurant not found: {restaurant_id}")
            
            # Handle menu item reference
            menu_item = None
            menu_item_id = data.get('menu_item_id') or data.get('menuItemId')
            if menu_item_id:
                try:
                    menu_item = MenuItem.objects.get(item_id=menu_item_id)
                except MenuItem.DoesNotExist:
                    logger.warning(f"Menu item not found: {menu_item_id}")
            
            # Extract value for ratings or order values
            value = None
            if behavior_type == 'rating':
                value = data.get('rating') or data.get('value')
            elif behavior_type == 'order':
                value = data.get('order_value') or data.get('value')
            
            # Build metadata - store original event and any additional context
            metadata = {
                'original_event': frontend_event,
                'timestamp': data.get('timestamp') or timezone.now().isoformat(),
                'source': 'restaurant_explorer',
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'session_id': request.session.session_key
            }
            
            # Add any additional metadata from request
            if data.get('metadata'):
                if isinstance(data['metadata'], dict):
                    metadata.update(data['metadata'])
                elif isinstance(data['metadata'], str):
                    try:
                        metadata.update(json.loads(data['metadata']))
                    except:
                        metadata['metadata_string'] = data['metadata']
            
            # Add search query if present
            if data.get('search_query') or data.get('query'):
                metadata['search_query'] = data.get('search_query') or data.get('query')
            
            # Add filter information
            if data.get('filters') or data.get('filter_type'):
                metadata['filters'] = {
                    'type': data.get('filter_type'),
                    'value': data.get('filter_value')
                }
            
            # Create the behavior record
            behavior = UserBehavior.objects.create(
                user=user,
                restaurant=restaurant,
                menu_item=menu_item,
                behavior_type=behavior_type,
                value=value,
                metadata=metadata,
                created_at=timezone.now()
            )
            
            logger.info(f"Tracked behavior: {frontend_event} -> {behavior_type} for user {user.id}")
            
            return Response({
                'status': 'success',
                'behavior_id': behavior.behavior_id,
                'mapped_type': behavior_type
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error tracking behavior: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Failed to track behavior'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AnonymousTrackUserBehaviorView(APIView):
    """
    Track anonymous user behavior (no authentication required)
    Stores with null user, can be linked later if user signs up
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            data = request.data
            frontend_event = data.get('event_type')
            
            if not frontend_event:
                return Response(
                    {'error': 'event_type is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Map to model behavior_type
            behavior_type = TrackUserBehaviorView.EVENT_TYPE_MAPPING.get(frontend_event, 'view')
            
            # Build metadata with anonymous session info
            metadata = {
                'original_event': frontend_event,
                'timestamp': data.get('timestamp') or timezone.now().isoformat(),
                'source': 'restaurant_explorer',
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'session_id': request.session.session_key or 'anonymous',
                'anonymous': True
            }
            
            # Add any additional metadata
            if data.get('metadata'):
                if isinstance(data['metadata'], dict):
                    metadata.update(data['metadata'])
            
            # Create behavior with null user
            behavior = UserBehavior.objects.create(
                user=None,  # Anonymous user
                behavior_type=behavior_type,
                metadata=metadata,
                created_at=timezone.now()
            )
            
            # Store session ID in metadata for later linking
            if request.session.session_key:
                request.session['anonymous_behavior_ids'] = (
                    request.session.get('anonymous_behavior_ids', []) + [behavior.behavior_id]
                )
            
            return Response({
                'status': 'success',
                'behavior_id': behavior.behavior_id
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error tracking anonymous behavior: {str(e)}")
            return Response(
                {'error': 'Failed to track behavior'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )