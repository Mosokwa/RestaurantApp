# management/commands/loyalty.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
import random
from datetime import timedelta


class Command(BaseCommand):
    help = 'Create loyalty transactions, referrals, and reward redemptions'
    
    def add_arguments(self, parser):
        parser.add_argument('--skip-existing', action='store_true')
        parser.add_argument('--clean', action='store_true')
    
    def handle(self, *args, **options):
        from api.models import (
            Customer, CustomerLoyalty, PointsTransaction, Reward, 
            RewardRedemption, DiscountVoucher, Referral,
            MultiRestaurantLoyaltyProgram, Restaurant
        )
        
        if options['clean']:
            PointsTransaction.objects.all().delete()
            RewardRedemption.objects.all().delete()
            Referral.objects.all().delete()
            DiscountVoucher.objects.all().delete()
            self.stdout.write("  Cleaned existing loyalty data")
        
        customers = list(Customer.objects.all())
        restaurants = list(Restaurant.objects.filter(status='active'))
        loyalty_program = MultiRestaurantLoyaltyProgram.objects.first()
        
        if not customers:
            self.stdout.write(self.style.ERROR("  No customers found! Run customers first."))
            return
        
        # Create sample rewards
        rewards_data = [
            {'name': '10% Off Next Order', 'type': 'discount', 'points': 500, 'discount_percent': 10, 'tier': 'bronze'},
            {'name': 'Free Delivery', 'type': 'free_delivery', 'points': 300, 'tier': 'bronze'},
            {'name': 'TZS 10,000 Voucher', 'type': 'voucher', 'points': 1000, 'discount_amount': 10000, 'tier': 'silver'},
            {'name': 'Free Menu Item', 'type': 'free_item', 'points': 800, 'tier': 'silver'},
            {'name': '20% Off Next Order', 'type': 'discount', 'points': 1500, 'discount_percent': 20, 'tier': 'gold'},
            {'name': 'TZS 25,000 Voucher', 'type': 'voucher', 'points': 2500, 'discount_amount': 25000, 'tier': 'gold'},
            {'name': 'Free Meal for Two', 'type': 'voucher', 'points': 5000, 'discount_amount': 60000, 'tier': 'platinum'},
            {'name': 'Private Event Access', 'type': 'voucher', 'points': 10000, 'discount_amount': 100000, 'tier': 'platinum'},
        ]
        
        rewards_created = 0
        for reward_data in rewards_data:
            reward, created = Reward.objects.get_or_create(
                program=loyalty_program,
                name=reward_data['name'],
                defaults={
                    'reward_type': reward_data['type'],
                    'points_required': reward_data['points'],
                    'discount_percentage': reward_data.get('discount_percent'),
                    'discount_amount': reward_data.get('discount_amount'),
                    'min_tier_required': reward_data['tier'],
                    'is_active': True,
                    'valid_from': timezone.now() - timedelta(days=30),
                    'valid_until': timezone.now() + timedelta(days=365),
                }
            )
            if created:
                rewards_created += 1
        
        self.stdout.write(f"  Created {rewards_created} rewards")
        
        # Create points transactions for each customer
        loyalty_profiles = []
        for customer in customers:
            try:
                loyalty = customer.loyalty_profile
                loyalty_profiles.append(loyalty)
            except Exception:
                loyalty = CustomerLoyalty.objects.create(
                    customer=customer,
                    program=loyalty_program,
                    current_points=random.randint(0, 8000),
                    lifetime_points=random.randint(0, 15000),
                    tier='bronze',
                    total_orders=random.randint(0, 30),
                    total_spent=random.randint(0, 500000)
                )
                loyalty_profiles.append(loyalty)
        
        # Create points transactions
        transactions_created = 0
        for loyalty in loyalty_profiles[:500]:
            num_transactions = random.randint(1, 15)
            for t in range(num_transactions):
                days_ago = random.randint(1, 90)
                points = random.randint(50, 500)
                
                PointsTransaction.objects.create(
                    customer_loyalty=loyalty,
                    points=points,
                    transaction_type=random.choice(['earned', 'signup_bonus', 'referral_bonus']),
                    reason=f"Order reward from {random.choice(['daily order', 'weekly bonus', 'special promotion', 'birthday bonus'])}",
                    transaction_date=timezone.now() - timedelta(days=days_ago),
                    expires_at=timezone.now() + timedelta(days=365 - days_ago),
                    is_active=True
                )
                transactions_created += 1
                
                if points > 0:
                    loyalty.current_points += points
                    loyalty.lifetime_points += points
                    loyalty.save()
        
        self.stdout.write(f"  Created {transactions_created} points transactions")
        
        # Create referrals
        customers_list = list(customers)
        referrals_created = 0
        for i in range(min(100, len(customers_list) // 2)):
            referrer = random.choice(customers_list)
            referred_email = f"referred_{i}_{random.randint(1,9999)}@example.com"
            
            referral = Referral.objects.create(
                referrer=referrer,
                referred_email=referred_email,
                referral_code=referrer.loyalty_profile.referral_code,
                status=random.choice(['pending', 'completed', 'expired']),
                created_at=timezone.now() - timedelta(days=random.randint(1, 60)),
                expires_at=timezone.now() + timedelta(days=random.randint(1, 30))
            )
            
            if referral.status == 'completed':
                referral.completed_at = referral.created_at + timedelta(days=random.randint(1, 14))
                referral.save()
            
            referrals_created += 1
        
        self.stdout.write(f"  Created {referrals_created} referrals")
        
        # Create reward redemptions
        rewards_list = list(Reward.objects.filter(is_active=True))
        redemptions_created = 0
        
        for loyalty in loyalty_profiles[:200]:
            if loyalty.current_points >= 300 and rewards_list:
                if random.random() < 0.3:
                    eligible_rewards = [r for r in rewards_list if loyalty.current_points >= r.points_required]
                    if eligible_rewards:
                        reward = random.choice(eligible_rewards)
                        restaurant = random.choice(restaurants) if restaurants else None
                        
                        redemption = RewardRedemption.objects.create(
                            customer_loyalty=loyalty,
                            reward=reward,
                            points_used=reward.points_required,
                            status=random.choice(['pending', 'completed', 'cancelled']),
                            restaurant=restaurant if restaurant else restaurants[0] if restaurants else None,
                            created_at=timezone.now() - timedelta(days=random.randint(1, 30)),
                            expires_at=timezone.now() + timedelta(days=random.randint(30, 90))
                        )
                        
                        if redemption.status == 'completed':
                            redemption.redeemed_at = redemption.created_at + timedelta(days=random.randint(1, 7))
                            redemption.save()
                            
                            # Create discount voucher - FIXED: Don't try to set redemption field
                            if reward.reward_type in ['discount', 'voucher']:
                                DiscountVoucher.objects.create(
                                    code=redemption.redemption_code,
                                    discount_type='percentage' if reward.reward_type == 'discount' else 'fixed',
                                    discount_value=reward.discount_percentage or reward.discount_amount or 10,
                                    valid_from=redemption.created_at,
                                    valid_until=redemption.expires_at,
                                    is_used=random.random() < 0.5
                                )
                            
                            # Deduct points
                            loyalty.current_points -= reward.points_required
                            loyalty.save()
                            
                            redemptions_created += 1
        
        self.stdout.write(f"  Created {redemptions_created} reward redemptions")
        self.stdout.write(f"  ✅ Loyalty data population complete")