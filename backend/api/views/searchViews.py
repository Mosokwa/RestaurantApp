from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.db.models import Q, IntegerField, Count, When, Case
from rest_framework.permissions import AllowAny
from ..search_utils import RestaurantSearchEngine, SearchUtils
from ..models import Cuisine, Restaurant, MenuItem, MenuCategory
from ..serializers import (
    MenuItemSearchSerializer, RestaurantSearchSerializer, SearchFilterSerializer, SearchSuggestionSerializer, RestaurantSerializer
)
import logging
import json
import traceback

logger = logging.getLogger(__name__)

class ComprehensiveSearchView(APIView):
    """
    Comprehensive search endpoint
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        # Get all query parameters
        query = request.query_params.get('q', '').strip()
        latitude = request.query_params.get('lat')
        longitude = request.query_params.get('lng')
        radius = float(request.query_params.get('radius', 10))
        min_rating = request.query_params.get('min_rating')
        cuisine = request.query_params.get('cuisine', '')
        price_range = request.query_params.get('price_range', '')
        dietary = request.query_params.get('dietary', '')
        sort_by = request.query_params.get('sort_by', 'relevance')
        is_open_now = request.query_params.get('is_open_now', 'false').lower() == 'true'
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        
        logger.info(f"Search - Query: '{query}'")
        
        # Start with all active restaurants
        queryset = Restaurant.objects.filter(status='active').prefetch_related(
            'cuisines', 'branches', 'branches__address'
        )
        
        # ========== TEXT SEARCH ==========
        if query:
            try:
                # Split into terms
                search_terms = query.split()
                
                # Create Q objects for different search types
                # IMPORTANT: We're using django.db.models.Q directly
                from django.db.models import Q as DjangoQ
                
                name_condition = DjangoQ()
                
                for term in search_terms:
                    if len(term) >= 2:
                        name_condition |= DjangoQ(name__icontains=term)
                
                # Find restaurants by cuisine
                cuisine_ids = []
                try:
                    cuisine_ids = list(Cuisine.objects.filter(
                        name__icontains=query
                    ).values_list('cuisine_id', flat=True))
                except Exception as e:
                    logger.error(f"Error finding cuisines: {e}")
                
                # Find restaurants by menu items
                restaurant_ids_by_menu = []
                try:
                    restaurant_ids_by_menu = list(MenuItem.objects.filter(
                        name__icontains=query,
                        is_available=True
                    ).values_list('category__restaurant_id', flat=True).distinct())
                except Exception as e:
                    logger.error(f"Error finding menu items: {e}")
                
                # Build final search condition
                search_condition = name_condition
                
                if cuisine_ids:
                    search_condition |= DjangoQ(cuisines__cuisine_id__in=cuisine_ids)
                
                if restaurant_ids_by_menu:
                    search_condition |= DjangoQ(restaurant_id__in=restaurant_ids_by_menu)
                
                # Apply filter
                if search_condition:
                    queryset = queryset.filter(search_condition).distinct()
                    
            except Exception as e:
                logger.error(f"Error in text search: {e}")
                traceback.print_exc()
        
        # ========== CUISINE FILTER ==========
        if cuisine:
            cuisine_list = [c.strip() for c in cuisine.split(',') if c.strip()]
            if cuisine_list:
                queryset = queryset.filter(cuisines__name__in=cuisine_list).distinct()
        
        # ========== PRICE RANGE FILTER ==========
        if price_range:
            price_levels = [p.strip() for p in price_range.split(',') if p.strip()]
            if price_levels:
                # If you have price_level field
                queryset = queryset.filter(price_level__in=price_levels)
        
        # ========== DIETARY FILTER ==========
        if dietary:
            dietary_list = [d.strip() for d in dietary.split(',') if d.strip()]
            if dietary_list:
                from django.db.models import Q as DjangoQ
                diet_condition = DjangoQ()
                
                if 'vegetarian' in dietary_list:
                    diet_condition |= DjangoQ(menu_items__is_vegetarian=True)
                if 'vegan' in dietary_list:
                    diet_condition |= DjangoQ(menu_items__is_vegan=True)
                if 'gluten_free' in dietary_list:
                    diet_condition |= DjangoQ(menu_items__is_gluten_free=True)
                
                if diet_condition:
                    restaurant_ids_with_diet = MenuItem.objects.filter(
                        diet_condition,
                        is_available=True,
                        category__restaurant__status='active'
                    ).values_list('category__restaurant_id', flat=True).distinct()
                    
                    if restaurant_ids_with_diet:
                        queryset = queryset.filter(restaurant_id__in=restaurant_ids_with_diet)
        
        # ========== RATING FILTER ==========
        if min_rating:
            try:
                min_rating = float(min_rating)
                queryset = queryset.filter(overall_rating__gte=min_rating)
            except ValueError:
                pass
        
        # ========== LOCATION FILTER ==========
        if latitude and longitude:
            try:
                latitude = float(latitude)
                longitude = float(longitude)
                
                from ..search_utils import SearchUtils
                nearby_branches = SearchUtils.get_restaurant_branches_nearby(
                    latitude, longitude, radius
                )
                restaurant_ids = [b.restaurant_id for b in nearby_branches]
                if restaurant_ids:
                    queryset = queryset.filter(restaurant_id__in=restaurant_ids)
            except Exception as e:
                logger.error(f"Location filter error: {e}")
        
        # ========== OPEN NOW FILTER ==========
        if is_open_now:
            try:
                from django.utils import timezone
                
                now = timezone.now()
                current_day = now.strftime('%A').lower()
                current_time = now.strftime('%H:%M')
                
                # Get all restaurants and filter in Python
                all_restaurants = list(queryset)
                open_restaurant_ids = []
                
                for restaurant in all_restaurants:
                    for branch in restaurant.branches.all():
                        try:
                            hours = branch.operating_hours
                            if isinstance(hours, str):
                                hours = json.loads(hours)
                            
                            day_hours = hours.get(current_day, {})
                            open_time = day_hours.get('open', '00:00')
                            close_time = day_hours.get('close', '23:59')
                            
                            if open_time <= current_time <= close_time:
                                open_restaurant_ids.append(restaurant.restaurant_id)
                                break
                        except Exception:
                            continue
                
                if open_restaurant_ids:
                    queryset = queryset.filter(restaurant_id__in=open_restaurant_ids)
                else:
                    queryset = Restaurant.objects.none()
            except Exception as e:
                logger.error(f"Open now filter error: {e}")
        
        # ========== SORTING ==========
        if sort_by == 'rating':
            queryset = queryset.order_by('-overall_rating', '-total_reviews')
        elif sort_by == 'price_low':
            queryset = queryset.order_by('price_level')
        elif sort_by == 'price_high':
            queryset = queryset.order_by('-price_level')
        else:  # relevance
            queryset = queryset.order_by('-is_featured', '-overall_rating')
        
        # ========== PAGINATION ==========
        total_count = queryset.count()
        start = (page - 1) * page_size
        end = start + page_size
        paginated_restaurants = queryset[start:end]
        
        # ========== SERIALIZE ==========
        from ..serializers import RestaurantSearchSerializer
        serializer = RestaurantSearchSerializer(
            paginated_restaurants, 
            many=True, 
            context={'request': request}
        )
        
        # Add distance if location provided
        restaurant_data = serializer.data
        if latitude and longitude:
            try:
                from ..search_utils import SearchUtils
                for i, restaurant in enumerate(paginated_restaurants):
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
            except Exception as e:
                logger.error(f"Distance calculation error: {e}")
        
        response_data = {
            'results': restaurant_data,
            'total_count': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': (total_count + page_size - 1) // page_size
        }
        
        logger.info(f"Returning {len(restaurant_data)} of {total_count} restaurants")
        
        return Response(response_data)

class SearchSuggestionsView(APIView):
    """
    Provide search suggestions for autocomplete
    Returns restaurants, cuisines, and menu items matching the query
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        # Get query parameter - handle both ?q=query and ?q[query]=query formats
        query = request.query_params.get('q', '')
        if not query and 'q[query]' in request.query_params:
            query = request.query_params.get('q[query]', '')
        
        query = query.strip()
        limit = int(request.query_params.get('limit', 8))
        filter_type = request.query_params.get('type', '')  # Optional: restaurant, cuisine, menu_item
        
        logger.info(f"Search suggestions - Query: '{query}', Limit: {limit}, Type: {filter_type}")
        
        if not query or len(query) < 2:
            return Response({'suggestions': []})
        
        suggestions = []
        
        # ========== 1. RESTAURANT SUGGESTIONS ==========
        if not filter_type or filter_type == 'restaurant':
            restaurant_matches = Restaurant.objects.filter(
                name__icontains=query,
                status='active'
            ).prefetch_related('cuisines')[:5]
            
            for restaurant in restaurant_matches:
                # Get cuisine names for display
                cuisine_names = [c.name for c in restaurant.cuisines.all()[:3]]
                cuisine_text = ', '.join(cuisine_names) if cuisine_names else 'Restaurant'
                
                suggestions.append({
                    'type': 'restaurant',
                    'name': restaurant.name,
                    'id': restaurant.restaurant_id,
                    'cuisine': cuisine_text,
                    'rating': float(restaurant.overall_rating) if restaurant.overall_rating else None,
                    'match_type': 'direct'
                })
        
        # ========== 2. RESTAURANTS BY CUISINE ==========
        if not filter_type or filter_type == 'restaurant':
            # Find cuisines matching the query
            cuisine_matches = Cuisine.objects.filter(
                name__icontains=query,
                is_active=True
            )
            
            if cuisine_matches.exists():
                # Get restaurants that have these cuisines
                cuisine_restaurants = Restaurant.objects.filter(
                    cuisines__in=cuisine_matches,
                    status='active'
                ).distinct().prefetch_related('cuisines')[:3]
                
                for restaurant in cuisine_restaurants:
                    # Skip if already added as direct match
                    if any(s.get('id') == restaurant.restaurant_id for s in suggestions if s.get('type') == 'restaurant'):
                        continue
                    
                    # Get the matching cuisine name
                    matching_cuisines = [c.name for c in restaurant.cuisines.all() if query.lower() in c.name.lower()]
                    cuisine_text = matching_cuisines[0] if matching_cuisines else 'Related cuisine'
                    
                    suggestions.append({
                        'type': 'restaurant',
                        'name': restaurant.name,
                        'id': restaurant.restaurant_id,
                        'cuisine': f"Serves {cuisine_text}",
                        'rating': float(restaurant.overall_rating) if restaurant.overall_rating else None,
                        'match_type': 'by_cuisine'
                    })
        
        # ========== 3. RESTAURANTS BY MENU ITEMS ==========
        if not filter_type or filter_type == 'restaurant':
            # Find menu items matching the query
            menu_item_matches = MenuItem.objects.filter(
                name__icontains=query,
                is_available=True,
                category__restaurant__status='active'
            ).select_related('category__restaurant').prefetch_related('category__restaurant__cuisines')[:5]
            
            seen_ids = set([s.get('id') for s in suggestions if s.get('type') == 'restaurant' and s.get('id')])
            
            for item in menu_item_matches:
                restaurant = item.category.restaurant
                if restaurant.restaurant_id in seen_ids:
                    continue
                
                seen_ids.add(restaurant.restaurant_id)
                
                # Get cuisine names
                cuisine_names = [c.name for c in restaurant.cuisines.all()[:2]]
                cuisine_text = ', '.join(cuisine_names) if cuisine_names else ''
                
                suggestions.append({
                    'type': 'restaurant',
                    'name': restaurant.name,
                    'id': restaurant.restaurant_id,
                    'cuisine': cuisine_text,
                    'rating': float(restaurant.overall_rating) if restaurant.overall_rating else None,
                    'menu_item': item.name,
                    'match_type': 'by_menu_item'
                })
        
        # ========== 4. CUISINE SUGGESTIONS ==========
        if filter_type == 'cuisine' or filter_type == '':
            cuisine_suggestions = Cuisine.objects.filter(
                name__icontains=query,
                is_active=True
            )[:3]
            
            for cuisine in cuisine_suggestions:
                # Count restaurants serving this cuisine
                restaurant_count = Restaurant.objects.filter(
                    cuisines=cuisine,
                    status='active'
                ).count()
                
                suggestions.append({
                    'type': 'cuisine',
                    'name': cuisine.name,
                    'id': cuisine.cuisine_id,
                    'cuisine_name': cuisine.name,
                    'restaurant_count': restaurant_count
                })
        
        # ========== 5. MENU ITEM SUGGESTIONS ==========
        if filter_type == 'menu_item' or filter_type == '':
            menu_suggestions = []
            for item in menu_item_matches[:3]:  # Reuse from above
                menu_suggestions.append({
                    'type': 'menu_item',
                    'name': item.name,
                    'id': item.item_id,
                    'restaurant_name': item.category.restaurant.name,
                    'price': str(item.price) if item.price else None
                })
            suggestions.extend(menu_suggestions)
        
        # Sort suggestions: restaurants first, then cuisines, then menu items
        def sort_key(s):
            if s['type'] == 'restaurant':
                match_priority = {'direct': 0, 'by_cuisine': 1, 'by_menu_item': 2}.get(s.get('match_type'), 3)
                return (0, match_priority)
            elif s['type'] == 'cuisine':
                return (1, 0)
            else:  # menu_item
                return (2, 0)
        
        suggestions.sort(key=sort_key)
        
        # Limit total results
        suggestions = suggestions[:limit]
        
        logger.info(f"Returning {len(suggestions)} suggestions")
        
        serializer = SearchSuggestionSerializer(suggestions, many=True)
        return Response({'suggestions': serializer.data})

