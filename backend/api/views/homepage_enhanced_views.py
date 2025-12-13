from datetime import timedelta, datetime, time as datetime_time
from django.utils import timezone
from django.db.models import Q, Avg, F, ExpressionWrapper, DurationField
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from django.db import models

from ..models import (
    Restaurant, MenuItem, UserBehavior, Customer,
    PopularCategory, Order
)
from ..serializers import (
    RestaurantSearchSerializer, MenuItemSearchSerializer
)
from ..search_utils import RestaurantSearchEngine, SearchUtils


class QuickCategoriesView(APIView):
    """
    Get popular food categories for quick access
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        # Get categories with restaurant count
        categories = PopularCategory.objects.filter(
            is_active=True
        ).prefetch_related('restaurants')
        
        # Format response
        categories_data = []
        for category in categories:
            categories_data.append({
                'id': category.category_id,
                'name': category.name,
                'icon': category.icon,
                'color': category.color,
                'restaurant_count': category.active_restaurant_count,
                'search_query': category.search_query,
                'description': category.description,
                'display_order': category.display_order
            })
        
        # Sort by display_order
        categories_data.sort(key=lambda x: (x.get('display_order', 0), x['name']))
        
        return Response(categories_data)


class NewRestaurantsView(APIView):
    """
    Get newly added restaurants (last 30 days)
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        # Get location from query params
        latitude = request.query_params.get('lat')
        longitude = request.query_params.get('lng')
        city = request.query_params.get('city')
        limit = int(request.query_params.get('limit', 12))
        
        # Calculate date threshold (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        # Base queryset
        new_restaurants = Restaurant.objects.filter(
            status='active',
            created_at__gte=thirty_days_ago,
            branches__is_active=True
        ).distinct().prefetch_related('cuisines', 'branches')
        
        # Apply location filtering
        location_filters = {}
        if latitude and longitude:
            try:
                location_filters = {
                    'latitude': float(latitude),
                    'longitude': float(longitude),
                    'radius_km': 20
                }
            except (ValueError, TypeError):
                pass
        elif city:
            location_filters = {'city': city}
        
        if location_filters:
            search_engine = RestaurantSearchEngine(location_filters)
            restaurant_results, total_count = search_engine.search()
            restaurant_ids = [result['restaurant'].restaurant_id for result in restaurant_results]
            new_restaurants = new_restaurants.filter(restaurant_id__in=restaurant_ids)
        
        # Limit results
        new_restaurants = new_restaurants[:limit]
        
        # Serialize with location context
        context = {'request': request}
        if latitude and longitude:
            try:
                context['user_latitude'] = float(latitude)
                context['user_longitude'] = float(longitude)
            except (ValueError, TypeError):
                pass
        
        serializer = RestaurantSearchSerializer(new_restaurants, many=True, context=context)
        
        # Add newness indicator
        for i, restaurant_data in enumerate(serializer.data):
            restaurant = new_restaurants[i]
            days_ago = (timezone.now() - restaurant.created_at).days
            restaurant_data['new_for_days'] = days_ago
            restaurant_data['is_new'] = days_ago <= 7  # Highlight if less than 1 week old
        
        return Response(serializer.data)


