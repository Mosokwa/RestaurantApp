# management/commands/create_restaurants_and_branches.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from api.models.restaurant_models import Restaurant, Branch, Address
from api.models.menu_models import Cuisine
import random
from decimal import Decimal

User = get_user_model()

class Command(BaseCommand):
    help = 'Create restaurants and branches in Dar es Salaam'
    
    def handle(self, *args, **options):
        owners = User.objects.filter(user_type='owner')
        cuisines = Cuisine.objects.all()
        
        restaurants_data = [
            # Kigamboni/Kibada Area Restaurants (20 restaurants)
            {'name': 'Kibada Beach Grill', 'description': 'Fresh seafood and nyama choma with ocean view', 'story': 'Family-owned beachside restaurant since 1995', 'neighborhood': 'Kibada, Kigamboni', 'cuisines': ['Seafood', 'Nyama Choma', 'Swahili'], 'phone': '+255757111111', 'email': 'kibadabeach@example.com', 'lat': -6.8300, 'lng': 39.3100},
            {'name': 'Mama Ntilie Restaurant', 'description': 'Authentic Swahili home cooking', 'story': 'Mama Ntilie\'s secret recipes passed through generations', 'neighborhood': 'Kigamboni', 'cuisines': ['Swahili', 'Ugali & Fish', 'Pilau'], 'phone': '+255757111112', 'email': 'mamantilie@example.com', 'lat': -6.8320, 'lng': 39.3050},
            {'name': 'Kigamboni Pizza House', 'description': 'Wood-fired pizzas and Italian dishes', 'story': 'Italian-Tanzanian fusion since 2010', 'neighborhood': 'Kigamboni', 'cuisines': ['Italian', 'Fast Food'], 'phone': '+255757111113', 'email': 'kigambonipizza@example.com', 'lat': -6.8280, 'lng': 39.3080},
            {'name': 'Bahari View Restaurant', 'description': 'Fine dining with Indian Ocean view', 'story': 'Luxury dining experience in Kigamboni', 'neighborhood': 'Kibada, Kigamboni', 'cuisines': ['Swahili', 'Seafood', 'International'], 'phone': '+255757111114', 'email': 'bahariview@example.com', 'lat': -6.8310, 'lng': 39.3120},
            {'name': 'Chicken Inn Kigamboni', 'description': 'Fast food chicken and burgers', 'story': 'Popular fast food chain in Kigamboni', 'neighborhood': 'Kigamboni', 'cuisines': ['Fast Food', 'American'], 'phone': '+255757111115', 'email': 'chickeninn@example.com', 'lat': -6.8290, 'lng': 39.3030},
            {'name': 'Mishkaki Palace', 'description': 'Specializing in Tanzanian mishkaki', 'story': 'Best mishkaki in Kigamboni since 2005', 'neighborhood': 'Kigamboni', 'cuisines': ['Nyama Choma', 'Mishkaki'], 'phone': '+255757111116', 'email': 'mishkakipalace@example.com', 'lat': -6.8270, 'lng': 39.3060},
            {'name': 'Kibada Fresh Fish', 'description': 'Daily caught fish prepared traditional way', 'story': 'Local fishermen supply fresh catch daily', 'neighborhood': 'Kibada, Kigamboni', 'cuisines': ['Seafood', 'Ugali & Fish'], 'phone': '+255757111117', 'email': 'kibadafish@example.com', 'lat': -6.8330, 'lng': 39.3090},
            {'name': 'Kigamboni Coffee House', 'description': 'Coffee, breakfast and light meals', 'story': 'Cozy coffee shop with local beans', 'neighborhood': 'Kigamboni', 'cuisines': ['Breakfast', 'Beverages'], 'phone': '+255757111118', 'email': 'kigambonicoffee@example.com', 'lat': -6.8260, 'lng': 39.3040},
            {'name': 'Spice Island Restaurant', 'description': 'Zanzibari and Swahili fusion cuisine', 'story': 'Bringing Zanzibar flavors to Dar es Salaam', 'neighborhood': 'Kigamboni', 'cuisines': ['Swahili', 'Seafood'], 'phone': '+255757111119', 'email': 'spiceisland@example.com', 'lat': -6.8305, 'lng': 39.3070},
            {'name': 'Burger Joint Kigamboni', 'description': 'Gourmet burgers and craft beer', 'story': 'American-style burger restaurant', 'neighborhood': 'Kigamboni', 'cuisines': ['American', 'Fast Food'], 'phone': '+255757111120', 'email': 'burgerjoint@example.com', 'lat': -6.8250, 'lng': 39.3020},
            {'name': 'Vegetarian Delight', 'description': '100% vegetarian and vegan options', 'story': 'Healthy eating in Kigamboni', 'neighborhood': 'Kigamboni', 'cuisines': ['Vegetarian'], 'phone': '+255757111121', 'email': 'vegetariandelight@example.com', 'lat': -6.8285, 'lng': 39.3055},
            {'name': 'China Garden', 'description': 'Authentic Chinese cuisine', 'story': 'Chinese family recipes since 2008', 'neighborhood': 'Kigamboni', 'cuisines': ['Chinese'], 'phone': '+255757111122', 'email': 'chinagarden@example.com', 'lat': -6.8275, 'lng': 39.3035},
            {'name': 'Pizza Villa', 'description': 'Italian pizzas and pasta', 'story': 'Traditional Italian recipes', 'neighborhood': 'Kibada, Kigamboni', 'cuisines': ['Italian'], 'phone': '+255757111123', 'email': 'pizzavilla@example.com', 'lat': -6.8325, 'lng': 39.3105},
            {'name': 'Seafood Paradise', 'description': 'All-you-can-eat seafood buffet', 'story': 'Seafood lovers destination', 'neighborhood': 'Kibada, Kigamboni', 'cuisines': ['Seafood'], 'phone': '+255757111124', 'email': 'seafoodparadise@example.com', 'lat': -6.8295, 'lng': 39.3115},
            {'name': 'Sweet Treats Bakery', 'description': 'Freshly baked goods and desserts', 'story': 'Artisanal bakery since 2012', 'neighborhood': 'Kigamboni', 'cuisines': ['Desserts'], 'phone': '+255757111125', 'email': 'sweettreats@example.com', 'lat': -6.8265, 'lng': 39.3015},
            {'name': 'Mkuki Cafe', 'description': 'Local snacks and beverages', 'story': 'Community cafe since 2015', 'neighborhood': 'Kigamboni', 'cuisines': ['Breakfast', 'Beverages'], 'phone': '+255757111126', 'email': 'mkukicafe@example.com', 'lat': -6.8315, 'lng': 39.3085},
            {'name': 'Kibada Grill House', 'description': 'Charcoal grilled meats and fish', 'story': 'Traditional Tanzanian grill', 'neighborhood': 'Kibada, Kigamboni', 'cuisines': ['Barbecue', 'Nyama Choma'], 'phone': '+255757111127', 'email': 'kibadagrill@example.com', 'lat': -6.8340, 'lng': 39.3130},
            {'name': 'Ocean Breeze Restaurant', 'description': 'Beachfront dining with fresh seafood', 'story': 'Ocean view restaurant since 2000', 'neighborhood': 'Kigamboni', 'cuisines': ['Seafood', 'Swahili'], 'phone': '+255757111128', 'email': 'oceanbreeze@example.com', 'lat': -6.8240, 'lng': 39.3135},
            {'name': 'Kibada Kitchen', 'description': 'Home-style Tanzanian cooking', 'story': 'Family recipes from local chefs', 'neighborhood': 'Kibada, Kigamboni', 'cuisines': ['Swahili', 'Pilau'], 'phone': '+255757111129', 'email': 'kibadakitchen@example.com', 'lat': -6.8350, 'lng': 39.3140},
            {'name': 'Green Garden Restaurant', 'description': 'Organic and healthy meals', 'story': 'Focus on organic ingredients', 'neighborhood': 'Kigamboni', 'cuisines': ['Vegetarian', 'Healthy'], 'phone': '+255757111130', 'email': 'greengarden@example.com', 'lat': -6.8235, 'lng': 39.3065},
            
            # Other Dar es Salaam Restaurants (30 restaurants)
            {'name': 'Serengeti Grill', 'description': 'Fine dining with Tanzanian game meat', 'story': 'Premium restaurant in Masaki', 'neighborhood': 'Masaki', 'cuisines': ['Nyama Choma', 'Swahili'], 'phone': '+255757111131', 'email': 'serengetigrill@example.com', 'lat': -6.7800, 'lng': 39.2700},
            {'name': 'Mikocheni Bistro', 'description': 'European style bistro', 'story': 'French-Tanzanian fusion', 'neighborhood': 'Mikocheni', 'cuisines': ['Italian', 'French'], 'phone': '+255757111132', 'email': 'mikochenibistro@example.com', 'lat': -6.7900, 'lng': 39.2500},
            {'name': 'Sinza Food Court', 'description': 'Multiple food vendors in one place', 'story': 'Popular food court since 2010', 'neighborhood': 'Sinza', 'cuisines': ['Fast Food', 'Various'], 'phone': '+255757111133', 'email': 'sinzafood@example.com', 'lat': -6.8100, 'lng': 39.2300},
            {'name': 'Kariakoo Market Eatery', 'description': 'Local street food and snacks', 'story': 'In the heart of Kariakoo market', 'neighborhood': 'Kariakoo', 'cuisines': ['Street Food', 'Swahili'], 'phone': '+255757111134', 'email': 'kariakoo@example.com', 'lat': -6.8200, 'lng': 39.2800},
            {'name': 'Oyster Bay Seafood', 'description': 'Luxury seafood restaurant', 'story': 'Fine dining seafood experience', 'neighborhood': 'Oyster Bay', 'cuisines': ['Seafood', 'International'], 'phone': '+255757111135', 'email': 'oysterbay@example.com', 'lat': -6.7700, 'lng': 39.2800},
            {'name': 'Ilala Diner', 'description': '24-hour diner and cafe', 'story': 'Open round the clock since 2005', 'neighborhood': 'Ilala', 'cuisines': ['American', 'Breakfast'], 'phone': '+255757111136', 'email': 'ilaladiner@example.com', 'lat': -6.8300, 'lng': 39.2900},
            {'name': 'Temeke Tavern', 'description': 'Local bar and restaurant', 'story': 'Popular spot for drinks and food', 'neighborhood': 'Temeke', 'cuisines': ['Nyama Choma', 'Barbecue'], 'phone': '+255757111137', 'email': 'temeketavern@example.com', 'lat': -6.8400, 'lng': 39.3100},
            {'name': 'Mbagala Kitchen', 'description': 'Traditional Tanzanian dishes', 'story': 'Family restaurant since 1998', 'neighborhood': 'Mbagala', 'cuisines': ['Swahili', 'Pilau'], 'phone': '+255757111138', 'email': 'mbagala@example.com', 'lat': -6.8600, 'lng': 39.3200},
            {'name': 'Ubungo Food Plaza', 'description': 'Food court with various options', 'story': 'Convenient location near bus station', 'neighborhood': 'Ubungo', 'cuisines': ['Fast Food', 'Various'], 'phone': '+255757111139', 'email': 'ubungofood@example.com', 'lat': -6.8000, 'lng': 39.2200},
            {'name': 'Posta Cafe', 'description': 'Coffee and light meals', 'story': 'Historic cafe in city center', 'neighborhood': 'Posta', 'cuisines': ['Breakfast', 'Beverages'], 'phone': '+255757111140', 'email': 'postacafe@example.com', 'lat': -6.8205, 'lng': 39.2905},
            {'name': 'Tabata Grill', 'description': 'Charcoal grilled meats', 'story': 'Popular grill spot since 2003', 'neighborhood': 'Tabata', 'cuisines': ['Nyama Choma', 'Barbecue'], 'phone': '+255757111141', 'email': 'tabatagrill@example.com', 'lat': -6.8150, 'lng': 39.2400},
            {'name': 'Buguruni Bites', 'description': 'Local snacks and street food', 'story': 'Community favorite spot', 'neighborhood': 'Buguruni', 'cuisines': ['Street Food', 'Swahili'], 'phone': '+255757111142', 'email': 'buguruni@example.com', 'lat': -6.8350, 'lng': 39.2750},
            {'name': 'Changombe Kitchen', 'description': 'Home-style cooking', 'story': 'Traditional family recipes', 'neighborhood': 'Changombe', 'cuisines': ['Swahili', 'Ugali & Fish'], 'phone': '+255757111143', 'email': 'changombe@example.com', 'lat': -6.8450, 'lng': 39.2850},
            {'name': 'Mbezi Beach Restaurant', 'description': 'Beachfront dining', 'story': 'Relaxed beach atmosphere', 'neighborhood': 'Mbezi', 'cuisines': ['Seafood', 'Barbecue'], 'phone': '+255757111144', 'email': 'mbezi@example.com', 'lat': -6.7500, 'lng': 39.2600},
            {'name': 'Masaki Mediterranean', 'description': 'Mediterranean cuisine', 'story': 'Authentic Mediterranean flavors', 'neighborhood': 'Masaki', 'cuisines': ['Mediterranean', 'Lebanese'], 'phone': '+255757111145', 'email': 'masakimed@example.com', 'lat': -6.7850, 'lng': 39.2750},
            {'name': 'Mikocheni Indian', 'description': 'Authentic Indian cuisine', 'story': 'Indian family recipes', 'neighborhood': 'Mikocheni', 'cuisines': ['Indian'], 'phone': '+255757111146', 'email': 'mikocheniindian@example.com', 'lat': -6.7950, 'lng': 39.2550},
            {'name': 'Sinza Chinese', 'description': 'Chinese restaurant', 'story': 'Authentic Chinese dishes', 'neighborhood': 'Sinza', 'cuisines': ['Chinese'], 'phone': '+255757111147', 'email': 'sinzachinese@example.com', 'lat': -6.8050, 'lng': 39.2350},
            {'name': 'Kariakoo Pizza', 'description': 'Pizza delivery and takeaway', 'story': 'Popular pizza spot', 'neighborhood': 'Kariakoo', 'cuisines': ['Italian', 'Fast Food'], 'phone': '+255757111148', 'email': 'kariakooppizza@example.com', 'lat': -6.8150, 'lng': 39.2850},
            {'name': 'Oyster Bay Japanese', 'description': 'Japanese sushi and ramen', 'story': 'Authentic Japanese cuisine', 'neighborhood': 'Oyster Bay', 'cuisines': ['Japanese'], 'phone': '+255757111149', 'email': 'oysterbayjapanese@example.com', 'lat': -6.7750, 'lng': 39.2850},
            {'name': 'Ilala Mexican', 'description': 'Mexican food and tacos', 'story': 'Mexican flavors in Dar', 'neighborhood': 'Ilala', 'cuisines': ['Mexican'], 'phone': '+255757111150', 'email': 'ilalamexican@example.com', 'lat': -6.8350, 'lng': 39.2950},
            {'name': 'Temeke Thai', 'description': 'Thai cuisine', 'story': 'Authentic Thai recipes', 'neighborhood': 'Temeke', 'cuisines': ['Thai'], 'phone': '+255757111151', 'email': 'temekethai@example.com', 'lat': -6.8450, 'lng': 39.3150},
            {'name': 'Mbagala Korean', 'description': 'Korean BBQ', 'story': 'Korean dining experience', 'neighborhood': 'Mbagala', 'cuisines': ['Korean'], 'phone': '+255757111152', 'email': 'mbagalakorean@example.com', 'lat': -6.8650, 'lng': 39.3250},
            {'name': 'Ubungo French', 'description': 'French cuisine', 'story': 'French bistro atmosphere', 'neighborhood': 'Ubungo', 'cuisines': ['French'], 'phone': '+255757111153', 'email': 'ubungofrench@example.com', 'lat': -6.8050, 'lng': 39.2250},
            {'name': 'Posta Ethiopian', 'description': 'Ethiopian injera and stews', 'story': 'Authentic Ethiopian food', 'neighborhood': 'Posta', 'cuisines': ['Ethiopian'], 'phone': '+255757111154', 'email': 'postaethiopian@example.com', 'lat': -6.8250, 'lng': 39.2950},
            {'name': 'Tabata South African', 'description': 'South African braai', 'story': 'South African flavors', 'neighborhood': 'Tabata', 'cuisines': ['South African'], 'phone': '+255757111155', 'email': 'tabatasouthafrican@example.com', 'lat': -6.8200, 'lng': 39.2450},
            {'name': 'Buguruni Pakistani', 'description': 'Pakistani cuisine', 'story': 'Authentic Pakistani dishes', 'neighborhood': 'Buguruni', 'cuisines': ['Pakistani'], 'phone': '+255757111156', 'email': 'bugurunipakistani@example.com', 'lat': -6.8400, 'lng': 39.2800},
            {'name': 'Changombe Turkish', 'description': 'Turkish kebabs', 'story': 'Turkish street food', 'neighborhood': 'Changombe', 'cuisines': ['Turkish'], 'phone': '+255757111157', 'email': 'changomberturkish@example.com', 'lat': -6.8500, 'lng': 39.2900},
            {'name': 'Mbezi Caribbean', 'description': 'Caribbean jerk chicken', 'story': 'Caribbean flavors', 'neighborhood': 'Mbezi', 'cuisines': ['Caribbean'], 'phone': '+255757111158', 'email': 'mbezicaribbean@example.com', 'lat': -6.7550, 'lng': 39.2650},
            {'name': 'Masaki Vietnamese', 'description': 'Vietnamese pho', 'story': 'Vietnamese street food', 'neighborhood': 'Masaki', 'cuisines': ['Vietnamese'], 'phone': '+255757111159', 'email': 'masakivietnamese@example.com', 'lat': -6.7900, 'lng': 39.2800},
            {'name': 'Mikocheni Spanish', 'description': 'Spanish tapas', 'story': 'Spanish cuisine', 'neighborhood': 'Mikocheni', 'cuisines': ['Spanish'], 'phone': '+255757111160', 'email': 'mikochenispanish@example.com', 'lat': -6.8000, 'lng': 39.2600},
        ]
        
        neighborhoods_data = {
            'Kibada, Kigamboni': {'street': 'Beach Road', 'city': 'Dar es Salaam', 'state': 'Dar es Salaam', 'postal_code': '17101'},
            'Kigamboni': {'street': 'Mtongani Road', 'city': 'Dar es Salaam', 'state': 'Dar es Salaam', 'postal_code': '17102'},
            'Masaki': {'street': 'Haile Selassie Road', 'city': 'Dar es Salaam', 'state': 'Dar es Salaam', 'postal_code': '14101'},
            'Mikocheni': {'street': 'Mikocheni Road', 'city': 'Dar es Salaam', 'state': 'Dar es Salaam', 'postal_code': '14102'},
            'Sinza': {'street': 'Sinza Road', 'city': 'Dar es Salaam', 'state': 'Dar es Salaam', 'postal_code': '15101'},
            'Kariakoo': {'street': 'Mkwepu Street', 'city': 'Dar es Salaam', 'state': 'Dar es Salaam', 'postal_code': '11101'},
            'Ilala': {'street': 'Nyerere Road', 'city': 'Dar es Salaam', 'state': 'Dar es Salaam', 'postal_code': '11102'},
            'Temeke': {'street': 'Temeke Road', 'city': 'Dar es Salaam', 'state': 'Dar es Salaam', 'postal_code': '12101'},
            'Mbagala': {'street': 'Mbagala Road', 'city': 'Dar es Salaam', 'state': 'Dar es Salaam', 'postal_code': '12102'},
            'Ubungo': {'street': 'Morogoro Road', 'city': 'Dar es Salaam', 'state': 'Dar es Salaam', 'postal_code': '13101'},
            'Posta': {'street': 'Sokoine Drive', 'city': 'Dar es Salaam', 'state': 'Dar es Salaam', 'postal_code': '11103'},
            'Tabata': {'street': 'Tabata Road', 'city': 'Dar es Salaam', 'state': 'Dar es Salaam', 'postal_code': '15102'},
            'Buguruni': {'street': 'Buguruni Road', 'city': 'Dar es Salaam', 'state': 'Dar es Salaam', 'postal_code': '11104'},
            'Changombe': {'street': 'Changombe Road', 'city': 'Dar es Salaam', 'state': 'Dar es Salaam', 'postal_code': '11105'},
            'Mbezi': {'street': 'Bagamoyo Road', 'city': 'Dar es Salaam', 'state': 'Dar es Salaam', 'postal_code': '14103'},
            'Oyster Bay': {'street': 'Msasani Road', 'city': 'Dar es Salaam', 'state': 'Dar es Salaam', 'postal_code': '14104'},
        }
        
        created_count = 0
        for i, restaurant_data in enumerate(restaurants_data):
            owner = owners[i % len(owners)]
            neighborhood = restaurant_data['neighborhood']
            
            address_data = neighborhoods_data.get(neighborhood, neighborhoods_data['Kigamboni'])
            street_number = random.randint(1, 999)
            
            address = Address.objects.create(
                street_address=f"{street_number} {address_data['street']}",
                city=address_data['city'],
                state=address_data['state'],
                postal_code=address_data['postal_code'],
                latitude=restaurant_data['lat'],
                longitude=restaurant_data['lng']
            )
            
            restaurant = Restaurant.objects.create(
                owner=owner,
                name=restaurant_data['name'],
                description=restaurant_data['description'],
                story_description=restaurant_data['story'],
                phone_number=restaurant_data['phone'],
                email=restaurant_data['email'],
                status='active',
                is_verified=True,
                reservation_enabled=random.choice([True, False]),
                overall_rating=Decimal(str(round(random.uniform(3.5, 5.0), 2))),
                total_reviews=random.randint(10, 500),
                amenities=self.get_random_amenities()
            )
            
            for cuisine_name in restaurant_data['cuisines']:
                try:
                    cuisine = Cuisine.objects.get(name=cuisine_name)
                    restaurant.cuisines.add(cuisine)
                except Cuisine.DoesNotExist:
                    pass
            
            branch = Branch.objects.create(
                restaurant=restaurant,
                name='Main Branch',
                address=address,
                phone_number=restaurant_data['phone'],
                operating_hours=self.get_operating_hours(),
                is_active=True,
                is_main_branch=True
            )
            
            created_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Created {created_count} restaurants with branches'))
    
    def get_operating_hours(self):
        return {
            'monday': {'open': '08:00', 'close': '22:00'},
            'tuesday': {'open': '08:00', 'close': '22:00'},
            'wednesday': {'open': '08:00', 'close': '22:00'},
            'thursday': {'open': '08:00', 'close': '22:00'},
            'friday': {'open': '08:00', 'close': '23:00'},
            'saturday': {'open': '09:00', 'close': '23:00'},
            'sunday': {'open': '09:00', 'close': '21:00'},
        }
    
    def get_random_amenities(self):
        amenities = ['WiFi', 'Parking', 'Outdoor Seating', 'Air Conditioning', 'Takeaway', 'Delivery']
        return random.sample(amenities, random.randint(2, 4))