# management/commands/reviews.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
import random
from datetime import timedelta
from django.db import IntegrityError

class Command(BaseCommand):
    help = 'Create restaurant reviews, dish reviews, ratings, and responses'
    
    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=500, help='Number of reviews to create')
        parser.add_argument('--skip-existing', action='store_true')
        parser.add_argument('--clean', action='store_true')
    
    def handle(self, *args, **options):
        from api.models import (
            Restaurant, Customer, Order, RestaurantReview, DishReview,
            ReviewResponse, ReviewReport, ReviewHelpfulVote, RestaurantRating,
            DishRating, RatingAggregate, RestaurantReviewSettings
        )
        
        if options['clean']:
            RestaurantReview.objects.all().delete()
            DishReview.objects.all().delete()
            ReviewResponse.objects.all().delete()
            ReviewReport.objects.all().delete()
            ReviewHelpfulVote.objects.all().delete()
            RestaurantRating.objects.all().delete()
            DishRating.objects.all().delete()
            RatingAggregate.objects.all().delete()
            self.stdout.write("  Cleaned existing reviews and ratings")
        
        review_count = options['count']
        
        restaurants = list(Restaurant.objects.filter(status='active'))
        customers = list(Customer.objects.all())
        
        if not restaurants or not customers:
            self.stdout.write(self.style.ERROR("  No restaurants or customers found!"))
            return
        
        # Get completed orders for verified purchase reviews
        completed_orders = list(Order.objects.filter(status='delivered').select_related('customer', 'restaurant'))
        
        # Track which combinations have been used to avoid duplicates
        used_combinations = set()
        
        reviews_created = 0
        dish_reviews_created = 0
        responses_created = 0
        reports_created = 0
        votes_created = 0
        ratings_created = 0
        
        # Review tags for RestaurantRating and DishRating (not for DishReview)
        restaurant_tags = [
            'great_service', 'fast_delivery', 'friendly_staff', 'clean_environment',
            'good_ambiance', 'good_value', 'fresh_ingredients', 'generous_portions'
        ]
        
        dish_tags = [
            'delicious', 'spicy', 'fresh', 'flavorful', 'tender', 'crispy',
            'creamy', 'savory', 'sweet', 'generous_portion', 'well_presented'
        ]
        
        # Create restaurant reviews
        attempts = 0
        max_attempts = review_count * 3
        
        while reviews_created < review_count and attempts < max_attempts:
            attempts += 1
            
            # 70% from completed orders, 30% from random customers
            if completed_orders and random.random() < 0.7:
                order = random.choice(completed_orders)
                customer = order.customer
                restaurant = order.restaurant
                is_verified = True
            else:
                customer = random.choice(customers)
                restaurant = random.choice(restaurants)
                order = None
                is_verified = False
            
            # Check for duplicate combination
            combo_key = (restaurant.restaurant_id, customer.customer_id)
            if order:
                combo_key = (restaurant.restaurant_id, customer.customer_id, order.order_id)
            
            if combo_key in used_combinations:
                continue
            
            used_combinations.add(combo_key)
            
            # Generate ratings
            overall = Decimal(str(round(random.uniform(2.0, 5.0), 1)))
            food_quality = Decimal(str(round(random.uniform(2.0, 5.0), 1)))
            service_quality = Decimal(str(round(random.uniform(2.0, 5.0), 1)))
            ambiance = Decimal(str(round(random.uniform(2.0, 5.0), 1)))
            value_for_money = Decimal(str(round(random.uniform(2.0, 5.0), 1)))
            
            # Generate review text based on rating
            if overall >= 4.5:
                title = random.choice(['Amazing!', 'Perfect experience', 'Will definitely come back', 'Best in town'])
                comment = random.choice([
                    "Absolutely loved everything about this place. The food was incredible and service outstanding.",
                    "One of the best dining experiences I've had. Highly recommend!",
                    "Great atmosphere, delicious food, and friendly staff. 10/10",
                    "Everything was perfect from start to finish. Can't wait to come back."
                ])
            elif overall >= 3.5:
                title = random.choice(['Good experience', 'Solid choice', 'Pretty good', 'Worth a visit'])
                comment = random.choice([
                    "Good food and service. A few minor issues but overall positive.",
                    "Solid option in the area. Would come again.",
                    "Decent experience. Food was good, service was okay.",
                    "Pretty good overall. Some room for improvement but satisfied."
                ])
            else:
                title = random.choice(['Disappointing', 'Not worth it', 'Below expectations', 'Needs improvement'])
                comment = random.choice([
                    "Was really looking forward to this but left disappointed. Food was mediocre at best.",
                    "Service was slow and food wasn't great. Probably won't return.",
                    "Not what I expected given the reviews. Below average experience.",
                    "Many issues during our visit. Hope they improve."
                ])
            
            # Random photos (30% chance)
            photos = []
            if random.random() < 0.3:
                photos = [
                    'https://images.unsplash.com/photo-1546069901-ba9599a7e63c',
                    'https://images.unsplash.com/photo-1565299624946-b28f40a0ae38'
                ][:random.randint(1, 2)]
            
            status = 'approved' if random.random() > 0.1 else random.choice(['pending', 'rejected'])
            
            try:
                review = RestaurantReview.objects.create(
                    restaurant=restaurant,
                    customer=customer,
                    order=order,
                    overall_rating=overall,
                    food_quality=food_quality,
                    service_quality=service_quality,
                    ambiance=ambiance,
                    value_for_money=value_for_money,
                    title=title,
                    comment=comment,
                    photos=photos,
                    helpful_count=random.randint(0, 50),
                    status=status,
                    is_verified_purchase=is_verified,
                    created_at=timezone.now() - timedelta(days=random.randint(1, 90)),
                    approved_at=timezone.now() - timedelta(days=random.randint(1, 80)) if status == 'approved' else None
                )
                reviews_created += 1
            except IntegrityError:
                continue
            
            # Create owner response for some reviews (if approved)
            if status == 'approved' and random.random() < 0.4:
                from api.models import User
                responder = restaurant.owner
                
                response_text = random.choice([
                    "Thank you for your feedback! We're glad you enjoyed your experience.",
                    "Thanks for the review! We appreciate your business and hope to see you again soon.",
                    "We appreciate your honest feedback and will work on improving.",
                    "Thank you for dining with us! Your feedback helps us get better.",
                    "So happy to hear you had a great experience. Looking forward to serving you again!"
                ])
                
                ReviewResponse.objects.create(
                    review=review,
                    responder=responder,
                    comment=response_text,
                    is_public=True,
                    created_at=review.created_at + timedelta(days=random.randint(1, 7))
                )
                responses_created += 1
            
            # Create helpful votes
            num_votes = random.randint(0, 30)
            for _ in range(num_votes):
                other_customer = random.choice([c for c in customers if c != customer])
                try:
                    ReviewHelpfulVote.objects.get_or_create(
                        review=review,
                        customer=other_customer,
                        defaults={'is_helpful': random.random() > 0.2}
                    )
                    votes_created += 1
                except IntegrityError:
                    pass
            
            # Create report for some reviews
            if random.random() < 0.05:
                reporter = random.choice(customers)
                try:
                    ReviewReport.objects.create(
                        review=review,
                        reporter=reporter.user,
                        reason=random.choice(['spam', 'inappropriate', 'fake', 'harassment', 'other']),
                        description=random.choice(['This review seems fake', 'Inappropriate language used', 'Suspicious activity']),
                        status=random.choice(['pending', 'under_review', 'resolved', 'dismissed'])
                    )
                    reports_created += 1
                except IntegrityError:
                    pass
        
        self.stdout.write(f"  Created {reviews_created} restaurant reviews")
        
        # Create quick ratings (without full reviews)
        quick_ratings_created = 0
        for i in range(review_count // 2):
            customer = random.choice(customers)
            restaurant = random.choice(restaurants)
            overall = Decimal(str(round(random.uniform(2.0, 5.0), 1)))
            
            # Random tags
            tags = random.sample(restaurant_tags, random.randint(1, 3))
            
            # Check if rating already exists
            if RestaurantRating.objects.filter(restaurant=restaurant, customer=customer).exists():
                continue
            
            try:
                RestaurantRating.objects.create(
                    restaurant=restaurant,
                    customer=customer,
                    order=None,
                    overall_rating=overall,
                    food_quality=Decimal(str(round(random.uniform(2.0, 5.0), 1))) if random.random() > 0.3 else None,
                    service_quality=Decimal(str(round(random.uniform(2.0, 5.0), 1))) if random.random() > 0.3 else None,
                    ambiance=Decimal(str(round(random.uniform(2.0, 5.0), 1))) if random.random() > 0.3 else None,
                    value_for_money=Decimal(str(round(random.uniform(2.0, 5.0), 1))) if random.random() > 0.3 else None,
                    tags=tags,
                    is_verified_purchase=random.random() > 0.7,
                    is_quick_rating=True,
                    created_at=timezone.now() - timedelta(days=random.randint(1, 60))
                )
                quick_ratings_created += 1
            except IntegrityError:
                continue
        
        self.stdout.write(f"  Created {quick_ratings_created} quick restaurant ratings")
        
        # Create dish reviews (NOTE: DishReview does NOT have a tags field)
        from api.models import MenuItem, OrderItem
        
        menu_items = list(MenuItem.objects.filter(is_available=True))
        dish_combos_used = set()
        
        for i in range(review_count // 2):
            if not menu_items:
                break
            
            menu_item = random.choice(menu_items)
            customer = random.choice(customers)
            
            # Check for duplicate
            combo_key = (menu_item.item_id, customer.customer_id)
            if combo_key in dish_combos_used:
                continue
            dish_combos_used.add(combo_key)
            
            # Check if customer ordered this item
            order_item = OrderItem.objects.filter(
                menu_item=menu_item,
                order__customer=customer,
                order__status='delivered'
            ).first()
            
            is_verified = order_item is not None
            order = order_item.order if order_item else None
            
            rating = Decimal(str(round(random.uniform(2.0, 5.0), 1)))
            taste = Decimal(str(round(random.uniform(2.0, 5.0), 1)))
            portion = Decimal(str(round(random.uniform(2.0, 5.0), 1)))
            value = Decimal(str(round(random.uniform(2.0, 5.0), 1)))
            
            # Generate comment based on rating
            if rating >= 4.5:
                comment = random.choice([
                    "Absolutely delicious! Will order again.",
                    "One of the best dishes I've had. Highly recommend!",
                    "Perfectly cooked and full of flavor.",
                    "Exceeded my expectations. Amazing!"
                ])
            elif rating >= 3.5:
                comment = random.choice([
                    "Pretty good. Solid choice.",
                    "Tasty and well-prepared.",
                    "Good value for money. Would order again.",
                    "Nice flavors, decent portion size."
                ])
            else:
                comment = random.choice([
                    "Was disappointed. Not what I expected.",
                    "Below average. Needs improvement.",
                    "Not worth the price. Skip this one.",
                    "Flavors were off. Probably won't order again."
                ])
            
            # Photos for dish review (30% chance)
            photos = []
            if random.random() < 0.3:
                photos = ['https://images.unsplash.com/photo-1546069901-ba9599a7e63c']
            
            try:
                DishReview.objects.create(
                    menu_item=menu_item,
                    customer=customer,
                    order=order,
                    rating=rating,
                    comment=comment,
                    photos=photos,
                    taste_rating=taste,
                    portion_size_rating=portion,
                    value_rating=value,
                    helpful_count=random.randint(0, 20),
                    status='approved',
                    is_verified_purchase=is_verified,
                    created_at=timezone.now() - timedelta(days=random.randint(1, 60))
                )
                dish_reviews_created += 1
            except IntegrityError:
                continue
        
        self.stdout.write(f"  Created {dish_reviews_created} dish reviews")
        
        # Create dish quick ratings (this HAS tags field)
        dish_quick_ratings = 0
        for i in range(review_count // 3):
            if not menu_items:
                break
            
            menu_item = random.choice(menu_items)
            customer = random.choice(customers)
            
            # Check if rating already exists
            if DishRating.objects.filter(menu_item=menu_item, customer=customer).exists():
                continue
            
            rating = Decimal(str(round(random.uniform(2.0, 5.0), 1)))
            tags = random.sample(dish_tags, random.randint(0, 2)) if random.random() > 0.6 else []
            
            try:
                DishRating.objects.create(
                    menu_item=menu_item,
                    customer=customer,
                    order=None,
                    rating=rating,
                    taste=Decimal(str(round(random.uniform(2.0, 5.0), 1))) if random.random() > 0.4 else None,
                    portion_size=Decimal(str(round(random.uniform(2.0, 5.0), 1))) if random.random() > 0.4 else None,
                    value=Decimal(str(round(random.uniform(2.0, 5.0), 1))) if random.random() > 0.4 else None,
                    tags=tags,
                    is_verified_purchase=False,
                    is_quick_rating=True,
                    created_at=timezone.now() - timedelta(days=random.randint(1, 60))
                )
                dish_quick_ratings += 1
            except IntegrityError:
                continue
        
        # Update rating aggregates
        for restaurant in restaurants:
            try:
                restaurant.update_rating_stats()
            except Exception:
                pass
        
        for menu_item in menu_items[:100]:
            try:
                menu_item.update_rating_stats()
            except Exception:
                pass
        
        self.stdout.write(f"  ✅ Created {reviews_created} restaurant reviews")
        self.stdout.write(f"  ✅ Created {responses_created} owner responses")
        self.stdout.write(f"  ✅ Created {reports_created} review reports")
        self.stdout.write(f"  ✅ Created {votes_created} helpful votes")
        self.stdout.write(f"  ✅ Created {quick_ratings_created} quick restaurant ratings")
        self.stdout.write(f"  ✅ Created {dish_reviews_created} dish reviews")
        self.stdout.write(f"  ✅ Created {dish_quick_ratings} quick dish ratings")