# management/commands/_customers.py
from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from django.utils import timezone
import random
import string

class Command(BaseCommand):
    help = 'Create customers with varied preferences'
    
    FIRST_NAMES = ['James', 'Mary', 'John', 'Patricia', 'Robert', 'Jennifer', 'Michael', 'Linda', 'William', 'Elizabeth',
                   'David', 'Barbara', 'Richard', 'Susan', 'Joseph', 'Jessica', 'Thomas', 'Sarah', 'Charles', 'Karen',
                   'Christopher', 'Nancy', 'Daniel', 'Lisa', 'Matthew', 'Betty', 'Anthony', 'Margaret', 'Mark', 'Sandra',
                   'Paul', 'Ashley', 'Steven', 'Kimberly', 'Andrew', 'Emily', 'Kenneth', 'Donna', 'Joshua', 'Michelle',
                   'Kevin', 'Carol', 'Brian', 'Amanda', 'George', 'Melissa', 'Edward', 'Deborah', 'Ronald', 'Stephanie']
    
    LAST_NAMES = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez',
                  'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin',
                  'Lee', 'Perez', 'Thompson', 'White', 'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis', 'Robinson',
                  'Walker', 'Young', 'Allen', 'King', 'Wright', 'Scott', 'Torres', 'Nguyen', 'Hill', 'Flores',
                  'Green', 'Adams', 'Nelson', 'Baker', 'Hall', 'Rivera', 'Campbell', 'Mitchell', 'Carter', 'Roberts']
    
    TANZANIAN_NAMES = ['Juma', 'Mohamed', 'Hassan', 'Ali', 'Salim', 'Fatma', 'Aisha', 'Zainab', 'Mariam', 'Saida',
                       'Rashid', 'Hamza', 'Khadija', 'Farida', 'Abdallah', 'Mwanahamisi', 'Mbaraka', 'Neema', 'Baraka', 'Upendo']
    
    TANZANIAN_LAST = ['Juma', 'Mkono', 'Mtui', 'Mushi', 'Msafiri', 'Kibaki', 'Mwinyi', 'Mpata', 'Kisanga', 'Mrema']
    
    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=200, help='Number of customers to create')
        parser.add_argument('--skip-existing', action='store_true')
        parser.add_argument('--clean', action='store_true')
    
    def handle(self, *args, **options):
        from api.models import User, Customer, Cuisine, Restaurant, CustomerLoyalty, MultiRestaurantLoyaltyProgram
        
        count = options['count']
        
        if options['clean']:
            User.objects.filter(user_type='customer').delete()
            self.stdout.write("  Cleaned existing customers")
        
        existing_count = User.objects.filter(user_type='customer').count()
        if options['skip_existing'] and existing_count >= count:
            self.stdout.write(f"  {existing_count} customers already exist, skipping")
            return
        
        cuisines = list(Cuisine.objects.all())
        restaurants = list(Restaurant.objects.filter(status='active'))
        loyalty_program = MultiRestaurantLoyaltyProgram.objects.first()
        
        if not loyalty_program:
            self.stdout.write(self.style.ERROR("  No loyalty program found! Run _base_setup first."))
            return
        
        customers_created = 0
        
        # Create customers (mix of Tanzanian and international)
        for i in range(count):
            # Alternate between Tanzanian and international names
            use_tz_name = random.random() > 0.6
            
            if use_tz_name:
                first_name = random.choice(self.TANZANIAN_NAMES)
                last_name = random.choice(self.TANZANIAN_LAST)
            else:
                first_name = random.choice(self.FIRST_NAMES)
                last_name = random.choice(self.LAST_NAMES)
            
            username = f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 999)}"
            email = f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 999)}@customer.com"
            phone = f"071{random.randint(1000000, 9999999)}"
            
            user = User.objects.create(
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone_number=phone,
                user_type='customer',
                is_verified=True,
                email_verified=random.random() > 0.1,  # 90% verified
                password=make_password('customer123'),
                verification_code=''.join(random.choices(string.digits, k=6)),
                verification_code_expires=timezone.now() + timezone.timedelta(days=7)
            )
            
            # Dietary preferences
            dietary_prefs = {
                'vegetarian': random.random() > 0.85,
                'vegan': random.random() > 0.95,
                'gluten_free': random.random() > 0.9,
                'halal': random.random() > 0.7 if use_tz_name else random.random() > 0.85,
                'dairy_free': random.random() > 0.92,
                'nut_free': random.random() > 0.92,
            }
            
            # Favorite cuisines (2-5 random cuisines)
            fav_cuisines = random.sample(cuisines, min(random.randint(2, 5), len(cuisines)))
            
            # Favorite restaurants (0-8 random restaurants)
            fav_restaurants = random.sample(restaurants, min(random.randint(0, 8), len(restaurants)))
            
            customer = Customer.objects.create(
                user=user,
                date_of_birth=timezone.datetime(random.randint(1980, 2005), random.randint(1, 12), random.randint(1, 28)),
                loyalty_points=random.randint(0, 25000),
                dietary_preferences=dietary_prefs,
                newsletter_subscribed=random.random() > 0.3,
                marketing_emails=random.random() > 0.4
            )
            
            customer.favorite_cuisines.add(*fav_cuisines)
            customer.favorite_restaurants.add(*fav_restaurants)
            
            # Create loyalty profile
            initial_points = random.randint(0, 5000)
            lifetime_points = initial_points + random.randint(0, 10000)
            
            # Determine tier based on points
            if initial_points >= 15000:
                tier = 'platinum'
            elif initial_points >= 5000:
                tier = 'gold'
            elif initial_points >= 1000:
                tier = 'silver'
            else:
                tier = 'bronze'
            
            CustomerLoyalty.objects.create(
                customer=customer,
                program=loyalty_program,
                current_points=initial_points,
                lifetime_points=lifetime_points,
                tier=tier,
                total_orders=random.randint(0, 50),
                total_spent=random.randint(0, 1500000),
                restaurant_stats={}
            )
            
            customers_created += 1
            
            if customers_created % 50 == 0:
                self.stdout.write(f"  Created {customers_created}/{count} customers")
        
        self.stdout.write(f"  ✅ Created {customers_created} customers")