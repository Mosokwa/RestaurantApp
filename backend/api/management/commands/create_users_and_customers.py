# management/commands/create_users_and_customers.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from api.models.user_models import Customer, User
from datetime import date
import random
from faker import Faker

fake = Faker()
User = get_user_model()

class Command(BaseCommand):
    help = 'Create users, restaurant owners, and customers'
    
    def handle(self, *args, **options):
        # Clear existing test users
        User.objects.filter(email__contains='@example.com').delete()
        
        # Create 30 restaurant owners
        owners = []
        owner_names = [
            'John Mwenda', 'Fatuma Hassan', 'Robert Kimambo', 'Sarah Juma', 'David Mushi',
            'Aisha Omar', 'Joseph Lema', 'Grace Mbogo', 'Michael Kihongo', 'Zainab Ally',
            'Peter Mrema', 'Hannah Shayo', 'William Mwakyusa', 'Mariam Salim', 'Charles Mwita',
            'Neema Charles', 'Daniel Mollel', 'Rebecca Mwanjisi', 'James Ngalawa', 'Asha Rajabu',
            'Thomas Msangi', 'Esther Makame', 'Richard Mwasenga', 'Salma Khamis', 'Edward Lyimo',
            'Faith Kessy', 'Simon Mfinanga', 'Joyce Mbilinyi', 'Patrick Msofe', 'Rehema Jafari'
        ]
        
        for i, name in enumerate(owner_names):
            first_name, last_name = name.split(' ', 1)
            username = f"{first_name.lower()}.{last_name.lower()}"
            email = f"{username}@example.com"
            
            user = User.objects.create_user(
                username=username,
                email=email,
                password='password123',
                first_name=first_name,
                last_name=last_name,
                user_type='owner',
                phone_number=f'+2557{random.randint(10000000, 99999999)}',
                is_verified=True,
                email_verified=True
            )
            owners.append(user)
        
        # Create 200 customers
        customers_data = []
        for i in range(200):
            username = f'customer{i+1}'
            email = f'customer{i+1}@example.com'
            
            user = User.objects.create_user(
                username=username,
                email=email,
                password='password123',
                user_type='customer',
                phone_number=f'+2556{random.randint(10000000, 99999999)}',
                is_verified=True,
                email_verified=True
            )
            
            customer = Customer.objects.create(
                user=user,
                date_of_birth=fake.date_of_birth(minimum_age=18, maximum_age=70),
                loyalty_points=random.randint(0, 5000),
                dietary_preferences=self.get_random_dietary_preferences(),
                newsletter_subscribed=random.choice([True, False]),
                marketing_emails=random.choice([True, False])
            )
            
            customers_data.append(customer)
        
        self.stdout.write(self.style.SUCCESS(f'Created {len(owners)} owners and {len(customers_data)} customers'))
    
    def get_random_dietary_preferences(self):
        preferences = {
            'vegetarian': random.choice([True, False]),
            'vegan': random.choice([True, False]),
            'gluten_free': random.choice([True, False]),
            'halal': random.choice([True, True, False]),
            'spicy_food_lover': random.choice([True, False]),
            'seafood_allergy': random.choice([True, False]),
            'nut_allergy': random.choice([True, False]),
            'dairy_free': random.choice([True, False]),
            'low_carb': random.choice([True, False]),
            'low_sodium': random.choice([True, False]),
            'kosher': random.choice([True, False]),
        }
        return preferences