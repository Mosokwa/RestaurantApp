# management/commands/create_loyalty_data.py
from django.core.management.base import BaseCommand
from api.models.loyalty_models import (
    MultiRestaurantLoyaltyProgram, RestaurantLoyaltySettings, CustomerLoyalty,
    PointsTransaction, Reward, RewardRedemption, DiscountVoucher
)
from api.models.restaurant_models import Restaurant
from api.models.user_models import Customer
from api.models.menu_models import MenuItem
import random
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Create loyalty program data'
    
    def handle(self, *args, **options):
        # Create loyalty program
        program, created = MultiRestaurantLoyaltyProgram.objects.get_or_create(
            name='Dar es Salaam Restaurant Loyalty Program',
            defaults={
                'program_type': 'global',
                'is_active': True,
                'default_points_per_dollar': Decimal('10.00'),
                'global_signup_bonus_points': 500,
                'global_referral_bonus_points': 1000,
                'bronze_min_points': 0,
                'silver_min_points': 5000,
                'gold_min_points': 15000,
                'platinum_min_points': 30000
            }
        )
        
        # Create restaurant loyalty settings for 30 restaurants
        restaurants = Restaurant.objects.all()[:30]
        for restaurant in restaurants:
            RestaurantLoyaltySettings.objects.get_or_create(
                restaurant=restaurant,
                program=program,
                defaults={
                    'is_loyalty_enabled': True,
                    'custom_points_per_dollar': Decimal(str(random.choice([8, 10, 12, 15]))),
                    'custom_signup_bonus_points': random.randint(300, 800),
                    'minimum_order_amount_for_points': Decimal(str(random.choice([5000, 10000, 15000]))),
                    'allow_point_redemption': True,
                    'allow_reward_redemption': True,
                    'points_expiry_days': random.choice([180, 365, 730]),
                    'max_points_per_order': random.choice([None, 1000, 2000, 3000])
                }
            )
        
        # Create customer loyalty profiles for 100 customers
        customers = Customer.objects.all()[:100]
        for customer in customers:
            loyalty, created = CustomerLoyalty.objects.get_or_create(
                customer=customer,
                program=program,
                defaults={
                    'current_points': random.randint(0, 40000),
                    'lifetime_points': random.randint(1000, 50000),
                    'total_orders': random.randint(5, 100),
                    'total_spent': Decimal(str(random.randint(50000, 500000))),
                    'restaurant_stats': self.get_restaurant_stats(customer)
                }
            )
            
            if created:
                # Update tier
                loyalty._update_tier()
                loyalty.save()
            
            # Create points transactions
            num_transactions = random.randint(5, 20)
            for i in range(num_transactions):
                transaction_type = random.choice(['earned', 'redeemed', 'signup_bonus', 'referral_bonus'])
                if transaction_type == 'earned':
                    points = random.randint(100, 1000)
                elif transaction_type == 'redeemed':
                    points = -random.randint(100, 500)
                else:
                    points = random.randint(500, 1000)
                
                restaurant = random.choice(restaurants) if random.choice([True, False]) else None
                
                PointsTransaction.objects.create(
                    customer_loyalty=loyalty,
                    points=points,
                    transaction_type=transaction_type,
                    reason=self.get_transaction_reason(transaction_type),
                    restaurant=restaurant,
                    transaction_date=timezone.now() - timedelta(days=random.randint(0, 180)),
                    is_active=random.choice([True, False])
                )
        
        # Create rewards
        rewards = [
            {'name': '10% Discount', 'type': 'discount', 'points': 1000, 'discount_percent': 10},
            {'name': '15% Discount', 'type': 'discount', 'points': 1500, 'discount_percent': 15},
            {'name': '20% Discount', 'type': 'discount', 'points': 2000, 'discount_percent': 20},
            {'name': 'Free Delivery', 'type': 'free_delivery', 'points': 500},
            {'name': 'Free Appetizer', 'type': 'free_item', 'points': 800},
            {'name': 'Free Dessert', 'type': 'free_item', 'points': 600},
            {'name': '5000 TZS Voucher', 'type': 'voucher', 'points': 2500, 'discount_amount': 5000},
            {'name': '10000 TZS Voucher', 'type': 'voucher', 'points': 4500, 'discount_amount': 10000},
        ]
        
        for reward_data in rewards:
            reward = Reward.objects.create(
                program=program,
                name=reward_data['name'],
                description=f'Redeem for {reward_data["name"].lower()}',
                reward_type=reward_data['type'],
                points_required=reward_data['points'],
                discount_percentage=reward_data.get('discount_percent'),
                discount_amount=reward_data.get('discount_amount'),
                is_active=True,
                stock_quantity=random.choice([0, 100, 500]),
                min_tier_required=random.choice(['bronze', 'silver', 'gold', 'platinum']),
                valid_from=timezone.now(),
                valid_until=timezone.now() + timedelta(days=365)
            )
            
            # Add applicable restaurants
            applicable_restaurants = random.sample(list(restaurants), random.randint(5, 15))
            reward.applicable_restaurants.set(applicable_restaurants)
            
            # Create some reward redemptions
            num_redemptions = random.randint(0, 10)
            loyal_customers = CustomerLoyalty.objects.filter(current_points__gte=reward_data['points'])[:num_redemptions]
            
            for customer_loyalty in loyal_customers:
                redemption = RewardRedemption.objects.create(
                    customer_loyalty=customer_loyalty,
                    reward=reward,
                    points_used=reward_data['points'],
                    status=random.choice(['completed', 'pending']),
                    restaurant=random.choice(applicable_restaurants),
                    redeemed_at=timezone.now() - timedelta(days=random.randint(0, 90)) if random.choice([True, False]) else None
                )
                
                # Create discount voucher for discount rewards
                if reward.reward_type in ['discount', 'voucher']:
                    DiscountVoucher.objects.create(
                        code=f'VOUCHER{random.randint(100000, 999999)}',
                        restaurant=redemption.restaurant,
                        discount_type='percentage' if reward.reward_type == 'discount' else 'fixed',
                        discount_value=reward.discount_percentage or reward.discount_amount or Decimal('10'),
                        max_discount_amount=Decimal('5000') if reward.reward_type == 'discount' else None,
                        is_used=redemption.status == 'completed',
                        used_at=redemption.redeemed_at if redemption.status == 'completed' else None,
                        valid_from=timezone.now(),
                        valid_until=timezone.now() + timedelta(days=30)
                    )
        
        self.stdout.write(self.style.SUCCESS('Created loyalty program with rewards and customer profiles'))
    
    def get_restaurant_stats(self, customer):
        stats = {}
        orders = customer.orders.all()[:10]
        for order in orders:
            restaurant_id = str(order.restaurant.restaurant_id)
            if restaurant_id not in stats:
                stats[restaurant_id] = {
                    'orders': 0,
                    'spent': '0.00',
                    'last_order': timezone.now().isoformat(),
                    'restaurant_name': order.restaurant.name
                }
            
            stats[restaurant_id]['orders'] += 1
            current_spent = float(stats[restaurant_id]['spent'])
            stats[restaurant_id]['spent'] = str(current_spent + float(order.total_amount))
            stats[restaurant_id]['last_order'] = order.order_placed_at.isoformat()
        
        return stats
    
    def get_transaction_reason(self, transaction_type):
        reasons = {
            'earned': ['Order completion', 'Birthday bonus', 'Restaurant visit bonus', 'Special promotion'],
            'redeemed': ['Reward redemption', 'Points exchange'],
            'signup_bonus': ['Welcome bonus', 'New member bonus'],
            'referral_bonus': ['Friend referral', 'Referral program'],
            'adjusted': ['Points adjustment', 'Manual adjustment']
        }
        return random.choice(reasons.get(transaction_type, ['General']))