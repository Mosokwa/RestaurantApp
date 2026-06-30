# management/commands/_reservations.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
import random
from datetime import timedelta

class Command(BaseCommand):
    help = 'Create table reservations for restaurants with reservation enabled'
    
    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=300, help='Number of reservations to create')
        parser.add_argument('--skip-existing', action='store_true')
        parser.add_argument('--clean', action='store_true')
    
    def handle(self, *args, **options):
        from api.models import (
            Restaurant, Branch, Customer, Table, TimeSlot, Reservation
        )
        
        if options['clean']:
            Reservation.objects.all().delete()
            TimeSlot.objects.all().delete()
            Table.objects.all().delete()
            self.stdout.write("  Cleaned existing reservations and tables")
        
        reservation_count = options['count']
        
        # Get restaurants that have reservations enabled
        restaurants = list(Restaurant.objects.filter(
            status='active',
            reservation_enabled=True
        ))
        
        if not restaurants:
            self.stdout.write(self.style.ERROR("  No restaurants with reservations enabled found!"))
            return
        
        customers = list(Customer.objects.all())
        if not customers:
            self.stdout.write(self.style.ERROR("  No customers found! Run _customers first."))
            return
        
        reservations_created = 0
        tables_created = 0
        time_slots_created = 0
        
        # Create tables and reservations for each restaurant
        for restaurant in restaurants:
            branches = list(restaurant.branches.filter(is_active=True))
            
            for branch in branches:
                # Create tables for this branch
                table_types = ['indoor', 'outdoor', 'booth', 'private']
                capacities = [2, 4, 6, 8, 10, 12]
                
                num_tables = random.randint(10, 30)
                for i in range(num_tables):
                    table_type = random.choice(table_types)
                    capacity = random.choice(capacities)
                    
                    Table.objects.create(
                        restaurant=restaurant,
                        branch=branch,
                        table_number=f"T{i+1:03d}",
                        table_name=f"{table_type.title()} {i+1}",
                        capacity=capacity,
                        table_type=table_type,
                        is_available=True,
                        min_party_size=1,
                        max_party_size=capacity
                    )
                    tables_created += 1
                
                # Create time slots for next 30 days
                for days_ahead in range(1, 31):
                    date = timezone.now().date() + timedelta(days=days_ahead)
                    
                    # Lunch slots (12 PM - 3 PM)
                    for hour in [12, 13, 14]:
                        start_time = f"{hour:02d}:00"
                        end_time = f"{hour+1:02d}:00"
                        
                        TimeSlot.objects.create(
                            restaurant=restaurant,
                            branch=branch,
                            date=date,
                            start_time=start_time,
                            end_time=end_time,
                            max_capacity=random.randint(5, 20),
                            is_available=True
                        )
                        time_slots_created += 1
                    
                    # Dinner slots (6 PM - 10 PM)
                    for hour in [18, 19, 20, 21]:
                        start_time = f"{hour:02d}:00"
                        end_time = f"{hour+1:02d}:00"
                        
                        TimeSlot.objects.create(
                            restaurant=restaurant,
                            branch=branch,
                            date=date,
                            start_time=start_time,
                            end_time=end_time,
                            max_capacity=random.randint(10, 30),
                            is_available=True
                        )
                        time_slots_created += 1
                
                # Create reservations
                tables = list(Table.objects.filter(branch=branch))
                
                for _ in range(min(reservation_count // len(branches) // len(restaurants), 50)):
                    if not tables:
                        break
                    
                    customer = random.choice(customers)
                    table = random.choice(tables)
                    
                    # Random date within next 30 days
                    days_ahead = random.randint(1, 30)
                    reservation_date = timezone.now().date() + timedelta(days=days_ahead)
                    
                    # Random time between 12:00 and 21:00
                    hour = random.choice([12, 13, 14, 18, 19, 20, 21])
                    minute = random.choice([0, 15, 30, 45])
                    reservation_time = timezone.datetime.combine(
                        reservation_date, 
                        timezone.datetime.min.time().replace(hour=hour, minute=minute)
                    ).time()
                    
                    party_size = random.randint(1, min(10, table.capacity))
                    duration = random.choice([60, 90, 120])
                    
                    status = random.choice(['confirmed', 'pending', 'seated', 'completed', 'cancelled'])
                    
                    # Adjust status based on date
                    if reservation_date < timezone.now().date():
                        status = random.choice(['completed', 'cancelled', 'no_show'])
                    elif reservation_date == timezone.now().date():
                        if reservation_time < timezone.now().time():
                            status = random.choice(['completed', 'cancelled'])
                        else:
                            status = random.choice(['confirmed', 'pending'])
                    
                    reservation = Reservation.objects.create(
                        customer=customer,
                        restaurant=restaurant,
                        branch=branch,
                        table=table,
                        reservation_date=reservation_date,
                        reservation_time=reservation_time,
                        duration_minutes=duration,
                        party_size=party_size,
                        special_occasion=random.choice(['birthday', 'anniversary', 'business', 'date', 'family', 'none']),
                        special_requests=random.choice(['', 'Window seat please', 'High chair needed', 'Celebrating birthday', '']),
                        status=status,
                        created_at=timezone.now() - timedelta(days=random.randint(1, days_ahead))
                    )
                    
                    # Set appropriate timestamps based on status
                    if status == 'confirmed':
                        reservation.confirmation_sent = True
                    elif status == 'seated':
                        reservation.confirmation_sent = True
                        reservation.reminder_sent = True
                    elif status == 'completed':
                        reservation.confirmation_sent = True
                        reservation.reminder_sent = True
                    elif status == 'cancelled':
                        reservation.cancellation_reason = random.choice(['Changed mind', 'Emergency', 'Booking error'])
                    
                    reservation.save()
                    reservations_created += 1
        
        self.stdout.write(f"  ✅ Created {tables_created} tables")
        self.stdout.write(f"  ✅ Created {time_slots_created} time slots")
        self.stdout.write(f"  ✅ Created {reservations_created} reservations")