class UserFavoritesView(APIView):
    """
    Get user's favorite restaurants
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        limit = int(request.query_params.get('limit', 12))
        
        # Get favorite restaurant IDs from UserBehavior
        favorite_behaviors = UserBehavior.objects.filter(
            user=user,
            behavior_type='favorite',
            restaurant__isnull=False
        ).order_by('-created_at')
        
        favorite_restaurant_ids = []
        for behavior in favorite_behaviors:
            if behavior.restaurant_id and behavior.restaurant_id not in favorite_restaurant_ids:
                favorite_restaurant_ids.append(behavior.restaurant_id)
        
        # Get restaurants
        favorites = Restaurant.objects.filter(
            restaurant_id__in=favorite_restaurant_ids[:50],  # Limit IDs for query
            status='active'
        ).prefetch_related('cuisines', 'branches')
        
        # Apply location filtering if available
        latitude = request.query_params.get('lat')
        longitude = request.query_params.get('lng')
        city = request.query_params.get('city')
        
        location_filters = {}
        if latitude and longitude:
            try:
                location_filters = {
                    'latitude': float(latitude),
                    'longitude': float(longitude),
                    'radius_km': 50  # Larger radius for favorites
                }
            except (ValueError, TypeError):
                pass
        elif city:
            location_filters = {'city': city}
        
        if location_filters:
            # Sort by distance if location provided
            location_filtered = []
            for restaurant in favorites:
                try:
                    enhanced = SearchUtils.enhance_restaurant_with_location(
                        restaurant, 
                        float(latitude) if latitude else None,
                        float(longitude) if longitude else None
                    )
                    if hasattr(enhanced, 'distance_km') and enhanced.distance_km is not None:
                        location_filtered.append({
                            'restaurant': restaurant,
                            'distance': enhanced.distance_km
                        })
                except:
                    location_filtered.append({
                        'restaurant': restaurant,
                        'distance': float('inf')
                    })
            
            # Sort by distance
            location_filtered.sort(key=lambda x: x['distance'])
            favorites = [item['restaurant'] for item in location_filtered]
        
        # Limit results
        favorites = favorites[:limit]
        
        # Serialize
        context = {'request': request}
        if latitude and longitude:
            try:
                context['user_latitude'] = float(latitude)
                context['user_longitude'] = float(longitude)
            except (ValueError, TypeError):
                pass
        
        serializer = RestaurantSearchSerializer(favorites, many=True, context=context)
        
        # Add favorite metadata
        for i, restaurant_data in enumerate(serializer.data):
            restaurant = favorites[i]
            # Get when user favorited this restaurant
            favorite_behavior = favorite_behaviors.filter(
                restaurant_id=restaurant.restaurant_id
            ).first()
            if favorite_behavior:
                restaurant_data['favorited_at'] = favorite_behavior.created_at
                restaurant_data['is_favorite'] = True
        
        return Response(serializer.data)


class DietaryPicksView(APIView):
    """
    Get restaurants matching user's dietary preferences
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        limit = int(request.query_params.get('limit', 12))
        
        # Get user's dietary preferences
        try:
            customer = Customer.objects.get(user=user)
            dietary_preferences = customer.dietary_preferences or []
        except Customer.DoesNotExist:
            return Response({'error': 'Customer profile not found'}, status=status.HTTP_404_NOT_FOUND)
        
        if not dietary_preferences:
            return Response([])
        
        # Get location
        latitude = request.query_params.get('lat')
        longitude = request.query_params.get('lng')
        city = request.query_params.get('city')
        
        # Base queryset
        restaurants = Restaurant.objects.filter(
            status='active',
            branches__is_active=True
        ).distinct()
        
        # Apply location filtering
        location_filters = {}
        if latitude and longitude:
            try:
                location_filters = {
                    'latitude': float(latitude),
                    'longitude': float(longitude),
                    'radius_km': 20
                }
            except (ValueError, TypeError):
                pass
        elif city:
            location_filters = {'city': city}
        
        if location_filters:
            search_engine = RestaurantSearchEngine(location_filters)
            restaurant_results, total_count = search_engine.search()
            restaurant_ids = [result['restaurant'].restaurant_id for result in restaurant_results]
            restaurants = restaurants.filter(restaurant_id__in=restaurant_ids)
        
        # Calculate dietary match scores
        restaurants_with_scores = []
        for restaurant in restaurants:
            # Get menu items matching dietary preferences
            menu_items = MenuItem.objects.filter(
                category__restaurant=restaurant,
                is_available=True
            )
            
            match_count = 0
            for preference in dietary_preferences:
                if preference.lower() == 'vegetarian':
                    match_count += menu_items.filter(is_vegetarian=True).count()
                elif preference.lower() == 'vegan':
                    match_count += menu_items.filter(is_vegan=True).count()
                elif preference.lower() == 'gluten-free':
                    match_count += menu_items.filter(is_gluten_free=True).count()
            
            if match_count > 0:
                restaurants_with_scores.append({
                    'restaurant': restaurant,
                    'match_count': match_count,
                    'total_items': menu_items.count(),
                    'match_percentage': (match_count / max(menu_items.count(), 1)) * 100
                })
        
        # Sort by match percentage (highest first)
        restaurants_with_scores.sort(key=lambda x: x['match_percentage'], reverse=True)
        
        # Take top matches
        top_restaurants = [item['restaurant'] for item in restaurants_with_scores[:limit]]
        
        # Serialize
        context = {'request': request}
        if latitude and longitude:
            try:
                context['user_latitude'] = float(latitude)
                context['user_longitude'] = float(longitude)
            except (ValueError, TypeError):
                pass
        
        serializer = RestaurantSearchSerializer(top_restaurants, many=True, context=context)
        
        # Add dietary match info
        for i, restaurant_data in enumerate(serializer.data):
            match_info = restaurants_with_scores[i]
            restaurant_data['dietary_match'] = {
                'match_count': match_info['match_count'],
                'match_percentage': round(match_info['match_percentage'], 1),
                'user_preferences': dietary_preferences
            }
        
        return Response(serializer.data)


