# management/commands/generate_timeslots.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, datetime
from api.models import TimeSlot, Restaurant, Branch

class Command(BaseCommand):
    help = 'Generate time slots for all restaurants for the next 30 days'
    
    def handle(self, *args, **options):
        restaurants = Restaurant.objects.filter(reservation_enabled=True, status='active')
        
        total_slots_created = 0
        
        for restaurant in restaurants:
            branches = restaurant.branches.filter(is_active=True)
            
            for branch in branches:
                slots_created = self.generate_slots_for_branch(restaurant, branch)
                total_slots_created += slots_created
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully generated {total_slots_created} time slots')
        )
    
    def generate_slots_for_branch(self, restaurant, branch):
        """Generate time slots for a branch"""
        today = timezone.now().date()
        slots_created = 0
        
        for day in range(30):  # Next 30 days
            date = today + timedelta(days=day)
            day_name = date.strftime('%A').lower()
            operating_hours = branch.operating_hours.get(day_name, {})
            
            if operating_hours and operating_hours.get('open') and operating_hours.get('close'):
                slots = self.create_slots_for_day(restaurant, branch, date, operating_hours)
                slots_created += len(slots)
        
        return slots_created
    
    def create_slots_for_day(self, restaurant, branch, date, operating_hours):
        """Create time slots for a specific day"""
        open_time = datetime.strptime(operating_hours['open'], '%H:%M').time()
        close_time = datetime.strptime(operating_hours['close'], '%H:%M').time()
        
        slots = []
        current_time = open_time
        
        while current_time < close_time:
            slot_end = (datetime.combine(date, current_time) + 
                       timedelta(minutes=restaurant.time_slot_interval)).time()
            
            # Calculate max capacity based on available tables
            from api.models import Table
            available_tables = Table.objects.filter(
                restaurant=restaurant,
                branch=branch,
                is_available=True
            )
            max_capacity = sum(table.capacity for table in available_tables)
            
            # Create or update time slot
            slot, created = TimeSlot.objects.get_or_create(
                restaurant=restaurant,
                branch=branch,
                date=date,
                start_time=current_time,
                defaults={
                    'end_time': slot_end,
                    'max_capacity': max_capacity,
                    'is_available': max_capacity > 0
                }
            )
            
            if created:
                slots.append(slot)
            
            current_time = slot_end
        
        return slots

# management/commands/send_reservation_reminders.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from api.models import Reservation
from api.services.reservation_services import NotificationService

class Command(BaseCommand):
    help = 'Send reservation reminders 24 hours before reservation time'
    
    def handle(self, *args, **options):
        tomorrow = timezone.now().date() + timedelta(days=1)
        
        # Get reservations for tomorrow that haven't been reminded
        reservations = Reservation.objects.filter(
            reservation_date=tomorrow,
            reminder_sent=False,
            status__in=['confirmed', 'pending']
        )
        
        reminder_count = 0
        
        for reservation in reservations:
            try:
                # In a real implementation, you'd send actual reminders
                self.stdout.write(
                    f"Would send reminder for reservation {reservation.reservation_code}"
                )
                reservation.reminder_sent = True
                reservation.save()
                reminder_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Failed to send reminder for {reservation.reservation_code}: {str(e)}")
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Sent {reminder_count} reservation reminders')
        )