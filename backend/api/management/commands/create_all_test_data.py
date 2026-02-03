# management/commands/create_all_test_data.py
from django.core.management.base import BaseCommand
from django.core.management import call_command

class Command(BaseCommand):
    help = 'Create all test data in correct order'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-existing',
            action='store_true',
            help='Skip data that already exists',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Starting comprehensive test data creation...'))
        self.stdout.write(self.style.SUCCESS('📍 Location: Dar es Salaam, Tanzania'))
        self.stdout.write(self.style.SUCCESS('🎯 Focus: Kigamboni/Kibada area restaurants'))
        
        commands = [
            ('create_cuisines', {}),
            ('create_users_and_customers', {}),
            ('create_restaurants_and_branches', {}),
            ('create_menu_data', {}),
            ('create_orders', {}),
            ('create_reviews_and_ratings', {}),
            ('create_loyalty_data', {}),
            ('create_reservations', {}),
        ]
        
        for command, kwargs in commands:
            try:
                self.stdout.write(self.style.NOTICE(f'▶️  Running: {command}'))
                call_command(command, **kwargs)
                self.stdout.write(self.style.SUCCESS(f'   ✅ {command} completed'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   ❌ {command} failed: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS('\n🎉 All test data created successfully!'))
        self.stdout.write(self.style.SUCCESS('📊 Summary:'))
        self.stdout.write('   • 38 Tanzanian & International cuisines')
        self.stdout.write('   • 30 restaurant owners & 200 customers')
        self.stdout.write('   • 50 restaurants in Dar es Salaam (20 in Kigamboni/Kibada)')
        self.stdout.write('   • Complete menus with Tanzanian specialties')
        self.stdout.write('   • 1000+ orders with payments and tracking')
        self.stdout.write('   • Comprehensive reviews & ratings system')
        self.stdout.write('   • Multi-restaurant loyalty program')
        self.stdout.write('   • Table reservation system')