class RecentlyViewedView(APIView):
    """
    Get user's recently viewed restaurants
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        limit = int(request.query_params.get('limit', 12))
        
        # Get recently viewed restaurants
        recent_views = UserBehavior.objects.filter(
            user=user,
            behavior_type='view',
            restaurant__isnull=False
        ).select_related('restaurant').order_by('-created_at')
        
        # Get unique restaurants (most recent view for each)
        unique_restaurants = []
        seen_ids = set()
        
        for view in recent_views:
            if (view.restaurant_id and 
                view.restaurant_id not in seen_ids and 
                view.restaurant.status == 'active'):
                unique_restaurants.append(view.restaurant)
                seen_ids.add(view.restaurant_id)
            
            if len(unique_restaurants) >= limit * 2:  # Get more for location filtering
                break
        
        # Apply location filtering if available
        latitude = request.query_params.get('lat')
        longitude = request.query_params.get('lng')
        
        if latitude and longitude:
            # Calculate distances and sort
            restaurants_with_distance = []
            for restaurant in unique_restaurants:
                try:
                    enhanced = SearchUtils.enhance_restaurant_with_location(
                        restaurant,
                        float(latitude),
                        float(longitude)
                    )
                    distance = getattr(enhanced, 'distance_km', None)
                    restaurants_with_distance.append({
                        'restaurant': restaurant,
                        'distance': distance or float('inf')
                    })
                except:
                    restaurants_with_distance.append({
                        'restaurant': restaurant,
                        'distance': float('inf')
                    })
            
            # Sort by distance
            restaurants_with_distance.sort(key=lambda x: x['distance'])
            unique_restaurants = [item['restaurant'] for item in restaurants_with_distance]
        
        # Limit results
        unique_restaurants = unique_restaurants[:limit]
        
        # Serialize
        context = {'request': request}
        if latitude and longitude:
            try:
                context['user_latitude'] = float(latitude)
                context['user_longitude'] = float(longitude)
            except (ValueError, TypeError):
                pass
        
        serializer = RestaurantSearchSerializer(unique_restaurants, many=True, context=context)
        
        # Add view metadata
        for i, restaurant_data in enumerate(serializer.data):
            restaurant = unique_restaurants[i]
            # Get last view time
            last_view = recent_views.filter(restaurant=restaurant).first()
            if last_view:
                restaurant_data['last_viewed'] = last_view.created_at
                restaurant_data['view_count'] = recent_views.filter(restaurant=restaurant).count()
        
        return Response(serializer.data)
    
class TimeBasedRecommendationsView(APIView):
    """
    Get recommendations based on time of day - FIXED VERSION
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        # Determine current time period
        current_hour = timezone.now().hour
        time_period = self._get_time_period(current_hour)
        
        # Get location
        latitude = request.query_params.get('lat')
        longitude = request.query_params.get('lng')
        city = request.query_params.get('city')
        limit = int(request.query_params.get('limit', 8))
        
        # Base queryset
        restaurants = Restaurant.objects.filter(
            status='active',
            branches__is_active=True
        ).distinct().prefetch_related('cuisines', 'branches')
        
        # Apply location filtering
        location_filters = {}
        if latitude and longitude:
            try:
                location_filters = {
                    'latitude': float(latitude),
                    'longitude': float(longitude),
                    'radius_km': 15
                }
            except (ValueError, TypeError):
                pass
        elif city:
            location_filters = {'city': city}
        
        if location_filters:
            search_engine = RestaurantSearchEngine(location_filters)
            restaurant_results, total_count = search_engine.search()
            restaurant_ids = [result['restaurant'].restaurant_id for result in restaurant_results]
            restaurants = restaurants.filter(restaurant_id__in=restaurant_ids)
        
        # Filter based on time period
        time_based_restaurants = []
        for restaurant in restaurants:
            if self._is_relevant_for_time_period(restaurant, time_period, current_hour):
                time_based_restaurants.append(restaurant)
            
            if len(time_based_restaurants) >= limit * 2:
                break
        
        # Sort by relevance
        sorted_restaurants = self._sort_by_time_relevance(time_based_restaurants, time_period, current_hour)
        
        # Take top results
        top_restaurants = sorted_restaurants[:limit]
        
        # If not enough matches, fill with popular ones
        if len(top_restaurants) < limit:
            additional_needed = limit - len(top_restaurants)
            # FIXED: Removed '-order_count' - use only '-overall_rating'
            additional = restaurants.exclude(
                restaurant_id__in=[r.restaurant_id for r in top_restaurants]
            ).order_by('-overall_rating')[:additional_needed]
            top_restaurants.extend(list(additional))
        
        # Serialize
        context = {'request': request}
        if latitude and longitude:
            try:
                context['user_latitude'] = float(latitude)
                context['user_longitude'] = float(longitude)
            except (ValueError, TypeError):
                pass
        
        serializer = RestaurantSearchSerializer(top_restaurants, many=True, context=context)
        
        # Add time period info
        for restaurant_data in serializer.data:
            restaurant_data['time_period'] = time_period
            restaurant_data['time_reason'] = self._get_time_reason(time_period)
        
        return Response({
            'time_period': time_period,
            'restaurants': serializer.data,
            'total_count': len(top_restaurants)
        })
    
    def _get_time_period(self, hour):
        if 5 <= hour < 11:
            return 'breakfast'
        elif 11 <= hour < 16:
            return 'lunch'
        elif 16 <= hour < 21:
            return 'dinner'
        else:
            return 'late_night'
    
    def _is_relevant_for_time_period(self, restaurant, time_period, current_hour):
        # Simplified: Just check if any branch is open
        if not any(branch.is_open_now() for branch in restaurant.branches.all() if branch.is_active):
            return False
        
        # Quick keyword check
        menu_items = MenuItem.objects.filter(
            category__restaurant=restaurant,
            is_available=True
        )
        
        keywords = {
            'breakfast': ['breakfast', 'coffee', 'tea', 'pastry', 'bagel'],
            'lunch': ['sandwich', 'salad', 'wrap', 'soup'],
            'dinner': ['steak', 'pasta', 'seafood', 'grill'],
            'late_night': ['pizza', 'burger', 'fries', 'snack']
        }
        
        if time_period in keywords:
            q_objects = Q()
            for keyword in keywords[time_period]:
                q_objects |= Q(name__icontains=keyword)
            return menu_items.filter(q_objects).exists()
        
        return True
    
    def _sort_by_time_relevance(self, restaurants, time_period, current_hour):
        scored_restaurants = []
        
        for restaurant in restaurants:
            score = 0
            
            # Rating boost
            if restaurant.overall_rating:
                score += restaurant.overall_rating * 10
            
            # Open now boost
            if any(branch.is_open_now() for branch in restaurant.branches.all() if branch.is_active):
                score += 20
            
            # Time period specific boost
            if time_period == 'late_night':
                for branch in restaurant.branches.filter(is_active=True):
                    if branch.operating_hours:
                        current_day = timezone.now().strftime('%A').lower()
                        day_hours = branch.operating_hours.get(current_day, {})
                        if day_hours.get('close'):
                            try:
                                close_time = day_hours['close']
                                if ':' in close_time:
                                    closing_hour = int(close_time.split(':')[0])
                                else:
                                    closing_hour = int(close_time)
                                
                                if closing_hour >= 22 or closing_hour <= 4:
                                    score += 30
                            except:
                                pass
            
            scored_restaurants.append({
                'restaurant': restaurant,
                'score': score
            })
        
        scored_restaurants.sort(key=lambda x: x['score'], reverse=True)
        return [item['restaurant'] for item in scored_restaurants]
    
    def _get_time_reason(self, time_period):
        reasons = {
            'breakfast': 'Great for breakfast',
            'lunch': 'Perfect for lunch',
            'dinner': 'Ideal for dinner',
            'late_night': 'Open late'
        }
        return reasons.get(time_period, 'Recommended')




