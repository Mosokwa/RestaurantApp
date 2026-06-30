# management/commands/_base_data.py
from django.core.management.base import BaseCommand

TANZANIA_LOCATIONS = {
    'dar_es_salaam_areas': [
        'Kigamboni', 'Kibada', 'Mbagala', 'Kivukoni', 'Mikocheni', 
        'Masaki', 'Oysterbay', 'Kinondoni', 'Mbezi Beach', 'Kawe',
        'Msasani', 'Upanga', 'Kariakoo', 'Posta', 'Kisutu',
        'Temeke', 'Mtoni', 'Kurasini', 'Keko', "Chang'ombe"
    ],
    'other_regions': [
        ('Arusha', 'Arusha'), ('Moshi', 'Kilimanjaro'), ('Mwanza', 'Mwanza'),
        ('Dodoma', 'Dodoma'), ('Tanga', 'Tanga'), ('Mbeya', 'Mbeya'),
        ('Zanzibar', 'Unguja North'), ('Morogoro', 'Morogoro')
    ]
}

OTHER_COUNTRIES = [
    ('Nairobi', 'Kenya'), ('Kampala', 'Uganda'), ('Kigali', 'Rwanda'),
    ('Johannesburg', 'South Africa'), ('Lagos', 'Nigeria'), ('Accra', 'Ghana'),
    ('London', 'United Kingdom'), ('New York', 'USA'), ('Dubai', 'UAE'),
    ('Mumbai', 'India'), ('Singapore', 'Singapore')
]

CUISINES = [
    'Tanzanian', 'Swahili', 'Indian', 'Chinese', 'Italian', 'Mexican',
    'Japanese', 'Thai', 'Mediterranean', 'American', 'BBQ', 'Seafood',
    'Vegetarian', 'Vegan', 'Fast Food', 'Coffee & Tea', 'Bakery',
    'African Fusion', 'Ethiopian', 'Moroccan', 'Lebanese', 'Turkish'
]

MENU_CATEGORIES = {
    'Tanzanian': ['Nyama Choma', 'Ugali & Fish', 'Pilau', 'Samosas', 'Biryani', 'Zanzibar Pizza', 'Chips Mayai'],
    'Indian': ['Curries', 'Tandoori', 'Biryani', 'Naan & Breads', 'Vegetarian', 'Desserts'],
    'Italian': ['Pizzas', 'Pastas', 'Risottos', 'Salads', 'Desserts', 'Wine'],
    'Chinese': ['Noodles', 'Fried Rice', 'Dim Sum', 'Stir Fries', 'Soups'],
    'Fast Food': ['Burgers', 'Fried Chicken', 'Fries', 'Shakes', 'Wraps'],
    'Japanese': ['Sushi', 'Ramen', 'Tempura', 'Sashimi', 'Donburi'],
}

LOYALTY_PROGRAM_CONFIG = {
    'name': 'Global Loyalty Program',
    'program_type': 'global',
    'points_per_dollar': 1.00,
    'signup_bonus': 100,
    'referral_bonus': 500,
    'tiers': {'bronze': 0, 'silver': 1000, 'gold': 5000, 'platinum': 15000}
}

class ProgressTracker:
    def __init__(self, total, description):
        self.total = total
        self.current = 0
        self.description = description
        self.errors = []
    
    def update(self, increment=1, item_name=""):
        self.current += increment
        if self.current % max(1, self.total // 20) == 0 or self.current == self.total:
            print(f"  Progress: {self.current}/{self.total} ({self.description}) - {item_name}")
    
    def add_error(self, error):
        self.errors.append(error)
    
    def summary(self):
        if self.errors:
            print(f"  ⚠️ {len(self.errors)} errors occurred. First few: {self.errors[:3]}")
        print(f"  ✅ Completed: {self.current}/{self.total}")