class RestaurantSuggestionsView(APIView):
    """
    Search suggestions for restaurants only
    Used in the restaurant explorer page
    Returns restaurants based on name, cuisine, or menu items
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        query = request.query_params.get('q', '').strip()
        limit = int(request.query_params.get('limit', 8))

        print("="*50)
        print(f"RestaurantSuggestionsView - Query: '{query}'")
        print(f"Limit: {limit}")
        
        logger.info(f"Restaurant suggestions - Query: '{query}'")
        
        if not query or len(query) < 2:
            print("Query too short, returning empty")
            return Response({'suggestions': []})
        
        suggestions = []
        seen_restaurant_ids = set()
        
        # ========== 1. DIRECT RESTAURANT NAME MATCHES ==========
        restaurant_matches = Restaurant.objects.filter(
            name__icontains=query,
            status='active'
        ).prefetch_related('cuisines')[:5]
        
        for restaurant in restaurant_matches:
            seen_restaurant_ids.add(restaurant.restaurant_id)
            
            # Get cuisine names for display
            cuisine_names = [c.name for c in restaurant.cuisines.all()[:3]]
            cuisine_text = ', '.join(cuisine_names) if cuisine_names else 'Restaurant'
            
            suggestions.append({
                'type': 'restaurant',
                'name': restaurant.name,
                'id': restaurant.restaurant_id,
                'cuisine': cuisine_text,
                'rating': float(restaurant.overall_rating) if restaurant.overall_rating else None,
                'match_type': 'direct'
            })
        
        # ========== 2. RESTAURANTS BY CUISINE ==========
        cuisine_matches = Cuisine.objects.filter(
            name__icontains=query,
            is_active=True
        )
        
        if cuisine_matches.exists():
            restaurants_by_cuisine = Restaurant.objects.filter(
                cuisines__in=cuisine_matches,
                status='active'
            ).distinct().prefetch_related('cuisines')[:5]
            
            for restaurant in restaurants_by_cuisine:
                if restaurant.restaurant_id in seen_restaurant_ids:
                    continue
                    
                seen_restaurant_ids.add(restaurant.restaurant_id)
                
                # Get the matching cuisine name
                matching_cuisines = [c.name for c in restaurant.cuisines.all() if query.lower() in c.name.lower()]
                cuisine_text = matching_cuisines[0] if matching_cuisines else 'Restaurant'
                
                suggestions.append({
                    'type': 'restaurant',
                    'name': restaurant.name,
                    'id': restaurant.restaurant_id,
                    'cuisine': f"Serves {cuisine_text}",
                    'rating': float(restaurant.overall_rating) if restaurant.overall_rating else None,
                    'match_type': 'by_cuisine'
                })
        
        # ========== 3. RESTAURANTS BY MENU ITEMS ==========
        menu_item_matches = MenuItem.objects.filter(
            name__icontains=query,
            is_available=True,
            category__restaurant__status='active'
        ).select_related('category__restaurant').prefetch_related('category__restaurant__cuisines')[:5]
        
        for item in menu_item_matches:
            restaurant = item.category.restaurant
            if restaurant.restaurant_id in seen_restaurant_ids:
                continue
                
            seen_restaurant_ids.add(restaurant.restaurant_id)
            
            # Get cuisine names
            cuisine_names = [c.name for c in restaurant.cuisines.all()[:2]]
            cuisine_text = ', '.join(cuisine_names) if cuisine_names else ''
            
            suggestions.append({
                'type': 'restaurant',
                'name': restaurant.name,
                'id': restaurant.restaurant_id,
                'cuisine': cuisine_text,
                'rating': float(restaurant.overall_rating) if restaurant.overall_rating else None,
                'menu_item': item.name,
                'match_type': 'by_menu_item'
            })
        
        # Limit results
        suggestions = suggestions[:limit]
        print(f"Total suggestions: {len(suggestions)}")
        print(f"Returning: {suggestions}")
        print("="*50)
        
        logger.info(f"Returning {len(suggestions)} restaurant suggestions")
        
        serializer = SearchSuggestionSerializer(suggestions, many=True)
        return Response({'suggestions': serializer.data})

class MenuItemSuggestionsView(APIView):
    """
    Search suggestions for menu items only
    Used in the menu items explorer page
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        query = request.query_params.get('q', '').strip()
        limit = int(request.query_params.get('limit', 8))
        
        logger.info(f"Menu item suggestions - Query: '{query}'")
        
        if not query or len(query) < 2:
            return Response({'suggestions': []})
        
        suggestions = []
        
        # Menu item suggestions
        menu_item_matches = MenuItem.objects.filter(
            name__icontains=query,
            is_available=True,
            category__restaurant__status='active'
        ).select_related('category__restaurant')[:limit]
        
        for item in menu_item_matches:
            suggestions.append({
                'type': 'menu_item',
                'name': item.name,
                'id': item.item_id,
                'restaurant_name': item.category.restaurant.name,
                'price': str(item.price) if item.price else None,
                'description': item.description[:100] if item.description else None
            })
        
        logger.info(f"Returning {len(suggestions)} menu item suggestions")
        
        serializer = SearchSuggestionSerializer(suggestions, many=True)
        return Response({'suggestions': serializer.data})

