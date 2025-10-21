from django.core.management.base import BaseCommand
from django.utils import timezone
from api.models import MenuItem, PopularitySnapshot
from datetime import timedelta

class Command(BaseCommand):
    help = 'Update popularity scores and create daily snapshots'

    def handle(self, *args, **options):
        self.stdout.write('Starting popularity score update...')
        
        updated_count = 0
        snapshot_count = 0
        
        # Update all menu items
        for menu_item in MenuItem.objects.select_related('category__restaurant').all():
            # Update popularity metrics
            menu_item.update_popularity_metrics()
            updated_count += 1
            
            # Create daily snapshot
            today = timezone.now().date()
            if not PopularitySnapshot.objects.filter(
                menu_item=menu_item, date_recorded=today
            ).exists():
                
                # Calculate rank within restaurant
                restaurant_items = MenuItem.objects.filter(
                    category__restaurant=menu_item.category.restaurant
                ).order_by('-popularity_score')
                
                rank = list(restaurant_items).index(menu_item) + 1
                
                PopularitySnapshot.objects.create(
                    menu_item=menu_item,
                    score=menu_item.popularity_score,
                    order_count=menu_item.order_count,
                    rank=rank
                )
                snapshot_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully updated {updated_count} items, created {snapshot_count} snapshots'
            )
        )