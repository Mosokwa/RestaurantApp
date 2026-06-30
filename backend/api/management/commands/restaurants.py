# management/commands/_restaurants.py (EXPANDED VERSION)
from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
import random
import json

class Command(BaseCommand):
    help = 'Create restaurants and branches (Tanzania focused with rich data)'
    
    def add_arguments(self, parser):
        parser.add_argument('--skip-existing', action='store_true')
        parser.add_argument('--clean', action='store_true')
    
    def handle(self, *args, **options):
        from api.models import (
            User, Restaurant, Branch, Address, Cuisine, 
            RestaurantLoyaltySettings, MultiRestaurantLoyaltyProgram,
            RestaurantReviewSettings, RestaurantPerformanceMetrics
        )
        
        if options['clean']:
            Branch.objects.all().delete()
            Restaurant.objects.all().delete()
            Address.objects.all().delete()
            self.stdout.write("  Cleaned existing restaurants and branches")
        
        owners = list(User.objects.filter(user_type='owner'))
        if not owners:
            self.stdout.write(self.style.ERROR("  No owners found! Run _owners first."))
            return
        
        cuisines = list(Cuisine.objects.all())
        loyalty_program = MultiRestaurantLoyaltyProgram.objects.first()
        
        # ============================================================
        # ENHANCED RESTAURANTS DATA - TANZANIA FOCUSED
        # ============================================================
        
        restaurants_data = [
            # ========== KIGAMBONI / KIBADA AREA (Primary Testing Zone) ==========
            {
                'name': 'Kibada Seafood Paradise',
                'owner_idx': 0,
                'cuisines': ['Seafood', 'Tanzanian/Swahili'],
                'desc': 'Fresh seafood straight from the Indian Ocean, overlooking Kigamboni coastline. Our fishermen deliver daily catch every morning.',
                'story': 'Founded in 2010 by a local fishing family, Kibada Seafood Paradise started as a small beachside shack serving grilled fish to ferry passengers. Today, it\'s a Kigamboni landmark known for the freshest seafood in Dar es Salaam.',
                'phone': '0712345001',
                'email': 'info@kibadaseafood.com',
                'website': 'https://kibadaseafood.co.tz',
                'amenities': ['Ocean View', 'Outdoor Seating', 'Free WiFi', 'Parking', 'Family Friendly', 'Air Conditioning'],
                'gallery_images': [
                    'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4',
                    'https://images.unsplash.com/photo-1559339352-11d035aa65de'
                ],
                'is_featured': True,
                'reservation_enabled': True,
                'min_party_size': 1,
                'max_party_size': 20,
                'reservation_lead_time_hours': 2,
                'reservation_max_days_ahead': 30,
                'branches': [
                    {
                        'name': 'Main Beach Location',
                        'address': 'Plot 45, Kigamboni Beach Road',
                        'city': 'Kigamboni',
                        'is_main': True,
                        'hours': {
                            'monday': {'open': '11:00', 'close': '23:00'},
                            'tuesday': {'open': '11:00', 'close': '23:00'},
                            'wednesday': {'open': '11:00', 'close': '23:00'},
                            'thursday': {'open': '11:00', 'close': '23:00'},
                            'friday': {'open': '11:00', 'close': '00:00'},
                            'saturday': {'open': '10:00', 'close': '00:00'},
                            'sunday': {'open': '10:00', 'close': '22:00'},
                        },
                        'latitude': -6.8234,
                        'longitude': 39.3192
                    },
                    {
                        'name': 'Kibada Bypass Express',
                        'address': 'Kibada Bypass, Near Kibada Market',
                        'city': 'Kibada',
                        'is_main': False,
                        'hours': {
                            'monday': {'open': '10:00', 'close': '22:00'},
                            'tuesday': {'open': '10:00', 'close': '22:00'},
                            'wednesday': {'open': '10:00', 'close': '22:00'},
                            'thursday': {'open': '10:00', 'close': '22:00'},
                            'friday': {'open': '10:00', 'close': '23:00'},
                            'saturday': {'open': '10:00', 'close': '23:00'},
                            'sunday': {'open': '10:00', 'close': '21:00'},
                        },
                        'latitude': -6.8572,
                        'longitude': 39.2973
                    }
                ]
            },
            {
                'name': 'Kigamboni Sunset Grill',
                'owner_idx': 1,
                'cuisines': ['BBQ', 'American', 'Fast Food'],
                'desc': 'Best grilled meats and burgers with sunset views over the ocean. Famous for our signature BBQ sauce and live music on weekends.',
                'story': 'Started as a small roadside grill in 2015 by two friends who loved American BBQ. Their secret sauce recipe and friendly service made them a Kigamboni favorite. Now expanded with two locations.',
                'phone': '0712345002',
                'email': 'hello@sunsetgrill.co.tz',
                'website': 'https://sunsetgrill.co.tz',
                'amenities': ['Live Music', 'Outdoor Seating', 'Free Parking', 'TV Sports', 'Takeaway', 'Delivery'],
                'gallery_images': ['https://images.unsplash.com/photo-1555939594-58d7cb561ad1'],
                'is_featured': True,
                'reservation_enabled': False,
                'branches': [
                    {
                        'name': 'Ferry Terminal',
                        'address': 'Kigamboni Ferry Terminal Area',
                        'city': 'Kigamboni',
                        'is_main': True,
                        'hours': {
                            'monday': {'open': '12:00', 'close': '23:00'},
                            'tuesday': {'open': '12:00', 'close': '23:00'},
                            'wednesday': {'open': '12:00', 'close': '23:00'},
                            'thursday': {'open': '12:00', 'close': '23:00'},
                            'friday': {'open': '12:00', 'close': '01:00'},
                            'saturday': {'open': '12:00', 'close': '01:00'},
                            'sunday': {'open': '12:00', 'close': '22:00'},
                        },
                        'latitude': -6.8175,
                        'longitude': 39.2947
                    },
                    {
                        'name': 'Kibada Shopping Center',
                        'address': 'Kibada Shopping Center, Ground Floor',
                        'city': 'Kibada',
                        'is_main': False,
                        'hours': {
                            'monday': {'open': '11:00', 'close': '22:00'},
                            'tuesday': {'open': '11:00', 'close': '22:00'},
                            'wednesday': {'open': '11:00', 'close': '22:00'},
                            'thursday': {'open': '11:00', 'close': '22:00'},
                            'friday': {'open': '11:00', 'close': '23:00'},
                            'saturday': {'open': '11:00', 'close': '23:00'},
                            'sunday': {'open': '11:00', 'close': '21:00'},
                        },
                        'latitude': -6.8572,
                        'longitude': 39.2973
                    }
                ]
            },
            {
                'name': 'Kibada Spice Village',
                'owner_idx': 2,
                'cuisines': ['Indian', 'Tanzanian/Swahili', 'Vegetarian'],
                'desc': 'Authentic Indian and Swahili fusion cuisine in a tranquil garden setting. Specializing in vegetarian and vegan options.',
                'story': 'Run by a family with roots in both Zanzibar and Gujarat, this restaurant brings together the best of both culinary worlds. Our recipes have been passed down for four generations.',
                'phone': '0712345015',
                'email': 'spice@kibadavillage.com',
                'website': 'https://kibadaspice.com',
                'amenities': ['Garden Seating', 'Private Dining', 'Free WiFi', 'Parking', 'Vegetarian Options', 'Vegan Options', 'Family Friendly'],
                'gallery_images': ['https://images.unsplash.com/photo-1585937421612-70a008356fbe'],
                'is_featured': True,
                'reservation_enabled': True,
                'min_party_size': 2,
                'max_party_size': 30,
                'branches': [
                    {
                        'name': 'Garden Restaurant',
                        'address': 'Kibada Garden Estate, Plot 12',
                        'city': 'Kibada',
                        'is_main': True,
                        'hours': {
                            'monday': {'open': '12:00', 'close': '22:30'},
                            'tuesday': {'open': '12:00', 'close': '22:30'},
                            'wednesday': {'open': '12:00', 'close': '22:30'},
                            'thursday': {'open': '12:00', 'close': '22:30'},
                            'friday': {'open': '12:00', 'close': '23:30'},
                            'saturday': {'open': '11:00', 'close': '23:30'},
                            'sunday': {'open': '11:00', 'close': '22:00'},
                        },
                        'latitude': -6.8619,
                        'longitude': 39.2918
                    }
                ]
            },
            
            # ========== DAR ES SALAAM - OTHER DISTRICTS ==========
            {
                'name': 'Dar Spice Bazaar',
                'owner_idx': 2,
                'cuisines': ['Indian', 'Tanzanian/Swahili'],
                'desc': 'Authentic Indian and Swahili fusion cuisine in the heart of Dar. Our chefs combine traditional recipes with modern presentation.',
                'story': 'Bringing the flavors of Zanzibar spices to Dar es Salaam since 2015. Our head chef trained in Mumbai and Zanzibar before opening this beloved institution.',
                'phone': '0712345003',
                'email': 'spice@darbazaar.com',
                'website': 'https://darbazaar.co.tz',
                'amenities': ['Indoor Seating', 'Family Friendly', 'Takeaway', 'Delivery', 'Private Events', 'Air Conditioning'],
                'gallery_images': ['https://images.unsplash.com/photo-1505253758473-96b7015fcd40'],
                'is_featured': True,
                'reservation_enabled': True,
                'branches': [
                    {
                        'name': 'Mikocheni',
                        'address': 'Mikocheni Light Industrial Area, Chole Road',
                        'city': 'Mikocheni',
                        'is_main': True,
                        'hours': {
                            'monday': {'open': '11:00', 'close': '22:30'},
                            'tuesday': {'open': '11:00', 'close': '22:30'},
                            'wednesday': {'open': '11:00', 'close': '22:30'},
                            'thursday': {'open': '11:00', 'close': '22:30'},
                            'friday': {'open': '11:00', 'close': '23:30'},
                            'saturday': {'open': '11:00', 'close': '23:30'},
                            'sunday': {'open': '11:00', 'close': '22:00'},
                        },
                        'latitude': -6.7698,
                        'longitude': 39.2708
                    },
                    {
                        'name': 'Masaki',
                        'address': 'Masaki, Toure Drive, Sea Cliff Area',
                        'city': 'Masaki',
                        'is_main': False,
                        'hours': {
                            'monday': {'open': '12:00', 'close': '23:00'},
                            'tuesday': {'open': '12:00', 'close': '23:00'},
                            'wednesday': {'open': '12:00', 'close': '23:00'},
                            'thursday': {'open': '12:00', 'close': '23:00'},
                            'friday': {'open': '12:00', 'close': '00:00'},
                            'saturday': {'open': '12:00', 'close': '00:00'},
                            'sunday': {'open': '12:00', 'close': '22:30'},
                        },
                        'latitude': -6.7719,
                        'longitude': 39.2671
                    },
                    {
                        'name': 'Mbezi Beach',
                        'address': 'Mbezi Beach, UN Road, Near Peacock Hotel',
                        'city': 'Mbezi Beach',
                        'is_main': False,
                        'hours': {
                            'monday': {'open': '12:00', 'close': '22:00'},
                            'tuesday': {'open': '12:00', 'close': '22:00'},
                            'wednesday': {'open': '12:00', 'close': '22:00'},
                            'thursday': {'open': '12:00', 'close': '22:00'},
                            'friday': {'open': '12:00', 'close': '23:00'},
                            'saturday': {'open': '12:00', 'close': '23:00'},
                            'sunday': {'open': '12:00', 'close': '21:30'},
                        },
                        'latitude': -6.7431,
                        'longitude': 39.2180
                    }
                ]
            },
            {
                'name': 'Oysterbay Italian Kitchen',
                'owner_idx': 3,
                'cuisines': ['Italian', 'Mediterranean'],
                'desc': 'Authentic Italian pizzas, pastas, and wines by the beach. Our wood-fired oven pizzas are legendary.',
                'story': 'Family recipes passed down through generations from Naples, Italy. Now in Oysterbay since 2018, bringing true Italian hospitality to Dar.',
                'phone': '0712345004',
                'email': 'italian@oysterbay.co.tz',
                'website': 'https://oysterbayitalian.com',
                'amenities': ['Beach View', 'Wood-Fired Pizza', 'Wine Bar', 'Outdoor Seating', 'Free WiFi', 'Private Dining'],
                'gallery_images': ['https://images.unsplash.com/photo-1513104890138-7c749659a591'],
                'is_featured': True,
                'reservation_enabled': True,
                'branches': [
                    {
                        'name': 'Haile Selassie Road',
                        'address': 'Haile Selassie Road, Oysterbay',
                        'city': 'Oysterbay',
                        'is_main': True,
                        'hours': {
                            'monday': {'open': '12:00', 'close': '23:00'},
                            'tuesday': {'open': '12:00', 'close': '23:00'},
                            'wednesday': {'open': '12:00', 'close': '23:00'},
                            'thursday': {'open': '12:00', 'close': '23:00'},
                            'friday': {'open': '12:00', 'close': '00:00'},
                            'saturday': {'open': '12:00', 'close': '00:00'},
                            'sunday': {'open': '12:00', 'close': '22:00'},
                        },
                        'latitude': -6.7739,
                        'longitude': 39.2703
                    }
                ]
            },
            {
                'name': 'China Town Dar',
                'owner_idx': 4,
                'cuisines': ['Chinese', 'Asian Fusion'],
                'desc': 'Authentic Szechuan and Cantonese cuisine in Kariakoo. Known for our dim sum and Peking duck.',
                'story': 'The first dedicated Chinese restaurant in Dar es Salaam, established 2008 by Chef Zhang who brought authentic recipes from Hong Kong.',
                'phone': '0712345005',
                'email': 'info@chinatowndar.com',
                'website': 'https://chinatowndar.com',
                'amenities': ['Private Rooms', 'Karaoke', 'Free WiFi', 'Parking', 'Takeaway', 'Delivery'],
                'gallery_images': ['https://images.unsplash.com/photo-1563245372-f21724e3856d'],
                'is_featured': False,
                'reservation_enabled': True,
                'branches': [
                    {
                        'name': 'Kariakoo Main',
                        'address': 'Kariakoo Market Area, Libya Street',
                        'city': 'Kariakoo',
                        'is_main': True,
                        'hours': {
                            'monday': {'open': '10:00', 'close': '23:00'},
                            'tuesday': {'open': '10:00', 'close': '23:00'},
                            'wednesday': {'open': '10:00', 'close': '23:00'},
                            'thursday': {'open': '10:00', 'close': '23:00'},
                            'friday': {'open': '10:00', 'close': '00:00'},
                            'saturday': {'open': '10:00', 'close': '00:00'},
                            'sunday': {'open': '10:00', 'close': '22:00'},
                        },
                        'latitude': -6.8180,
                        'longitude': 39.2812
                    },
                    {
                        'name': 'Kinondoni',
                        'address': 'Kinondoni, Morogoro Road, Opposite MWEMBE Stadium',
                        'city': 'Kinondoni',
                        'is_main': False,
                        'hours': {
                            'monday': {'open': '11:00', 'close': '22:30'},
                            'tuesday': {'open': '11:00', 'close': '22:30'},
                            'wednesday': {'open': '11:00', 'close': '22:30'},
                            'thursday': {'open': '11:00', 'close': '22:30'},
                            'friday': {'open': '11:00', 'close': '23:30'},
                            'saturday': {'open': '11:00', 'close': '23:30'},
                            'sunday': {'open': '11:00', 'close': '22:00'},
                        },
                        'latitude': -6.7912,
                        'longitude': 39.2678
                    }
                ]
            },
            {
                'name': 'Mikocheni Sushi Bar',
                'owner_idx': 5,
                'cuisines': ['Japanese', 'Seafood'],
                'desc': 'Premium sushi and Japanese delicacies in Dar es Salaam. Omakase experience available for connoisseurs.',
                'story': 'Master sushi chefs from Tokyo bring authentic Japanese cuisine to Tanzania. Our fish is flown in twice weekly from Japan and sourced locally from Zanzibar.',
                'phone': '0712345006',
                'email': 'sushi@mikocheni.co.tz',
                'website': 'https://mikochenisushi.com',
                'amenities': ['Sushi Bar', 'Private Dining', 'Sake Selection', 'Free WiFi', 'Air Conditioning'],
                'gallery_images': ['https://images.unsplash.com/photo-1579871494447-9811cf80d66c'],
                'is_featured': True,
                'reservation_enabled': True,
                'branches': [
                    {
                        'name': 'Mikocheni B',
                        'address': 'Mikocheni B, Chole Road, Next to Quality Center',
                        'city': 'Mikocheni',
                        'is_main': True,
                        'hours': {
                            'monday': {'open': '12:00', 'close': '22:30'},
                            'tuesday': {'open': '12:00', 'close': '22:30'},
                            'wednesday': {'open': '12:00', 'close': '22:30'},
                            'thursday': {'open': '12:00', 'close': '22:30'},
                            'friday': {'open': '12:00', 'close': '23:30'},
                            'saturday': {'open': '12:00', 'close': '23:30'},
                            'sunday': {'open': '12:00', 'close': '21:30'},
                        },
                        'latitude': -6.7698,
                        'longitude': 39.2708
                    }
                ]
            },
            {
                'name': 'Tanzania Coffee House',
                'owner_idx': 6,
                'cuisines': ['Coffee & Tea', 'Bakery', 'Fast Food'],
                'desc': 'Premium Tanzanian coffee and fresh pastries. We roast our own beans from Kilimanjaro and Mbeya regions.',
                'story': 'Directly sourcing beans from Kilimanjaro coffee farmers since 2012. Our mission is to bring the best Tanzanian coffee to the world.',
                'phone': '0712345007',
                'email': 'coffee@tanzhouse.com',
                'website': 'https://tanzaniacoffeehouse.com',
                'amenities': ['Coffee Roastery', 'Free WiFi', 'Work-Friendly', 'Outdoor Seating', 'Pastry Shop', 'Takeaway'],
                'gallery_images': ['https://images.unsplash.com/photo-1442512595331-e89e73853f31'],
                'is_featured': True,
                'reservation_enabled': False,
                'branches': [
                    {
                        'name': 'Upanga',
                        'address': 'Upanga, Samora Avenue, Near PPF Tower',
                        'city': 'Upanga',
                        'is_main': True,
                        'hours': {
                            'monday': {'open': '07:00', 'close': '21:00'},
                            'tuesday': {'open': '07:00', 'close': '21:00'},
                            'wednesday': {'open': '07:00', 'close': '21:00'},
                            'thursday': {'open': '07:00', 'close': '21:00'},
                            'friday': {'open': '07:00', 'close': '22:00'},
                            'saturday': {'open': '08:00', 'close': '22:00'},
                            'sunday': {'open': '08:00', 'close': '20:00'},
                        },
                        'latitude': -6.8125,
                        'longitude': 39.2881
                    },
                    {
                        'name': 'Posta',
                        'address': 'Posta, Ghana Avenue, Opposite Post Office',
                        'city': 'Posta',
                        'is_main': False,
                        'hours': {
                            'monday': {'open': '07:30', 'close': '20:00'},
                            'tuesday': {'open': '07:30', 'close': '20:00'},
                            'wednesday': {'open': '07:30', 'close': '20:00'},
                            'thursday': {'open': '07:30', 'close': '20:00'},
                            'friday': {'open': '07:30', 'close': '21:00'},
                            'saturday': {'open': '08:30', 'close': '21:00'},
                            'sunday': {'open': '09:00', 'close': '19:00'},
                        },
                        'latitude': -6.8064,
                        'longitude': 39.2841
                    },
                    {
                        'name': 'Mbezi Beach',
                        'address': 'Mbezi Beach, Bagamoyo Road, Near Mlimani City',
                        'city': 'Mbezi Beach',
                        'is_main': False,
                        'hours': {
                            'monday': {'open': '08:00', 'close': '21:00'},
                            'tuesday': {'open': '08:00', 'close': '21:00'},
                            'wednesday': {'open': '08:00', 'close': '21:00'},
                            'thursday': {'open': '08:00', 'close': '21:00'},
                            'friday': {'open': '08:00', 'close': '22:00'},
                            'saturday': {'open': '09:00', 'close': '22:00'},
                            'sunday': {'open': '09:00', 'close': '20:00'},
                        },
                        'latitude': -6.7431,
                        'longitude': 39.2180
                    }
                ]
            },
            {
                'name': 'Spice Route Zanzibar',
                'owner_idx': 7,
                'cuisines': ['African Fusion', 'Seafood'],
                'desc': 'Experience the authentic flavors of Zanzibar in Dar. Traditional Zanzibari recipes with a modern twist.',
                'story': 'Our family has been cooking Zanzibari cuisine for over 50 years. We bring the spices and recipes from Stone Town to Dar es Salaam.',
                'phone': '0712345008',
                'email': 'info@spiceroute.co.tz',
                'website': 'https://spiceroutezanzibar.com',
                'amenities': ['Rooftop Seating', 'Shisha Lounge', 'Live Music', 'Full Bar', 'Private Events'],
                'gallery_images': ['https://images.unsplash.com/photo-1517248135467-4c7edcad34c4'],
                'is_featured': True,
                'reservation_enabled': True,
                'branches': [
                    {
                        'name': 'Mbagala',
                        'address': 'Mbagala, Kilwa Road, Near Mbagala Market',
                        'city': 'Mbagala',
                        'is_main': True,
                        'hours': {
                            'monday': {'open': '12:00', 'close': '23:00'},
                            'tuesday': {'open': '12:00', 'close': '23:00'},
                            'wednesday': {'open': '12:00', 'close': '23:00'},
                            'thursday': {'open': '12:00', 'close': '23:00'},
                            'friday': {'open': '12:00', 'close': '01:00'},
                            'saturday': {'open': '12:00', 'close': '01:00'},
                            'sunday': {'open': '12:00', 'close': '22:30'},
                        },
                        'latitude': -6.8863,
                        'longitude': 39.2765
                    },
                    {
                        'name': 'Kigamboni',
                        'address': 'Kigamboni, Ferry Terminal Second Floor',
                        'city': 'Kigamboni',
                        'is_main': False,
                        'hours': {
                            'monday': {'open': '12:00', 'close': '23:00'},
                            'tuesday': {'open': '12:00', 'close': '23:00'},
                            'wednesday': {'open': '12:00', 'close': '23:00'},
                            'thursday': {'open': '12:00', 'close': '23:00'},
                            'friday': {'open': '12:00', 'close': '00:00'},
                            'saturday': {'open': '12:00', 'close': '00:00'},
                            'sunday': {'open': '12:00', 'close': '22:00'},
                        },
                        'latitude': -6.8175,
                        'longitude': 39.2947
                    }
                ]
            },
            
            # ========== MORE DAR ES SALAAM RESTAURANTS ==========
            {
                'name': 'Msasani Bay Bistro',
                'owner_idx': 1,
                'cuisines': ['Mediterranean', 'European', 'Seafood'],
                'desc': 'Chic bistro serving Mediterranean-European fusion with stunning ocean views. Perfect for date nights.',
                'story': 'French-trained chef brings European elegance to Msasani Bay. Opened in 2019, quickly became a favorite for special occasions.',
                'phone': '0712345011',
                'email': 'dine@msasanibay.com',
                'website': 'https://msasanibaybistro.com',
                'amenities': ['Ocean View', 'Fine Dining', 'Wine Cellar', 'Valet Parking', 'Private Dining', 'Air Conditioning'],
                'gallery_images': ['https://images.unsplash.com/photo-1414235077428-338989a2e8c0'],
                'is_featured': True,
                'reservation_enabled': True,
                'min_party_size': 2,
                'max_party_size': 12,
                'branches': [
                    {
                        'name': 'Msasani Bay',
                        'address': 'Msasani Bay, Olympio Street, Waterfront',
                        'city': 'Msasani',
                        'is_main': True,
                        'hours': {
                            'monday': {'open': '12:00', 'close': '22:30'},
                            'tuesday': {'open': '12:00', 'close': '22:30'},
                            'wednesday': {'open': '12:00', 'close': '22:30'},
                            'thursday': {'open': '12:00', 'close': '22:30'},
                            'friday': {'open': '12:00', 'close': '23:30'},
                            'saturday': {'open': '11:00', 'close': '23:30'},
                            'sunday': {'open': '11:00', 'close': '22:00'},
                        },
                        'latitude': -6.7483,
                        'longitude': 39.2875
                    }
                ]
            },
            {
                'name': 'Kawe Street Food Market',
                'owner_idx': 8,
                'cuisines': ['Fast Food', 'Tanzanian/Swahili', 'Asian Fusion'],
                'desc': 'Vibrant food market with 10 different vendors under one roof. Something for everyone!',
                'story': 'Born from the idea of bringing together Dar\'s best street food vendors in one clean, modern space. Opened 2021.',
                'phone': '0712345012',
                'email': 'info@kawefoodmarket.com',
                'website': 'https://kawefoodmarket.com',
                'amenities': ['Food Court', 'Family Friendly', 'Free WiFi', 'Kids Play Area', 'Parking', 'Halal Certified'],
                'gallery_images': ['https://images.unsplash.com/photo-1522337094846-8a1b2d78dde5'],
                'is_featured': False,
                'reservation_enabled': False,
                'branches': [
                    {
                        'name': 'Kawe',
                        'address': 'Kawe, Mwai Kibaki Road, Next to Quality Center Mall',
                        'city': 'Kawe',
                        'is_main': True,
                        'hours': {
                            'monday': {'open': '11:00', 'close': '22:00'},
                            'tuesday': {'open': '11:00', 'close': '22:00'},
                            'wednesday': {'open': '11:00', 'close': '22:00'},
                            'thursday': {'open': '11:00', 'close': '22:00'},
                            'friday': {'open': '11:00', 'close': '23:00'},
                            'saturday': {'open': '10:00', 'close': '23:00'},
                            'sunday': {'open': '10:00', 'close': '21:00'},
                        },
                        'latitude': -6.7542,
                        'longitude': 39.2345
                    }
                ]
            },
            {
                'name': 'Temeke Tandoori House',
                'owner_idx': 9,
                'cuisines': ['Indian', 'Pakistani', 'BBQ'],
                'desc': 'Authentic tandoori and BBQ from the subcontinent. Famous for our seekh kebabs and butter naan.',
                'story': 'Family-run since 2005, serving the South Dar community with love and authentic recipes from Lahore.',
                'phone': '0712345013',
                'email': 'tandoori@temeke.com',
                'website': '',
                'amenities': ['Family Seating', 'Takeaway', 'Delivery', 'Parking', 'Halal Certified'],
                'gallery_images': [],
                'is_featured': False,
                'reservation_enabled': False,
                'branches': [
                    {
                        'name': 'Temeke Main',
                        'address': 'Temeke, Chang\'ombe Road, Near Temeke Market',
                        'city': 'Temeke',
                        'is_main': True,
                        'hours': {
                            'monday': {'open': '12:00', 'close': '23:00'},
                            'tuesday': {'open': '12:00', 'close': '23:00'},
                            'wednesday': {'open': '12:00', 'close': '23:00'},
                            'thursday': {'open': '12:00', 'close': '23:00'},
                            'friday': {'open': '12:00', 'close': '00:00'},
                            'saturday': {'open': '12:00', 'close': '00:00'},
                            'sunday': {'open': '12:00', 'close': '22:30'},
                        },
                        'latitude': -6.8863,
                        'longitude': 39.2965
                    }
                ]
            },
            {
                'name': 'Mbezi Beach Pizza Club',
                'owner_idx': 4,
                'cuisines': ['Italian', 'Fast Food'],
                'desc': 'Casual pizza joint with beach views. Perfect for families and groups.',
                'story': 'Two Italian-Tanzanian friends combined their love for pizza and the beach to create this local favorite.',
                'phone': '0712345014',
                'email': 'pizza@mbezibeach.com',
                'website': 'https://mbezibeachpizza.com',
                'amenities': ['Beach Access', 'Kids Menu', 'Outdoor Seating', 'Free WiFi', 'Parking', 'Takeaway'],
                'gallery_images': ['https://images.unsplash.com/photo-1513104890138-7c749659a591'],
                'is_featured': True,
                'reservation_enabled': False,
                'branches': [
                    {
                        'name': 'Mbezi Beach',
                        'address': 'Mbezi Beach, Along Beach Road',
                        'city': 'Mbezi Beach',
                        'is_main': True,
                        'hours': {
                            'monday': {'open': '12:00', 'close': '22:00'},
                            'tuesday': {'open': '12:00', 'close': '22:00'},
                            'wednesday': {'open': '12:00', 'close': '22:00'},
                            'thursday': {'open': '12:00', 'close': '22:00'},
                            'friday': {'open': '12:00', 'close': '23:00'},
                            'saturday': {'open': '11:00', 'close': '23:00'},
                            'sunday': {'open': '11:00', 'close': '21:30'},
                        },
                        'latitude': -6.7412,
                        'longitude': 39.2134
                    }
                ]
            },
            
            # ========== OTHER TANZANIAN REGIONS ==========
            {
                'name': 'Kilimanjaro Cafe & Grill',
                'owner_idx': 0,
                'cuisines': ['Tanzanian/Swahili', 'BBQ'],
                'desc': 'Traditional Tanzanian cuisine with a view of Mount Kilimanjaro. Our nyama choma is legendary.',
                'story': 'Serving authentic local dishes since 1998. Founded by a family of Maasai warriors who turned their love for grilling into Arusha\'s most famous restaurant.',
                'phone': '0712345009',
                'email': 'kili@arushacafe.com',
                'website': 'https://kilimanjarocafe.com',
                'amenities': ['Mountain View', 'Outdoor Seating', 'Live Traditional Music', 'Parking', 'Family Friendly', 'Gift Shop'],
                'gallery_images': ['https://images.unsplash.com/photo-1544148103-0773bf10d330'],
                'is_featured': True,
                'reservation_enabled': True,
                'branches': [
                    {
                        'name': 'Arusha Main',
                        'address': 'Sokoine Road, Arusha, Near Clock Tower',
                        'city': 'Arusha',
                        'country': 'Tanzania',
                        'is_main': True,
                        'hours': {
                            'monday': {'open': '08:00', 'close': '23:00'},
                            'tuesday': {'open': '08:00', 'close': '23:00'},
                            'wednesday': {'open': '08:00', 'close': '23:00'},
                            'thursday': {'open': '08:00', 'close': '23:00'},
                            'friday': {'open': '08:00', 'close': '00:00'},
                            'saturday': {'open': '08:00', 'close': '00:00'},
                            'sunday': {'open': '08:00', 'close': '22:00'},
                        },
                        'latitude': -3.3667,
                        'longitude': 36.6833
                    },
                    {
                        'name': 'Moshi Branch',
                        'address': 'Moshi, Moshi-Arusha Highway, Near TFA',
                        'city': 'Moshi',
                        'country': 'Tanzania',
                        'is_main': False,
                        'hours': {
                            'monday': {'open': '09:00', 'close': '22:00'},
                            'tuesday': {'open': '09:00', 'close': '22:00'},
                            'wednesday': {'open': '09:00', 'close': '22:00'},
                            'thursday': {'open': '09:00', 'close': '22:00'},
                            'friday': {'open': '09:00', 'close': '23:00'},
                            'saturday': {'open': '09:00', 'close': '23:00'},
                            'sunday': {'open': '09:00', 'close': '21:00'},
                        },
                        'latitude': -3.3348,
                        'longitude': 37.3403
                    }
                ]
            },
            {
                'name': 'Mwanza Fish Market Restaurant',
                'owner_idx': 1,
                'cuisines': ['Seafood', 'Tanzanian/Swahili'],
                'desc': 'Fresh Nile perch and tilapia from Lake Victoria. Dine on the floating deck!',
                'story': 'Directly sourcing fish from local fishermen daily since 2005. Our location on the lake offers the freshest catch possible.',
                'phone': '0712345010',
                'email': 'fish@mwanza.com',
                'website': '',
                'amenities': ['Lake View', 'Floating Deck', 'Fresh Fish Market', 'Parking', 'Family Friendly'],
                'gallery_images': ['https://images.unsplash.com/photo-1559847844-5315695dadae'],
                'is_featured': False,
                'reservation_enabled': False,
                'branches': [
                    {
                        'name': 'Capri Point',
                        'address': 'Capri Point, Mwanza, Lake Victoria Shore',
                        'city': 'Mwanza',
                        'country': 'Tanzania',
                        'is_main': True,
                        'hours': {
                            'monday': {'open': '10:00', 'close': '22:00'},
                            'tuesday': {'open': '10:00', 'close': '22:00'},
                            'wednesday': {'open': '10:00', 'close': '22:00'},
                            'thursday': {'open': '10:00', 'close': '22:00'},
                            'friday': {'open': '10:00', 'close': '23:00'},
                            'saturday': {'open': '10:00', 'close': '23:00'},
                            'sunday': {'open': '10:00', 'close': '21:00'},
                        },
                        'latitude': -2.5167,
                        'longitude': 32.9000
                    }
                ]
            },
            {
                'name': 'Dodoma Grill & Lounge',
                'owner_idx': 2,
                'cuisines': ['BBQ', 'American', 'Fast Food'],
                'desc': 'Modern grill restaurant in Tanzania\'s capital city. Popular with government officials and families.',
                'story': 'Established in 2018 to bring international grill standards to Dodoma. Now a favorite spot for dinner and drinks.',
                'phone': '0712345016',
                'email': 'info@dodomagrill.com',
                'website': 'https://dodomagrill.com',
                'amenities': ['Air Conditioning', 'Sports TV', 'Full Bar', 'Free WiFi', 'Parking', 'Private Rooms'],
                'gallery_images': [],
                'is_featured': False,
                'reservation_enabled': True,
                'branches': [
                    {
                        'name': 'Dodoma Central',
                        'address': 'Dodoma, Jamhuri Street, Near Parliament',
                        'city': 'Dodoma',
                        'country': 'Tanzania',
                        'is_main': True,
                        'hours': {
                            'monday': {'open': '11:00', 'close': '23:00'},
                            'tuesday': {'open': '11:00', 'close': '23:00'},
                            'wednesday': {'open': '11:00', 'close': '23:00'},
                            'thursday': {'open': '11:00', 'close': '23:00'},
                            'friday': {'open': '11:00', 'close': '01:00'},
                            'saturday': {'open': '11:00', 'close': '01:00'},
                            'sunday': {'open': '12:00', 'close': '22:00'},
                        },
                        'latitude': -6.1630,
                        'longitude': 35.7516
                    }
                ]
            },
            {
                'name': 'Zanzibar Rock Restaurant',
                'owner_idx': 3,
                'cuisines': ['Seafood', 'Mediterranean', 'African Fusion'],
                'desc': 'Famous restaurant built on a rock in the Indian Ocean. Only accessible during low tide!',
                'story': 'One of the most photographed restaurants in the world. Built in 2012 on a traditional fishermen\'s rock, now a Zanzibar landmark.',
                'phone': '+255777123456',
                'email': 'reservations@therockzanzibar.com',
                'website': 'https://therockzanzibar.com',
                'amenities': ['Ocean Access', 'Instagram Spot', 'Private Dining', 'Sunset Views', 'Boat Transfers'],
                'gallery_images': ['https://images.unsplash.com/photo-1570211776045-af3a51026f4a'],
                'is_featured': True,
                'reservation_enabled': True,
                'min_party_size': 2,
                'max_party_size': 8,
                'reservation_lead_time_hours': 24,
                'branches': [
                    {
                        'name': 'Michamvi Beach',
                        'address': 'Michamvi Beach, South East Coast, Zanzibar',
                        'city': 'Zanzibar',
                        'country': 'Tanzania',
                        'is_main': True,
                        'hours': {
                            'monday': {'open': '12:00', 'close': '21:00'},
                            'tuesday': {'open': '12:00', 'close': '21:00'},
                            'wednesday': {'open': '12:00', 'close': '21:00'},
                            'thursday': {'open': '12:00', 'close': '21:00'},
                            'friday': {'open': '12:00', 'close': '22:00'},
                            'saturday': {'open': '12:00', 'close': '22:00'},
                            'sunday': {'open': '12:00', 'close': '21:00'},
                        },
                        'latitude': -6.2312,
                        'longitude': 39.5512
                    }
                ]
            },
            
            # ========== INTERNATIONAL LOCATIONS ==========
            {
                'name': 'Serengeti Grill - Nairobi',
                'owner_idx': 2,
                'cuisines': ['African Fusion', 'BBQ'],
                'desc': 'Bringing Tanzanian flavors to Nairobi. Experience East African BBQ in Kenya\'s capital.',
                'story': 'Cross-border culinary experience celebrating the best of East African cuisine. Our chef won "Best BBQ in East Africa" 2022.',
                'phone': '+254712345678',
                'email': 'nairobi@serengetigrill.com',
                'website': 'https://serengetigrill.co.ke',
                'amenities': ['Outdoor Seating', 'Full Bar', 'Live Music Fri/Sat', 'Parking', 'Family Friendly'],
                'gallery_images': ['https://images.unsplash.com/photo-1555939594-58d7cb561ad1'],
                'is_featured': True,
                'reservation_enabled': True,
                'branches': [
                    {
                        'name': 'Westlands',
                        'address': 'Westlands, Waiyaki Way, Nairobi',
                        'city': 'Nairobi',
                        'country': 'Kenya',
                        'is_main': True,
                        'hours': {
                            'monday': {'open': '12:00', 'close': '23:00'},
                            'tuesday': {'open': '12:00', 'close': '23:00'},
                            'wednesday': {'open': '12:00', 'close': '23:00'},
                            'thursday': {'open': '12:00', 'close': '23:00'},
                            'friday': {'open': '12:00', 'close': '01:00'},
                            'saturday': {'open': '12:00', 'close': '01:00'},
                            'sunday': {'open': '12:00', 'close': '22:00'},
                        },
                        'latitude': -1.2667,
                        'longitude': 36.8000
                    }
                ]
            },
            {
                'name': 'Zanzibar Delights - London',
                'owner_idx': 3,
                'cuisines': ['Tanzanian/Swahili', 'Seafood'],
                'desc': 'Authentic Zanzibari cuisine in the heart of London. Taste of Stone Town in UK.',
                'story': 'Family recipes from Stone Town now in the UK. Founded by a Zanzibari-British family keeping their heritage alive through food.',
                'phone': '+442079460123',
                'email': 'london@zanzibardelights.com',
                'website': 'https://zanzibardelights.co.uk',
                'amenities': ['Halal Certified', 'Takeaway', 'Delivery', 'Private Dining', 'Wheelchair Access'],
                'gallery_images': ['https://images.unsplash.com/photo-1517248135467-4c7edcad34c4'],
                'is_featured': True,
                'reservation_enabled': True,
                'branches': [
                    {
                        'name': 'Edgware Road',
                        'address': 'Edgware Road, London, W2 1EA',
                        'city': 'London',
                        'country': 'United Kingdom',
                        'is_main': True,
                        'hours': {
                            'monday': {'open': '12:00', 'close': '22:30'},
                            'tuesday': {'open': '12:00', 'close': '22:30'},
                            'wednesday': {'open': '12:00', 'close': '22:30'},
                            'thursday': {'open': '12:00', 'close': '22:30'},
                            'friday': {'open': '12:00', 'close': '23:30'},
                            'saturday': {'open': '12:00', 'close': '23:30'},
                            'sunday': {'open': '12:00', 'close': '21:30'},
                        },
                        'latitude': 51.5195,
                        'longitude': -0.1674
                    }
                ]
            },
            {
                'name': 'Kilimanjaro Eatery - NYC',
                'owner_idx': 4,
                'cuisines': ['East African', 'Vegetarian', 'Vegan'],
                'desc': 'Plant-based East African cuisine in New York. Vegan-friendly traditional dishes from Tanzania.',
                'story': 'Vegan-friendly traditional dishes from Tanzania, adapted for modern plant-based diets.',
                'phone': '+12125551234',
                'email': 'nyc@kilieatery.com',
                'website': 'https://kilieatery.com',
                'amenities': ['Vegan Options', 'Gluten Free Options', 'Takeaway', 'Delivery', 'Free WiFi'],
                'gallery_images': ['https://images.unsplash.com/photo-1544148103-0773bf10d330'],
                'is_featured': False,
                'reservation_enabled': True,
                'branches': [
                    {
                        'name': 'East Village',
                        'address': 'East Village, Manhattan, NYC, NY 10003',
                        'city': 'New York',
                        'country': 'USA',
                        'is_main': True,
                        'hours': {
                            'monday': {'open': '11:00', 'close': '22:00'},
                            'tuesday': {'open': '11:00', 'close': '22:00'},
                            'wednesday': {'open': '11:00', 'close': '22:00'},
                            'thursday': {'open': '11:00', 'close': '22:00'},
                            'friday': {'open': '11:00', 'close': '23:00'},
                            'saturday': {'open': '10:00', 'close': '23:00'},
                            'sunday': {'open': '10:00', 'close': '21:00'},
                        },
                        'latitude': 40.7262,
                        'longitude': -73.9838
                    }
                ]
            },
            {
                'name': 'Safari Bites - Johannesburg',
                'owner_idx': 5,
                'cuisines': ['BBQ', 'Fast Food', 'African Fusion'],
                'desc': 'Quick-service African street food in Joburg. Inspired by Dar es Salaam street food culture.',
                'story': 'Inspired by Dar es Salaam street food culture. Bringing the taste of East African street food to South Africa.',
                'phone': '+27111234567',
                'email': 'joburg@safaribites.com',
                'website': 'https://safaribites.co.za',
                'amenities': ['Fast Service', 'Takeaway', 'Delivery', 'Drive Thru', 'Outdoor Seating'],
                'gallery_images': [],
                'is_featured': False,
                'reservation_enabled': False,
                'branches': [
                    {
                        'name': 'Sandton City',
                        'address': 'Sandton City, Johannesburg, 2196',
                        'city': 'Johannesburg',
                        'country': 'South Africa',
                        'is_main': True,
                        'hours': {
                            'monday': {'open': '10:00', 'close': '21:00'},
                            'tuesday': {'open': '10:00', 'close': '21:00'},
                            'wednesday': {'open': '10:00', 'close': '21:00'},
                            'thursday': {'open': '10:00', 'close': '21:00'},
                            'friday': {'open': '10:00', 'close': '22:00'},
                            'saturday': {'open': '10:00', 'close': '22:00'},
                            'sunday': {'open': '10:00', 'close': '20:00'},
                        },
                        'latitude': -26.1076,
                        'longitude': 28.0567
                    }
                ]
            },
            {
                'name': 'Lagos Spice Market',
                'owner_idx': 6,
                'cuisines': ['West African', 'Indian Fusion'],
                'desc': 'Fusion of Nigerian and Tanzanian flavors. East meets West Africa on a plate.',
                'story': 'Bringing East African spices to West Africa. A culinary bridge between two vibrant food cultures.',
                'phone': '+2348123456789',
                'email': 'lagos@spicemarket.com',
                'website': '',
                'amenities': ['Live Music', 'Full Bar', 'Private Events', 'Parking', 'Security'],
                'gallery_images': [],
                'is_featured': False,
                'reservation_enabled': True,
                'branches': [
                    {
                        'name': 'Victoria Island',
                        'address': 'Victoria Island, Lagos, Nigeria',
                        'city': 'Lagos',
                        'country': 'Nigeria',
                        'is_main': True,
                        'hours': {
                            'monday': {'open': '12:00', 'close': '23:00'},
                            'tuesday': {'open': '12:00', 'close': '23:00'},
                            'wednesday': {'open': '12:00', 'close': '23:00'},
                            'thursday': {'open': '12:00', 'close': '23:00'},
                            'friday': {'open': '12:00', 'close': '02:00'},
                            'saturday': {'open': '12:00', 'close': '02:00'},
                            'sunday': {'open': '12:00', 'close': '22:00'},
                        },
                        'latitude': 6.4281,
                        'longitude': 3.4219
                    }
                ]
            }
        ]
        
        # ============================================================
        # CREATE ALL RESTAURANTS AND BRANCHES
        # ============================================================
        
        restaurant_count = 0
        branch_count = 0
        
        for data in restaurants_data:
            owner = owners[data['owner_idx'] % len(owners)]
            
            # Create restaurant with all details
            restaurant = Restaurant.objects.create(
                owner=owner,
                name=data['name'],
                description=data['desc'],
                story_description=data['story'],
                phone_number=data['phone'],
                email=data['email'],
                website=data.get('website', ''),
                amenities=data['amenities'],
                gallery_images=data.get('gallery_images', []),
                status='active',
                is_verified=True,
                is_featured=data.get('is_featured', False),
                reservation_enabled=data.get('reservation_enabled', False),
                min_party_size=data.get('min_party_size', 1),
                max_party_size=data.get('max_party_size', 20),
                reservation_lead_time_hours=data.get('reservation_lead_time_hours', 2),
                reservation_max_days_ahead=data.get('reservation_max_days_ahead', 30),
                overall_rating=Decimal(str(round(random.uniform(3.5, 4.9), 1))),
                total_reviews=random.randint(20, 500)
            )
            
            # Add cuisines
            for cuisine_name in data['cuisines']:
                cuisine = next((c for c in cuisines if c.name == cuisine_name), None)
                if cuisine:
                    restaurant.cuisines.add(cuisine)
            
            # Create branches
            for branch_data in data['branches']:
                address = Address.objects.create(
                    street_address=branch_data['address'],
                    city=branch_data['city'],
                    country=branch_data.get('country', 'Tanzania'),
                    postal_code=random.choice(['11101', '11102', '11103', '']),
                    latitude=branch_data.get('latitude', random.uniform(-6.9, -6.7)),
                    longitude=branch_data.get('longitude', random.uniform(39.1, 39.3))
                )
                
                Branch.objects.create(
                    restaurant=restaurant,
                    name=branch_data.get('name', f"{restaurant.name} - {branch_data['city']}"),
                    address=address,
                    phone_number=restaurant.phone_number,
                    operating_hours=branch_data['hours'],
                    is_active=True,
                    is_main_branch=branch_data.get('is_main', False)
                )
                branch_count += 1
            
            # Create loyalty settings
            RestaurantLoyaltySettings.objects.create(
                restaurant=restaurant,
                program=loyalty_program,
                is_loyalty_enabled=random.choice([True, True, True, False]),  # 75% enabled
                custom_points_per_dollar=random.choice([None, Decimal('1.00'), Decimal('1.50'), Decimal('2.00')]),
                minimum_order_amount_for_points=Decimal(random.choice([0, 10, 15, 20])),
                points_expiry_days=365,
                allow_point_redemption=True
            )
            
            restaurant_count += 1
            
            if restaurant_count % 5 == 0:
                self.stdout.write(f"  Created {restaurant_count} restaurants, {branch_count} branches")
        
        # Generate performance metrics for all restaurants (signal should handle this)
        self.stdout.write(f"  ✅ Created {restaurant_count} restaurants with {branch_count} branches total")
        self.stdout.write("  📍 Focus areas: Kigamboni, Kibada, and all major Dar es Salaam districts")
        self.stdout.write("  🌍 Also created branches in Arusha, Mwanza, Zanzibar, and international locations")