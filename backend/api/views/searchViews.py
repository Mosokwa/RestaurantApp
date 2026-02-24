from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.db.models import Q, IntegerField, Count, When, Case
from rest_framework.permissions import AllowAny
from ..search_utils import RestaurantSearchEngine, SearchUtils
from ..models import Cuisine, Restaurant, MenuItem
from ..serializers import (
    MenuItemSearchSerializer, RestaurantSearchSerializer, SearchFilterSerializer, SearchSuggestionSerializer, RestaurantSerializer
)
import logging

logger = logging.getLogger(__name__)

class ComprehensiveSearchView(APIView):
    """
    Comprehensive search endpoint - FIXED to match suggestion logic
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        # Validate and parse filters
        filter_serializer = SearchFilterSerializer(data=request.query_params)
        if not filter_serializer.is_valid():
            return Response(filter_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        filters = filter_serializer.validated_data
        query = filters.get('query', '').strip()
        
        logger.info(f"Search query: '{query}'")
        
        # Start with active restaurants
        queryset = Restaurant.objects.filter(status='active').prefetch_related(
            'cuisines', 'branches', 'branches__address'
        )
        
        # ========== TEXT SEARCH - MAKE IT MATCH SUGGESTIONS ==========
        if query:
            # Split into individual terms (just like suggestions do)
            search_terms = query.split()
            q_objects = Q()
            
            for term in search_terms:
                if len(term) < 2:  # Skip very short terms
                    continue
                    
                # Search in restaurant name, description, AND cuisine names
                q_objects |= Q(name__icontains=term)
                q_objects |= Q(description__icontains=term)
                q_objects |= Q(cuisines__name__icontains=term)
            
            if q_objects:
                queryset = queryset.filter(q_objects).distinct()
                logger.info(f"Found {queryset.count()} restaurants matching '{query}'")
                
                # Debug: log the first few matches
                if queryset.count() > 0:
                    for r in queryset[:5]:
                        cuisines = [c.name for c in r.cuisines.all()]
                        logger.info(f"  Match: {r.name} - Cuisines: {cuisines}")
            else:
                logger.info(f"No restaurants found matching '{query}'")
        
        # ========== LOCATION FILTER ==========
        latitude = filters.get('latitude')
        longitude = filters.get('longitude')
        radius_km = filters.get('radius_km', 10)
        
        if latitude and longitude:
            try:
                # Get branches within radius
                nearby_branches = SearchUtils.get_restaurant_branches_nearby(
                    latitude, longitude, radius_km
                )
                restaurant_ids = [branch.restaurant_id for branch in nearby_branches]
                queryset = queryset.filter(restaurant_id__in=restaurant_ids)
                logger.info(f"Location filter applied: {len(restaurant_ids)} restaurants within {radius_km}km")
            except Exception as e:
                logger.error(f"Location filter error: {e}")
        
        # ========== CUISINE FILTER ==========
        cuisine_param = filters.get('cuisine')
        if cuisine_param:
            cuisine_ids = [int(id.strip()) for id in cuisine_param.split(',') if id.strip().isdigit()]
            if cuisine_ids:
                queryset = queryset.filter(cuisines__cuisine_id__in=cuisine_ids).distinct()
        
        # ========== RATING FILTER ==========
        min_rating = filters.get('min_rating', 0)
        if min_rating and min_rating > 0:
            queryset = queryset.filter(overall_rating__gte=min_rating)
        
        # ========== PRICE RANGE FILTER ==========
        price_range = filters.get('price_range')
        if price_range:
            # This depends on how you store price ranges
            price_ranges = price_range.split(',')
            # Add your price filter logic here
        
        # ========== DIETARY FILTER ==========
        dietary = filters.get('dietary_preferences', [])
        if dietary:
            # This would filter menu items, but for restaurants you might filter by tags
            # Add your dietary filter logic here
            pass
        
        # ========== OPEN NOW FILTER ==========
        is_open_now = filters.get('is_open_now', False)
        if is_open_now:
            # Filter restaurants that have at least one branch open now
            from django.utils import timezone
            now = timezone.now()
            current_day = now.strftime('%A').lower()
            current_time = now.strftime('%H:%M')
            
            # This is a simplified version - you might need a more complex query
            queryset = queryset.filter(
                branches__is_active=True,
                branches__operating_hours__contains={current_day: {'open__lte': current_time, 'close__gte': current_time}}
            ).distinct()
        
        # ========== SORTING ==========
        sort_by = filters.get('sort_by', 'relevance')
        
        if sort_by == 'rating':
            queryset = queryset.order_by('-overall_rating', '-total_reviews')
        elif sort_by == 'distance' and latitude and longitude:
            # Distance sorting would require annotation
            # For now, just order by relevance
            queryset = queryset.order_by('-is_featured', '-overall_rating')
        elif sort_by == 'price_low':
            queryset = queryset.order_by('price_range')  # If you have price_range field
        elif sort_by == 'price_high':
            queryset = queryset.order_by('-price_range')
        else:  # relevance
            if query:
                # Boost restaurants that match search terms in name
                queryset = queryset.annotate(
                    name_match=Count(Case(
                        When(name__icontains=query, then=1),
                        output_field=IntegerField()
                    )) * 2
                ).order_by('-name_match', '-is_featured', '-overall_rating')
            else:
                queryset = queryset.order_by('-is_featured', '-overall_rating')
        
        # ========== PAGINATION ==========
        page = filters.get('page', 1)
        page_size = filters.get('page_size', 20)
        start = (page - 1) * page_size
        end = start + page_size
        
        total_count = queryset.count()
        paginated_restaurants = queryset[start:end]
        
        # ========== SERIALIZE ==========
        serializer = RestaurantSearchSerializer(
            paginated_restaurants, 
            many=True, 
            context={'request': request}
        )
        
        # Add distance information if location provided
        restaurant_data = serializer.data
        if latitude and longitude:
            for i, restaurant in enumerate(paginated_restaurants):
                # Calculate distance to nearest branch
                distances = []
                for branch in restaurant.branches.all():
                    if branch.address and branch.address.latitude and branch.address.longitude:
                        dist = SearchUtils.calculate_distance(
                            latitude, longitude,
                            float(branch.address.latitude),
                            float(branch.address.longitude)
                        )
                        if dist:
                            distances.append(dist)
                
                if distances and i < len(restaurant_data):
                    restaurant_data[i]['distance_km'] = round(min(distances), 2)
        
        response_data = {
            'results': restaurant_data,
            'total_count': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': (total_count + page_size - 1) // page_size
        }
        
        logger.info(f"Returning {len(restaurant_data)} results out of {total_count} total")
        
        return Response(response_data)

class SearchSuggestionsView(APIView):
    """
    Provide search suggestions for autocomplete
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        query = request.query_params.get('q', '').strip().lower()
        limit = int(request.query_params.get('limit', 10))
        
        if not query or len(query) < 2:
            return Response({'suggestions': []})
        
        suggestions = []
        
        # Restaurant name suggestions
        restaurant_matches = Restaurant.objects.filter(
            name__icontains=query,
            status='active'
        )[:5]
        
        for restaurant in restaurant_matches:
            suggestions.append({
                'type': 'restaurant',
                'name': restaurant.name,
                'id': restaurant.restaurant_id
            })
        
        # Menu item suggestions
        menu_item_matches = MenuItem.objects.filter(
            name__icontains=query,
            is_available=True,
            category__restaurant__status='active'
        ).select_related('category__restaurant')[:5]
        
        for item in menu_item_matches:
            suggestions.append({
                'type': 'menu_item',
                'name': item.name,
                'id': item.item_id,
                'restaurant_name': item.category.restaurant.name
            })
        
        # Cuisine suggestions
        cuisine_matches = Cuisine.objects.filter(
            name__icontains=query,
            is_active=True
        )[:3]
        
        for cuisine in cuisine_matches:
            suggestions.append({
                'type': 'cuisine',
                'name': cuisine.name,
                'cuisine_name': cuisine.name
            })
        
        # Limit results
        suggestions = suggestions[:limit]
        
        serializer = SearchSuggestionSerializer(suggestions, many=True)
        return Response({'suggestions': serializer.data})

