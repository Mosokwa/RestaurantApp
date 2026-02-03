# management/commands/create_reservations.py
from django.core.management.base import BaseCommand
from api.models.reservation_models import Reservation, Table, TimeSlot
from api.models.restaurant_models import Restaurant, Branch
from api.models.user_models import Customer
import random
from django.utils import timezone
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Create reservation data'
    
    def handle(self, *args, **options):
        customers = list(Customer.objects.all()[:50])
        restaurants = list(Restaurant.objects.filter(reservation_enabled=True)[:20])
        
        if not restaurants:
            self.stdout.write(self.style.WARNING('No restaurants with reservation enabled found'))
            return
        
        reservations_created = 0
        tables_created = 0
        
        for restaurant in restaurants:
            branch = restaurant.branches.first()
            if not branch:
                continue
            
            # Create tables for this restaurant
            num_tables = random.randint(5, 15)  # Reduced from 10-30
            for i in range(num_tables):
                table_number = i + 1
                capacity = random.choice([2, 2, 2, 4, 4, 4, 6, 8])
                
                # Check if table already exists
                if not Table.objects.filter(restaurant=restaurant, table_number=table_number).exists():
                    Table.objects.create(
                        restaurant=restaurant,
                        branch=branch,
                        table_number=str(table_number),
                        table_name=random.choice([None, f'Table {table_number}', f'Booth {table_number}']),
                        capacity=capacity,
                        table_type=random.choice(['indoor', 'outdoor', 'booth', 'bar']),
                        is_available=True,
                        min_party_size=2 if capacity <= 4 else 4,
                        max_party_size=capacity,
                        position_x=random.randint(0, 100),
                        position_y=random.randint(0, 100)
                    )
                    tables_created += 1
            
            # Create reservations
            num_reservations = random.randint(10, 40)  # Reduced from 20-100
            tables = list(Table.objects.filter(restaurant=restaurant))
            
            if not tables:
                continue
            
            # Track created reservations per day to avoid duplicates
            reservations_per_date = {}
            
            for _ in range(num_reservations):
                customer = random.choice(customers)
                table = random.choice(tables)
                
                # Create reservation date (past 30 days to future 30 days)
                days_offset = random.randint(-30, 30)
                reservation_date = timezone.now().date() + timedelta(days=days_offset)
                
                # Generate unique time for this date and table
                date_key = f"{reservation_date}_{table.table_id}"
                if date_key not in reservations_per_date:
                    reservations_per_date[date_key] = []
                
                # Try different times until we find an available slot
                max_attempts = 10
                for attempt in range(max_attempts):
                    # Generate random time between 11:00 and 21:00
                    hour = random.randint(11, 20)
                    minute = random.choice([0, 15, 30, 45])
                    reservation_time = datetime.strptime(f'{hour}:{minute:02d}', '%H:%M').time()
                    
                    # Check if this time is already taken for this table on this date
                    existing_reservation = Reservation.objects.filter(
                        restaurant=restaurant,
                        table=table,
                        reservation_date=reservation_date,
                        reservation_time=reservation_time,
                        status__in=['confirmed', 'pending', 'seated']
                    ).exists()
                    
                    if not existing_reservation:
                        # Check if time is in our tracked list
                        if reservation_time not in reservations_per_date[date_key]:
                            break
                
                if attempt == max_attempts - 1:
                    continue  # Skip if we couldn't find a unique time
                
                reservations_per_date[date_key].append(reservation_time)
                
                party_size = random.randint(2, min(8, table.capacity))
                duration_minutes = random.choice([60, 90, 120])
                
                status_choices = ['confirmed', 'confirmed', 'confirmed', 'pending', 'completed', 'cancelled']
                status = random.choice(status_choices)
                
                reservation = Reservation.objects.create(
                    customer=customer,
                    restaurant=restaurant,
                    branch=branch,
                    table=table,
                    reservation_date=reservation_date,
                    reservation_time=reservation_time,
                    duration_minutes=duration_minutes,
                    party_size=party_size,
                    special_occasion=random.choice(['none', 'birthday', 'anniversary', 'business', 'date', 'family']),
                    special_requests=random.choice(['', 'Window seat please', 'Quiet area', 'High chair needed', '']),
                    status=status,
                    confirmation_sent=status in ['confirmed', 'seated', 'completed'],
                    reminder_sent=random.choice([True, False]) if status in ['confirmed', 'seated'] else False
                )
                
                # Create time slot if reservation is confirmed
                if status in ['confirmed', 'seated', 'completed']:
                    end_hour = hour + (duration_minutes // 60)
                    end_minute = minute + (duration_minutes % 60)
                    if end_minute >= 60:
                        end_hour += 1
                        end_minute -= 60
                    
                    end_time = datetime.strptime(f'{end_hour}:{end_minute:02d}', '%H:%M').time()
                    
                    # Check if time slot already exists
                    if not TimeSlot.objects.filter(
                        branch=branch,
                        date=reservation_date,
                        start_time=reservation_time
                    ).exists():
                        TimeSlot.objects.create(
                            restaurant=restaurant,
                            branch=branch,
                            date=reservation_date,
                            start_time=reservation_time,
                            end_time=end_time,
                            max_capacity=table.capacity,
                            reserved_count=1,
                            is_available=False
                        )
                
                reservations_created += 1
        
        self.stdout.write(self.style.SUCCESS(f'Created {tables_created} tables and {reservations_created} reservations'))