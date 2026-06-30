# management/commands/menu.py
from django.core.management.base import BaseCommand
from decimal import Decimal
import random
from django.utils import timezone

class Command(BaseCommand):
    help = 'Create menu categories, items, modifiers, and offers'
    
    def add_arguments(self, parser):
        parser.add_argument('--skip-existing', action='store_true')
        parser.add_argument('--clean', action='store_true')
    
    def handle(self, *args, **options):
        from api.models import (
            Restaurant, MenuCategory, MenuItem, ItemModifierGroup, 
            ItemModifier, MenuItemModifier, SpecialOffer
        )
        
        if options['clean']:
            MenuItem.objects.all().delete()
            MenuCategory.objects.all().delete()
            ItemModifierGroup.objects.all().delete()
            SpecialOffer.objects.all().delete()
            MenuItemModifier.objects.all().delete()
            self.stdout.write("  Cleaned existing menu items")
        
        restaurants = list(Restaurant.objects.filter(status='active'))
        if not restaurants:
            self.stdout.write(self.style.ERROR("  No restaurants found! Run _restaurants first."))
            return
        
        total_items = 0
        total_categories = 0
        total_offers = 0
        
        # Define menu item templates by cuisine type
        menu_templates = {
            'Tanzanian/Swahili': {
                'categories': ['Nyama Choma', 'Seafood Specials', 'Ugali & Sides', 'Traditional Soups', 'Zanzibar Specialties', 'Local Desserts'],
                'items': [
                    ('Nyama Choma (Grilled Meat)', 12000, 'Grilled beef/goat with kachumbari', 'main'),
                    ('Mchicha na Nyama', 8000, 'Spinach with meat', 'main'),
                    ('Wali wa Nazi', 5000, 'Coconut rice', 'side'),
                    ('Samaki wa Kupaka', 15000, 'Grilled fish in coconut sauce', 'main'),
                    ('Mishkaki', 10000, 'Marinated beef skewers (10 pcs)', 'main'),
                    ('Zanzibar Pizza', 7000, 'Stuffed crepe-style pizza', 'main'),
                    ('Urojo Soup', 6000, 'Zanzibar mix soup', 'main'),
                    ('Biriyani ya Kuku', 14000, 'Spiced chicken rice', 'main'),
                    ('Viazi Karai', 4000, 'Spiced potato fritters', 'side'),
                    ('Mandaazi', 3000, 'Sweet fried doughnuts', 'dessert'),
                ]
            },
            'Indian': {
                'categories': ['Tandoori Specials', 'Curries', 'Biryanis', 'Breads', 'Vegetarian', 'Desserts', 'Beverages'],
                'items': [
                    ('Butter Chicken', 18000, 'Creamy tomato curry', 'main'),
                    ('Chicken Tikka Masala', 17000, 'Grilled chicken in spiced gravy', 'main'),
                    ('Lamb Rogan Josh', 20000, 'Slow-cooked lamb curry', 'main'),
                    ('Palak Paneer', 12000, 'Spinach with cottage cheese', 'main'),
                    ('Garlic Naan', 3000, 'Leavened flatbread', 'side'),
                    ('Chicken Biryani', 16000, 'Aromatic rice with chicken', 'main'),
                    ('Gulab Jamun', 4000, 'Milk-solid dumplings in syrup', 'dessert'),
                    ('Masala Dosa', 10000, 'Crispy crepe with spiced potato', 'main'),
                    ('Samosa', 5000, 'Fried pastry with spiced filling', 'side'),
                    ('Mango Lassi', 5000, 'Yogurt drink with mango', 'beverage'),
                ]
            },
            'Italian': {
                'categories': ['Pizzas', 'Pastas', 'Risottos', 'Antipasti', 'Desserts', 'Wines'],
                'items': [
                    ('Margherita Pizza', 15000, 'Fresh mozzarella, basil, tomato', 'main'),
                    ('Pepperoni Pizza', 18000, 'Spicy pepperoni, mozzarella', 'main'),
                    ('Spaghetti Carbonara', 16000, 'Egg, cheese, pancetta', 'main'),
                    ('Fettuccine Alfredo', 17000, 'Creamy parmesan sauce', 'main'),
                    ('Lasagna Classica', 19000, 'Layered beef bolognese', 'main'),
                    ('Tiramisu', 7000, 'Coffee-flavored dessert', 'dessert'),
                    ('Bruschetta', 6000, 'Toasted bread with tomatoes', 'side'),
                    ('Gelato (Pistachio)', 5000, 'Italian ice cream', 'dessert'),
                    ('Arancini', 8000, 'Fried rice balls', 'side'),
                ]
            },
            'Chinese': {
                'categories': ['Noodles', 'Fried Rice', 'Dim Sum', 'Stir Fries', 'Soups', 'Desserts'],
                'items': [
                    ('Chow Mein', 10000, 'Stir-fried noodles with vegetables', 'main'),
                    ('Fried Rice', 8000, 'Egg fried rice', 'side'),
                    ('Kung Pao Chicken', 14000, 'Spicy diced chicken with peanuts', 'main'),
                    ('Sweet & Sour Pork', 13000, 'Crispy pork in tangy sauce', 'main'),
                    ('Dim Sum Platter', 12000, 'Mixed dumplings (8 pcs)', 'main'),
                    ('Hot & Sour Soup', 6000, 'Spicy and tangy soup', 'main'),
                    ('Spring Rolls', 5000, 'Crispy vegetable rolls', 'side'),
                ]
            },
            'Japanese': {
                'categories': ['Sushi', 'Sashimi', 'Ramen', 'Tempura', 'Donburi', 'Sides'],
                'items': [
                    ('California Roll', 18000, 'Crab, avocado, cucumber (8 pcs)', 'main'),
                    ('Spicy Tuna Roll', 20000, 'Tuna with spicy mayo (8 pcs)', 'main'),
                    ('Salmon Sashimi', 22000, 'Fresh salmon slices (5 pcs)', 'main'),
                    ('Tonkotsu Ramen', 19000, 'Pork bone broth ramen', 'main'),
                    ('Tempura Udon', 16000, 'Noodles with tempura shrimp', 'main'),
                    ('Chicken Katsu Don', 15000, 'Breaded chicken rice bowl', 'main'),
                    ('Edamame', 4000, 'Steamed soybeans', 'side'),
                ]
            },
            'Fast Food': {
                'categories': ['Burgers', 'Fried Chicken', 'Wraps & Sandwiches', 'Fries & Sides', 'Shakes', 'Desserts'],
                'items': [
                    ('Classic Beef Burger', 12000, 'Beef patty with lettuce, tomato', 'main'),
                    ('Double Cheeseburger', 16000, 'Two patties, double cheese', 'main'),
                    ('Crispy Chicken Burger', 13000, 'Fried chicken fillet', 'main'),
                    ('Fried Chicken (6 pcs)', 14000, 'Crispy fried chicken', 'main'),
                    ('Chicken Wrap', 10000, 'Grilled chicken in tortilla', 'main'),
                    ('French Fries', 4000, 'Seasoned fries', 'side'),
                    ('Chocolate Milkshake', 6000, 'Thick chocolate shake', 'beverage'),
                    ('Onion Rings', 5000, 'Crispy battered onions', 'side'),
                ]
            },
            'Seafood': {
                'categories': ['Grilled Fish', 'Prawns', 'Lobster', 'Seafood Platters', 'Soups', 'Sides'],
                'items': [
                    ('Grilled Whole Fish', 25000, 'Fresh catch of the day', 'main'),
                    ('Garlic Butter Prawns', 22000, 'Large prawns in garlic sauce', 'main'),
                    ('Seafood Platter', 45000, 'Mix of fish, prawns, calamari', 'main'),
                    ('Lobster Thermidor', 55000, 'Lobster in creamy sauce', 'main'),
                    ('Calamari Rings', 15000, 'Crispy squid rings', 'main'),
                    ('Fish & Chips', 16000, 'Beer-battered fish with fries', 'main'),
                    ('Seafood Chowder', 10000, 'Creamy seafood soup', 'main'),
                ]
            },
            'BBQ': {
                'categories': ['Grilled Meats', 'Chicken', 'Ribs', 'Sausages', 'Sauces', 'Sides'],
                'items': [
                    ('Beef Ribs', 28000, 'Slow-smoked beef ribs', 'main'),
                    ('Pulled Pork Sandwich', 15000, 'Slow-cooked pork in bun', 'main'),
                    ('BBQ Chicken', 14000, 'Grilled chicken with BBQ sauce', 'main'),
                    ('Pork Shoulder', 22000, 'Smoked pork shoulder', 'main'),
                    ('Brisket', 30000, 'Slow-smoked beef brisket', 'main'),
                    ('Corn on Cob', 4000, 'Grilled corn with butter', 'side'),
                    ('Coleslaw', 3000, 'Creamy cabbage salad', 'side'),
                ]
            }
        }
        
        # Default template for any cuisine not found
        default_template = {
            'categories': ['Specials', 'Main Dishes', 'Sides', 'Desserts', 'Beverages'],
            'items': [
                ('House Special', 15000, 'Chef\'s special dish', 'main'),
                ('Grilled Chicken', 12000, 'Grilled chicken with sides', 'main'),
                ('Beef Steak', 18000, 'Juicy beef steak', 'main'),
                ('French Fries', 4000, 'Crispy fries', 'side'),
                ('Garden Salad', 5000, 'Fresh mixed salad', 'side'),
                ('Ice Cream', 3000, 'Vanilla ice cream', 'dessert'),
                ('Soft Drink', 2000, 'Coca cola, Sprite, Fanta', 'beverage'),
            ]
        }
        
        # Create modifiers first
        modifier_groups = {
            'Size': {'required': True, 'min': 1, 'max': 1},
            'Spice Level': {'required': True, 'min': 1, 'max': 1},
            'Extra Toppings': {'required': False, 'min': 0, 'max': 5},
            'Sauce': {'required': False, 'min': 0, 'max': 2},
            'Customization': {'required': False, 'min': 0, 'max': 3},
        }
        
        modifier_options = {
            'Size': [('Small', 0), ('Medium', 2000), ('Large', 4000)],
            'Spice Level': [('Mild', 0), ('Medium', 0), ('Hot', 0), ('Extra Hot', 0)],
            'Extra Toppings': [('Extra Cheese', 1500), ('Bacon', 2000), ('Guacamole', 2500), ('Extra Meat', 3000)],
            'Sauce': [('BBQ', 500), ('Garlic Mayo', 500), ('Spicy Chili', 500), ('Honey Mustard', 500)],
            'Customization': [('No Onion', 0), ('Extra Veggies', 1000), ('Gluten Free Bun', 2000), ('Double Meat', 4000)],
        }
        
        modifier_group_objs = {}
        for group_name, config in modifier_groups.items():
            group, created = ItemModifierGroup.objects.get_or_create(
                name=group_name,
                defaults={
                    'is_required': config['required'],
                    'min_selections': config['min'],
                    'max_selections': config['max']
                }
            )
            modifier_group_objs[group_name] = group
            
            # Create modifier options
            for option_name, price in modifier_options[group_name]:
                ItemModifier.objects.get_or_create(
                    modifier_group=group,
                    name=option_name,
                    defaults={'price_modifier': price, 'is_available': True}
                )
        
        self.stdout.write(f"  Created {len(modifier_group_objs)} modifier groups")
        
        # Create menu for each restaurant
        for restaurant in restaurants:
            # Determine primary cuisine for this restaurant
            primary_cuisine = restaurant.cuisines.first()
            cuisine_name = primary_cuisine.name if primary_cuisine else 'Fast Food'
            
            # Find matching template or use default
            template = None
            for template_key in menu_templates.keys():
                if template_key.lower() in cuisine_name.lower() or cuisine_name.lower() in template_key.lower():
                    template = menu_templates[template_key]
                    break
            
            # If no match found, use default template
            if template is None:
                template = default_template
                self.stdout.write(f"  Using default template for {restaurant.name} (cuisine: {cuisine_name})")
            
            # Create categories
            categories = []
            display_order = 0
            for cat_name in template['categories']:
                category, created = MenuCategory.objects.get_or_create(
                    restaurant=restaurant,
                    name=cat_name,
                    defaults={
                        'display_order': display_order,
                        'is_active': True,
                        'is_featured': display_order < 3
                    }
                )
                if created:
                    total_categories += 1
                categories.append(category)
                display_order += 1
            
            # Create menu items
            items_created = 0
            for item_name, price, desc, item_type in template['items']:
                if not categories:
                    continue
                category = random.choice(categories)
                
                menu_item = MenuItem.objects.create(
                    category=category,
                    name=item_name,
                    description=desc,
                    price=Decimal(price),
                    item_type=item_type,
                    is_available=True,
                    is_featured=random.choice([True, False, False]),
                    preparation_time=random.choice([10, 15, 20, 25, 30]),
                    calories=random.choice([300, 450, 600, 800, 1000, None]),
                    popularity_score=random.randint(0, 200),
                    order_count=random.randint(0, 500)
                )
                
                # Add random modifiers to some items using MenuItemModifier
                if random.random() > 0.5 and modifier_group_objs:
                    num_modifiers = random.randint(1, 2)
                    selected_groups = random.sample(list(modifier_group_objs.values()), 
                                                   min(num_modifiers, len(modifier_group_objs)))
                    for group in selected_groups:
                        MenuItemModifier.objects.get_or_create(
                            menu_item=menu_item,
                            modifier_group=group
                        )
                
                items_created += 1
                total_items += 1
            
            # Create special offers for each restaurant
            num_offers = random.randint(2, 5)
            for _ in range(num_offers):
                offer_type = random.choice(['percentage', 'fixed', 'bogo', 'combo'])
                discount_value = Decimal(str(random.choice([10, 15, 20, 25, 30, 40, 50]))) if offer_type == 'percentage' else Decimal(str(random.choice([5000, 10000, 15000, 20000])))
                
                # Get some items for this offer
                applicable_items = list(restaurant.menu_categories.first().menu_items.all()[:random.randint(1, 5)]) if restaurant.menu_categories.exists() else []
                
                valid_from = timezone.now() - timezone.timedelta(days=random.randint(0, 10))
                valid_until = valid_from + timezone.timedelta(days=random.randint(7, 60))
                
                SpecialOffer.objects.create(
                    restaurant=restaurant,
                    title=f"{random.choice(['Weekend', 'Happy Hour', 'Special', 'Festival', 'Flash Sale'])} {offer_type.upper()} Deal",
                    description=f"Get {discount_value}{'% off' if offer_type == 'percentage' else ' TZS off'} on selected items",
                    offer_type=offer_type,
                    discount_value=discount_value,
                    min_order_amount=Decimal(str(random.choice([0, 20000, 30000, 50000]))),
                    valid_from=valid_from,
                    valid_until=valid_until,
                    is_active=True,
                    is_featured=random.choice([True, False]),
                    display_priority=random.randint(0, 100)
                )
                total_offers += 1
            
            if restaurant.restaurant_id % 5 == 0:
                self.stdout.write(f"  Created menu for {restaurant.name}: {items_created} items")
        
        self.stdout.write(f"  ✅ Created {total_items} menu items, {total_categories} categories, {total_offers} offers")