class MenuItemSearchView(APIView):
    """
    Dedicated menu item search across all restaurants
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        filter_serializer = SearchFilterSerializer(data=request.query_params)
        if not filter_serializer.is_valid():
            return Response(filter_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        filters = filter_serializer.validated_data
        
        if not filters.get('query'):
            return Response({'error': 'Search query is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Search for menu items        
        queryset = MenuItem.objects.filter(
            is_available=True,
            category__restaurant__status='active'
        ).select_related('category', 'category__restaurant')
        
        # Text search
        search_terms = filters['query'].split()
        q_objects = Q()
        
        for term in search_terms:
            q_objects |= Q(name__icontains=term)
            q_objects |= Q(description__icontains=term)
        
        queryset = queryset.filter(q_objects)
        
        # Apply filters
        dietary_filters = filters.get('dietary_preferences', [])
        if dietary_filters:
            if 'vegetarian' in dietary_filters:
                queryset = queryset.filter(is_vegetarian=True)
            if 'vegan' in dietary_filters:
                queryset = queryset.filter(is_vegan=True)
            if 'gluten_free' in dietary_filters:
                queryset = queryset.filter(is_gluten_free=True)
        
        if filters.get('price_range'):
            min_price, max_price = SearchUtils.get_price_range_filter(filters['price_range'])
            queryset = queryset.filter(price__gte=min_price, price__lte=max_price)
        
        if filters.get('min_rating'):
            queryset = queryset.filter(category__restaurant__overall_rating__gte=filters['min_rating'])
        
        # Location-based filtering
        menu_items_with_distance = []
        for item in queryset.distinct():
            distance = None
            if filters.get('latitude') and filters.get('longitude'):
                # Find minimum distance to any branch of the restaurant
                distances = []
                for branch in item.category.restaurant.branches.all():
                    if branch.address.latitude and branch.address.longitude:
                        dist = SearchUtils.calculate_distance(
                            filters['latitude'], filters['longitude'],
                            float(branch.address.latitude), float(branch.address.longitude)
                        )
                        if dist is not None:
                            distances.append(dist)
                
                distance = min(distances) if distances else None
            
            menu_items_with_distance.append({
                'item': item,
                'distance_km': distance
            })
        
        # Sort results
        sort_by = filters.get('sort_by', 'relevance')
        if sort_by == 'distance':
            menu_items_with_distance.sort(key=lambda x: x['distance_km'] or float('inf'))
        elif sort_by == 'price_low':
            menu_items_with_distance.sort(key=lambda x: x['item'].price)
        elif sort_by == 'price_high':
            menu_items_with_distance.sort(key=lambda x: x['item'].price, reverse=True)
        elif sort_by == 'rating':
            menu_items_with_distance.sort(
                key=lambda x: x['item'].category.restaurant.overall_rating, 
                reverse=True
            )
        
        # Paginate
        page = filters.get('page', 1)
        page_size = filters.get('page_size', 20)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        paginated_items = menu_items_with_distance[start_idx:end_idx]
        
        # Serialize results
        serializer = MenuItemSearchSerializer(
            [item['item'] for item in paginated_items],
            many=True,
            context={'request': request}
        )
        
        # Add distance to serialized data
        result_data = serializer.data
        for i, item_data in enumerate(result_data):
            if paginated_items[i]['distance_km'] is not None:
                item_data['distance_km'] = round(paginated_items[i]['distance_km'], 2)
        
        return Response({
            'query': filters['query'],
            'results': result_data,
            'total_count': len(menu_items_with_distance),
            'page': page,
            'page_size': page_size,
            'total_pages': (len(menu_items_with_distance) + page_size - 1) // page_size
        })


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def restaurant_search(request):
    """Advanced restaurant search endpoint"""
    query = request.query_params.get('q', '')
    cuisine = request.query_params.get('cuisine', '')
    city = request.query_params.get('city', '')
    min_rating = request.query_params.get('min_rating', 0)
    
    queryset = Restaurant.objects.filter(status='active')
    
    if query:
        queryset = queryset.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(cuisines__name__icontains=query)
        )
    
    if cuisine:
        queryset = queryset.filter(cuisines__name__icontains=cuisine)
    
    if city:
        queryset = queryset.filter(branches__address__city__icontains=city)
    
    if min_rating:
        queryset = queryset.filter(overall_rating__gte=float(min_rating))
    
    queryset = queryset.distinct().prefetch_related('cuisines')
    serializer = RestaurantSerializer(queryset, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def nearby_restaurants(request):
    """Find restaurants near a location"""
    latitude = request.query_params.get('lat')
    longitude = request.query_params.get('lng')
    radius = request.query_params.get('radius', 10)  # Default 10km radius
    
    if not latitude or not longitude:
        return Response(
            {'error': 'Latitude and longitude parameters required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # This is a simplified version - in production, use PostGIS for real geo queries
    restaurants = Restaurant.objects.filter(
        status='active',
        branches__is_active=True
    ).distinct().prefetch_related('cuisines')
    
    serializer = RestaurantSerializer(restaurants, many=True)
    return Response(serializer.data)