# management/commands/populate_all.py
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import transaction
import sys

class Command(BaseCommand):
    help = 'Populate the entire database with test data in correct order'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-existing',
            action='store_true',
            help='Skip creation if data already exists'
        )
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Clean existing data before populating'
        )
        parser.add_argument(
            '--continue-on-error',
            action='store_true',
            help='Continue even if individual commands fail'
        )
        parser.add_argument(
            '--customers',
            type=int,
            default=200,
            help='Number of customers to create'
        )
        parser.add_argument(
            '--orders',
            type=int,
            default=500,
            help='Number of orders to create'
        )
    
    def handle(self, *args, **options):
        skip_existing = options['skip_existing']
        clean = options['clean']
        continue_on_error = options.get('continue_on_error', False)
        customers_count = options['customers']
        orders_count = options['orders']
        
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(self.style.SUCCESS('STARTING DATABASE POPULATION'))
        self.stdout.write(self.style.SUCCESS('='*60))
        
        # List of command names (without .py extension)
        # These must match your actual command filenames
        commands = [
            ('base_setup', 'Setting up base data (cuisines, loyalty program)'),
            ('owners', 'Creating restaurant owners'),
            ('restaurants', 'Creating restaurants and branches'),
            ('menu', 'Creating menu categories and items'),
            ('customers', f'Creating {customers_count} customers'),
            ('orders', f'Creating {orders_count} orders and order items'),
            ('loyalty', 'Setting up loyalty data'),
            ('analytics', 'Populating analytics data'),
            ('reservations', 'Creating reservations'),
            ('reviews', 'Creating reviews and ratings'),
            ('personalization', 'Populating user behavior and personalization'),
        ]
        
        for command_name, description in commands:
            self.stdout.write(f"\n📦 {description}...")
            try:
                # Build args based on command
                cmd_args = []
                if skip_existing:
                    cmd_args.append('--skip-existing')
                if clean:
                    cmd_args.append('--clean')
                if command_name == 'customers' and customers_count:
                    cmd_args.extend(['--count', str(customers_count)])
                if command_name == 'orders' and orders_count:
                    cmd_args.extend(['--count', str(orders_count)])
                
                call_command(command_name, *cmd_args, stdout=sys.stdout)
                self.stdout.write(self.style.SUCCESS(f"  ✓ {description} completed"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  ✗ Failed: {str(e)}"))
                if not continue_on_error:
                    raise
                self.stdout.write(self.style.WARNING("  Continuing to next command..."))
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('POPULATION COMPLETE!'))
        self.stdout.write(self.style.SUCCESS('='*60))
        
        # Summary
        self.stdout.write("\n📊 DATA SUMMARY:")
        self.stdout.write("  You can now test:")
        self.stdout.write("  - Restaurant discovery (filtering by cuisine, location, rating)")
        self.stdout.write("  - Order placement and tracking")
        self.stdout.write("  - Loyalty points earning and redemption")
        self.stdout.write("  - Reservation system")
        self.stdout.write("  - Reviews and ratings")
        self.stdout.write("  - Personalized recommendations")
        self.stdout.write("  - Analytics dashboards")