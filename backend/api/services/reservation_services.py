# services.py
from django.utils import timezone
from django.db.models import Q, F
from datetime import timedelta, datetime
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)

class ReservationService:
    
    @staticmethod
    def find_available_tables(restaurant, branch, reservation_date, reservation_time, duration_minutes, party_size):
        """Find all available tables for given criteria"""
        from ..models import Table, Reservation
        
        # Convert to datetime for comparison
        reservation_datetime = timezone.make_aware(
            datetime.combine(reservation_date, reservation_time)
        )
        reservation_end = reservation_datetime + timedelta(minutes=duration_minutes)
        
        # Get all suitable tables
        suitable_tables = Table.objects.filter(
            restaurant=restaurant,
            branch=branch,
            is_available=True,
            min_party_size__lte=party_size,
            max_party_size__gte=party_size
        )
        
        available_tables = []
        for table in suitable_tables:
            if ReservationService.is_table_available(
                table, reservation_date, reservation_time, duration_minutes
            ):
                available_tables.append(table)
        
        return available_tables
    
    @staticmethod
    def is_table_available(table, reservation_date, reservation_time, duration_minutes):
        """Check if a specific table is available"""
        from ..models import Reservation
        
        reservation_datetime = timezone.make_aware(
            datetime.combine(reservation_date, reservation_time)
        )
        reservation_end = reservation_datetime + timedelta(minutes=duration_minutes)
        
        # Find overlapping reservations
        overlapping = Reservation.objects.filter(
            table=table,
            reservation_date=reservation_date,
            status__in=['confirmed', 'pending', 'seated']
        ).exclude(
            Q(reservation_time__gte=reservation_end.time()) |
            Q(
                F('reservation_time') + 
                F('duration_minutes') * timedelta(minutes=1) <= reservation_datetime.time()
            )
        )
        
        return not overlapping.exists()
    
    @staticmethod
    def generate_time_slots(restaurant, branch, date, party_size):
        """Generate available time slots for a restaurant on a specific date"""
        from ..models import TimeSlot
        
        # Get operating hours for the day
        day_name = date.strftime('%A').lower()
        operating_hours = branch.operating_hours.get(day_name, {})
        
        if not operating_hours:
            return []
        
        open_time = datetime.strptime(operating_hours['open'], '%H:%M').time()
        close_time = datetime.strptime(operating_hours['close'], '%H:%M').time()
        
        # Generate slots based on restaurant's interval
        slots = []
        current_time = open_time
        
        while current_time < close_time:
            slot_end = (datetime.combine(date, current_time) + 
                       timedelta(minutes=restaurant.time_slot_interval)).time()
            
            # Check if any tables are available for this slot
            available_tables = ReservationService.find_available_tables(
                restaurant, branch, date, current_time, 
                restaurant.time_slot_interval, party_size
            )
            
            if available_tables:
                total_capacity = sum(table.capacity for table in available_tables)
                slots.append({
                    'start_time': current_time.strftime('%H:%M'),
                    'end_time': slot_end.strftime('%H:%M'),
                    'available_tables': len(available_tables),
                    'total_capacity': total_capacity,
                    'is_available': True
                })
            else:
                slots.append({
                    'start_time': current_time.strftime('%H:%M'),
                    'end_time': slot_end.strftime('%H:%M'),
                    'available_tables': 0,
                    'total_capacity': 0,
                    'is_available': False
                })
            
            # Move to next slot
            current_time = slot_end
        
        return slots
    
    @staticmethod
    def validate_reservation_request(restaurant, branch, reservation_date, reservation_time, duration_minutes, party_size):
        """Comprehensive validation for reservation request"""
        from django.core.exceptions import ValidationError
        
        # Check restaurant rules
        reservation_datetime = timezone.make_aware(
            datetime.combine(reservation_date, reservation_time)
        )
        
        is_valid, message = restaurant.can_accept_reservation(party_size, reservation_datetime)
        if not is_valid:
            raise ValidationError(message)
        
        # Check branch operating hours
        day_name = reservation_date.strftime('%A').lower()
        operating_hours = branch.operating_hours.get(day_name, {})
        
        if not operating_hours:
            raise ValidationError(f"Branch is closed on {day_name}")
        
        # Check if within operating hours
        open_time = datetime.strptime(operating_hours['open'], '%H:%M').time()
        close_time = datetime.strptime(operating_hours['close'], '%H:%M').time()
        reservation_end = (datetime.combine(reservation_date, reservation_time) + 
                          timedelta(minutes=duration_minutes)).time()
        
        if not (open_time <= reservation_time <= close_time and
                open_time <= reservation_end <= close_time):
            raise ValidationError("Reservation time must be within operating hours")
        
        # Check duration is allowed
        allowed_durations = restaurant.get_available_durations()
        if duration_minutes not in allowed_durations:
            raise ValidationError(f"Duration must be one of: {allowed_durations} minutes")
        
        return True
    
    @staticmethod
    def auto_assign_table(restaurant, branch, reservation_date, reservation_time, duration_minutes, party_size):
        """Automatically assign the best available table with complete prioritization logic"""
        available_tables = ReservationService.find_available_tables(
            restaurant, branch, reservation_date, reservation_time, duration_minutes, party_size
        )
        
        if not available_tables:
            return None
        
        # COMPLETE PRIORITIZATION LOGIC:
        # 1. First priority: Tables with exact capacity match
        exact_match_tables = [t for t in available_tables if t.capacity == party_size]
        if exact_match_tables:
            # Among exact matches, prefer indoor tables, then by table number
            best_table = min(exact_match_tables, 
                key=lambda t: (
                    0 if t.table_type == 'indoor' else 1,  # Prefer indoor
                    t.table_number  # Then by table number for consistency
                )
            )
            return best_table
        
        # 2. Second priority: Tables with smallest adequate capacity (but not too large)
        # We want the smallest table that can accommodate the party, but avoid tables that are too large
        adequate_tables = [t for t in available_tables if t.capacity >= party_size]
        if adequate_tables:
            # Calculate a score that balances capacity fit and table type preference
            type_priority = {'indoor': 0, 'outdoor': 1, 'booth': 2, 'bar': 3, 'private': 4}
            
            def calculate_table_score(table):
                # Capacity score: lower is better, but penalize tables that are too large
                capacity_diff = table.capacity - party_size
                capacity_score = capacity_diff * 10  # Base penalty for extra capacity
                
                # Heavy penalty for tables that are way too large (more than 4 extra seats)
                if capacity_diff > 4:
                    capacity_score += 100
                
                # Table type score
                type_score = type_priority.get(table.table_type, 5)
                
                # Special consideration for private rooms - only if party size justifies it
                if table.table_type == 'private' and party_size < 6:
                    type_score += 10  # Penalize private rooms for small parties
                
                return (capacity_score, type_score, table.table_number)
            
            best_table = min(adequate_tables, key=calculate_table_score)
            return best_table
        
        # 3. If no single table can accommodate, check for combining tables
        # This is more complex and might require manual assignment
        # For now, return the largest available table
        largest_table = max(available_tables, key=lambda t: t.capacity)
        if largest_table.capacity >= party_size - 2:  # Allow slight overflow
            return largest_table
        
        return None  # No suitable table found
    
    @staticmethod
    def get_restaurant_availability_summary(restaurant, start_date, end_date, party_size=2):
        """Get availability summary for a restaurant over a date range"""
        from collections import defaultdict
        import calendar
        
        availability_summary = defaultdict(list)
        
        current_date = start_date
        while current_date <= end_date:
            day_name = current_date.strftime('%A').lower()
            
            # Check each branch
            for branch in restaurant.branches.filter(is_active=True):
                operating_hours = branch.operating_hours.get(day_name, {})
                if operating_hours:
                    # Generate time slots for this day
                    time_slots = ReservationService.generate_time_slots(
                        restaurant, branch, current_date, party_size
                    )
                    
                    # Count available slots
                    available_slots = [slot for slot in time_slots if slot['is_available']]
                    
                    availability_summary[current_date].append({
                        'branch_id': branch.branch_id,
                        'branch_name': str(branch.address),
                        'available_slots': len(available_slots),
                        'total_slots': len(time_slots),
                        'first_available_time': available_slots[0]['start_time'] if available_slots else None,
                        'last_available_time': available_slots[-1]['start_time'] if available_slots else None
                    })
            
            current_date += timedelta(days=1)
        
        return dict(availability_summary)
    
    @staticmethod
    def calculate_restaurant_occupancy(restaurant, date):
        """Calculate occupancy rate for a restaurant on a specific date"""
        from ..models import Reservation, Table
        
        # Get all reservations for the date
        reservations = Reservation.objects.filter(
            restaurant=restaurant,
            reservation_date=date,
            status__in=['confirmed', 'seated']
        )
        
        # Get total table capacity
        total_capacity = sum(
            table.capacity for table in Table.objects.filter(
                restaurant=restaurant,
                is_available=True
            )
        )
        
        if total_capacity == 0:
            return 0.0
        
        # Calculate total reserved capacity
        reserved_capacity = sum(reservation.party_size for reservation in reservations)
        
        # Calculate occupancy rate
        occupancy_rate = (reserved_capacity / total_capacity) * 100
        
        return round(occupancy_rate, 2)

