from datetime import timedelta
from django.utils import timezone 
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q, Count, Sum
from rest_framework.permissions import AllowAny, IsAuthenticated
from ..search_utils import RestaurantSearchEngine, SearchUtils
from ..models import Restaurant, MenuItem, SpecialOffer
from ..serializers import (
    RestaurantSearchSerializer, SpecialOfferSerializer
)

class PopularRestaurantsView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        # Get location from query params
        latitude = request.query_params.get('lat')
        longitude = request.query_params.get('lng')
        city = request.query_params.get('city')

        print(f"Enhanced search - city: {city}, coordinates: {latitude}, {longitude}")
        
        # Use the ENHANCED search functionality
        # from .search_utils import RestaurantSearchEngine
        
        filters = {
            'latitude': float(latitude) if latitude and latitude != 'null' else None,
            'longitude': float(longitude) if longitude and longitude != 'null' else None,
            'city': city,
            'radius_km': 15,
            'min_rating': 4.0,
            'sort_by': 'relevance',  # Use enhanced relevance scoring
            'is_open_now': True
        }
        
        search_engine = RestaurantSearchEngine(filters)
        restaurant_results, total_count = search_engine.search()
        
        # Take top 12 results
        top_restaurants = []
        for result in restaurant_results[:12]:  # ← FIXED: Iterate through results
            top_restaurants.append(result['restaurant'])  # ← FIXED: Access 'restaurant' key
        
        # Enhanced fallback with city-based search
        if not top_restaurants and city:
            print("No location-based results, trying city-based search...")
            city_restaurants = SearchUtils.get_restaurants_by_city(city, limit=12)
            top_restaurants = list(city_restaurants)
        
        # Final fallback to featured restaurants
        if not top_restaurants:
            print("Fallback to featured restaurants")
            top_restaurants = Restaurant.objects.filter(
                status='active', 
                is_featured=True,
                branches__is_active=True
            ).distinct()[:12]
        
        print(f"Final restaurants count: {len(top_restaurants)}")
        
        # Enhanced context with location data
        context = {'request': request}
        if latitude and longitude:
            try:
                context['user_latitude'] = float(latitude)
                context['user_longitude'] = float(longitude)
            except (ValueError, TypeError):
                pass
        
        # Use enhanced serializer
        serializer = RestaurantSearchSerializer(top_restaurants, many=True, context=context)
        
        # Add search metadata to response
        response_data = {
            'restaurants': serializer.data,
            'search_metadata': {
                'has_location': bool(latitude and longitude),
                'city_used': city,
                'total_found': len(top_restaurants),
                'search_type': 'enhanced'
            }
        }
        
        return Response(response_data)

from decimal import Decimal
class TrendingDishesView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        # Get location from query params
        latitude = request.query_params.get('lat')
        longitude = request.query_params.get('lng')
        city = request.query_params.get('city')
        
        print(f"Trending dishes - city: {city}, coordinates: {latitude}, {longitude}")
        

        from django.db.models.functions import Coalesce
        
        # Calculate date range for trending (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        # Base queryset for menu items
        trending_items = MenuItem.objects.filter(
            is_available=True,
            category__restaurant__status='active',
            category__restaurant__branches__is_active=True
        ).distinct()
        
        # Apply location filtering if coordinates provided
        if latitude and longitude:
            try:
                nearby_branches = SearchUtils.get_restaurant_branches_nearby(
                    float(latitude), float(longitude), 20  # 20km radius
                )
                restaurant_ids = [branch.restaurant_id for branch in nearby_branches]
                trending_items = trending_items.filter(
                    category__restaurant_id__in=restaurant_ids
                )
                print(f"Filtered by location: {len(restaurant_ids)} restaurants")
            except (ValueError, TypeError) as e:
                print(f"Location filtering error: {e}")
        
        # Fallback to city filtering if no coordinates but city provided
        elif city:
            trending_items = trending_items.filter(
                category__restaurant__branches__address__city__icontains=city
            )
            print(f"Filtered by city: {city}")
        
        # FIXED: Proper annotation without mixed type errors

        trending_items = trending_items.annotate(
            recent_order_count=Count(
                'order_items',
                filter=Q(order_items__order__order_placed_at__gte=thirty_days_ago)
            ),
            recent_revenue=Coalesce(Sum(
                'order_items__total_price',
                filter=Q(
                    order_items__order__order_placed_at__gte=thirty_days_ago,
                    order_items__order__status='delivered'
                )
            ), Decimal('0.0'))  # Ensure it's always a float
        ).filter(recent_order_count__gt=0)  # Only items with recent orders
        
        # FIXED: Calculate trending score without mixed types
        items_with_scores = []
        for item in trending_items:
            # Convert to float for calculation
            order_count = float(item.recent_order_count)
            revenue = float(item.recent_revenue)
            trending_score = (order_count * 0.6) + (revenue * 0.4)
            
            items_with_scores.append({
                'item': item,
                'trending_score': trending_score
            })
        
        # STEP 3: Sort by trending score
        items_with_scores.sort(key=lambda x: x['trending_score'], reverse=True)
        
        # STEP 4: Take top 12
        top_items = [item_data['item'] for item_data in items_with_scores[:12]]
        
        # Create enhanced response with location context
        result = []
        for item in top_items:
            # Calculate distance if coordinates provided
            distance_km = None
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
                        distance_km = round(min(distances), 2)
                except (ValueError, TypeError):
                    pass
            
            result.append({
                'item_id': item.item_id,
                'name': item.name,
                'description': item.description,
                'price': float(item.price),
                'image': request.build_absolute_uri(item.image.url) if item.image else None,
                'restaurant': {
                    'id': item.category.restaurant.restaurant_id,
                    'name': item.category.restaurant.name,
                    'rating': float(item.category.restaurant.overall_rating),
                    'distance_km': distance_km,
                    'is_open': any(branch.is_open_now() for branch in item.category.restaurant.branches.all() if branch.is_active)
                },
                'dietary_info': {
                    'vegetarian': item.is_vegetarian,
                    'vegan': item.is_vegan,
                    'gluten_free': item.is_gluten_free,
                    'spicy': item.is_spicy
                },
                'trending_metrics': {
                    'recent_orders': item.recent_order_count,
                    'recent_revenue': float(item.recent_revenue),
                    'trending_score': float(item.trending_score)
                },
                'preparation_time': item.preparation_time
            })
        
        print(f"Returning {len(result)} trending dishes")
        return Response(result)

class PersonalizedRecommendationsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Get location from query params
        latitude = request.query_params.get('lat')
        longitude = request.query_params.get('lng')
        city = request.query_params.get('city')
        
        print(f"Personalized recommendations for {user.username} - location: {latitude}, {longitude}")
        
        # Base queryset with location filtering using enhanced utils
        recommended_items = MenuItem.objects.filter(
            is_available=True,
            category__restaurant__status='active'
        )
        
        # Apply location filtering using enhanced search engine
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
            restaurant_ids = []
            for result in restaurant_results:  # ← FIXED: Iterate through results
                restaurant_ids.append(result['restaurant'].restaurant_id)  # ← FIXED: Access properly
            recommended_items = recommended_items.filter(category__restaurant_id__in=restaurant_ids)
        
        # For new users or users without preferences, return popular items near location
        if not hasattr(user, 'customer_profile') or user.customer_profile.favorite_cuisines.count() == 0:
            print("New user or no preferences - returning popular items")
            
            # Get popular items from last 30 days
            thirty_days_ago = timezone.now() - timedelta(days=30)
            
            popular_items = recommended_items.annotate(
                recent_order_count=Count(
                    'order_items',
                    filter=Q(order_items__order__order_placed_at__gte=thirty_days_ago)
                )
            ).filter(order_count__gt=0).order_by('-recent_order_count')[:6]
            
            result = []
            for item in popular_items:
                # Calculate distance using enhanced utils
                distance_km = None
                if latitude and longitude:
                    try:
                        restaurant = item.category.restaurant
                        restaurant = SearchUtils.enhance_restaurant_with_location(
                            restaurant, float(latitude), float(longitude)
                        )
                        distance_km = getattr(restaurant, 'distance_km', None)
                    except (ValueError, TypeError):
                        pass
                
                result.append({
                    'item_id': item.item_id,
                    'name': item.name,
                    'price': float(item.price),
                    'image': request.build_absolute_uri(item.image.url) if item.image else None,
                    'restaurant': item.category.restaurant.name,
                    'restaurant_rating': float(item.category.restaurant.overall_rating),
                    'distance_km': distance_km,
                    'reason': 'Popular in your area',
                    'dietary_info': {
                        'vegetarian': item.is_vegetarian,
                        'vegan': item.is_vegan,
                        'gluten_free': item.is_gluten_free
                    }
                })
            
            return Response(result)
        
        # For returning users with preferences
        customer = user.customer_profile
        favorite_cuisines = customer.favorite_cuisines.all()
        
        print(f"User has {favorite_cuisines.count()} favorite cuisines")
        
        # Get recommended items based on favorite cuisines and location
        recommended_items = recommended_items.filter(
            category__restaurant__cuisines__in=favorite_cuisines
        ).distinct().annotate(
            total_order_count=Count('order_items')
        ).order_by('-total_order_count')[:6]
        
        result = []
        for item in recommended_items:
            # Calculate distance using enhanced utils
            distance_km = None
            if latitude and longitude:
                try:
                    restaurant = item.category.restaurant
                    restaurant = SearchUtils.enhance_restaurant_with_location(
                        restaurant, float(latitude), float(longitude)
                    )
                    distance_km = getattr(restaurant, 'distance_km', None)
                except (ValueError, TypeError):
                    pass
            
            # Determine recommendation reason
            if favorite_cuisines:
                cuisine_names = [cuisine.name for cuisine in favorite_cuisines[:2]]
                if len(cuisine_names) == 1:
                    reason = f'Based on your preference for {cuisine_names[0]} cuisine'
                else:
                    reason = f'Based on your preferences for {", ".join(cuisine_names)} cuisines'
            else:
                reason = 'Recommended based on your order history'
            
            result.append({
                'item_id': item.item_id,
                'name': item.name,
                'price': float(item.price),
                'image': request.build_absolute_uri(item.image.url) if item.image else None,
                'restaurant': item.category.restaurant.name,
                'restaurant_rating': float(item.category.restaurant.overall_rating),
                'distance_km': distance_km,
                'reason': reason,
                'dietary_info': {
                    'vegetarian': item.is_vegetarian,
                    'vegan': item.is_vegan,
                    'gluten_free': item.is_gluten_free
                },
                'cuisine_match': [cuisine.name for cuisine in item.category.restaurant.cuisines.all() 
                                 if cuisine in favorite_cuisines]
            })
        
        print(f"Returning {len(result)} personalized recommendations")
        return Response(result)

