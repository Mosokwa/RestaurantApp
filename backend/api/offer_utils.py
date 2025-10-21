from django.utils import timezone
from datetime import datetime, timedelta

def get_todays_featured_offers():
    """Get all featured offers valid for today"""
    from .models import SpecialOffer
    
    today = timezone.now()
    return SpecialOffer.objects.filter(
        is_active=True,
        is_featured=True,
        valid_from__lte=today,
        valid_until__gte=today
    ).extra(
        where=["""
            (valid_days = '[]' OR 
            valid_days::jsonb ? LOWER(TO_CHAR(NOW(), 'day')))
        """]
    ).order_by('-display_priority', '-created_at')

def get_weekly_offer_schedule(restaurant=None):
    """Get weekly schedule of offers for a restaurant or all restaurants"""
    from .models import SpecialOffer
    
    days_of_week = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    schedule = {}
    
    for day in days_of_week:
        offers_query = SpecialOffer.objects.filter(
            is_active=True,
            valid_days__contains=[day],
            valid_from__lte=timezone.now(),
            valid_until__gte=timezone.now()
        )
        
        if restaurant:
            offers_query = offers_query.filter(restaurant=restaurant)
        
        schedule[day] = offers_query.order_by('-display_priority')
    
    return schedule