class CombinedSuggestionsView(APIView):
    """
    Combined search suggestions for restaurants, menu items, and cuisines
    Used in global search
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        query = request.query_params.get('q', '').strip()
        limit = int(request.query_params.get('limit', 8))
        
        logger.info(f"Combined suggestions - Query: '{query}'")
        
        if not query or len(query) < 2:
            return Response({'suggestions': []})
        
        suggestions = []
        
        # ========== RESTAURANT SUGGESTIONS ==========
        restaurant_matches = Restaurant.objects.filter(
            name__icontains=query,
            status='active'
        ).prefetch_related('cuisines')[:3]
        
        for restaurant in restaurant_matches:
            cuisine_names = [c.name for c in restaurant.cuisines.all()[:2]]
            cuisine_text = ', '.join(cuisine_names) if cuisine_names else 'Restaurant'
            
            suggestions.append({
                'type': 'restaurant',
                'name': restaurant.name,
                'id': restaurant.restaurant_id,
                'cuisine': cuisine_text,
                'rating': float(restaurant.overall_rating) if restaurant.overall_rating else None,
            })
        
        # ========== MENU ITEM SUGGESTIONS ==========
        menu_item_matches = MenuItem.objects.filter(
            name__icontains=query,
            is_available=True,
            category__restaurant__status='active'
        ).select_related('category__restaurant')[:3]
        
        for item in menu_item_matches:
            suggestions.append({
                'type': 'menu_item',
                'name': item.name,
                'id': item.item_id,
                'restaurant_name': item.category.restaurant.name,
                'price': str(item.price) if item.price else None,
            })
        
        # ========== CUISINE SUGGESTIONS ==========
        cuisine_matches = Cuisine.objects.filter(
            name__icontains=query,
            is_active=True
        )[:2]
        
        for cuisine in cuisine_matches:
            restaurant_count = Restaurant.objects.filter(
                cuisines=cuisine,
                status='active'
            ).count()
            
            suggestions.append({
                'type': 'cuisine',
                'name': cuisine.name,
                'id': cuisine.cuisine_id,
                'restaurant_count': restaurant_count
            })
        
        # Limit results
        suggestions = suggestions[:limit]
        
        logger.info(f"Returning {len(suggestions)} combined suggestions")
        
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

from django.core.paginator import Paginator, EmptyPage

class DiscoverSearchView(APIView):
    """
    Combined search that returns paginated results for each section
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            # Get search query
            query = request.query_params.get('q', '').strip()
            
            # Get filter parameters
            content_type = request.query_params.get('type', 'all')
            sort_by = request.query_params.get('sort_by', 'relevance')
            dietary = request.query_params.get('dietary', '')
            price_range = request.query_params.get('price_range', '')
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 20))
            
            logger.info(f"Discover search - Query: '{query}', Type: {content_type}, Page: {page}")
            
            # Return empty if query too short
            if not query or len(query) < 2:
                return self._empty_response(query)
            
            # Initialize collections
            all_restaurant_ids = set()
            restaurant_match_info = {}
            
            # Lists for other result types
            matched_cuisines = []
            matched_categories = []
            matched_dishes = []
            
            # Counts for total items
            restaurant_total = 0
            cuisine_total = 0
            category_total = 0
            dish_total = 0
            
            # ===== STEP 1: CHECK RESTAURANTS =====
            logger.info("Step 1: Checking restaurants...")
            restaurant_matches = Restaurant.objects.filter(
                Q(name__icontains=query) | 
                Q(description__icontains=query),
                status='active'
            ).distinct().prefetch_related('cuisines')
            
            restaurant_total = restaurant_matches.count()
            logger.info(f"Found {restaurant_total} restaurants matching by name")
            
            for restaurant in restaurant_matches:
                all_restaurant_ids.add(restaurant.restaurant_id)
                restaurant_match_info[restaurant.restaurant_id] = {
                    'direct_match': True,
                    'has_cuisine': False,
                    'has_category': False,
                    'has_dish': False
                }
            
            # ===== STEP 2: CHECK CUISINES =====
            logger.info("Step 2: Checking cuisines...")
            cuisine_matches = Cuisine.objects.filter(
                name__icontains=query,
                is_active=True
            )
            
            cuisine_total = cuisine_matches.count()
            logger.info(f"Found {cuisine_total} cuisines matching")
            
            if cuisine_total > 0:
                matched_cuisines = list(cuisine_matches)
                
                # Get restaurants with these cuisines
                restaurants_with_cuisine = Restaurant.objects.filter(
                    cuisines__in=cuisine_matches,
                    status='active'
                ).distinct().prefetch_related('cuisines')
                
                for restaurant in restaurants_with_cuisine:
                    all_restaurant_ids.add(restaurant.restaurant_id)
                    if restaurant.restaurant_id not in restaurant_match_info:
                        restaurant_match_info[restaurant.restaurant_id] = {
                            'direct_match': False,
                            'has_cuisine': True,
                            'has_category': False,
                            'has_dish': False
                        }
                    else:
                        restaurant_match_info[restaurant.restaurant_id]['has_cuisine'] = True
            
            # ===== STEP 3: CHECK CATEGORIES =====
            logger.info("Step 3: Checking categories...")
            category_matches = MenuCategory.objects.filter(
                name__icontains=query,
                is_active=True,
                restaurant__status='active'
            ).select_related('restaurant')
            
            category_total = category_matches.count()
            logger.info(f"Found {category_total} categories matching")
            
            if category_total > 0:
                matched_categories = list(category_matches)
                
                # Get restaurants with these categories
                restaurants_with_category = Restaurant.objects.filter(
                    menu_categories__in=category_matches,
                    status='active'
                ).distinct().prefetch_related('cuisines')
                
                for restaurant in restaurants_with_category:
                    all_restaurant_ids.add(restaurant.restaurant_id)
                    if restaurant.restaurant_id not in restaurant_match_info:
                        restaurant_match_info[restaurant.restaurant_id] = {
                            'direct_match': False,
                            'has_cuisine': False,
                            'has_category': True,
                            'has_dish': False
                        }
                    else:
                        restaurant_match_info[restaurant.restaurant_id]['has_category'] = True
            
            # ===== STEP 4: CHECK DISHES =====
            logger.info("Step 4: Checking dishes...")
            dish_matches = MenuItem.objects.filter(
                Q(name__icontains=query) | 
                Q(description__icontains=query),
                is_available=True,
                category__restaurant__status='active'
            ).select_related('category__restaurant')
            
            dish_total = dish_matches.count()
            logger.info(f"Found {dish_total} dishes matching")
            
            if dish_total > 0:
                matched_dishes = list(dish_matches)
                
                # Get restaurants with these dishes
                restaurant_ids_from_dishes = set()
                for dish in dish_matches:
                    if dish.category and dish.category.restaurant:
                        restaurant_ids_from_dishes.add(dish.category.restaurant.restaurant_id)
                
                restaurants_with_dish = Restaurant.objects.filter(
                    restaurant_id__in=restaurant_ids_from_dishes,
                    status='active'
                ).distinct().prefetch_related('cuisines')
                
                for restaurant in restaurants_with_dish:
                    all_restaurant_ids.add(restaurant.restaurant_id)
                    if restaurant.restaurant_id not in restaurant_match_info:
                        restaurant_match_info[restaurant.restaurant_id] = {
                            'direct_match': False,
                            'has_cuisine': False,
                            'has_category': False,
                            'has_dish': True
                        }
                    else:
                        restaurant_match_info[restaurant.restaurant_id]['has_dish'] = True
            
            # ===== STEP 5: APPLY DIETARY FILTER TO RESTAURANTS =====
            if dietary and all_restaurant_ids:
                logger.info(f"Applying dietary filter: {dietary}")
                restaurant_ids_with_dietary = self._get_restaurants_with_dietary_options(dietary)
                
                if restaurant_ids_with_dietary:
                    all_restaurant_ids = all_restaurant_ids.intersection(restaurant_ids_with_dietary)
                    logger.info(f"After dietary filter: {len(all_restaurant_ids)} restaurants remain")
            
            # ===== STEP 6: BUILD RESTAURANTS RESULT WITH PAGINATION =====
            restaurant_results = []
            restaurant_pagination = None
            if all_restaurant_ids and (content_type in ['all', 'restaurants']):
                logger.info(f"Building restaurants result with {len(all_restaurant_ids)} unique restaurants")
                
                restaurants = Restaurant.objects.filter(
                    restaurant_id__in=all_restaurant_ids,
                    status='active'
                ).distinct().prefetch_related('cuisines')
                
                def sort_key(restaurant):
                    info = restaurant_match_info.get(restaurant.restaurant_id, {})
                    if info.get('direct_match'):
                        return 0
                    if info.get('has_cuisine'):
                        return 1
                    if info.get('has_category'):
                        return 2
                    if info.get('has_dish'):
                        return 3
                    return 4
                
                sorted_restaurants = sorted(restaurants, key=sort_key)
                
                # Create paginator for all restaurants
                paginator = Paginator(sorted_restaurants, page_size)
                
                # Get requested page
                try:
                    page_obj = paginator.page(page)
                except EmptyPage:
                    page_obj = paginator.page(paginator.num_pages)
                
                # Serialize the current page
                serializer = RestaurantSearchSerializer(
                    page_obj.object_list,
                    many=True,
                    context={'request': request}
                )
                
                restaurant_results = serializer.data
                
                # Add match info to serialized data
                for i, restaurant in enumerate(page_obj.object_list):
                    if i < len(restaurant_results):
                        info = restaurant_match_info.get(restaurant.restaurant_id, {})
                        restaurant_results[i]['direct_match'] = info.get('direct_match', False)
                        restaurant_results[i]['has_cuisine'] = info.get('has_cuisine', False)
                        restaurant_results[i]['has_category'] = info.get('has_category', False)
                        restaurant_results[i]['has_dish'] = info.get('has_dish', False)
                
                restaurant_pagination = {
                    'current_page': page_obj.number,
                    'total_pages': paginator.num_pages,
                    'total_items': paginator.count,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous()
                }
            
            # ===== STEP 7: BUILD DISHES RESULT WITH PAGINATION =====
            dish_results = []
            dish_pagination = None
            if matched_dishes and (content_type in ['all', 'dishes']):
                logger.info(f"Building dishes result with {len(matched_dishes)} dishes")
                
                dishes_queryset = MenuItem.objects.filter(
                    item_id__in=[d.item_id for d in matched_dishes]
                ).select_related('category__restaurant')
                
                if dietary:
                    dishes_queryset = self._apply_dietary_filter_to_items_safe(dishes_queryset, dietary)
                
                if price_range:
                    dishes_queryset = self._apply_price_filter_to_items(dishes_queryset, price_range)
                
                if sort_by == 'price_low':
                    dishes_queryset = dishes_queryset.order_by('price')
                elif sort_by == 'price_high':
                    dishes_queryset = dishes_queryset.order_by('-price')
                elif sort_by == 'popularity':
                    dishes_queryset = dishes_queryset.order_by('-popularity_score')
                
                # Create paginator
                paginator = Paginator(dishes_queryset, page_size)
                
                try:
                    page_obj = paginator.page(page)
                except EmptyPage:
                    page_obj = paginator.page(paginator.num_pages)
                
                serializer = MenuItemSearchSerializer(
                    page_obj.object_list,
                    many=True,
                    context={'request': request}
                )
                dish_results = serializer.data
                
                dish_pagination = {
                    'current_page': page_obj.number,
                    'total_pages': paginator.num_pages,
                    'total_items': paginator.count,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous()
                }
            
            # ===== STEP 8: BUILD CUISINES RESULT WITH PAGINATION =====
            cuisine_results = []
            cuisine_pagination = None
            if matched_cuisines and (content_type in ['all', 'cuisines']):
                logger.info(f"Building cuisines result with {len(matched_cuisines)} cuisines")
                
                # Create paginator for cuisines
                paginator = Paginator(matched_cuisines, page_size)
                
                try:
                    page_obj = paginator.page(page)
                except EmptyPage:
                    page_obj = paginator.page(paginator.num_pages)
                
                cuisine_data = []
                for cuisine in page_obj.object_list:
                    restaurant_count = Restaurant.objects.filter(
                        cuisines=cuisine,
                        status='active'
                    ).count()
                    
                    cuisine_data.append({
                        'cuisine_id': cuisine.cuisine_id,
                        'name': cuisine.name,
                        'description': cuisine.description,
                        'restaurant_count': restaurant_count,
                        'type': 'cuisine',
                        'icon': self._get_cuisine_icon(cuisine.name)
                    })
                cuisine_results = cuisine_data
                
                cuisine_pagination = {
                    'current_page': page_obj.number,
                    'total_pages': paginator.num_pages,
                    'total_items': paginator.count,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous()
                }
            
            # ===== STEP 9: BUILD CATEGORIES RESULT WITH PAGINATION =====
            category_results = []
            category_pagination = None
            if matched_categories and (content_type in ['all', 'categories']):
                logger.info(f"Building categories result with {len(matched_categories)} categories")
                
                # Create paginator for categories
                paginator = Paginator(matched_categories, page_size)
                
                try:
                    page_obj = paginator.page(page)
                except EmptyPage:
                    page_obj = paginator.page(paginator.num_pages)
                
                category_data = []
                for category in page_obj.object_list:
                    item_count = category.menu_items.filter(is_available=True).count()
                    
                    category_data.append({
                        'category_id': category.category_id,
                        'name': category.name,
                        'restaurant_name': category.restaurant.name if category.restaurant else '',
                        'restaurant_id': category.restaurant.restaurant_id if category.restaurant else None,
                        'item_count': item_count,
                        'type': 'category',
                        'description': category.description
                    })
                category_results = category_data
                
                category_pagination = {
                    'current_page': page_obj.number,
                    'total_pages': paginator.num_pages,
                    'total_items': paginator.count,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous()
                }
            
            # ===== BUILD FINAL RESPONSE =====
            results = {
                'restaurants': restaurant_results,
                'menu_items': dish_results,
                'cuisines': cuisine_results,
                'categories': category_results
            }
            
            # Build sections for UI
            sections = []
            
            if dish_total > 0:
                sections.append({
                    'type': 'menu_items',
                    'title': 'Dishes',
                    'icon': '🍽️',
                    'color': '#4cc9f0',
                    'total_count': dish_total
                })
            
            if category_total > 0:
                sections.append({
                    'type': 'categories',
                    'title': 'Categories',
                    'icon': '📋',
                    'color': '#F9C74F',
                    'total_count': category_total
                })
            
            if cuisine_total > 0:
                sections.append({
                    'type': 'cuisines',
                    'title': 'Cuisines',
                    'icon': '🍜',
                    'color': '#90BE6D',
                    'total_count': cuisine_total
                })
            
            if len(all_restaurant_ids) > 0:
                sections.append({
                    'type': 'restaurants',
                    'title': 'Restaurants',
                    'icon': '🏢',
                    'color': '#e63946',
                    'total_count': len(all_restaurant_ids)
                })
            
            total_results = len(restaurant_results) + len(dish_results) + len(cuisine_results) + len(category_results)
            
            logger.info(f"=== DISCOVER SEARCH RESULTS FOR '{query}' ===")
            logger.info(f"Restaurants: {len(restaurant_results)} of {len(all_restaurant_ids)} (Page {restaurant_pagination.get('current_page', 1) if restaurant_pagination else 1})")
            logger.info(f"Dishes: {len(dish_results)} of {dish_total} (Page {dish_pagination.get('current_page', 1) if dish_pagination else 1})")
            logger.info(f"Cuisines: {len(cuisine_results)} of {cuisine_total} (Page {cuisine_pagination.get('current_page', 1) if cuisine_pagination else 1})")
            logger.info(f"Categories: {len(category_results)} of {category_total} (Page {category_pagination.get('current_page', 1) if category_pagination else 1})")
            
            return Response({
                'query': query,
                'total_results': total_results,
                'sections': sections,
                'results': results,
                'pagination': {
                    'restaurants': restaurant_pagination,
                    'menu_items': dish_pagination,
                    'cuisines': cuisine_pagination,
                    'categories': category_pagination
                },
                'applied_filters': {
                    'type': content_type,
                    'dietary': dietary,
                    'price_range': price_range,
                    'sort_by': sort_by
                }
            })
            
        except Exception as e:
            logger.error(f"Unexpected error in discover search: {str(e)}")
            import traceback
            traceback.print_exc()
            return self._empty_response(query)
    
    def _empty_response(self, query):
        return Response({
            'query': query,
            'total_results': 0,
            'sections': [],
            'results': {
                'restaurants': [],
                'menu_items': [],
                'cuisines': [],
                'categories': []
            },
            'pagination': {
                'restaurants': None,
                'menu_items': None,
                'cuisines': None,
                'categories': None
            },
            'applied_filters': {
                'type': 'all',
                'dietary': '',
                'price_range': '',
                'sort_by': 'relevance'
            }
        })
    
    def _get_restaurants_with_dietary_options(self, dietary):
        try:
            dietary_list = [d.strip() for d in dietary.split(',') if d.strip()]
            if not dietary_list:
                return set()
            
            from django.db.models import Q
            diet_condition = Q()
            
            if 'vegetarian' in dietary_list:
                diet_condition |= Q(is_vegetarian=True)
            if 'vegan' in dietary_list:
                diet_condition |= Q(is_vegan=True)
            if 'gluten_free' in dietary_list:
                diet_condition |= Q(is_gluten_free=True)
            
            if diet_condition:
                matching_menu_items = MenuItem.objects.filter(
                    diet_condition,
                    is_available=True
                ).select_related('category__restaurant')
                
                restaurant_ids = set()
                for item in matching_menu_items:
                    if item.category and item.category.restaurant:
                        restaurant_ids.add(item.category.restaurant.restaurant_id)
                
                return restaurant_ids
            
            return set()
        except Exception as e:
            logger.error(f"Error getting restaurants with dietary options: {str(e)}")
            return set()
    
    def _apply_dietary_filter_to_items_safe(self, queryset, dietary):
        try:
            dietary_list = [d.strip() for d in dietary.split(',') if d.strip()]
            
            if 'vegetarian' in dietary_list:
                queryset = queryset.filter(is_vegetarian=True)
            if 'vegan' in dietary_list:
                queryset = queryset.filter(is_vegan=True)
            if 'gluten_free' in dietary_list:
                queryset = queryset.filter(is_gluten_free=True)
            
            return queryset
        except Exception as e:
            logger.error(f"Error in dietary filter for items: {str(e)}")
            return queryset
    
    def _apply_price_filter_to_items(self, queryset, price_range):
        try:
            min_price, max_price = self._parse_price_range(price_range)
            return queryset.filter(price__gte=min_price, price__lte=max_price)
        except Exception as e:
            logger.error(f"Error in price filter for items: {str(e)}")
            return queryset
    
    def _parse_price_range(self, price_range):
        ranges = {
            '$': (0, 10),
            '$$': (10, 20),
            '$$$': (20, 35),
            '$$$$': (35, 100)
        }
        return ranges.get(price_range, (0, 1000))
    
    def _get_cuisine_icon(self, cuisine_name):
        cuisine_icons = {
            'italian': '🍕',
            'chinese': '🥡',
            'japanese': '🍣',
            'mexican': '🌮',
            'indian': '🍛',
            'thai': '🍜',
            'american': '🍔',
            'french': '🥖',
            'greek': '🥙',
            'mediterranean': '🥗',
        }
        
        cuisine_lower = cuisine_name.lower()
        for key, icon in cuisine_icons.items():
            if key in cuisine_lower:
                return icon
        
        return '🍽️'