class RestaurantsYouMightLikeView(APIView):
    """
    Recommend restaurants based on user's order history and behavior
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        limit = int(request.query_params.get('limit', 8))
        
        # Get user's order history
        user_orders = Order.objects.filter(
            customer__user=user,
            status='delivered'
        ).prefetch_related('items__menu_item')
        
        # If user has no order history, return empty or popular ones
        if not user_orders.exists():
            # Option 1: Return empty (won't show section)
            # return Response({'recommendations': [], 'message': 'No order history yet'})
            
            # Option 2: Return popular restaurants as "Try these popular spots"
            return self._get_popular_fallback(request, limit)
        
        # Get location
        latitude = request.query_params.get('lat')
        longitude = request.query_params.get('lng')
        city = request.query_params.get('city')
        
        # Get user behaviors
        user_behaviors = UserBehavior.objects.filter(user=user)
        
        # Extract user preferences
        user_preferences = self._extract_user_preferences(user_orders, user_behaviors)
        
        # Find similar restaurants
        similar_restaurants = self._find_similar_restaurants(user_preferences, limit)
        
        # Apply location filtering
        if latitude and longitude:
            try:
                location_filtered = []
                for restaurant in similar_restaurants:
                    enhanced = SearchUtils.enhance_restaurant_with_location(
                        restaurant,
                        float(latitude),
                        float(longitude)
                    )
                    distance = getattr(enhanced, 'distance_km', None)
                    location_filtered.append({
                        'restaurant': restaurant,
                        'distance': distance or float('inf')
                    })
                
                # Sort by distance
                location_filtered.sort(key=lambda x: x['distance'])
                similar_restaurants = [item['restaurant'] for item in location_filtered]
            except:
                pass
        elif city:
            similar_restaurants = [
                r for r in similar_restaurants 
                if r.branches.filter(address__city__icontains=city).exists()
            ]
        
        # Limit results
        similar_restaurants = similar_restaurants[:limit]
        
        # If no similar restaurants found, fallback to popular
        if not similar_restaurants:
            return self._get_popular_fallback(request, limit)
        
        # Serialize
        context = {'request': request}
        if latitude and longitude:
            try:
                context['user_latitude'] = float(latitude)
                context['user_longitude'] = float(longitude)
            except (ValueError, TypeError):
                pass
        
        serializer = RestaurantSearchSerializer(similar_restaurants, many=True, context=context)
        
        # Add recommendation reasons
        for i, restaurant_data in enumerate(serializer.data):
            restaurant = similar_restaurants[i]
            reason = self._get_recommendation_reason(restaurant, user_preferences)
            restaurant_data['recommendation_reason'] = reason
            match_score = self._calculate_match_score(restaurant, user_preferences)
            restaurant_data['match_score'] = match_score
            restaurant_data['has_significant_match'] = match_score > 30  # Only show if meaningful match
        
        return Response({
            'recommendations': serializer.data,
            'total_count': len(similar_restaurants),
            'user_preferences_summary': user_preferences.get('summary', {}),
            'is_personalized': True
        })
    
    def _get_popular_fallback(self, request, limit):
        """Get popular restaurants as fallback for new users"""
        latitude = request.query_params.get('lat')
        longitude = request.query_params.get('lng')
        city = request.query_params.get('city')
        
        # Get popular restaurants
        restaurants = Restaurant.objects.filter(
            status='active',
            is_featured=True,
            branches__is_active=True
        ).order_by('-overall_rating')[:limit]
        
        # Apply location filtering if possible
        if latitude and longitude:
            try:
                location_filtered = []
                for restaurant in restaurants:
                    enhanced = SearchUtils.enhance_restaurant_with_location(
                        restaurant,
                        float(latitude),
                        float(longitude)
                    )
                    distance = getattr(enhanced, 'distance_km', None)
                    location_filtered.append({
                        'restaurant': restaurant,
                        'distance': distance or float('inf')
                    })
                
                location_filtered.sort(key=lambda x: x['distance'])
                restaurants = [item['restaurant'] for item in location_filtered]
            except:
                pass
        
        # Serialize
        context = {'request': request}
        if latitude and longitude:
            try:
                context['user_latitude'] = float(latitude)
                context['user_longitude'] = float(longitude)
            except:
                pass
        
        serializer = RestaurantSearchSerializer(restaurants, many=True, context=context)
        
        # Add fallback reason
        for restaurant_data in serializer.data:
            restaurant_data['recommendation_reason'] = 'Popular spot you might like'
            restaurant_data['match_score'] = 0
            restaurant_data['has_significant_match'] = False
        
        return Response({
            'recommendations': serializer.data,
            'total_count': len(restaurants),
            'user_preferences_summary': {'message': 'Based on popular restaurants'},
            'is_personalized': False  # Flag to indicate this is not personalized
        })
    
    def _extract_user_preferences(self, orders, behaviors):
        """Extract user preferences from orders and behaviors"""
        preferences = {
            'cuisines': {},
            'price_range': {'min': float('inf'), 'max': 0, 'avg': 0},
            'restaurant_types': {},
            'frequently_ordered_items': [],
            'order_times': {}
        }
        
        # Analyze orders
        total_order_value = 0
        order_count = orders.count()
        
        for order in orders:
            # Track cuisines
            for order_item in order.items.all():
                menu_item = order_item.menu_item
                if menu_item:
                    restaurant = menu_item.category.restaurant
                    for cuisine in restaurant.cuisines.all():
                        preferences['cuisines'][cuisine.name] = preferences['cuisines'].get(cuisine.name, 0) + 1
            
            # Track price range
            order_value = float(order.total_amount)
            preferences['price_range']['min'] = min(preferences['price_range']['min'], order_value)
            preferences['price_range']['max'] = max(preferences['price_range']['max'], order_value)
            total_order_value += order_value
            
            # Track order times
            order_hour = order.order_placed_at.hour
            time_period = self._get_time_period(order_hour)
            preferences['order_times'][time_period] = preferences['order_times'].get(time_period, 0) + 1
        
        if order_count > 0:
            preferences['price_range']['avg'] = total_order_value / order_count
        
        # Analyze behaviors
        for behavior in behaviors:
            if behavior.behavior_type == 'favorite' and behavior.restaurant:
                restaurant = behavior.restaurant
                for cuisine in restaurant.cuisines.all():
                    preferences['cuisines'][cuisine.name] = preferences['cuisines'].get(cuisine.name, 0) + 5  # Higher weight for favorites
        
        # Normalize and summarize
        total_cuisine_orders = sum(preferences['cuisines'].values())
        if total_cuisine_orders > 0:
            for cuisine in preferences['cuisines']:
                preferences['cuisines'][cuisine] = preferences['cuisines'][cuisine] / total_cuisine_orders
        
        # Get top preferences
        top_cuisines = sorted(
            preferences['cuisines'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        preferences['summary'] = {
            'top_cuisines': [cuisine for cuisine, score in top_cuisines],
            'avg_order_value': preferences['price_range']['avg'],
            'favorite_time_period': max(preferences['order_times'].items(), key=lambda x: x[1])[0] if preferences['order_times'] else None
        }
        
        return preferences
    
    def _find_similar_restaurants(self, preferences, limit):
        """Find restaurants similar to user's preferences"""
        from django.db.models import Q
        
        # Start with all active restaurants
        restaurants = Restaurant.objects.filter(
            status='active',
            branches__is_active=True
        ).prefetch_related('cuisines')
        
        # Filter by top cuisines if available
        if preferences['summary']['top_cuisines']:
            cuisine_filter = Q()
            for cuisine_name in preferences['summary']['top_cuisines']:
                cuisine_filter |= Q(cuisines__name__icontains=cuisine_name)
            restaurants = restaurants.filter(cuisine_filter).distinct()
        
        # Score restaurants based on match
        scored_restaurants = []
        for restaurant in restaurants:
            score = 0
            
            # Cuisine match
            restaurant_cuisines = [c.name for c in restaurant.cuisines.all()]
            for pref_cuisine, pref_score in preferences['cuisines'].items():
                if any(pref_cuisine.lower() in cuisine.lower() for cuisine in restaurant_cuisines):
                    score += pref_score * 100
            
            # Price range match
            avg_menu_price = MenuItem.objects.filter(
                category__restaurant=restaurant,
                is_available=True
            ).aggregate(avg_price=Avg('price'))['avg_price'] or 0
            
            if preferences['price_range']['avg'] > 0:
                price_diff = abs(float(avg_menu_price) - preferences['price_range']['avg'])
                if price_diff < 10:  # Within $10 range
                    score += 50 - (price_diff * 5)
            
            # Rating boost
            if restaurant.overall_rating:
                score += restaurant.overall_rating * 20
            
            scored_restaurants.append({
                'restaurant': restaurant,
                'score': score
            })
        
        # Sort by score and take top
        scored_restaurants.sort(key=lambda x: x['score'], reverse=True)
        top_scored = scored_restaurants[:limit * 2]  # Get more for location filtering
        
        return [item['restaurant'] for item in top_scored]
    
    def _get_time_period(self, hour):
        """Same as TimeBasedRecommendationsView"""
        if 5 <= hour < 11:
            return 'breakfast'
        elif 11 <= hour < 16:
            return 'lunch'
        elif 16 <= hour < 21:
            return 'dinner'
        else:
            return 'late_night'
    
    def _get_recommendation_reason(self, restaurant, preferences):
        """Generate human-readable recommendation reason"""
        reasons = []
        
        # Cuisine match
        restaurant_cuisines = [c.name for c in restaurant.cuisines.all()]
        for pref_cuisine in preferences['summary']['top_cuisines'][:2]:
            if any(pref_cuisine.lower() in cuisine.lower() for cuisine in restaurant_cuisines):
                reasons.append(f"Similar to your favorite {pref_cuisine} restaurants")
                break
        
        if not reasons:
            reasons.append("Based on your dining preferences")
        
        # Add rating if high
        if restaurant.overall_rating and restaurant.overall_rating >= 4.0:
            reasons.append(f"Highly rated ({restaurant.overall_rating:.1f}⭐)")
        
        return " • ".join(reasons[:2])
    
    def _calculate_match_score(self, restaurant, preferences):
        """Calculate match score percentage"""
        score = 0
        max_score = 0
        
        # Cuisine match (up to 60 points)
        restaurant_cuisines = [c.name.lower() for c in restaurant.cuisines.all()]
        for pref_cuisine, pref_score in preferences['cuisines'].items():
            max_score += 20
            if any(pref_cuisine.lower() in cuisine for cuisine in restaurant_cuisines):
                score += pref_score * 20
        
        # Price match (up to 20 points)
        avg_menu_price = MenuItem.objects.filter(
            category__restaurant=restaurant,
            is_available=True
        ).aggregate(avg_price=Avg('price'))['avg_price'] or 0
        
        if preferences['price_range']['avg'] > 0:
            max_score += 20
            price_diff = abs(float(avg_menu_price) - preferences['price_range']['avg'])
            if price_diff < 20:
                score += 20 - price_diff
        
        # Rating (up to 20 points)
        max_score += 20
        if restaurant.overall_rating:
            score += restaurant.overall_rating * 4
        
        if max_score > 0:
            return min(100, int((score / max_score) * 100))
        return 0


