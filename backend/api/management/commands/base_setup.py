# management/commands/_base_setup.py
from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from decimal import Decimal
import random

class Command(BaseCommand):
    help = 'Setup base data: cuisines, loyalty program'
    
    def add_arguments(self, parser):
        parser.add_argument('--skip-existing', action='store_true')
        parser.add_argument('--clean', action='store_true')
    
    def handle(self, *args, **options):
        from api.models import Cuisine, MultiRestaurantLoyaltyProgram, User
        
        if options['clean']:
            Cuisine.objects.all().delete()
            MultiRestaurantLoyaltyProgram.objects.all().delete()
            self.stdout.write("  Cleaned existing base data")
        
        # Create Cuisines
        cuisines = [
            'Tanzanian/Swahili', 'Indian', 'Chinese', 'Italian', 'Mexican',
            'Japanese', 'Thai', 'Mediterranean', 'American', 'BBQ', 
            'Seafood', 'Vegetarian', 'Vegan', 'Fast Food', 'Coffee & Tea',
            'Bakery', 'African Fusion', 'Ethiopian', 'Moroccan', 'Lebanese',
            'Turkish', 'Greek', 'French', 'Spanish', 'German', 'Korean',
            'Vietnamese', 'Caribbean', 'Brazilian', 'Peruvian'
        ]
        
        created_count = 0
        for cuisine_name in cuisines:
            obj, created = Cuisine.objects.get_or_create(name=cuisine_name)
            if created:
                created_count += 1
        
        self.stdout.write(f"  Created {created_count} cuisines")
        
        # Create Global Loyalty Program (if not exists)
        loyalty_program, created = MultiRestaurantLoyaltyProgram.objects.get_or_create(
            program_type='global',
            defaults={
                'name': 'Global Loyalty Program',
                'is_active': True,
                'default_points_per_dollar': 1.00,
                'global_signup_bonus_points': 100,
                'global_referral_bonus_points': 500,
                'bronze_min_points': 0,
                'silver_min_points': 1000,
                'gold_min_points': 5000,
                'platinum_min_points': 15000,
            }
        )
        
        if created:
            self.stdout.write("  Created global loyalty program")
        else:
            self.stdout.write("  Global loyalty program already exists")
        
        # Create superuser if doesn't exist
        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@restaurantapp.com',
                password='admin123',
                user_type='admin',
                is_verified=True,
                email_verified=True
            )
            self.stdout.write("  Created admin user (admin/admin123)")