class LoadMoreSectionView(APIView):
    """
    Dedicated endpoint for loading more results for a specific section
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        section_type = request.query_params.get('section')
        query = request.query_params.get('q', '').strip()
        page = int(request.query_params.get('page', 2))
        page_size = int(request.query_params.get('page_size', 20))
        
        filters = {
            'dietary': request.query_params.get('dietary', ''),
            'price_range': request.query_params.get('price_range', ''),
            'location': request.query_params.get('location', '')
        }
        
        logger.info(f"LoadMoreSectionView - Section: {section_type}, Query: '{query}', Page: {page}")
        
        # Call the method directly
        results = self.get_section_results(section_type, query, page, filters)
        
        if not results:
            return Response({'error': 'Invalid section type'}, status=400)
        
        return Response(results)
    
    def get_section_results(self, section_type, query, page, filters):
        """Get paginated results for a specific section"""
        from ..serializers import RestaurantSearchSerializer, MenuItemSearchSerializer
        from django.core.paginator import Paginator, EmptyPage
        from django.db.models import Q  # IMPORT Q HERE
        
        queryset = None
        serializer_class = None
        
        if section_type == 'restaurants':
            # First get all restaurant IDs that match the search
            restaurant_ids = set()
            
            # Restaurants matching by name
            name_matches = Restaurant.objects.filter(
                Q(name__icontains=query) | Q(description__icontains=query),
                status='active'
            ).values_list('restaurant_id', flat=True)
            restaurant_ids.update(name_matches)
            
            # Restaurants with matching cuisines
            cuisine_matches = Restaurant.objects.filter(
                cuisines__name__icontains=query,
                status='active'
            ).values_list('restaurant_id', flat=True)
            restaurant_ids.update(cuisine_matches)
            
            # Restaurants with matching menu items
            dish_matches = MenuItem.objects.filter(
                Q(name__icontains=query) | Q(description__icontains=query),
                is_available=True,
                category__restaurant__status='active'
            ).values_list('category__restaurant__restaurant_id', flat=True)
            restaurant_ids.update(dish_matches)
            
            # Restaurants with matching categories
            category_matches = MenuCategory.objects.filter(
                name__icontains=query,
                is_active=True,
                restaurant__status='active'
            ).values_list('restaurant__restaurant_id', flat=True)
            restaurant_ids.update(category_matches)
            
            # Get the full restaurant objects
            queryset = Restaurant.objects.filter(
                restaurant_id__in=restaurant_ids,
                status='active'
            ).distinct().prefetch_related('cuisines')
            
            serializer_class = RestaurantSearchSerializer
            
        elif section_type == 'menu_items':
            queryset = MenuItem.objects.filter(
                Q(name__icontains=query) | Q(description__icontains=query),
                is_available=True,
                category__restaurant__status='active'
            ).distinct().select_related('category__restaurant')
            serializer_class = MenuItemSearchSerializer
            
        elif section_type == 'cuisines':
            queryset = Cuisine.objects.filter(
                name__icontains=query,
                is_active=True
            ).distinct()
            serializer_class = None
            
        elif section_type == 'categories':
            queryset = MenuCategory.objects.filter(
                name__icontains=query,
                is_active=True,
                restaurant__status='active'
            ).distinct().select_related('restaurant')
            serializer_class = None
            
        else:
            return None
        
        # Apply filters
        if filters.get('dietary') and section_type == 'menu_items':
            dietary_list = [d.strip() for d in filters['dietary'].split(',') if d.strip()]
            if 'vegetarian' in dietary_list:
                queryset = queryset.filter(is_vegetarian=True)
            if 'vegan' in dietary_list:
                queryset = queryset.filter(is_vegan=True)
            if 'gluten_free' in dietary_list:
                queryset = queryset.filter(is_gluten_free=True)
        
        if filters.get('price_range') and section_type == 'menu_items':
            min_price, max_price = self._parse_price_range(filters['price_range'])
            queryset = queryset.filter(price__gte=min_price, price__lte=max_price)
        
        # Create paginator
        paginator = Paginator(queryset, 20)
        
        logger.info(f"{section_type} load more - Total found: {paginator.count}")
        logger.info(f"{section_type} load more - Total pages: {paginator.num_pages}")
        logger.info(f"{section_type} load more - Requested page: {page}")
        
        try:
            page_obj = paginator.page(page)
            logger.info(f"{section_type} load more - Items on page {page}: {len(page_obj.object_list)}")
        except EmptyPage:
            logger.info(f"{section_type} load more - Page {page} is empty, returning last page")
            page_obj = paginator.page(paginator.num_pages)
        
        # Serialize items based on type
        items = []
        if serializer_class:
            serializer = serializer_class(page_obj.object_list, many=True, context={'request': self.request})
            items = serializer.data
        else:
            if section_type == 'cuisines':
                for cuisine in page_obj.object_list:
                    items.append({
                        'cuisine_id': cuisine.cuisine_id,
                        'name': cuisine.name,
                        'description': cuisine.description,
                        'restaurant_count': Restaurant.objects.filter(
                            cuisines=cuisine,
                            status='active'
                        ).count(),
                        'type': 'cuisine',
                        'icon': self._get_cuisine_icon(cuisine.name)
                    })
            elif section_type == 'categories':
                for category in page_obj.object_list:
                    items.append({
                        'category_id': category.category_id,
                        'name': category.name,
                        'description': category.description,
                        'restaurant_name': category.restaurant.name if category.restaurant else '',
                        'restaurant_id': category.restaurant.restaurant_id if category.restaurant else None,
                        'item_count': category.menu_items.filter(is_available=True).count(),
                        'type': 'category'
                    })
        
        logger.info(f"LoadMoreSectionView - Returning {len(items)} items for {section_type} page {page}")
        
        return {
            'items': items,
            'pagination': {
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'total_items': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous()
            }
        }
    
    def _parse_price_range(self, price_range):
        ranges = {
            '$': (0, 10),
            '$$': (10, 20),
            '$$$': (20, 35),
            '$$$$': (35, 100)
        }
        return ranges.get(price_range, (0, 1000))
    
    def _get_cuisine_icon(self, cuisine_name):
        cuisine_icons = {
            'italian': '🍕',
            'chinese': '🥡',
            'japanese': '🍣',
            'mexican': '🌮',
            'indian': '🍛',
            'thai': '🍜',
            'american': '🍔',
            'french': '🥖',
            'greek': '🥙',
            'mediterranean': '🥗',
        }
        
        cuisine_lower = cuisine_name.lower()
        for key, icon in cuisine_icons.items():
            if key in cuisine_lower:
                return icon
        
        return '🍽️'