class FastDeliveryRestaurantsView(APIView):
    """
    Get restaurants with fastest delivery times
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        # Get location
        latitude = request.query_params.get('lat')
        longitude = request.query_params.get('lng')
        city = request.query_params.get('city')
        limit = int(request.query_params.get('limit', 8))
        
        # Base queryset
        restaurants = Restaurant.objects.filter(
            status='active',
            branches__is_active=True
        ).prefetch_related('branches')
        
        # Apply location filtering
        location_filters = {}
        if latitude and longitude:
            try:
                location_filters = {
                    'latitude': float(latitude),
                    'longitude': float(longitude),
                    'radius_km': 10
                }
            except (ValueError, TypeError):
                pass
        elif city:
            location_filters = {'city': city}
        
        if location_filters:
            search_engine = RestaurantSearchEngine(location_filters)
            restaurant_results, total_count = search_engine.search()
            restaurant_ids = [result['restaurant'].restaurant_id for result in restaurant_results]
            restaurants = restaurants.filter(restaurant_id__in=restaurant_ids)
        
        # Calculate delivery scores
        restaurants_with_scores = []
        for restaurant in restaurants:
            score = self._calculate_delivery_score(restaurant)
            if score > 0:
                restaurants_with_scores.append({
                    'restaurant': restaurant,
                    'delivery_score': score,
                    'estimated_time': self._estimate_delivery_time(score)
                })
        
        # Sort by delivery score (highest = fastest)
        restaurants_with_scores.sort(key=lambda x: x['delivery_score'], reverse=True)
        
        # Take top results
        top_restaurants = [item['restaurant'] for item in restaurants_with_scores[:limit]]
        
        # Serialize
        context = {'request': request}
        if latitude and longitude:
            try:
                context['user_latitude'] = float(latitude)
                context['user_longitude'] = float(longitude)
            except (ValueError, TypeError):
                pass
        
        serializer = RestaurantSearchSerializer(top_restaurants, many=True, context=context)
        
        # Add delivery info 
        for i, restaurant_data in enumerate(serializer.data):
            score_info = restaurants_with_scores[i]
            estimated_time = score_info['estimated_time']
            restaurant_data['delivery_info'] = {
                'estimated_time': estimated_time,
                'delivery_score': score_info['delivery_score'],
                'is_fast_delivery': self._is_fast_delivery(estimated_time)  # FIXED
            }
        
        return Response({
            'restaurants': serializer.data,
            'total_count': len(top_restaurants)
        })
    
    def _calculate_delivery_score(self, restaurant):
        """Calculate delivery speed score"""
        score = 0
        
        # Base score for being open
        if any(branch.is_open_now() for branch in restaurant.branches.all() if branch.is_active):
            score += 30
        
        # Rating boost (higher rated restaurants often deliver faster)
        if restaurant.overall_rating:
            score += restaurant.overall_rating * 10
        
        # Base popularity score (instead of order_count)
        score += 15
        
        # Preparation time from menu items
        avg_prep_time = MenuItem.objects.filter(
            category__restaurant=restaurant,
            is_available=True
        ).aggregate(avg_prep=Avg('preparation_time'))['avg_prep'] or 20
        
        # Lower prep time = higher score
        if avg_prep_time <= 15:
            score += 30
        elif avg_prep_time <= 25:
            score += 20
        elif avg_prep_time <= 35:
            score += 10
        
        return score
    
    def _estimate_delivery_time(self, score):
        """Estimate delivery time based on score"""
        if score >= 80:
            return "15-25 min"
        elif score >= 60:
            return "25-35 min"
        elif score >= 40:
            return "35-45 min"
        else:
            return "45-60 min"
    
    def _is_fast_delivery(self, estimated_time_str):
        """Check if estimated time is fast (30 minutes or less)"""
        try:
            # Extract numbers from string like "15-25 min"
            numbers = estimated_time_str.split(' ')[0].split('-')
            # Get the first number (minimum time)
            min_time = int(numbers[0])
            return min_time <= 30
        except:
            return False


class PriceRangeFilterView(APIView):
    """
    Get price range statistics and filters
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        # Get location
        latitude = request.query_params.get('lat')
        longitude = request.query_params.get('lng')
        city = request.query_params.get('city')
        
        # Base queryset
        restaurants = Restaurant.objects.filter(
            status='active',
            branches__is_active=True
        )
        
        # Apply location filtering
        location_filters = {}
        if latitude and longitude:
            try:
                location_filters = {
                    'latitude': float(latitude),
                    'longitude': float(longitude),
                    'radius_km': 15
                }
            except (ValueError, TypeError):
                pass
        elif city:
            location_filters = {'city': city}
        
        if location_filters:
            search_engine = RestaurantSearchEngine(location_filters)
            restaurant_results, total_count = search_engine.search()
            restaurant_ids = [result['restaurant'].restaurant_id for result in restaurant_results]
            restaurants = restaurants.filter(restaurant_id__in=restaurant_ids)
        
        # Calculate price ranges
        price_ranges = {
            '$': {'min': 0, 'max': 15, 'count': 0, 'label': 'Budget'},
            '$$': {'min': 15, 'max': 30, 'count': 0, 'label': 'Moderate'},
            '$$$': {'min': 30, 'max': 50, 'count': 0, 'label': 'Expensive'},
            '$$$$': {'min': 50, 'max': 1000, 'count': 0, 'label': 'Luxury'}
        }
        
        for restaurant in restaurants:
            # Get average menu price
            avg_price = MenuItem.objects.filter(
                category__restaurant=restaurant,
                is_available=True
            ).aggregate(avg_price=Avg('price'))['avg_price'] or 0
            
            # Categorize by price range
            if avg_price < 15:
                price_ranges['$']['count'] += 1
            elif avg_price < 30:
                price_ranges['$$']['count'] += 1
            elif avg_price < 50:
                price_ranges['$$$']['count'] += 1
            else:
                price_ranges['$$$$']['count'] += 1
        
        # Format response
        response_data = []
        for key, data in price_ranges.items():
            if data['count'] > 0:  # Only include ranges with restaurants
                response_data.append({
                    'range': key,
                    'label': data['label'],
                    'description': f'${data["min"]}+ per person',
                    'count': data['count'],
                    'min_price': data['min'],
                    'max_price': data['max']
                })
        
        return Response(response_data)


