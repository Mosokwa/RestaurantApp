# management/commands/create_menu_data.py
from django.core.management.base import BaseCommand
from api.models.menu_models import MenuCategory, MenuItem, ItemModifierGroup, ItemModifier, MenuItemModifier, SpecialOffer, PopularCategory
from api.models.restaurant_models import Restaurant
import random
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Create menu categories and items for restaurants'
    
    def handle(self, *args, **options):
        restaurants = Restaurant.objects.all()
        
        categories_data = [
            {'name': 'Nyama Choma', 'description': 'Grilled meats'},
            {'name': 'Seafood', 'description': 'Fresh fish and seafood'},
            {'name': 'Pilau & Biryani', 'description': 'Spiced rice dishes'},
            {'name': 'Swahili Dishes', 'description': 'Traditional coastal cuisine'},
            {'name': 'Ugali & Sides', 'description': 'Traditional staples'},
            {'name': 'Appetizers', 'description': 'Starters and snacks'},
            {'name': 'Salads', 'description': 'Fresh salads'},
            {'name': 'Soups', 'description': 'Hot soups'},
            {'name': 'Pizza', 'description': 'Italian pizzas'},
            {'name': 'Pasta', 'description': 'Italian pasta dishes'},
            {'name': 'Burgers', 'description': 'Beef and chicken burgers'},
            {'name': 'Sandwiches', 'description': 'Fresh sandwiches'},
            {'name': 'Desserts', 'description': 'Sweet treats'},
            {'name': 'Beverages', 'description': 'Drinks and refreshments'},
            {'name': 'Breakfast', 'description': 'Morning meals'},
            {'name': 'Kid\'s Menu', 'description': 'Meals for children'},
            {'name': 'Grilled Specialties', 'description': 'Charcoal grilled items'},
            {'name': 'Curries', 'description': 'Spicy curry dishes'},
            {'name': 'Noodles', 'description': 'Asian noodle dishes'},
            {'name': 'Rice Dishes', 'description': 'Various rice preparations'},
            {'name': 'Stews', 'description': 'Hearty stews'},
            {'name': 'Vegetarian', 'description': 'Vegetarian options'},
            {'name': 'Specials', 'description': 'Chef\'s specials'},
            {'name': 'Combo Meals', 'description': 'Value combos'},
        ]
        
        tanzanian_foods = [
            # Nyama Choma
            {'name': 'Beef Nyama Choma', 'description': 'Grilled beef with spices', 'price': 15000, 'type': 'main'},
            {'name': 'Goat Meat Choma', 'description': 'Grilled goat meat', 'price': 12000, 'type': 'main'},
            {'name': 'Chicken Choma', 'description': 'Grilled chicken pieces', 'price': 10000, 'type': 'main'},
            {'name': 'Pork Choma', 'description': 'Grilled pork ribs', 'price': 14000, 'type': 'main'},
            {'name': 'Mixed Grill Platter', 'description': 'Assorted grilled meats', 'price': 25000, 'type': 'main'},
            {'name': 'Mbuzi Choma', 'description': 'Goat meat roast', 'price': 18000, 'type': 'main'},
            {'name': 'Kuku Kienyeji Choma', 'description': 'Free range chicken', 'price': 16000, 'type': 'main'},
            {'name': 'Beef Ribs Choma', 'description': 'Grilled beef ribs', 'price': 20000, 'type': 'main'},
            
            # Seafood
            {'name': 'Grilled Tilapia', 'description': 'Whole grilled tilapia', 'price': 12000, 'type': 'main'},
            {'name': 'Fried Kingfish', 'description': 'Deep fried kingfish', 'price': 15000, 'type': 'main'},
            {'name': 'Prawns Masala', 'description': 'Spicy prawn curry', 'price': 18000, 'type': 'main'},
            {'name': 'Octopus Curry', 'description': 'Octopus in coconut curry', 'price': 16000, 'type': 'main'},
            {'name': 'Seafood Platter', 'description': 'Mixed seafood grill', 'price': 30000, 'type': 'main'},
            {'name': 'Fried Calamari', 'description': 'Crispy fried squid', 'price': 14000, 'type': 'main'},
            {'name': 'Grilled Lobster', 'description': 'Fresh grilled lobster', 'price': 35000, 'type': 'main'},
            {'name': 'Fish Fillet', 'description': 'Pan fried fish fillet', 'price': 13000, 'type': 'main'},
            
            # Swahili Dishes
            {'name': 'Chicken Biryani', 'description': 'Spiced rice with chicken', 'price': 8000, 'type': 'main'},
            {'name': 'Beef Pilau', 'description': 'Spiced rice with beef', 'price': 7000, 'type': 'main'},
            {'name': 'Mchuzi wa Samaki', 'description': 'Fish coconut curry', 'price': 9000, 'type': 'main'},
            {'name': 'Wali wa Nazi', 'description': 'Coconut rice', 'price': 4000, 'type': 'side'},
            {'name': 'Mishkaki (6 pieces)', 'description': 'Grilled meat skewers', 'price': 6000, 'type': 'main'},
            {'name': 'Kuku wa Kupaka', 'description': 'Chicken in coconut sauce', 'price': 11000, 'type': 'main'},
            {'name': 'Mtori', 'description': 'Banana soup with meat', 'price': 5000, 'type': 'main'},
            {'name': 'Viazi Karai', 'description': 'Fried potatoes', 'price': 3000, 'type': 'side'},
            
            # Ugali & Sides
            {'name': 'Ugali', 'description': 'Maize flour porridge', 'price': 1500, 'type': 'side'},
            {'name': 'Chips Mayai', 'description': 'French fry omelette', 'price': 5000, 'type': 'main'},
            {'name': 'Maharage', 'description': 'Beans in coconut sauce', 'price': 3000, 'type': 'side'},
            {'name': 'Sukuma Wiki', 'description': 'Collard greens', 'price': 2500, 'type': 'side'},
            {'name': 'Kachumbari', 'description': 'Fresh tomato salad', 'price': 2000, 'type': 'side'},
            {'name': 'Mchicha', 'description': 'Spinach with coconut', 'price': 2800, 'type': 'side'},
            {'name': 'Ndizi Nyama', 'description': 'Bananas with meat', 'price': 6500, 'type': 'main'},
            {'name': 'Kitimoto', 'description': 'Pork stew', 'price': 12000, 'type': 'main'},
            
            # International Foods
            {'name': 'Margherita Pizza', 'description': 'Classic cheese pizza', 'price': 12000, 'type': 'main'},
            {'name': 'Pepperoni Pizza', 'description': 'Pepperoni pizza', 'price': 15000, 'type': 'main'},
            {'name': 'Spaghetti Bolognese', 'description': 'Beef pasta', 'price': 10000, 'type': 'main'},
            {'name': 'Beef Burger', 'description': 'Classic beef burger', 'price': 8000, 'type': 'main'},
            {'name': 'Chicken Burger', 'description': 'Grilled chicken burger', 'price': 7500, 'type': 'main'},
            {'name': 'Club Sandwich', 'description': 'Triple decker sandwich', 'price': 9000, 'type': 'main'},
            {'name': 'Caesar Salad', 'description': 'Chicken caesar salad', 'price': 8500, 'type': 'main'},
            {'name': 'Fish and Chips', 'description': 'British classic', 'price': 11000, 'type': 'main'},
            {'name': 'Chicken Shawarma', 'description': 'Middle Eastern wrap', 'price': 7000, 'type': 'main'},
            {'name': 'Beef Tacos', 'description': 'Mexican tacos', 'price': 8000, 'type': 'main'},
            {'name': 'Chicken Tikka Masala', 'description': 'Indian curry', 'price': 12000, 'type': 'main'},
            {'name': 'Sushi Platter', 'description': 'Assorted sushi', 'price': 25000, 'type': 'main'},
            {'name': 'Pad Thai', 'description': 'Thai noodles', 'price': 11000, 'type': 'main'},
            {'name': 'Beef Stir Fry', 'description': 'Asian stir fry', 'price': 13000, 'type': 'main'},
            
            # Beverages
            {'name': 'Fresh Passion Juice', 'description': 'Fresh passion fruit juice', 'price': 3000, 'type': 'beverage'},
            {'name': 'Mango Juice', 'description': 'Fresh mango juice', 'price': 3000, 'type': 'beverage'},
            {'name': 'Soda', 'description': 'Soft drinks', 'price': 2000, 'type': 'beverage'},
            {'name': 'Bottled Water', 'description': '500ml bottled water', 'price': 1000, 'type': 'beverage'},
            {'name': 'Coffee', 'description': 'Fresh brewed coffee', 'price': 2500, 'type': 'beverage'},
            {'name': 'Tea', 'description': 'Hot tea', 'price': 1500, 'type': 'beverage'},
            {'name': 'Fresh Lemonade', 'description': 'Homemade lemonade', 'price': 2500, 'type': 'beverage'},
            {'name': 'Smoothie', 'description': 'Fruit smoothie', 'price': 4000, 'type': 'beverage'},
            {'name': 'Milkshake', 'description': 'Chocolate/vanilla milkshake', 'price': 3500, 'type': 'beverage'},
            {'name': 'Fresh Orange Juice', 'description': 'Fresh squeezed orange juice', 'price': 3200, 'type': 'beverage'},
            
            # Desserts
            {'name': 'Ice Cream', 'description': 'Vanilla ice cream', 'price': 3000, 'type': 'dessert'},
            {'name': 'Chocolate Cake', 'description': 'Chocolate slice', 'price': 4000, 'type': 'dessert'},
            {'name': 'Fruit Salad', 'description': 'Fresh fruit mix', 'price': 3500, 'type': 'dessert'},
            {'name': 'Cheesecake', 'description': 'New York cheesecake', 'price': 5000, 'type': 'dessert'},
            {'name': 'Brownie', 'description': 'Chocolate brownie', 'price': 3000, 'type': 'dessert'},
            {'name': 'Apple Pie', 'description': 'Warm apple pie', 'price': 4500, 'type': 'dessert'},
            {'name': 'Crème Brûlée', 'description': 'French dessert', 'price': 5500, 'type': 'dessert'},
            {'name': 'Tiramisu', 'description': 'Italian dessert', 'price': 5000, 'type': 'dessert'},
        ]
        
        # Create popular categories
        popular_categories_data = [
            {'name': 'Nyama Choma', 'icon': 'fa-fire', 'color': '#FF6B35', 'search_query': 'nyama choma'},
            {'name': 'Seafood', 'icon': 'fa-fish', 'color': '#4A90E2', 'search_query': 'seafood'},
            {'name': 'Swahili Food', 'icon': 'fa-utensils', 'color': '#FFD700', 'search_query': 'swahili'},
            {'name': 'Vegetarian', 'icon': 'fa-leaf', 'color': '#50C878', 'search_query': 'vegetarian'},
            {'name': 'Fast Food', 'icon': 'fa-hamburger', 'color': '#FF6B6B', 'search_query': 'fast food'},
            {'name': 'Pizza', 'icon': 'fa-pizza-slice', 'color': '#F7931E', 'search_query': 'pizza'},
            {'name': 'Breakfast', 'icon': 'fa-egg', 'color': '#FFB347', 'search_query': 'breakfast'},
            {'name': 'Desserts', 'icon': 'fa-ice-cream', 'color': '#DDA0DD', 'search_query': 'dessert'},
            {'name': 'Coffee', 'icon': 'fa-coffee', 'color': '#8B4513', 'search_query': 'coffee'},
            {'name': 'Chinese', 'icon': 'fa-dragon', 'color': '#C41E3A', 'search_query': 'chinese'},
        ]
        
        for cat_data in popular_categories_data:
            PopularCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'icon': cat_data['icon'],
                    'color': cat_data['color'],
                    'search_query': cat_data['search_query'],
                    'is_active': True,
                    'display_order': len(PopularCategory.objects.all()) + 1
                }
            )
        
        created_items = 0
        created_offers = 0
        
        for restaurant in restaurants:
            restaurant_categories = []
            for cat_data in random.sample(categories_data, random.randint(8, 15)):
                category, created = MenuCategory.objects.get_or_create(
                    restaurant=restaurant,
                    name=cat_data['name'],
                    defaults={
                        'description': cat_data['description'],
                        'display_order': len(restaurant_categories) + 1,
                        'is_active': True,
                        'is_featured': random.choice([True, False])
                    }
                )
                restaurant_categories.append(category)
            
            restaurant_items = []
            for food in random.sample(tanzanian_foods, random.randint(20, 40)):
                category = random.choice(restaurant_categories)
                
                is_vegetarian = False
                is_vegan = False
                is_gluten_free = random.choice([True, False])
                
                if 'vegetable' in food['name'].lower() or 'salad' in food['name'].lower() or 'fruit' in food['name'].lower():
                    is_vegetarian = random.choice([True, True, False])
                    is_vegan = random.choice([True, False])
                elif 'fish' in food['name'].lower() or 'seafood' in food['name'].lower():
                    is_vegetarian = False
                    is_vegan = False
                
                item = MenuItem.objects.create(
                    category=category,
                    name=food['name'],
                    description=food['description'],
                    price=Decimal(food['price']),
                    item_type=food['type'],
                    is_vegetarian=is_vegetarian,
                    is_vegan=is_vegan,
                    is_gluten_free=is_gluten_free,
                    is_available=True,
                    is_featured=random.choice([True, False]),
                    calories=random.randint(200, 1200) if random.choice([True, False]) else None,
                    preparation_time=random.randint(10, 45),
                    popularity_score=random.randint(0, 1000),
                    order_count=random.randint(0, 500),
                    display_order=created_items % 10
                )
                restaurant_items.append(item)
                created_items += 1
            
            # Create special offers for some restaurants
            if random.choice([True, False]) and len(restaurant_items) >= 3:
                offer_types = ['percentage', 'fixed', 'bogo']
                offer_type = random.choice(offer_types)
                
                if offer_type == 'percentage':
                    discount_value = Decimal(str(random.choice([10, 15, 20, 25, 30])))
                elif offer_type == 'fixed':
                    discount_value = Decimal(str(random.choice([2000, 3000, 5000, 7000])))
                else:
                    discount_value = Decimal('0')
                
                SpecialOffer.objects.create(
                    restaurant=restaurant,
                    title=random.choice([
                        'Weekend Special',
                        'Happy Hour Deal',
                        'Family Meal Deal',
                        'Student Discount',
                        'Lunch Special'
                    ]),
                    description='Limited time offer',
                    offer_type=offer_type,
                    discount_value=discount_value,
                    min_order_amount=Decimal('10000'),
                    valid_from=timezone.now(),
                    valid_until=timezone.now() + timedelta(days=random.randint(7, 30)),
                    is_active=True,
                    is_featured=random.choice([True, False]),
                    max_usage=random.randint(50, 200),
                    max_usage_per_user=random.randint(1, 3),
                    display_priority=random.randint(1, 10)
                )
                created_offers += 1
        
        self.stdout.write(self.style.SUCCESS(f'Created {created_items} menu items and {created_offers} special offers'))