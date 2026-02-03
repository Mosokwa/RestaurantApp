# management/commands/create_reviews_and_ratings.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random
from decimal import Decimal
from api.models.ratingsandreviews_models import (
    RestaurantReview, DishReview, RestaurantRating, DishRating, 
    ReviewHelpfulVote, RestaurantReviewSettings, RatingAggregate
)
from api.models.restaurant_models import Restaurant
from api.models.order_models import Order
from api.models.user_models import Customer
from api.models.menu_models import MenuItem

class Command(BaseCommand):
    help = 'Create reviews and ratings for restaurants and dishes'
    
    def handle(self, *args, **options):
        customers = list(Customer.objects.all()[:100])
        restaurants = list(Restaurant.objects.all())
        
        restaurant_review_count = 0
        dish_review_count = 0
        
        # Create review settings for all restaurants first
        for restaurant in restaurants:
            RestaurantReviewSettings.objects.get_or_create(restaurant=restaurant)
        
        # Create restaurant reviews
        for restaurant in restaurants:
            # Get unique customers for this restaurant to avoid duplicate reviews
            restaurant_customers = list(set(customers))  # Make unique
            
            num_reviews = random.randint(10, 50)  # Reduced from 10-100 to avoid duplicates
            selected_customers = random.sample(restaurant_customers, min(num_reviews, len(restaurant_customers)))
            
            for customer in selected_customers:
                review_date = timezone.now() - timedelta(days=random.randint(0, 180))
                
                # Get a unique order for this customer-restaurant pair
                customer_orders = Order.objects.filter(customer=customer, restaurant=restaurant)
                order = None
                if customer_orders.exists():
                    # Try to find an order without a review
                    orders_without_reviews = []
                    for ord in customer_orders:
                        try:
                            RestaurantReview.objects.get(restaurant=restaurant, customer=customer, order=ord)
                        except RestaurantReview.DoesNotExist:
                            orders_without_reviews.append(ord)
                    
                    if orders_without_reviews:
                        order = random.choice(orders_without_reviews)
                    else:
                        order = customer_orders.first()  # Use first order even if reviewed
                else:
                    # No orders - create review without order link
                    order = None
                
                # Check if review already exists for this combination
                try:
                    existing_review = RestaurantReview.objects.get(
                        restaurant=restaurant,
                        customer=customer,
                        order=order
                    )
                    continue  # Skip if review already exists
                except RestaurantReview.DoesNotExist:
                    pass
                
                overall_rating = Decimal(str(round(random.uniform(3.0, 5.0), 1)))
                food_quality = Decimal(str(round(random.uniform(3.0, 5.0), 1)))
                service_quality = Decimal(str(round(random.uniform(3.0, 5.0), 1)))
                ambiance = Decimal(str(round(random.uniform(3.0, 5.0), 1)))
                value_for_money = Decimal(str(round(random.uniform(3.0, 5.0), 1)))
                
                review = RestaurantReview.objects.create(
                    restaurant=restaurant,
                    customer=customer,
                    order=order,
                    overall_rating=overall_rating,
                    food_quality=food_quality,
                    service_quality=service_quality,
                    ambiance=ambiance,
                    value_for_money=value_for_money,
                    title=self.get_review_title(overall_rating),
                    comment=self.get_review_comment(overall_rating),
                    is_verified_purchase=order is not None,
                    status='approved',
                    created_at=review_date
                )
                
                # Create helpful votes (only for some reviews)
                if random.choice([True, False]):
                    # Get other customers who haven't voted on this review
                    voters = [c for c in customers if c != customer]
                    if voters:
                        num_voters = min(3, len(voters))
                        helpful_customers = random.sample(voters, num_voters)
                        for helpful_customer in helpful_customers:
                            try:
                                ReviewHelpfulVote.objects.create(
                                    review=review,
                                    customer=helpful_customer,
                                    is_helpful=random.choice([True, True, False])
                                )
                            except Exception:
                                pass  # Skip if vote already exists
                
                restaurant_review_count += 1
            
            # Create standalone ratings (without full reviews)
            num_ratings = random.randint(5, 30)  # Reduced from 5-50
            rating_customers = random.sample(customers, min(num_ratings, len(customers)))
            
            for customer in rating_customers:
                # Get an order or use None
                order = Order.objects.filter(customer=customer, restaurant=restaurant).first()
                
                # Check if rating already exists
                try:
                    existing_rating = RestaurantRating.objects.get(
                        restaurant=restaurant,
                        customer=customer,
                        order=order
                    )
                    continue  # Skip if rating already exists
                except RestaurantRating.DoesNotExist:
                    pass
                
                RestaurantRating.objects.create(
                    restaurant=restaurant,
                    customer=customer,
                    order=order,
                    overall_rating=Decimal(str(round(random.uniform(3.0, 5.0), 1))),
                    food_quality=Decimal(str(round(random.uniform(3.0, 5.0), 1))) if random.choice([True, False]) else None,
                    service_quality=Decimal(str(round(random.uniform(3.0, 5.0), 1))) if random.choice([True, False]) else None,
                    ambiance=Decimal(str(round(random.uniform(3.0, 5.0), 1))) if random.choice([True, False]) else None,
                    value_for_money=Decimal(str(round(random.uniform(3.0, 5.0), 1))) if random.choice([True, False]) else None,
                    tags=random.sample(['great_service', 'fast_delivery', 'friendly_staff', 'clean_environment', 'good_value'], random.randint(1, 3)),
                    is_verified_purchase=order is not None,
                    is_quick_rating=random.choice([True, False])
                )
        
        # Create dish reviews and ratings (reduced scope)
        restaurant_sample = restaurants[:20]  # Only 20 restaurants
        for restaurant in restaurant_sample:
            menu_items = list(MenuItem.objects.filter(category__restaurant=restaurant))
            if not menu_items:
                continue
                
            menu_sample = menu_items[:10]  # Only 10 items per restaurant
            
            for menu_item in menu_sample:
                num_reviews = random.randint(0, 10)  # Reduced from 0-20
                if num_reviews == 0:
                    continue
                    
                item_customers = random.sample(customers, min(num_reviews, len(customers)))
                
                for customer in item_customers:
                    order = Order.objects.filter(customer=customer, restaurant=restaurant).first()
                    
                    # Check if dish review already exists
                    try:
                        existing_review = DishReview.objects.get(
                            menu_item=menu_item,
                            customer=customer,
                            order=order
                        )
                        continue
                    except DishReview.DoesNotExist:
                        pass
                    
                    DishReview.objects.create(
                        menu_item=menu_item,
                        customer=customer,
                        order=order,
                        rating=Decimal(str(round(random.uniform(3.0, 5.0), 1))),
                        comment=self.get_dish_review_comment(),
                        status='approved'
                    )
                    dish_review_count += 1
                
                # Create standalone dish ratings
                num_ratings = random.randint(0, 8)  # Reduced from 0-15
                rating_customers = random.sample(customers, min(num_ratings, len(customers)))
                
                for customer in rating_customers:
                    order = Order.objects.filter(customer=customer, restaurant=restaurant).first()
                    
                    # Check if dish rating already exists
                    try:
                        existing_rating = DishRating.objects.get(
                            menu_item=menu_item,
                            customer=customer,
                            order=order
                        )
                        continue
                    except DishRating.DoesNotExist:
                        pass
                    
                    DishRating.objects.create(
                        menu_item=menu_item,
                        customer=customer,
                        order=order,
                        rating=Decimal(str(round(random.uniform(3.0, 5.0), 1))),
                        taste=Decimal(str(round(random.uniform(3.0, 5.0), 1))) if random.choice([True, False]) else None,
                        portion_size=Decimal(str(round(random.uniform(3.0, 5.0), 1))) if random.choice([True, False]) else None,
                        value=Decimal(str(round(random.uniform(3.0, 5.0), 1))) if random.choice([True, False]) else None,
                        tags=random.sample(['delicious', 'fresh', 'flavorful', 'generous_portion', 'well_presented'], random.randint(1, 3)),
                        is_verified_purchase=order is not None
                    )
        
        # Update rating aggregates
        self.update_rating_aggregates()
        
        self.stdout.write(self.style.SUCCESS(
            f'Created {restaurant_review_count} restaurant reviews and {dish_review_count} dish reviews'
        ))
    
    def get_review_title(self, rating):
        if rating >= 4.5:
            return random.choice(['Excellent!', 'Amazing experience', 'Perfect in every way', 'Will definitely return'])
        elif rating >= 4.0:
            return random.choice(['Very good', 'Great food and service', 'Highly recommended', 'Enjoyed our meal'])
        elif rating >= 3.0:
            return random.choice(['Good experience', 'Satisfied', 'Decent food', 'Average experience'])
        else:
            return random.choice(['Could be better', 'Needs improvement', 'Disappointing'])
    
    def get_review_comment(self, rating):
        if rating >= 4.5:
            return random.choice([
                'The food was absolutely delicious and service was outstanding. Will definitely come back!',
                'Best restaurant in the area. Everything was perfect from start to finish.',
                'Excellent quality and great atmosphere. Highly recommend this place.',
                'Amazing experience! The staff was very attentive and the food was top-notch.'
            ])
        elif rating >= 4.0:
            return random.choice([
                'Good food and nice atmosphere. Service was prompt and friendly.',
                'Enjoyed our meal here. The portions were generous and flavors were great.',
                'Nice place for a meal. Would recommend to friends and family.',
                'Good value for money. The food was tasty and service was good.'
            ])
        elif rating >= 3.0:
            return random.choice([
                'Average experience. Food was okay but nothing special.',
                'Decent place for a quick meal. Could use some improvements.',
                'Food was acceptable but service was a bit slow.',
                'Not bad, but there are better options in the area.'
            ])
        else:
            return random.choice([
                'Disappointing experience. Food was cold and service was poor.',
                'Expected better based on the reviews. Would not return.',
                'Many things could be improved. Food quality was below average.',
                'Service was very slow and food was not fresh.'
            ])
    
    def get_dish_review_comment(self):
        return random.choice([
            'Very tasty!',
            'Perfectly cooked',
            'Good portion size',
            'Could use more seasoning',
            'Authentic flavor',
            'Fresh ingredients',
            'Well presented',
            'A bit too salty',
            'Excellent texture',
            'Would order again'
        ])
    
    def update_rating_aggregates(self):
        from django.db.models import Avg, Count
        # Update restaurant rating aggregates
        for restaurant in Restaurant.objects.all():
            ratings = restaurant.ratings.all()
            reviews = restaurant.reviews.filter(status='approved')
            
            if ratings.exists():
                total_ratings = ratings.count()
                avg_overall = ratings.aggregate(avg=Avg('overall_rating'))['avg'] or Decimal('0')
                avg_food = ratings.aggregate(avg=Avg('food_quality'))['avg'] or Decimal('0')
                avg_service = ratings.aggregate(avg=Avg('service_quality'))['avg'] or Decimal('0')
                avg_ambiance = ratings.aggregate(avg=Avg('ambiance'))['avg'] or Decimal('0')
                avg_value = ratings.aggregate(avg=Avg('value_for_money'))['avg'] or Decimal('0')
                
                # Calculate distribution
                distribution = {str(i): 0 for i in range(1, 6)}
                for rating in ratings:
                    distribution[str(int(float(rating.overall_rating)))] += 1
                
                # Get tag frequencies
                all_tags = []
                for rating in ratings.filter(tags__len__gt=0):
                    all_tags.extend(rating.tags)
                
                tag_frequencies = {}
                for tag in all_tags:
                    tag_frequencies[tag] = tag_frequencies.get(tag, 0) + 1
                
                aggregate, created = RatingAggregate.objects.get_or_create(
                    content_type='restaurant',
                    object_id=restaurant.restaurant_id
                )
                
                aggregate.total_ratings = total_ratings
                aggregate.average_rating = Decimal(str(round(float(avg_overall), 2)))
                aggregate.average_food_quality = Decimal(str(round(float(avg_food), 2)))
                aggregate.average_service_quality = Decimal(str(round(float(avg_service), 2)))
                aggregate.average_ambiance = Decimal(str(round(float(avg_ambiance), 2)))
                aggregate.average_value = Decimal(str(round(float(avg_value), 2)))
                aggregate.rating_distribution = distribution
                aggregate.tag_frequencies = tag_frequencies
                aggregate.save()
                
                # Update restaurant overall rating (use reviews count for display)
                restaurant.overall_rating = aggregate.average_rating
                restaurant.total_reviews = reviews.count()  # Use reviews count, not ratings count
                restaurant.save()