class HomepageSpecialOffersView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        # Get location from query params
        latitude = request.query_params.get('lat')
        longitude = request.query_params.get('lng')
        city = request.query_params.get('city')
        
        print(f"Special offers - location: {latitude}, {longitude}, city: {city}")
        
        # Get active special offers
        offers = SpecialOffer.objects.filter(
            is_active=True,
            valid_from__lte=timezone.now(),
            valid_until__gte=timezone.now()
        ).select_related('restaurant').prefetch_related('restaurant__branches')
        
        # Use enhanced search engine for location filtering
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
            restaurant_ids = []
            for result in restaurant_results:  # ← FIXED: Iterate through results
                restaurant_ids.append(result['restaurant'].restaurant_id)  # ← FIXED: Access properly
            offers = offers.filter(restaurant_id__in=restaurant_ids)
            print(f"Location-based offers: {offers.count()}")
        
        # Only include valid offers and enhance with location data using enhanced utils
        valid_offers = []
        for offer in offers:
            if offer.is_valid():
                # Calculate distance using enhanced utils
                distance_km = None
                if latitude and longitude:
                    try:
                        restaurant = offer.restaurant
                        restaurant = SearchUtils.enhance_restaurant_with_location(
                            restaurant, float(latitude), float(longitude)
                        )
                        distance_km = getattr(restaurant, 'distance_km', None)
                    except (ValueError, TypeError):
                        pass
                
                # Add enhanced location data to offer object
                offer.distance_km = distance_km
                offer.has_open_branch = any(
                    branch.is_open_now() for branch in offer.restaurant.branches.all() 
                    if branch.is_active
                )
                valid_offers.append(offer)
        
        # Enhanced sorting with location priority
        if latitude and longitude:
            valid_offers.sort(key=lambda x: (
                x.distance_km or float('inf'),  # Closest first
                not x.has_open_branch,  # Open restaurants first
                x.valid_until  # Sooner expiring offers first
            ))
        else:
            # Sort by offer relevance
            valid_offers.sort(key=lambda x: (
                not x.restaurant.is_featured,
                not x.has_open_branch,
                x.valid_until
            ))
        
        # Take top 6 offers
        top_offers = valid_offers[:6]
        
        # Serialize with enhanced context
        context = {'request': request}
        if latitude and longitude:
            try:
                context['user_latitude'] = float(latitude)
                context['user_longitude'] = float(longitude)
            except (ValueError, TypeError):
                pass
        
        # Use enhanced serializer
        serializer = SpecialOfferSerializer(top_offers, many=True, context=context)
        
        # Enhance serialized data with additional information
        enhanced_data = serializer.data
        for i, offer_data in enumerate(enhanced_data):
            offer_data['distance_km'] = top_offers[i].distance_km if hasattr(top_offers[i], 'distance_km') else None
            offer_data['has_open_branch'] = top_offers[i].has_open_branch if hasattr(top_offers[i], 'has_open_branch') else False
            offer_data['location_priority'] = self._get_location_priority(top_offers[i].distance_km)
        
        print(f"Returning {len(enhanced_data)} special offers")
        return Response(enhanced_data)
    
    def _get_location_priority(self, distance_km):
        """Helper method to determine location priority"""
        if distance_km is None:
            return 'unknown'
        if distance_km <= 2:
            return 'very_near'
        elif distance_km <= 5:
            return 'near'
        elif distance_km <= 10:
            return 'moderate'
        elif distance_km <= 20:
            return 'far'
        else:
            return 'very_far'