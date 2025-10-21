# management/commands/send_reservation_reminders.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, datetime
from api.models import Reservation
from api.services.reservation_services import NotificationService

class Command(BaseCommand):
    help = 'Send reservation reminders 24 hours before reservation time'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be sent without actually sending',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        tomorrow = timezone.now().date() + timedelta(days=1)
        now = timezone.now()
        
        # Get reservations for tomorrow that haven't been reminded
        reservations = Reservation.objects.filter(
            reservation_date=tomorrow,
            reminder_sent=False,
            status__in=['confirmed', 'pending']
        ).select_related('customer__user', 'restaurant', 'branch', 'table')
        
        reminder_count = 0
        errors = []
        
        for reservation in reservations:
            try:
                # Calculate the exact reminder time (24 hours before reservation)
                reservation_datetime = timezone.make_aware(
                    datetime.combine(reservation.reservation_date, reservation.reservation_time)
                )
                reminder_time = reservation_datetime - timedelta(hours=24)
                
                # Only send if we're within 1 hour of the ideal reminder time
                if abs((reminder_time - now).total_seconds()) <= 3600:
                    if dry_run:
                        self.stdout.write(
                            self.style.WARNING(f"DRY RUN: Would send reminder for {reservation.reservation_code}")
                        )
                    else:
                        NotificationService.send_reservation_reminder(reservation)
                        self.stdout.write(
                            self.style.SUCCESS(f"Sent reminder for {reservation.reservation_code}")
                        )
                    
                    reminder_count += 1
                else:
                    self.stdout.write(
                        f"Skipping {reservation.reservation_code} - not within reminder window"
                    )
                    
            except Exception as e:
                error_msg = f"Failed to send reminder for {reservation.reservation_code}: {str(e)}"
                errors.append(error_msg)
                self.stdout.write(self.style.ERROR(error_msg))
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f"DRY RUN: Would have sent {reminder_count} reservation reminders")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully sent {reminder_count} reservation reminders')
            )
        
        if errors:
            self.stdout.write(
                self.style.ERROR(f'Encountered {len(errors)} errors during reminder sending')
            )