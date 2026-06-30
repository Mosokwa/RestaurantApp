# management/commands/_personalization.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
import random
from datetime import timedelta

class Command(BaseCommand):
    help = 'Populate user behavior data for personalization and recommendations'
    
    def add_arguments(self, parser):
        parser.add_argument('--skip-existing', action='store_true')
        parser.add_argument('--clean', action='store_true')
    
    def handle(self, *args, **options):
        from api.models import (
            User, Customer, Restaurant, MenuItem, UserBehavior,
            UserPreference, Recommendation, SimilarityMatrix
        )
        
        if options['clean']:
            UserBehavior.objects.all().delete()
            UserPreference.objects.all().delete()
            Recommendation.objects.all().delete()
            SimilarityMatrix.objects.all().delete()
            self.stdout.write("  Cleaned existing personalization data")
        
        customers = list(Customer.objects.all())
        restaurants = list(Restaurant.objects.filter(status='active'))
        menu_items = list(MenuItem.objects.filter(is_available=True)[:200])
        
        if not customers:
            self.stdout.write(self.style.ERROR("  No customers found! Run _customers first."))
            return
        
        behaviors_created = 0
        preferences_created = 0
        recommendations_created = 0
        similarity_records = 0
        
        # Create user behaviors for each customer
        for customer in customers[:300]:  # Limit to 300 customers for performance
            user = customer.user
            
            # Create view behaviors (restaurants viewed)
            num_restaurant_views = random.randint(3, 20)
            for _ in range(num_restaurant_views):
                restaurant = random.choice(restaurants)
                days_ago = random.randint(1, 60)
                
                UserBehavior.objects.create(
                    user=user,
                    restaurant=restaurant,
                    behavior_type='view',
                    metadata={'source': random.choice(['search', 'homepage', 'category', 'recommendation']), 'time_spent': random.randint(10, 300)},
                    created_at=timezone.now() - timedelta(days=days_ago)
                )
                behaviors_created += 1
            
            # Create view behaviors (menu items viewed)
            num_item_views = random.randint(5, 30)
            for _ in range(num_item_views):
                if menu_items:
                    menu_item = random.choice(menu_items)
                    days_ago = random.randint(1, 60)
                    
                    UserBehavior.objects.create(
                        user=user,
                        menu_item=menu_item,
                        restaurant=menu_item.category.restaurant,
                        behavior_type='view',
                        metadata={'source': random.choice(['search', 'menu', 'recommendation']), 'time_spent': random.randint(5, 120)},
                        created_at=timezone.now() - timedelta(days=days_ago)
                    )
                    behaviors_created += 1
            
            # Create favorite behaviors
            num_favorites = random.randint(0, 10)
            for _ in range(num_favorites):
                if random.random() > 0.5:
                    restaurant = random.choice(restaurants)
                    UserBehavior.objects.create(
                        user=user,
                        restaurant=restaurant,
                        behavior_type='favorite',
                        created_at=timezone.now() - timedelta(days=random.randint(1, 90))
                    )
                else:
                    if menu_items:
                        menu_item = random.choice(menu_items)
                        UserBehavior.objects.create(
                            user=user,
                            menu_item=menu_item,
                            restaurant=menu_item.category.restaurant,
                            behavior_type='favorite',
                            created_at=timezone.now() - timedelta(days=random.randint(1, 90))
                        )
                behaviors_created += 1
            
            # Create search behaviors
            search_terms = ['pizza', 'burger', 'seafood', 'chicken', 'vegetarian', 'coffee', 'sushi', 'bbq', 'pasta', 'salad']
            num_searches = random.randint(0, 15)
            for _ in range(num_searches):
                term = random.choice(search_terms)
                UserBehavior.objects.create(
                    user=user,
                    behavior_type='search',
                    metadata={'query': term, 'results_count': random.randint(1, 50)},
                    created_at=timezone.now() - timedelta(days=random.randint(1, 60))
                )
                behaviors_created += 1
        
        self.stdout.write(f"  Created {behaviors_created} user behavior records")
        
        # Create/update user preferences
        for customer in customers[:200]:
            user = customer.user
            
            # Calculate cuisine scores based on behaviors
            behaviors = UserBehavior.objects.filter(
                user=user,
                behavior_type__in=['view', 'order', 'favorite']
            ).select_related('restaurant')
            
            cuisine_scores = {}
            restaurant_type_scores = {}
            
            for behavior in behaviors:
                if behavior.restaurant:
                    for cuisine in behavior.restaurant.cuisines.all():
                        cuisine_scores[cuisine.name] = cuisine_scores.get(cuisine.name, 0) + 1
            
            # Normalize scores (max 10)
            if cuisine_scores:
                max_score = max(cuisine_scores.values())
                for cuisine in cuisine_scores:
                    cuisine_scores[cuisine] = round(cuisine_scores[cuisine] / max_score * 10, 1)
            
            # Dietary preferences from customer
            dietary_weights = customer.dietary_preferences.copy()
            
            # Price preferences (based on order history)
            from api.models import Order
            orders = Order.objects.filter(customer=customer, status='delivered')
            if orders.exists():
                avg_order_total = sum(o.total_amount for o in orders) / len(orders)
                price_prefs = {
                    'min': float(avg_order_total * Decimal('0.5')),
                    'max': float(avg_order_total * Decimal('2')),
                    'preferred': float(avg_order_total),
                    'avg_spend': float(avg_order_total)
                }
            else:
                price_prefs = {'min': 5, 'max': 50, 'preferred': 20}
            
            UserPreference.objects.update_or_create(
                user=user,
                defaults={
                    'cuisine_scores': cuisine_scores,
                    'dietary_weights': dietary_weights,
                    'price_preferences': price_prefs,
                    'preferred_locations': [random.choice(['Kigamboni', 'Mikocheni', 'Masaki', 'Mbezi Beach']) for _ in range(random.randint(1, 3))],
                    'restaurant_type_scores': {'fast_food': random.uniform(0, 1), 'fine_dining': random.uniform(0, 1)},
                    'avg_order_value': price_prefs['preferred'],
                    'order_frequency_days': random.randint(3, 21),
                    'preferred_order_times': {'lunch': random.uniform(0, 1), 'dinner': random.uniform(0, 1)}
                }
            )
            preferences_created += 1
        
        self.stdout.write(f"  Created/updated {preferences_created} user preferences")
        
        # Create recommendations for users
        for customer in customers[:100]:
            user = customer.user
            preference = getattr(user, 'preferences', None)
            
            if not preference:
                continue
            
            # Personalized restaurant recommendations
            top_cuisines = sorted(preference.cuisine_scores.items(), key=lambda x: x[1], reverse=True)[:3]
            
            recommended_restaurants = []
            for cuisine_name, score in top_cuisines:
                matching = [r for r in restaurants if r.cuisines.filter(name=cuisine_name).exists()]
                recommended_restaurants.extend(random.sample(matching, min(3, len(matching))))
            
            recommended_restaurants = list(set(recommended_restaurants))[:8]
            
            # Generate recommendation
            recommendation = Recommendation.objects.create(
                user=user,
                recommendation_type='personalized',
                scores={'cuisine_matching': 0.85, 'price_match': 0.72, 'location_match': 0.68},
                algorithm_metadata={'version': '1.0', 'model': 'collaborative_filtering'},
                is_active=True,
                expires_at=timezone.now() + timedelta(days=7),
                generated_at=timezone.now()
            )
            recommendation.recommended_restaurants.set(recommended_restaurants)
            
            if menu_items:
                # Personalized menu item recommendations
                recommended_items = random.sample(menu_items, min(10, len(menu_items)))
                recommendation.recommended_menu_items.set(recommended_items)
            
            recommendations_created += 1
        
        self.stdout.write(f"  Created {recommendations_created} recommendations")
        
        # Create similarity matrix for menu items
        if len(menu_items) >= 10:
            for i in range(min(100, len(menu_items) * 2)):
                item_a = random.choice(menu_items)
                item_b = random.choice([m for m in menu_items if m != item_a])
                
                # Calculate simple similarity based on category and cuisine
                similarity = 0.0
                if item_a.category == item_b.category:
                    similarity += 0.5
                if item_a.category.restaurant == item_b.category.restaurant:
                    similarity += 0.3
                
                # Add random variation
                similarity += random.uniform(0, 0.2)
                similarity = min(0.9999, similarity)
                
                SimilarityMatrix.objects.get_or_create(
                    matrix_type='menu_items',
                    item_a_id=item_a.item_id,
                    item_b_id=item_b.item_id,
                    defaults={
                        'similarity_score': Decimal(str(round(similarity, 4))),
                        'calculation_method': 'category_based'
                    }
                )
                similarity_records += 1
        
        self.stdout.write(f"  Created {similarity_records} similarity matrix records")
        self.stdout.write(f"  ✅ Personalization data population complete")