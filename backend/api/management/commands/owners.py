# management/commands/_owners.py
from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from django.utils import timezone
import random
import string

class Command(BaseCommand):
    help = 'Create restaurant owners'
    
    OWNERS = [
        ('john_moshi', 'John', 'Moshi', 'john@kitchen.co.tz', '0712345678'),
        ('sarah_mtui', 'Sarah', 'Mtui', 'sarah@tasteoftz.com', '0723456789'),
        ('hamza_juma', 'Hamza', 'Juma', 'hamza@spicebazaar.com', '0734567890'),
        ('fatma_said', 'Fatma', 'Said', 'fatma@zanzibardelights.com', '0745678901'),
        ('james_mbowe', 'James', 'Mbowe', 'james@darstreetfood.com', '0756789012'),
        ('grace_mushi', 'Grace', 'Mushi', 'grace@kilimanjrocafe.com', '0767890123'),
        ('ali_hassan', 'Ali', 'Hassan', 'ali@indianflavours.co.tz', '0778901234'),
        ('rehema_kibaki', 'Rehema', 'Kibaki', 'rehema@seasidegrill.com', '0789012345'),
        ('peter_nyambo', 'Peter', 'Nyambo', 'peter@pizzahub.co.tz', '0790123456'),
        ('amina_juma', 'Amina', 'Juma', 'amina@coffeecorner.com', '0711223344'),
    ]
    
    def add_arguments(self, parser):
        parser.add_argument('--skip-existing', action='store_true')
        parser.add_argument('--clean', action='store_true')
    
    def handle(self, *args, **options):
        from api.models import User
        
        if options['clean']:
            User.objects.filter(user_type='owner').delete()
            self.stdout.write("  Cleaned existing owners")
        
        created_count = 0
        for username, first_name, last_name, email, phone in self.OWNERS:
            if options['skip_existing'] and User.objects.filter(username=username).exists():
                continue
            
            user = User.objects.create(
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone_number=phone,
                user_type='owner',
                is_restaurant_owner=True,
                is_verified=True,
                email_verified=True,
                password=make_password('owner123'),
                verification_code=''.join(random.choices(string.digits, k=6)),
                verification_code_expires=timezone.now() + timezone.timedelta(days=7)
            )
            created_count += 1
        
        self.stdout.write(f"  Created {created_count} owners")