class LocalFavoritesView(APIView):
    """
    Get editor's picks / local favorite restaurants
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        # Get location
        latitude = request.query_params.get('lat')
        longitude = request.query_params.get('lng')
        city = request.query_params.get('city')
        limit = int(request.query_params.get('limit', 6))
        
        # Get featured restaurants
        restaurants = Restaurant.objects.filter(
            status='active',
            is_featured=True,
            branches__is_active=True
        ).distinct().prefetch_related('cuisines', 'branches')
        
        # Apply location filtering
        location_filters = {}
        if latitude and longitude:
            try:
                location_filters = {
                    'latitude': float(latitude),
                    'longitude': float(longitude),
                    'radius_km': 20
                }
            except (ValueError, TypeError):
                pass
        elif city:
            location_filters = {'city': city}
        
        if location_filters:
            search_engine = RestaurantSearchEngine(location_filters)
            restaurant_results, total_count = search_engine.search()
            restaurant_ids = [result['restaurant'].restaurant_id for result in restaurant_results]
            restaurants = restaurants.filter(restaurant_id__in=restaurant_ids)
        
        # Take top results
        restaurants = restaurants.order_by('-overall_rating')[:limit]
        
        # Serialize
        context = {'request': request}
        if latitude and longitude:
            try:
                context['user_latitude'] = float(latitude)
                context['user_longitude'] = float(longitude)
            except (ValueError, TypeError):
                pass
        
        serializer = RestaurantSearchSerializer(restaurants, many=True, context=context)
        
        # Add editor's pick info
        for restaurant_data in serializer.data:
            restaurant_data['is_editor_pick'] = True
            restaurant_data['editor_note'] = 'Local favorite'
        
        return Response({
            'restaurants': serializer.data,
            'total_count': len(restaurants)
        })


class TrendingTodayView(APIView):
    """
    Get trending menu items for today
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        from datetime import timedelta
        
        # Get location
        latitude = request.query_params.get('lat')
        longitude = request.query_params.get('lng')
        city = request.query_params.get('city')
        limit = int(request.query_params.get('limit', 8))
        
        # Get items ordered today or recently popular
        today = timezone.now().date()
        
        # Get menu items with high popularity or recent orders
        menu_items = MenuItem.objects.filter(
            is_available=True,
            category__restaurant__status='active',
            category__restaurant__branches__is_active=True
        ).select_related('category', 'category__restaurant')
        
        # Apply location filtering
        if latitude and longitude:
            try:
                nearby_branches = SearchUtils.get_restaurant_branches_nearby(
                    float(latitude), float(longitude), 15
                )
                restaurant_ids = [branch.restaurant_id for branch in nearby_branches]
                menu_items = menu_items.filter(category__restaurant_id__in=restaurant_ids)
            except (ValueError, TypeError):
                pass
        elif city:
            menu_items = menu_items.filter(
                category__restaurant__branches__address__city__icontains=city
            )
        
        # Sort by popularity score (you have popularity_score in MenuItem)
        trending_items = menu_items.order_by('-popularity_score')[:limit]
        
        # Format response
        result = []
        for item in trending_items:
            item_data = {
                'item_id': item.item_id,
                'name': item.name,
                'description': item.description,
                'price': float(item.price),
                'image': request.build_absolute_uri(item.image.url) if item.image else None,
                'popularity_score': item.popularity_score,
                'restaurant': {
                    'id': item.category.restaurant.restaurant_id,
                    'name': item.category.restaurant.name,
                    'rating': float(item.category.restaurant.overall_rating)
                }
            }
            
            # Add distance if location available
            if latitude and longitude:
                try:
                    distances = []
                    for branch in item.category.restaurant.branches.all():
                        if branch.address.latitude and branch.address.longitude:
                            dist = SearchUtils.calculate_distance(
                                float(latitude), float(longitude),
                                float(branch.address.latitude), float(branch.address.longitude)
                            )
                            if dist is not None:
                                distances.append(dist)
                    
                    if distances:
                        item_data['distance_km'] = round(min(distances), 2)
                except:
                    pass
            
            result.append(item_data)
        
        return Response(result)
    
