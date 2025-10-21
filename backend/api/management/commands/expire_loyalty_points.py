from django.core.management.base import BaseCommand
from django.utils import timezone
import logging
from api.services.loyalty_services import LoyaltyService

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Expire loyalty points that have reached their expiration date'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be expired without actually expiring points',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write(f"{'DRY RUN: ' if dry_run else ''}Starting loyalty points expiration...")
        
        if dry_run:
            from api.models import PointsTransaction
            expired_count = PointsTransaction.objects.filter(
                expires_at__lte=timezone.now(),
                is_active=True,
                points__gt=0
            ).count()
            
            self.stdout.write(
                self.style.WARNING(f"DRY RUN: Would expire {expired_count} points transactions")
            )
        else:
            expired_count = LoyaltyService.expire_points()
            if expired_count > 0:
                self.stdout.write(
                    self.style.SUCCESS(f"Successfully expired {expired_count} points transactions")
                )
            else:
                self.stdout.write("No points to expire")
        
        self.stdout.write("Loyalty points expiration completed")