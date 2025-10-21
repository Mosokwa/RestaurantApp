from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.db.models import Q
from rest_framework.permissions import AllowAny
from ..search_utils import RestaurantSearchEngine, SearchUtils
from ..models import Cuisine, Restaurant, MenuItem
from ..serializers import (
    MenuItemSearchSerializer, RestaurantSearchSerializer, SearchFilterSerializer, SearchSuggestionSerializer, RestaurantSerializer
)

class ComprehensiveSearchView(APIView):
    """
    Comprehensive search endpoint - NO MANUAL PAGINATION NEEDED
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        # Validate and parse filters
        filter_serializer = SearchFilterSerializer(data=request.query_params)
        if not filter_serializer.is_valid():
            return Response(filter_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        filters = filter_serializer.validated_data
        
        # Search for restaurants
        search_engine = RestaurantSearchEngine(filters)
        restaurant_results, total_count = search_engine.search()
        
        # Get ALL results - DRF will paginate automatically
        restaurant_data = []
        for result in restaurant_results:  # ← FIXED: Iterate through results
            restaurant_data.append(result['restaurant'])  # ← FIXED: Access 'restaurant' key
        
        # Search for menu items if query provided
        menu_item_results = []
        if filters.get('query'):
            menu_item_results = self._search_menu_items(filters)
        
        # Serialize results - NO PAGINATION LOGIC
        restaurant_serializer = RestaurantSearchSerializer(
            restaurant_data, 
            many=True,
            context={'request': request}
        )
        
        menu_item_serializer = MenuItemSearchSerializer(
            menu_item_results, 
            many=True,
            context={'request': request}
        )
        
        # Add distance information
        restaurant_data_with_distance = restaurant_serializer.data
        for i, result in enumerate(restaurant_results):  # ← FIXED: Use restaurant_results
            if result['distance_km'] is not None:  # ← FIXED: Access distance properly
                if i < len(restaurant_data_with_distance):
                    restaurant_data_with_distance[i]['distance_km'] = round(result['distance_km'], 2)
        
        response_data = {
            'query': filters.get('query', ''),
            'filters': filters,
            'restaurants': {
                'results': restaurant_data_with_distance,
                'total_count': total_count  # ← FIXED: Use the returned total_count
            },
            'menu_items': {
                'results': menu_item_serializer.data,
                'total_count': len(menu_item_results)
            }
        }
        
        return Response(response_data)
    
    def _search_menu_items(self, filters):
        """Search for menu items across all restaurants"""
        
        queryset = MenuItem.objects.filter(
            is_available=True,
            category__restaurant__status='active'
        ).select_related('category', 'category__restaurant')
        
        # Text search
        if filters.get('query'):
            search_terms = filters['query'].split()
            q_objects = Q()
            
            for term in search_terms:
                q_objects |= Q(name__icontains=term)
                q_objects |= Q(description__icontains=term)
                q_objects |= Q(category__name__icontains=term)
                q_objects |= Q(category__restaurant__name__icontains=term)
            
            queryset = queryset.filter(q_objects)
        
        # Dietary preferences filter
        dietary_filters = filters.get('dietary_preferences', [])
        if dietary_filters:
            if 'vegetarian' in dietary_filters:
                queryset = queryset.filter(is_vegetarian=True)
            if 'vegan' in dietary_filters:
                queryset = queryset.filter(is_vegan=True)
            if 'gluten_free' in dietary_filters:
                queryset = queryset.filter(is_gluten_free=True)
        
        # Price range filter
        if filters.get('price_range'):
            min_price, max_price = SearchUtils.get_price_range_filter(filters['price_range'])
            queryset = queryset.filter(price__gte=min_price, price__lte=max_price)
        
        # Location filter
        if filters.get('latitude') and filters.get('longitude'):
            nearby_branches = SearchUtils.get_restaurant_branches_nearby(
                filters['latitude'], filters['longitude'], filters.get('radius_km', 10)
            )
            restaurant_ids = [branch.restaurant_id for branch in nearby_branches]
            queryset = queryset.filter(category__restaurant_id__in=restaurant_ids)
        
        # Rating filter
        if filters.get('min_rating'):
            queryset = queryset.filter(category__restaurant__overall_rating__gte=filters['min_rating'])
        
        return list(queryset.distinct()[:50])  # Limit to 50 results

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