class ExploreOtherCitiesView(APIView):
    """
    Show popular restaurants from other cities
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        # Get current user's city from query params
        current_city = request.query_params.get('current_city', '').lower()
        limit_per_city = 2
        max_cities = 3
        
        # Get unique cities with active restaurants
        from django.db.models import Count
        from ..models import Address
        
        # Find cities with most restaurants (excluding current city)
        city_counts = Address.objects.filter(
            branch__restaurant__status='active',
            branch__is_active=True
        ).exclude(city__iexact=current_city).values('city').annotate(
            restaurant_count=Count('branch__restaurant', distinct=True)
        ).filter(restaurant_count__gte=2).order_by('-restaurant_count')[:max_cities]
        
        result = []
        for city_info in city_counts:
            city_name = city_info['city']
            
            # Get featured restaurants from this city
            restaurants = Restaurant.objects.filter(
                status='active',
                branches__address__city__iexact=city_name,
                branches__is_active=True
            ).distinct().order_by('-overall_rating', '-is_featured')[:limit_per_city]
            
            if restaurants.exists():
                # Serialize
                serializer = RestaurantSearchSerializer(restaurants, many=True, context={'request': request})
                
                result.append({
                    'city': city_name,
                    'restaurant_count': city_info['restaurant_count'],
                    'restaurants': serializer.data
                })
        
        return Response(result)


class RestaurantStoriesView(APIView):
    """
    Get restaurants with interesting stories/background
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        limit = int(request.query_params.get('limit', 4))
        
        # Get restaurants with story descriptions
        restaurants = Restaurant.objects.filter(
            status='active',
            story_description__isnull=False,
            story_description__gt='',  # Not empty
            branches__is_active=True
        ).distinct().order_by('-overall_rating', '-is_featured')[:limit]
        
        # Serialize with story context
        serializer = RestaurantSearchSerializer(restaurants, many=True, context={'request': request})
        
        # Add story excerpts
        for i, restaurant_data in enumerate(serializer.data):
            restaurant = restaurants[i]
            story = restaurant.story_description
            # Create excerpt (first 100 chars)
            excerpt = story[:100] + '...' if len(story) > 100 else story
            restaurant_data['story_excerpt'] = excerpt
            restaurant_data['has_story'] = True
        
        return Response({
            'stories': serializer.data,
            'total_count': len(restaurants)
        })