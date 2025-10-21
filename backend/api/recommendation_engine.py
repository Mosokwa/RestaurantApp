import math
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from django.db.models import Q, Count, Avg, Sum
from django.utils import timezone
from decimal import Decimal

from api.models import MenuItem

class RecommendationEngine:
    def __init__(self):
        self.min_similarity_threshold = 0.1
        self.recent_days = 30  # Consider behaviors from last 30 days as recent
        
    def calculate_user_preferences(self, user):
        """
        Calculate and update user preferences based on their behavior history
        """
        from .models import UserBehavior, UserPreference, Order, OrderItem
        
        # Get user behaviors from last 6 months
        six_months_ago = timezone.now() - timedelta(days=180)
        behaviors = UserBehavior.objects.filter(
            user=user, 
            created_at__gte=six_months_ago
        )
        
        # Get order history for more detailed analysis
        orders = Order.objects.filter(
            customer__user=user,
            order_placed_at__gte=six_months_ago
        )
        
        preferences, created = UserPreference.objects.get_or_create(user=user)
        
        # Calculate cuisine preferences
        cuisine_scores = self._calculate_cuisine_preferences(behaviors, orders)
        preferences.cuisine_scores = cuisine_scores
        
        # Calculate dietary preferences
        dietary_weights = self._calculate_dietary_preferences(behaviors, orders)
        preferences.dietary_weights = dietary_weights
        
        # Calculate price preferences
        price_prefs = self._calculate_price_preferences(orders)
        preferences.price_preferences = price_prefs
        
        # Calculate order patterns
        order_metrics = self._calculate_order_metrics(orders)
        preferences.avg_order_value = order_metrics['avg_order_value']
        preferences.order_frequency_days = order_metrics['order_frequency_days']
        preferences.preferred_order_times = order_metrics['preferred_order_times']
        
        preferences.save()
        return preferences
    
    def _calculate_cuisine_preferences(self, behaviors, orders):
        """Calculate weighted cuisine preferences based on user behavior"""
        cuisine_weights = defaultdict(float)
        total_weight = 0
        
        # Weight different behavior types
        behavior_weights = {
            'order': 5.0,      # Highest weight for actual orders
            'rating': 4.0,     # High weight for ratings
            'favorite': 3.0,   # Medium weight for favorites
            'view': 1.0,       # Low weight for views
        }
        
        # Process behaviors
        for behavior in behaviors:
            if behavior.restaurant and behavior.restaurant.cuisines.exists():
                weight = behavior_weights.get(behavior.behavior_type, 1.0)
                
                # Apply time decay (recent behaviors weigh more)
                days_ago = (timezone.now() - behavior.created_at).days
                time_decay = max(0.1, 1.0 - (days_ago / 180.0))  # Linear decay over 6 months
                
                for cuisine in behavior.restaurant.cuisines.all():
                    cuisine_weights[cuisine.name] += weight * time_decay
                    total_weight += weight * time_decay
        
        # Process orders for more detailed cuisine analysis
        for order in orders:
            if order.restaurant.cuisines.exists():
                # Higher weight for completed orders
                order_weight = 10.0 if order.status == 'delivered' else 2.0
                
                for cuisine in order.restaurant.cuisines.all():
                    cuisine_weights[cuisine.name] += order_weight
                    total_weight += order_weight
        
        # Normalize scores to 0-1 range
        if total_weight > 0:
            return {cuisine: float(weight / total_weight) 
                   for cuisine, weight in cuisine_weights.items()}
        
        return {}
    
    def _calculate_dietary_preferences(self, behaviors, orders):
        """Calculate dietary preference weights"""
        dietary_weights = defaultdict(float)
        total_interactions = 0
        
        # Analyze menu items from behaviors and orders
        all_menu_items = []
        
        # Get menu items from behaviors
        for behavior in behaviors:
            if behavior.menu_item:
                all_menu_items.append(behavior.menu_item)
        
        # Get menu items from orders
        for order in orders:
            for order_item in order.order_items.all():
                all_menu_items.append(order_item.menu_item)
        
        # Calculate dietary preferences
        for item in all_menu_items:
            total_interactions += 1
            
            if item.is_vegetarian:
                dietary_weights['vegetarian'] += 1
            if item.is_vegan:
                dietary_weights['vegan'] += 1
            if item.is_gluten_free:
                dietary_weights['gluten_free'] += 1
            if item.is_spicy:
                dietary_weights['spicy'] += 1
        
        # Normalize weights
        if total_interactions > 0:
            return {pref: float(count / total_interactions) 
                   for pref, count in dietary_weights.items()}
        
        return {}
    
    def _calculate_price_preferences(self, orders):
        """Calculate user's price range preferences"""
        completed_orders = orders.filter(status='delivered')
        
        if not completed_orders.exists():
            return {'min': 10, 'max': 50, 'preferred': 25}
        
        order_values = [float(order.total_amount) for order in completed_orders]
        
        return {
            'min': min(order_values) if order_values else 10,
            'max': max(order_values) if order_values else 50,
            'preferred': sum(order_values) / len(order_values) if order_values else 25,
            'std_dev': math.sqrt(sum((x - (sum(order_values)/len(order_values))) ** 2 for x in order_values) / len(order_values)) if order_values else 10
        }
    
    def _calculate_order_metrics(self, orders):
        """Calculate order frequency and timing patterns"""
        completed_orders = orders.filter(status='delivered').order_by('order_placed_at')
        
        if len(completed_orders) < 2:
            return {
                'avg_order_value': Decimal('0.00'),
                'order_frequency_days': 0,
                'preferred_order_times': {}
            }
        
        # Calculate average order value
        avg_value = completed_orders.aggregate(avg_value=Avg('total_amount'))['avg_value'] or Decimal('0.00')
        
        # Calculate order frequency
        order_dates = [order.order_placed_at for order in completed_orders]
        time_diffs = [(order_dates[i+1] - order_dates[i]).days for i in range(len(order_dates)-1)]
        avg_frequency = sum(time_diffs) / len(time_diffs) if time_diffs else 0
        
        # Calculate preferred order times
        time_slots = defaultdict(int)
        for order in completed_orders:
            hour = order.order_placed_at.hour
            if 6 <= hour < 11:
                time_slots['breakfast'] += 1
            elif 11 <= hour < 15:
                time_slots['lunch'] += 1
            elif 15 <= hour < 18:
                time_slots['afternoon'] += 1
            elif 18 <= hour < 22:
                time_slots['dinner'] += 1
            else:
                time_slots['late_night'] += 1
        
        total_orders = len(completed_orders)
        preferred_times = {slot: count / total_orders for slot, count in time_slots.items()}
        
        return {
            'avg_order_value': avg_value,
            'order_frequency_days': avg_frequency,
            'preferred_order_times': preferred_times
        }
    
    def calculate_item_similarity(self, item1, item2, similarity_type='menu_item'):
        """
        Calculate similarity between two items using cosine similarity
        """
        if similarity_type == 'menu_item':
            return self._calculate_menu_item_similarity(item1, item2)
        elif similarity_type == 'restaurant':
            return self._calculate_restaurant_similarity(item1, item2)
        
        return 0.0
    
    def _calculate_menu_item_similarity(self, item1, item2):
        """Calculate similarity between two menu items"""
        # Feature vectors based on item attributes
        features1 = self._get_menu_item_features(item1)
        features2 = self._get_menu_item_features(item2)
        
        return self._cosine_similarity(features1, features2)
    
    def _get_menu_item_features(self, item):
        """Extract feature vector for menu item"""
        # Normalize features to 0-1 range
        features = []
        
        # Price (normalized to $0-100 range)
        price_feature = min(float(item.price) / 100.0, 1.0)
        features.append(price_feature)
        
        # Dietary features (binary)
        features.append(1.0 if item.is_vegetarian else 0.0)
        features.append(1.0 if item.is_vegan else 0.0)
        features.append(1.0 if item.is_gluten_free else 0.0)
        features.append(1.0 if item.is_spicy else 0.0)
        
        # Item type (one-hot encoded)
        item_types = ['main', 'beverage', 'dessert', 'side', 'combo']
        type_features = [1.0 if item.item_type == t else 0.0 for t in item_types]
        features.extend(type_features)
        
        # Preparation time (normalized to 0-60 minutes)
        prep_time_feature = min(item.preparation_time / 60.0, 1.0)
        features.append(prep_time_feature)
        
        return features
    
    def _calculate_restaurant_similarity(self, rest1, rest2):
        """Calculate similarity between two restaurants"""
        features1 = self._get_restaurant_features(rest1)
        features2 = self._get_restaurant_features(rest2)
        
        return self._cosine_similarity(features1, features2)
    
    def _get_restaurant_features(self, restaurant):
        """Extract feature vector for restaurant"""
        features = []
        
        # Rating (normalized to 0-5)
        rating_feature = float(restaurant.overall_rating) / 5.0
        features.append(rating_feature)
        
        # Price level (estimated from menu items)
        avg_price = restaurant.menu_categories.aggregate(
            avg_price=Avg('menu_items__price')
        )['avg_price'] or Decimal('0.00')
        price_feature = min(float(avg_price) / 50.0, 1.0)
        features.append(price_feature)
        
        # Cuisine features (one-hot for top cuisines)
        top_cuisines = ['Italian', 'Mexican', 'Chinese', 'Indian', 'American', 'Japanese']
        cuisine_names = [c.name for c in restaurant.cuisines.all()]
        cuisine_features = [1.0 if cuisine in cuisine_names else 0.0 for cuisine in top_cuisines]
        features.extend(cuisine_features)
        
        # Restaurant features (binary)
        features.append(1.0 if restaurant.is_featured else 0.0)
        features.append(1.0 if restaurant.is_verified else 0.0)
        
        return features
    
    def _cosine_similarity(self, vec1, vec2):
        """Calculate cosine similarity between two vectors"""
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(a * a for a in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def get_personalized_recommendations(self, user, limit=10, location_context=None):
        """
        Generate personalized recommendations for a user
        """
        from .models import MenuItem, Restaurant, UserPreference, UserBehavior
        
        # Update user preferences first
        preferences = self.calculate_user_preferences(user)
        
        # Get recent user behaviors for context
        recent_behaviors = UserBehavior.objects.filter(
            user=user,
            created_at__gte=timezone.now() - timedelta(days=self.recent_days)
        )
        
        recommendations = []
        
        # 1. Content-based filtering based on user preferences
        content_based_recs = self._content_based_filtering(user, preferences, limit//2, location_context)
        recommendations.extend(content_based_recs)
        
        # 2. Collaborative filtering (users with similar preferences)
        collaborative_recs = self._collaborative_filtering(user, preferences, limit//4, location_context)
        recommendations.extend(collaborative_recs)
        
        # 3. Popular items in user's area
        popular_recs = self._popular_items_filtering(user, limit//4, location_context)
        recommendations.extend(popular_recs)
        
        # Remove duplicates and sort by score
        unique_recommendations = self._deduplicate_recommendations(recommendations)
        
        return sorted(unique_recommendations, key=lambda x: x['score'], reverse=True)[:limit]
    
    def _content_based_filtering(self, user, preferences, limit, location_context):
        """Content-based recommendations using user preferences"""
        from .models import MenuItem, Restaurant
        
        recommendations = []
        
        # Get all available menu items
        menu_items = MenuItem.objects.filter(
            is_available=True,
            category__restaurant__status='active'
        ).select_related('category', 'category__restaurant')
        
        # Apply location filter if provided
        if location_context and location_context.get('latitude') and location_context.get('longitude'):
            from .search_utils import SearchUtils
            nearby_branches = SearchUtils.get_restaurant_branches_nearby(
                location_context['latitude'], location_context['longitude'], 20
            )
            restaurant_ids = [branch.restaurant_id for branch in nearby_branches]
            menu_items = menu_items.filter(category__restaurant_id__in=restaurant_ids)
        
        for item in menu_items:
            score = self._calculate_item_preference_score(item, preferences)
            
            if score > self.min_similarity_threshold:
                recommendations.append({
                    'type': 'menu_item',
                    'item': item,
                    'score': score,
                    'reason': 'Matches your taste preferences',
                    'algorithm': 'content_based'
                })
        
        return recommendations
    
    def _calculate_item_preference_score(self, item, preferences):
        """Calculate how well an item matches user preferences"""
        score = 0.0
        total_weight = 0
        
        # Cuisine matching
        restaurant_cuisines = [c.name for c in item.category.restaurant.cuisines.all()]
        for cuisine, weight in preferences.cuisine_scores.items():
            if cuisine in restaurant_cuisines:
                score += weight * 0.3  # Cuisine weight
                total_weight += 0.3
        
        # Dietary preferences matching
        if item.is_vegetarian and preferences.dietary_weights.get('vegetarian', 0) > 0.5:
            score += preferences.dietary_weights['vegetarian'] * 0.2
            total_weight += 0.2
        
        if item.is_gluten_free and preferences.dietary_weights.get('gluten_free', 0) > 0.5:
            score += preferences.dietary_weights['gluten_free'] * 0.2
            total_weight += 0.2
        
        # Price preference matching
        price_prefs = preferences.price_preferences
        item_price = float(item.price)
        preferred_price = price_prefs.get('preferred', 25)
        price_std = price_prefs.get('std_dev', 10)
        
        # Gaussian distribution around preferred price
        price_diff = abs(item_price - preferred_price)
        price_score = math.exp(-0.5 * (price_diff / price_std) ** 2)
        score += price_score * 0.3
        total_weight += 0.3
        
        # Normalize score
        if total_weight > 0:
            return score / total_weight
        
        return score
    
    def _collaborative_filtering(self, user, preferences, limit, location_context):
        """
        Simple collaborative filtering based on order patterns
        In a production system, this would use more sophisticated algorithms
        """
        from .models import Order, OrderItem
        
        # Get items frequently ordered together with user's recent orders
        recent_orders = Order.objects.filter(
            customer__user=user,
            order_placed_at__gte=timezone.now() - timedelta(days=60)
        )
        
        if not recent_orders.exists():
            return []
        
        # Get items from user's recent orders
        user_item_ids = set()
        for order in recent_orders:
            for order_item in order.order_items.all():
                user_item_ids.add(order_item.menu_item.item_id)
        
        # Find users who ordered the same items
        similar_users_orders = OrderItem.objects.filter(
            menu_item_id__in=user_item_ids
        ).exclude(order__customer__user=user).values('order__customer__user').distinct()
        
        similar_user_ids = [order['order__customer__user'] for order in similar_users_orders]
        
        if not similar_user_ids:
            return []
        
        # Get popular items among similar users
        from django.db.models import Count
        popular_items = OrderItem.objects.filter(
            order__customer__user_id__in=similar_user_ids,
            order__order_placed_at__gte=timezone.now() - timedelta(days=90)
        ).exclude(menu_item_id__in=user_item_ids).values(
            'menu_item'
        ).annotate(
            order_count=Count('menu_item')
        ).order_by('-order_count')[:limit*2]  # Get more than needed for filtering
        
        recommendations = []
        for item_data in popular_items:
            try:
                item = MenuItem.objects.get(pk=item_data['menu_item'])
                
                # Apply location filter
                if location_context and location_context.get('latitude') and location_context.get('longitude'):
                    from .search_utils import SearchUtils
                    nearby_branches = SearchUtils.get_restaurant_branches_nearby(
                        location_context['latitude'], location_context['longitude'], 20
                    )
                    restaurant_ids = [branch.restaurant_id for branch in nearby_branches]
                    if item.category.restaurant_id not in restaurant_ids:
                        continue
                
                score = min(item_data['order_count'] / 10.0, 1.0)  # Normalize based on order count
                
                recommendations.append({
                    'type': 'menu_item',
                    'item': item,
                    'score': score,
                    'reason': 'Popular among users with similar tastes',
                    'algorithm': 'collaborative'
                })
            except MenuItem.DoesNotExist:
                continue
        
        return recommendations
    
    def _popular_items_filtering(self, user, limit, location_context):
        """Recommend popular items in user's area"""
        from .models import MenuItem, OrderItem
        from django.db.models import Count
        
        # Base queryset for popular items
        popular_items = OrderItem.objects.filter(
            order__status='delivered',
            order__order_placed_at__gte=timezone.now() - timedelta(days=30)
        ).values('menu_item').annotate(
            order_count=Count('menu_item')
        ).order_by('-order_count')[:limit*3]  # Get more for location filtering
        
        recommendations = []
        for item_data in popular_items:
            try:
                item = MenuItem.objects.get(pk=item_data['menu_item'], is_available=True)
                
                # Apply location filter
                if location_context and location_context.get('latitude') and location_context.get('longitude'):
                    from .search_utils import SearchUtils
                    nearby_branches = SearchUtils.get_restaurant_branches_nearby(
                        location_context['latitude'], location_context['longitude'], 20
                    )
                    restaurant_ids = [branch.restaurant_id for branch in nearby_branches]
                    if item.category.restaurant_id not in restaurant_ids:
                        continue
                
                score = min(item_data['order_count'] / 20.0, 1.0)  # Normalize based on order count
                
                recommendations.append({
                    'type': 'menu_item',
                    'item': item,
                    'score': score,
                    'reason': 'Trending in your area',
                    'algorithm': 'popularity'
                })
            except MenuItem.DoesNotExist:
                continue
        
        return recommendations[:limit]
    
    def _deduplicate_recommendations(self, recommendations):
        """Remove duplicate recommendations and combine scores"""
        unique_items = {}
        
        for rec in recommendations:
            item_id = rec['item'].item_id
            if item_id in unique_items:
                # Combine scores from different algorithms
                unique_items[item_id]['score'] = (unique_items[item_id]['score'] + rec['score']) / 2
                unique_items[item_id]['reasons'].append(rec['reason'])
                unique_items[item_id]['algorithms'].append(rec['algorithm'])
            else:
                unique_items[item_id] = {
                    'type': rec['type'],
                    'item': rec['item'],
                    'score': rec['score'],
                    'reasons': [rec['reason']],
                    'algorithms': [rec['algorithm']]
                }
        
        # Convert back to list
        return list(unique_items.values())
    
    def get_trending_recommendations(self, user, limit=10, location_context=None):
        """Get trending recommendations based on recent popularity"""
        from .models import MenuItem, OrderItem
        from django.db.models import Count
        from datetime import datetime, timedelta
        
        # Items with most orders in last 7 days
        one_week_ago = timezone.now() - timedelta(days=7)
        
        trending_items = OrderItem.objects.filter(
            order__status='delivered',
            order__order_placed_at__gte=one_week_ago
        ).values('menu_item').annotate(
            order_count=Count('menu_item'),
            recent_orders=Count('menu_item', filter=Q(order__order_placed_at__gte=one_week_ago))
        ).order_by('-recent_orders')[:limit]
        
        recommendations = []
        for item_data in trending_items:
            try:
                item = MenuItem.objects.get(pk=item_data['menu_item'], is_available=True)
                
                # Apply location filter if provided
                if location_context and location_context.get('latitude') and location_context.get('longitude'):
                    from .search_utils import SearchUtils
                    nearby_branches = SearchUtils.get_restaurant_branches_nearby(
                        location_context['latitude'], location_context['longitude'], 20
                    )
                    restaurant_ids = [branch.restaurant_id for branch in nearby_branches]
                    if item.category.restaurant_id not in restaurant_ids:
                        continue
                
                growth_rate = self._calculate_growth_rate(item.item_id)
                score = min(item_data['recent_orders'] / 10.0, 1.0) * (1 + growth_rate)
                
                recommendations.append({
                    'type': 'menu_item',
                    'item': item,
                    'score': score,
                    'reason': f"Trending (+{int(growth_rate * 100)}% growth)",
                    'algorithm': 'trending'
                })
            except MenuItem.DoesNotExist:
                continue
        
        return recommendations
    
    def _calculate_growth_rate(self, item_id):
        """Calculate growth rate for an item compared to previous period"""
        from .models import OrderItem
        from datetime import datetime, timedelta
        
        now = timezone.now()
        current_start = now - timedelta(days=7)
        previous_start = current_start - timedelta(days=7)
        previous_end = current_start - timedelta(days=1)
        
        current_orders = OrderItem.objects.filter(
            menu_item_id=item_id,
            order__status='delivered',
            order__order_placed_at__gte=current_start
        ).count()
        
        previous_orders = OrderItem.objects.filter(
            menu_item_id=item_id,
            order__status='delivered',
            order__order_placed_at__range=[previous_start, previous_end]
        ).count()
        
        if previous_orders > 0:
            return (current_orders - previous_orders) / previous_orders
        elif current_orders > 0:
            return 1.0  # New trending item
        
        return 0.0
    
    def get_similar_items(self, item_id, item_type='menu_item', limit=5):
        """Get items similar to a given item"""
        from .models import MenuItem, Restaurant
        
        if item_type == 'menu_item':
            try:
                target_item = MenuItem.objects.get(pk=item_id)
                all_items = MenuItem.objects.filter(
                    is_available=True,
                    category__restaurant__status='active'
                ).exclude(pk=item_id)
                
                similarities = []
                for item in all_items:
                    similarity = self.calculate_item_similarity(target_item, item, 'menu_item')
                    if similarity > self.min_similarity_threshold:
                        similarities.append((item, similarity))
                
                # Sort by similarity and return top results
                similarities.sort(key=lambda x: x[1], reverse=True)
                return [{'item': item, 'similarity': sim} for item, sim in similarities[:limit]]
                
            except MenuItem.DoesNotExist:
                return []
        
        return []
    

    # ========== NEW RESTAURANT-SCOPED METHODS FOR USING ON THE RESTAURANT'S HOMEPAGE ==========
    def get_restaurant_homepage_recommendations(self, user, restaurant_id, **kwargs):
        """
        Get comprehensive recommendations for a restaurant's homepage
        """
        scoped_engine = RestaurantScopedEngine()
        return scoped_engine.get_restaurant_recommendations(user, restaurant_id, **kwargs)

class RestaurantScopedEngine:
    """
    Enhanced engine for restaurant-specific recommendations
    Uses the existing infrastructure but scoped to individual restaurants
    """
    
    def __init__(self):
        self.engine = RecommendationEngine()
        self.min_similarity_threshold = 0.1
    
    def get_restaurant_recommendations(self, user, restaurant_id, limit=10, recommendation_types=None, **kwargs):
        """
        Get recommendations specific to a restaurant's homepage
        """
        from .models import Restaurant, MenuItem
        
        try:
            restaurant = Restaurant.objects.get(pk=restaurant_id)
        except Restaurant.DoesNotExist:
            return []
        
        if recommendation_types is None:
            recommendation_types = ['popular', 'similar', 'frequently_bought_together', 'personalized']
        
        all_recommendations = []
        
        if 'popular' in recommendation_types:
            popular_recs = self._get_restaurant_popular_items(restaurant, user, limit//2)
            all_recommendations.extend(popular_recs)
        
        if 'similar' in recommendation_types and 'current_item_id' in kwargs:
            similar_recs = self._get_restaurant_similar_items(
                restaurant, kwargs['current_item_id'], limit//3
            )
            all_recommendations.extend(similar_recs)
        
        if 'frequently_bought_together' in recommendation_types and 'current_item_id' in kwargs:
            fbt_recs = self._get_restaurant_frequently_bought_together(
                restaurant, kwargs['current_item_id'], limit//3
            )
            all_recommendations.extend(fbt_recs)
        
        if 'personalized' in recommendation_types:
            personalized_recs = self._get_restaurant_personalized_recommendations(
                restaurant, user, limit//2
            )
            all_recommendations.extend(personalized_recs)
        
        # Deduplicate and return
        return self._deduplicate_and_sort(all_recommendations, limit)
    
    def _get_restaurant_popular_items(self, restaurant, user, limit):
        """Get popular items within this specific restaurant"""
        from .models import MenuItem
        
        # Use existing popularity_score field enhanced with restaurant context
        popular_items = MenuItem.objects.filter(
            category__restaurant=restaurant,
            is_available=True
        ).order_by('-popularity_score', '-is_featured')[:limit*2]
        
        recommendations = []
        for item in popular_items:
            # Enhance score with user context if available
            base_score = item.popularity_score / 100.0  # Normalize to 0-1
            user_adjusted_score = self._adjust_score_for_user(item, user, base_score)
            
            recommendations.append({
                'type': 'menu_item',
                'item': item,
                'score': user_adjusted_score,
                'reason': 'Popular in this restaurant',
                'algorithm': 'restaurant_popularity'
            })
        
        return sorted(recommendations, key=lambda x: x['score'], reverse=True)[:limit]
    
    def _get_restaurant_similar_items(self, restaurant, current_item_id, limit):
        """Get items similar to current item within the same restaurant"""
        from .models import MenuItem
        
        try:
            current_item = MenuItem.objects.get(pk=current_item_id, category__restaurant=restaurant)
        except MenuItem.DoesNotExist:
            return []
        
        # Get all items from same restaurant
        restaurant_items = MenuItem.objects.filter(
            category__restaurant=restaurant,
            is_available=True
        ).exclude(pk=current_item_id)
        
        similarities = []
        for item in restaurant_items:
            similarity = self.engine.calculate_item_similarity(current_item, item, 'menu_item')
            if similarity > self.engine.min_similarity_threshold:
                similarities.append({
                    'type': 'menu_item',
                    'item': item,
                    'score': similarity,
                    'reason': f"Similar to {current_item.name}",
                    'algorithm': 'restaurant_similarity'
                })
        
        return sorted(similarities, key=lambda x: x['score'], reverse=True)[:limit]
    
    def _get_restaurant_frequently_bought_together(self, restaurant, current_item_id, limit):
        """Get items frequently bought together within this restaurant"""
        from .models import ItemAssociation
        
        # Use your existing ItemAssociation model but filtered by restaurant
        associations = ItemAssociation.objects.filter(
            source_item_id=current_item_id,
            target_item__category__restaurant=restaurant,
            target_item__is_available=True
        ).select_related('target_item').order_by('-confidence')[:limit*2]
        
        recommendations = []
        for assoc in associations:
            if assoc.target_item.is_available:
                recommendations.append({
                    'type': 'menu_item',
                    'item': assoc.target_item,
                    'score': float(assoc.confidence),
                    'reason': 'Frequently bought together',
                    'algorithm': 'frequently_bought_together'
                })
        
        return recommendations[:limit]
    
    def _get_restaurant_personalized_recommendations(self, restaurant, user, limit):
        """Get personalized recommendations within this restaurant"""
        from .models import MenuItem, UserPreference
        
        # Get user preferences
        try:
            preferences = UserPreference.objects.get(user=user)
        except UserPreference.DoesNotExist:
            preferences = self.engine.calculate_user_preferences(user)
        
        # Get all available items in restaurant
        menu_items = MenuItem.objects.filter(
            category__restaurant=restaurant,
            is_available=True
        )
        
        recommendations = []
        for item in menu_items:
            score = self.engine._calculate_item_preference_score(item, preferences)
            
            if score > self.engine.min_similarity_threshold:
                recommendations.append({
                    'type': 'menu_item',
                    'item': item,
                    'score': score,
                    'reason': 'Matches your taste preferences',
                    'algorithm': 'restaurant_personalized'
                })
        
        return sorted(recommendations, key=lambda x: x['score'], reverse=True)[:limit]
    
    def _adjust_score_for_user(self, item, user, base_score):
        """Adjust popularity score based on user preferences"""
        try:
            from .models import UserPreference
            preferences = UserPreference.objects.get(user=user)
            
            # Boost score if item matches user's cuisine preferences
            restaurant_cuisines = [c.name for c in item.category.restaurant.cuisines.all()]
            cuisine_match = any(cuisine in preferences.cuisine_scores 
                              for cuisine in restaurant_cuisines)
            
            if cuisine_match:
                base_score *= 1.3  # 30% boost for preferred cuisines
            
            # Boost for dietary preferences
            if (item.is_vegetarian and preferences.dietary_weights.get('vegetarian', 0) > 0.7):
                base_score *= 1.2
            if (item.is_gluten_free and preferences.dietary_weights.get('gluten_free', 0) > 0.7):
                base_score *= 1.15
            
            return min(base_score, 1.0)  # Cap at 1.0
            
        except UserPreference.DoesNotExist:
            return base_score
    
    def _deduplicate_and_sort(self, recommendations, limit):
        """Deduplicate recommendations and sort by score"""
        seen_items = set()
        unique_recommendations = []
        
        for rec in sorted(recommendations, key=lambda x: x['score'], reverse=True):
            item_id = rec['item'].item_id
            if item_id not in seen_items:
                seen_items.add(item_id)
                unique_recommendations.append(rec)
            
            if len(unique_recommendations) >= limit:
                break
        
        return unique_recommendations