class NotificationService:
    
    @staticmethod
    def send_reservation_confirmation(reservation):
        """Send reservation confirmation email/SMS"""
        from django.core.mail import send_mail
        from django.conf import settings
        from django.template.loader import render_to_string
        
        try:
            subject = f"Reservation Confirmation - {reservation.restaurant.name}"
            
            # HTML email template
            html_message = render_to_string('emails/reservation_confirmation.html', {
                'reservation': reservation,
                'customer': reservation.customer,
                'restaurant': reservation.restaurant
            })
            
            text_message = f"""
            Dear {reservation.customer.user.get_full_name() or reservation.customer.user.username},
            
            Your reservation has been confirmed!
            
            Reservation Details:
            - Restaurant: {reservation.restaurant.name}
            - Date: {reservation.reservation_date}
            - Time: {reservation.reservation_time}
            - Party Size: {reservation.party_size}
            - Reservation Code: {reservation.reservation_code}
            - Table: {reservation.table.table_number if reservation.table else 'To be assigned'}
            
            Thank you for choosing us!
            """
            
            send_mail(
                subject=subject,
                message=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[reservation.customer.user.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            reservation.confirmation_sent = True
            reservation.save()
            
            logger.info(f"Confirmation sent for reservation {reservation.reservation_code}")
            
        except Exception as e:
            logger.error(f"Failed to send confirmation email: {str(e)}")
    
    @staticmethod
    def send_reservation_reminder(reservation):
        """Send reservation reminder 24 hours before - COMPLETE IMPLEMENTATION"""
        from django.core.mail import send_mail
        from django.conf import settings
        from django.template.loader import render_to_string
        
        try:
            # Check if reminder was already sent
            if reservation.reminder_sent:
                logger.info(f"Reminder already sent for reservation {reservation.reservation_code}")
                return
            
            subject = f"Reservation Reminder - {reservation.restaurant.name}"
            
            # HTML email template for reminder
            html_message = render_to_string('emails/reservation_reminder.html', {
                'reservation': reservation,
                'customer': reservation.customer,
                'restaurant': reservation.restaurant
            })
            
            text_message = f"""
            Dear {reservation.customer.user.get_full_name() or reservation.customer.user.username},
            
            This is a friendly reminder about your upcoming reservation.
            
            Reservation Details:
            - Restaurant: {reservation.restaurant.name}
            - Date: {reservation.reservation_date}
            - Time: {reservation.reservation_time}
            - Party Size: {reservation.party_size}
            - Reservation Code: {reservation.reservation_code}
            - Table: {reservation.table.table_number if reservation.table else 'To be assigned'}
            
            Address: {reservation.branch.address.street_address}, {reservation.branch.address.city}
            
            Please contact us at {reservation.restaurant.phone_number} if you need to make any changes.
            
            We look forward to serving you!
            """
            
            send_mail(
                subject=subject,
                message=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[reservation.customer.user.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            reservation.reminder_sent = True
            reservation.save()
            
            logger.info(f"Reminder sent for reservation {reservation.reservation_code}")
            
        except Exception as e:
            logger.error(f"Failed to send reminder email: {str(e)}")
    
    @staticmethod
    def send_reservation_cancellation(reservation, reason=""):
        """Send cancellation notification - COMPLETE IMPLEMENTATION"""
        from django.core.mail import send_mail
        from django.conf import settings
        from django.template.loader import render_to_string
        
        try:
            subject = f"Reservation Cancelled - {reservation.restaurant.name}"
            
            # HTML email template for cancellation
            html_message = render_to_string('emails/reservation_cancellation.html', {
                'reservation': reservation,
                'customer': reservation.customer,
                'restaurant': reservation.restaurant,
                'reason': reason
            })
            
            text_message = f"""
            Dear {reservation.customer.user.get_full_name() or reservation.customer.user.username},
            
            Your reservation has been cancelled.
            
            Reservation Details:
            - Restaurant: {reservation.restaurant.name}
            - Date: {reservation.reservation_date}
            - Time: {reservation.reservation_time}
            - Reservation Code: {reservation.reservation_code}
            - Reason: {reason or 'Not specified'}
            
            We hope to see you another time!
            
            If you have any questions, please contact us at {reservation.restaurant.phone_number}.
            """
            
            send_mail(
                subject=subject,
                message=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[reservation.customer.user.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            logger.info(f"Cancellation notification sent for reservation {reservation.reservation_code}")
            
        except Exception as e:
            logger.error(f"Failed to send cancellation email: {str(e)}")
    
    @staticmethod
    def send_reservation_modification(reservation, old_date, old_time, old_table):
        """Send notification when reservation is modified"""
        from django.core.mail import send_mail
        from django.conf import settings
        from django.template.loader import render_to_string
        
        try:
            subject = f"Reservation Updated - {reservation.restaurant.name}"
            
            html_message = render_to_string('emails/reservation_modification.html', {
                'reservation': reservation,
                'customer': reservation.customer,
                'restaurant': reservation.restaurant,
                'old_date': old_date,
                'old_time': old_time,
                'old_table': old_table
            })
            
            text_message = f"""
            Dear {reservation.customer.user.get_full_name() or reservation.customer.user.username},
            
            Your reservation has been updated.
            
            Previous Reservation:
            - Date: {old_date}
            - Time: {old_time}
            - Table: {old_table.table_number if old_table else 'Not assigned'}
            
            Updated Reservation:
            - Date: {reservation.reservation_date}
            - Time: {reservation.reservation_time}
            - Table: {reservation.table.table_number if reservation.table else 'To be assigned'}
            - Reservation Code: {reservation.reservation_code}
            
            If you did not request this change, please contact us immediately at {reservation.restaurant.phone_number}.
            """
            
            send_mail(
                subject=subject,
                message=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[reservation.customer.user.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            logger.info(f"Modification notification sent for reservation {reservation.reservation_code}")
            
        except Exception as e:
            logger.error(f"Failed to send modification email: {str(e)}")
    
    @staticmethod
    def send_waitlist_notification(reservation, available_tables):
        """Send notification when a waitlisted reservation becomes available"""
        from django.core.mail import send_mail
        from django.conf import settings
        
        try:
            subject = f"Table Available - {reservation.restaurant.name}"
            
            table_options = "\n".join([f"- Table {table.table_number} ({table.capacity} people)" 
                                     for table in available_tables])
            
            text_message = f"""
            Dear {reservation.customer.user.get_full_name() or reservation.customer.user.username},
            
            Great news! A table has become available at {reservation.restaurant.name}.
            
            We have the following tables available for your party of {reservation.party_size}:
            {table_options}
            
            Please click here to confirm your reservation: [LINK_TO_CONFIRM]
            
            This table will be held for you for the next 30 minutes.
            
            Reservation Details:
            - Date: {reservation.reservation_date}
            - Time: {reservation.reservation_time}
            - Reservation Code: {reservation.reservation_code}
            
            If we don't hear from you within 30 minutes, we'll release the table to other guests.
            """
            
            send_mail(
                subject=subject,
                message=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[reservation.customer.user.email],
                fail_silently=False,
            )
            
            logger.info(f"Waitlist notification sent for reservation {reservation.reservation_code}")
            
        except Exception as e:
            logger.error(f"Failed to send waitlist notification: {str(e)}")