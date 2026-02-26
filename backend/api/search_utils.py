import math
from django.db.models import Q
from geopy.distance import geodesic
from decimal import Decimal, InvalidOperation

class SearchUtils:
    @staticmethod
    def calculate_distance(lat1, lon1, lat2, lon2):
        """
        Calculate the distance between two points in kilometers using Haversine formula
        """
        try:
            # Convert to float if they're strings
            lat1 = float(lat1)
            lon1 = float(lon1)
            lat2 = float(lat2)
            lon2 = float(lon2)
            
            # Radius of the Earth in kilometers
            R = 6371.0
            
            # Convert to radians
            lat1_rad = math.radians(lat1)
            lon1_rad = math.radians(lon1)
            lat2_rad = math.radians(lat2)
            lon2_rad = math.radians(lon2)
            
            # Differences
            dlat = lat2_rad - lat1_rad
            dlon = lon2_rad - lon1_rad
            
            # Haversine formula
            a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            distance = R * c
            
            return round(distance, 2)
        except (ValueError, TypeError) as e:
            print(f"Error calculating distance: {e}")
            return None
    
    @staticmethod
    def get_restaurant_branches_nearby(lat, lng, radius_km):
        """
        Get restaurant branches within radius (simplified - in production use PostGIS)
        """
        from .models import Branch
        
        # This is a simplified version - in production, use proper geospatial queries
        branches = Branch.objects.filter(
            is_active=True,
            address__latitude__isnull=False,
            address__longitude__isnull=False
        ).select_related('restaurant', 'address')
        
        # Filter in Python (not efficient for large datasets - use PostGIS in production)
        nearby_branches = []
        for branch in branches:
            distance = SearchUtils.calculate_distance(
                lat, lng,
                float(branch.address.latitude),
                float(branch.address.longitude)
            )
            if distance and distance <= radius_km:
                nearby_branches.append(branch)
        
        return nearby_branches
    
    @staticmethod
    def get_restaurants_by_city(city_name, limit=50):
        """Get restaurants in a specific city - NEW PRACTICAL METHOD"""
        from .models import Restaurant
        
        restaurants = Restaurant.objects.filter(
            status='active',
            branches__address__city__icontains=city_name,
            branches__is_active=True
        ).distinct().prefetch_related('branches', 'branches__address')[:limit]
        
        return restaurants
    
    @staticmethod
    def get_price_range_filter(price_range):
        """Convert price range to actual price filters"""
        price_filters = {
            '$': (0, 10),      # Budget: $0-$10
            '$$': (10, 25),    # Moderate: $10-$25
            '$$$': (25, 50),   # Expensive: $25-$50
            '$$$$': (50, 1000) # Premium: $50+
        }
        return price_filters.get(price_range, (0, 1000))
    
    @staticmethod
    def calculate_relevance_score(restaurant, query, user_location=None):
        """Enhanced relevance scoring with location priority"""
        score = 0.0
        
        # Text match scoring (increased weights for better differentiation)
        if query:
            query_lower = query.lower()
            name_match = restaurant.name.lower()
            desc_match = restaurant.description.lower() if restaurant.description else ""
            
            # Exact match bonus
            if query_lower == name_match:
                score += 150
            elif query_lower in name_match:
                score += 100
            elif name_match.startswith(query_lower):
                score += 90
            elif query_lower in desc_match:
                score += 40
        
        # Rating scoring (exponential bonus for high ratings)
        rating = getattr(restaurant, 'overall_rating', 0)
        if rating:
            try:
                rating = float(rating)
                score += (rating ** 2) * 15  # 4.5★ gets more than 2× 3.0★
            except (ValueError, TypeError):
                pass
        
        # Featured/verified bonus
        if getattr(restaurant, 'is_featured', False):
            score += 60  # Increased from 50
        if getattr(restaurant, 'is_verified', False):
            score += 40  # Increased from 30
        
        # Review count scoring (logarithmic to prevent domination by large counts)
        total_reviews = getattr(restaurant, 'total_reviews', 0)
        if total_reviews and total_reviews > 0:
            try:
                reviews_score = min(math.log(float(total_reviews) + 1) * 8, 30)
                score += reviews_score
            except (ValueError, TypeError):
                pass
        
        # Location priority scoring if coordinates provided
        if user_location and 'latitude' in user_location and 'longitude' in user_location:
            location_score = SearchUtils.calculate_location_priority(
                user_location['latitude'], 
                user_location['longitude'], 
                restaurant
            )
            score += location_score
        
        return round(score, 2)
    
    @staticmethod
    def calculate_location_priority(latitude, longitude, restaurant):
        """Calculate priority score based on location relevance - NEW METHOD"""
        if latitude is None or longitude is None:
            return 0
        
        try:
            # Calculate distance to nearest branch
            distances = []
            for branch in restaurant.branches.all():
                if branch.address.latitude and branch.address.longitude:
                    dist = SearchUtils.calculate_distance(
                        latitude, longitude,
                        float(branch.address.latitude), float(branch.address.longitude)
                    )
                    if dist is not None:
                        distances.append(dist)
            
            if not distances:
                return 0
            
            min_distance = min(distances)
            
            # Convert distance to priority score (closer = higher score)
            # Uses exponential decay for better distance differentiation
            if min_distance <= 2:    # Within 2km - very high priority
                return 120
            elif min_distance <= 5:  # Within 5km - high priority
                return 90
            elif min_distance <= 10: # Within 10km - medium priority
                return 60
            elif min_distance <= 20: # Within 20km - low priority
                return 30
            else:                    # Beyond 20km - minimal priority
                return 10
                
        except (ValueError, TypeError):
            return 0
    
    @staticmethod
    def enhance_restaurant_with_location(restaurant, latitude, longitude):
        """Add location-based information to restaurant object - NEW METHOD"""
        if latitude is not None and longitude is not None:
            try:
                distances = []
                open_branches = []
                
                for branch in restaurant.branches.all():
                    if branch.address.latitude and branch.address.longitude:
                        dist = SearchUtils.calculate_distance(
                            latitude, longitude,
                            float(branch.address.latitude), float(branch.address.longitude)
                        )
                        if dist is not None:
                            distances.append(dist)
                            if branch.is_open_now():
                                open_branches.append(branch)
                
                if distances:
                    restaurant.distance_km = round(min(distances), 2)
                    restaurant.nearest_branch_distance = min(distances)
                    restaurant.has_open_branch = len(open_branches) > 0
                    restaurant.open_branches_count = len(open_branches)
            except (ValueError, TypeError):
                pass
        
        # Add open status
        restaurant.is_open_now = any(
            branch.is_open_now() for branch in restaurant.branches.all() 
            if branch.is_active
        )
        
        return restaurant

