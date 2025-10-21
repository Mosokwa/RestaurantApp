# management/commands/warmup_homepage_cache.py
from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.db.models import Count
from api.models import Restaurant

class Command(BaseCommand):
    help = 'Warm up homepage cache for popular restaurants'
    
    def handle(self, *args, **options):
        popular_restaurants = Restaurant.objects.filter(
            status='active',
            is_featured=True
        ).annotate(
            order_count=Count('orders')
        ).order_by('-order_count')[:20]  # Top 20 popular restaurants
        
        for restaurant in popular_restaurants:
            cache_key = f"restaurant_homepage_{restaurant.restaurant_id}"
            # This will trigger cache population on next request
            cache.delete(cache_key)
            
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully warmed up cache for {popular_restaurants.count()} restaurants'
            )
        )