# management/commands/setup_test_data.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
import random
from decimal import Decimal

class Command(BaseCommand):
    help = 'Setup complete test data for the restaurant platform (Dar es Salaam, Tanzania)'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting test data setup for Dar es Salaam restaurants...'))
        
        # Execute commands in proper order
        commands = [
            'create_cuisines',
            'create_users_and_customers',
            'create_restaurants_and_branches',
            'create_restaurant_staff',
            'create_menu_data',
            'create_customer_preferences',
            'create_orders',
            'create_reviews_and_ratings',
            'create_loyalty_data',
            'create_reservations',
            'create_special_offers',
            'create_analytics_data',
        ]
        
        for cmd_name in commands:
            try:
                self.stdout.write(self.style.NOTICE(f'Running {cmd_name}...'))
                cmd = self.load_command(cmd_name)
                cmd.handle()
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error in {cmd_name}: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS('✅ Test data setup completed successfully!'))
    
    def load_command(self, command_name):
        from django.core.management import call_command
        import importlib
        
        module_name = f"api.management.commands.{command_name}"
        module = importlib.import_module(module_name)
        return module.Command()