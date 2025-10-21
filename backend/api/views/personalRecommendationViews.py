from datetime import timedelta
from django.utils import timezone
from rest_framework import viewsets, status
from api.recommendation_engine import RecommendationEngine
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from ..models import Recommendation, Order, UserBehavior, UserPreference, Restaurant, MenuItem
from ..serializers import (
    PreferenceUpdateSerializer, RecommendationResponseSerializer, TrendingRecommendationSerializer, UserBehaviorSerializer, UserPreferenceSerializer
)

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
    API endpoint for personalized recommendations
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get personalized recommendations for the user"""
        limit = int(request.query_params.get('limit', 10))
        location_context = self._get_location_context(request)
        
        engine = RecommendationEngine()
        recommendations = engine.get_personalized_recommendations(
            request.user, limit, location_context
        )
        
        # Convert to serializable format
        serialized_items = self._serialize_recommendations(recommendations, request.user, location_context)
        
        response_data = {
            'user_id': request.user.id,
            'recommendation_type': 'personalized',
            'items': serialized_items,
            'generated_at': timezone.now(),
            'expires_at': timezone.now() + timedelta(hours=24)  # Recommendations expire in 24 hours
        }
        
        # Store the recommendation for future reference
        self._store_recommendation(request.user, 'personalized', recommendations)
        
        serializer = RecommendationResponseSerializer(response_data)
        return Response(serializer.data)
    
    def _get_location_context(self, request):
        """Extract location context from request"""
        location_context = {}
        
        # Try to get location from query params
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        
        if lat and lng:
            try:
                location_context['latitude'] = float(lat)
                location_context['longitude'] = float(lng)
            except (ValueError, TypeError):
                pass
        
        # Try to get location from user's last order or profile
        if not location_context:
            last_order = Order.objects.filter(customer__user=request.user).last()
            if last_order and last_order.delivery_address:
                # Extract coordinates from address if available
                pass
        
        return location_context
    
    def _serialize_recommendations(self, recommendations, user, location_context, request):
        """Convert recommendation objects to serializable format"""
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
                'reasons': rec.get('reasons', [rec.get('reason', 'Recommended for you')]),
                'algorithms': rec.get('algorithms', [rec.get('algorithm', 'unknown')]),
            }
            
            # Add image if available
            if rec['item'].image:
                item_data['image'] = request.build_absolute_uri(rec['item'].image.url)
            
            # Calculate distance if location context is available
            if location_context and location_context.get('latitude') and location_context.get('longitude'):
                from ..search_utils import SearchUtils
                distance = SearchUtils.calculate_distance(
                    location_context['latitude'], location_context['longitude'],
                    rec['item'].category.restaurant.latitude, rec['item'].category.restaurant.longitude
                )
                item_data['distance_km'] = distance
            
            serialized_items.append(item_data)
        
        return serialized_items
    
    def _store_recommendation(self, user, rec_type, recommendations):
        """Store the generated recommendation in the database"""
        # Extract restaurant and menu item IDs
        restaurant_ids = set()
        menu_item_ids = set()
        scores = {}
        
        for rec in recommendations:
            if rec['type'] == 'menu_item':
                menu_item_ids.add(rec['item'].item_id)
                scores[f"menu_item_{rec['item'].item_id}"] = rec['score']
                restaurant_ids.add(rec['item'].category.restaurant.restaurant_id)
        
        # Create recommendation record
        recommendation = Recommendation.objects.create(
            user=user,
            recommendation_type=rec_type,
            scores=scores,
            expires_at=timezone.now() + timedelta(hours=24)
        )
        
        # Add related items
        if restaurant_ids:
            recommendation.recommended_restaurants.add(*restaurant_ids)
        if menu_item_ids:
            recommendation.recommended_menu_items.add(*menu_item_ids)
        
        return recommendation

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
    API endpoint for tracking user behaviors
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Track a user behavior (view, click, etc.)"""
        behavior_type = request.data.get('behavior_type')
        restaurant_id = request.data.get('restaurant_id')
        menu_item_id = request.data.get('menu_item_id')
        value = request.data.get('value')
        metadata = request.data.get('metadata', {})
        
        # Validate behavior type
        valid_types = [choice[0] for choice in UserBehavior.BEHAVIOR_TYPES]
        if behavior_type not in valid_types:
            return Response(
                {'error': f'Invalid behavior type. Must be one of: {", ".join(valid_types)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create behavior record
        behavior_data = {
            'user': request.user,
            'behavior_type': behavior_type,
            'value': value,
            'metadata': metadata
        }
        
        if restaurant_id:
            try:
                behavior_data['restaurant'] = Restaurant.objects.get(pk=restaurant_id)
            except Restaurant.DoesNotExist:
                return Response(
                    {'error': 'Restaurant not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        if menu_item_id:
            try:
                behavior_data['menu_item'] = MenuItem.objects.get(pk=menu_item_id)
            except MenuItem.DoesNotExist:
                return Response(
                    {'error': 'Menu item not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        behavior = UserBehavior.objects.create(**behavior_data)
        
        # Trigger preference recalculation for significant behaviors
        if behavior_type in ['order', 'rating', 'favorite']:
            try:
                engine = RecommendationEngine()
                engine.calculate_user_preferences(request.user)
            except Exception as e:
                # Log but don't fail the request
                print(f"Preference recalculation failed: {e}")
        
        return Response({
            'status': 'behavior_tracked',
            'behavior_id': behavior.behavior_id
        }, status=status.HTTP_201_CREATED)