# management/commands/create_cuisines.py
from django.core.management.base import BaseCommand
from api.models.menu_models import Cuisine

class Command(BaseCommand):
    help = 'Create Tanzanian and international cuisines'
    
    def handle(self, *args, **options):
        cuisines = [
            {'name': 'Swahili', 'description': 'Traditional coastal dishes with coconut and spices'},
            {'name': 'Nyama Choma', 'description': 'Tanzanian grilled meat specialties'},
            {'name': 'Ugali & Fish', 'description': 'Traditional Tanzanian staple with fresh fish'},
            {'name': 'Pilau', 'description': 'Spiced rice dish with meat or vegetables'},
            {'name': 'Chipsi Mayai', 'description': 'Tanzanian chips omelette'},
            {'name': 'Mishkaki', 'description': 'Tanzanian meat skewers'},
            {'name': 'Wali na Maharage', 'description': 'Rice and beans'},
            {'name': 'Supu', 'description': 'Traditional Tanzanian soups'},
            {'name': 'Italian', 'description': 'Pizza, pasta and Italian classics'},
            {'name': 'Chinese', 'description': 'Authentic Chinese cuisine'},
            {'name': 'Indian', 'description': 'Indian curries and breads'},
            {'name': 'American', 'description': 'Burgers, fries and American classics'},
            {'name': 'Mexican', 'description': 'Tacos, burritos and Mexican flavors'},
            {'name': 'Japanese', 'description': 'Sushi, ramen and Japanese cuisine'},
            {'name': 'Lebanese', 'description': 'Middle Eastern and Lebanese dishes'},
            {'name': 'Fast Food', 'description': 'Quick service and fast food'},
            {'name': 'Seafood', 'description': 'Fresh seafood dishes'},
            {'name': 'Vegetarian', 'description': 'Vegetarian and plant-based options'},
            {'name': 'Breakfast', 'description': 'Breakfast and brunch items'},
            {'name': 'Desserts', 'description': 'Sweets and desserts'},
            {'name': 'Beverages', 'description': 'Drinks and beverages'},
            {'name': 'Barbecue', 'description': 'Grilled and smoked meats'},
            {'name': 'Thai', 'description': 'Thai cuisine and curries'},
            {'name': 'Korean', 'description': 'Korean BBQ and dishes'},
            {'name': 'French', 'description': 'French cuisine and pastries'},
            {'name': 'Ethiopian', 'description': 'Ethiopian injera and stews'},
            {'name': 'South African', 'description': 'South African braai and dishes'},
            {'name': 'Mediterranean', 'description': 'Mediterranean and Greek food'},
            {'name': 'Pakistani', 'description': 'Pakistani curries and rice'},
            {'name': 'Turkish', 'description': 'Turkish kebabs and meze'},
            {'name': 'Caribbean', 'description': 'Caribbean jerk and stews'},
            {'name': 'Vietnamese', 'description': 'Vietnamese pho and spring rolls'},
            {'name': 'Spanish', 'description': 'Spanish tapas and paella'},
            {'name': 'Portuguese', 'description': 'Portuguese seafood and stews'},
            {'name': 'Australian', 'description': 'Australian cafe food'},
            {'name': 'Brazilian', 'description': 'Brazilian churrasco'},
            {'name': 'Malaysian', 'description': 'Malaysian street food'},
            {'name': 'Indonesian', 'description': 'Indonesian satay and nasi goreng'},
            {'name': 'Fusion', 'description': 'Fusion cuisine combining different styles'},
        ]
        
        created_count = 0
        for cuisine_data in cuisines:
            cuisine, created = Cuisine.objects.get_or_create(
                name=cuisine_data['name'],
                defaults={
                    'description': cuisine_data['description'],
                    'is_active': True
                }
            )
            if created:
                created_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Created {created_count} cuisines'))