class RestaurantSearchEngine:
    """Enhanced search engine with better location handling"""
    
    def __init__(self, filters):
        self.filters = filters
        self.query = filters.get('query', '').strip()
    
    def search(self):
        from .models import Restaurant
        
        # Start with base queryset
        queryset = Restaurant.objects.filter(status='active').prefetch_related(
            'cuisines', 'branches', 'branches__address'
        )

        # Enhanced search by name, cuisine, and menu items
        if self.query:
            from django.db.models import Q
            from .models import Cuisine, MenuItem
            
            search_terms = self.query.split()
            restaurant_q = Q()
            
            for term in search_terms:
                if len(term) < 2:
                    continue
                restaurant_q |= Q(name__icontains=term)
            
            # Find by cuisine
            cuisine_ids = Cuisine.objects.filter(
                name__icontains=self.query
            ).values_list('cuisine_id', flat=True)
            
            # Find by menu item
            restaurant_ids_by_menu = MenuItem.objects.filter(
                name__icontains=self.query,
                is_available=True
            ).values_list('category__restaurant_id', flat=True).distinct()
            
            # Combine all conditions
            final_q = restaurant_q
            if cuisine_ids:
                final_q |= Q(cuisines__cuisine_id__in=cuisine_ids)
            if restaurant_ids_by_menu:
                final_q |= Q(restaurant_id__in=restaurant_ids_by_menu)
            
            queryset = queryset.filter(final_q).distinct()
        
        # Apply city filter if no coordinates but city provided
        if not self.filters.get('latitude') and self.filters.get('city'):
            city_restaurants = SearchUtils.get_restaurants_by_city(self.filters['city'])
            restaurant_ids = [r.restaurant_id for r in city_restaurants]
            queryset = queryset.filter(restaurant_id__in=restaurant_ids)
        
        # Apply text search
        if self.query:
            queryset = self._apply_text_search(queryset)
        
        # Apply location filter
        if self.filters.get('latitude') and self.filters.get('longitude'):
            queryset = self._apply_location_filter(queryset)
        
        # Apply other filters
        queryset = self._apply_filters(queryset)
        
        # Calculate relevance and distance
        restaurants_with_scores = []
        user_location = None
        if self.filters.get('latitude') and self.filters.get('longitude'):
            user_location = {
                'latitude': self.filters['latitude'],
                'longitude': self.filters['longitude']
            }
        
        for restaurant in queryset:
            restaurant = SearchUtils.enhance_restaurant_with_location(
                restaurant, 
                self.filters.get('latitude'), 
                self.filters.get('longitude')
            )
            
            relevance_score = SearchUtils.calculate_relevance_score(
                restaurant, self.query, user_location
            )
            
            restaurants_with_scores.append({
                'restaurant': restaurant,
                'relevance_score': relevance_score,
                'distance_km': getattr(restaurant, 'distance_km', None),
                'is_open_now': getattr(restaurant, 'is_open_now', False)
            })
        
        # Sort results (but don't paginate internally)
        sorted_results = self._sort_results(restaurants_with_scores)
        
        # RETURN ALL RESULTS - DRF will handle pagination
        return sorted_results, len(sorted_results)
    
    def _apply_text_search(self, queryset):
        """Enhanced text search with better term handling"""
        if not self.query:
            return queryset
        
        search_terms = [term.strip() for term in self.query.split() if term.strip()]
        if not search_terms:
            return queryset
        
        q_objects = Q()
        
        for term in search_terms:
            # Exact phrase matching for quoted terms
            if term.startswith('"') and term.endswith('"'):
                exact_term = term[1:-1]
                q_objects |= Q(name__icontains=exact_term)
                q_objects |= Q(description__icontains=exact_term)
                q_objects |= Q(cuisines__name__icontains=exact_term)
            else:
                # Individual term matching
                q_objects |= Q(name__icontains=term)
                q_objects |= Q(description__icontains=term)
                q_objects |= Q(cuisines__name__icontains=term)
        
        return queryset.filter(q_objects).distinct()
    
    def _apply_location_filter(self, queryset):
        """Location filter with fallback to city"""
        latitude = self.filters['latitude']
        longitude = self.filters['longitude']
        radius_km = self.filters.get('radius_km', 10)
        
        # Get nearby branches
        nearby_branches = SearchUtils.get_restaurant_branches_nearby(
            latitude, longitude, radius_km
        )
        
        # Get restaurant IDs from nearby branches
        restaurant_ids = [branch.restaurant_id for branch in nearby_branches]
        
        # If no nearby restaurants but city is provided, fallback to city
        if not restaurant_ids and self.filters.get('city'):
            city_restaurants = SearchUtils.get_restaurants_by_city(self.filters['city'])
            restaurant_ids = [r.restaurant_id for r in city_restaurants]
        
        return queryset.filter(restaurant_id__in=restaurant_ids) if restaurant_ids else queryset.none()
    
    def _apply_filters(self, queryset):
        """Apply various filters with enhanced logic"""
        # Cuisine filter
        if self.filters.get('cuisine'):
            queryset = queryset.filter(cuisines__name__icontains=self.filters['cuisine'])
        
        # Rating filter
        if self.filters.get('min_rating'):
            queryset = queryset.filter(overall_rating__gte=self.filters['min_rating'])
        
        # Open now filter - enhanced with location-aware opening hours
        if self.filters.get('is_open_now'):
            from django.utils import timezone
            current_time = timezone.now()
            
            # Filter restaurants with branches currently open
            restaurant_ids = []
            for restaurant in queryset:
                for branch in restaurant.branches.all():
                    if branch.is_open_now():
                        restaurant_ids.append(restaurant.restaurant_id)
                        break
            
            queryset = queryset.filter(restaurant_id__in=restaurant_ids)
        
        return queryset.distinct()
    
    def _sort_results(self, restaurants_with_scores):
        """Enhanced sorting with better distance handling"""
        sort_by = self.filters.get('sort_by', 'relevance')
        
        if sort_by == 'distance':
            # Sort by distance, but prioritize open restaurants
            return sorted(restaurants_with_scores, 
                         key=lambda x: (
                             x['distance_km'] or float('inf'),
                             not x.get('is_open_now', False),
                             -x['relevance_score']
                         ))
        
        elif sort_by == 'rating':
            # Sort by rating, prioritize high-rated open restaurants
            return sorted(restaurants_with_scores, 
                         key=lambda x: (
                             -x['restaurant'].overall_rating,
                             not x.get('is_open_now', False),
                             -x['relevance_score']
                         ))
        
        elif sort_by == 'delivery_time':
            # Estimate delivery time based on distance and preparation time
            return sorted(restaurants_with_scores,
                         key=lambda x: (
                             x['distance_km'] or float('inf') + 30,  # 30min prep time estimate
                             -x['relevance_score']
                         ))
        
        else:  # relevance (default)
            # Sort by relevance score, then distance, then open status
            return sorted(restaurants_with_scores, 
                         key=lambda x: (
                             -x['relevance_score'],
                             x['distance_km'] or float('inf'),
                             not x.get('is_open_now', False)
                         ))