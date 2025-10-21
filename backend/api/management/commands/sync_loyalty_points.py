from django.core.management.base import BaseCommand
from django.db.models import Q
import logging
from api.models import Order
from api.services.loyalty_services import LoyaltyService

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Sync loyalty points for orders that should have received points but did not'

    def add_arguments(self, parser):
        parser.add_argument(
            '--order-id',
            type=int,
            help='Process a specific order ID',
        )
        parser.add_argument(
            '--restaurant-id',
            type=int,
            help='Process orders for a specific restaurant',
        )

    def handle(self, *args, **options):
        order_id = options.get('order_id')
        restaurant_id = options.get('restaurant_id')
        
        self.stdout.write("Starting loyalty points synchronization...")
        
        # Build query for eligible orders
        query = Q(status='delivered', loyalty_points_awarded=False)
        
        if order_id:
            query &= Q(order_id=order_id)
        
        if restaurant_id:
            query &= Q(restaurant_id=restaurant_id)
        
        eligible_orders = Order.objects.filter(query)
        total_orders = eligible_orders.count()
        
        self.stdout.write(f"Found {total_orders} eligible orders for points synchronization")
        
        processed = 0
        successful = 0
        failed = 0
        
        for order in eligible_orders:
            try:
                self.stdout.write(f"Processing order {order.order_id}...")
                success, message = LoyaltyService.award_order_points(order)
                
                if success:
                    successful += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"Successfully awarded points for order {order.order_id}")
                    )
                else:
                    failed += 1
                    self.stdout.write(
                        self.style.ERROR(f"Failed to award points for order {order.order_id}: {message}")
                    )
                
                processed += 1
                
            except Exception as e:
                failed += 1
                self.stdout.write(
                    self.style.ERROR(f"Error processing order {order.order_id}: {e}")
                )
                logger.error(f"Error processing order {order.order_id}: {e}")
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Sync completed: {processed} processed, {successful} successful, {failed} failed"
            )
        )