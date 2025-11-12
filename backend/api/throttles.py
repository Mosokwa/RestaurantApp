# throttles.py
from rest_framework.throttling import SimpleRateThrottle, AnonRateThrottle, UserRateThrottle
from django_ratelimit.decorators import ratelimit
from django_ratelimit.core import is_ratelimited
from django.core.cache import cache
from django.conf import settings
class AuthThrottle(SimpleRateThrottle):
    scope = 'auth'
    
    def get_cache_key(self, request, view):
        if request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)
        
        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }

class PasswordResetThrottle(SimpleRateThrottle):
    scope = 'password_reset'
    
    def get_cache_key(self, request, view):
        email = request.data.get('email', '')
        return self.cache_format % {
            'scope': self.scope,
            'ident': email
        }
    
class RateLimitExceeded(Exception):
    def __init__(self, wait_time=None):
        self.wait_time = wait_time
        super().__init__(f"Rate limit exceeded. Try again in {wait_time} seconds.")

class ProductionRateLimit:
    """
    Production-ready rate limiting with multiple strategies
    """
    
    def __init__(self, key=None, rate='5/m', method='POST', group=None):
        self.key = key or 'ip'
        self.rate = rate
        self.method = method
        self.group = group
    
    def parse_rate(self, rate):
        """
        Parse rate string (e.g., '5/m', '100/h', '10/s')
        """
        try:
            num, period = rate.split('/')
            num = int(num)
            
            if period == 's':
                return num, 1
            elif period == 'm':
                return num, 60
            elif period == 'h':
                return num, 60 * 60
            elif period == 'd':
                return num, 60 * 60 * 24
            else:
                return num, 60  # Default to minutes
        except (ValueError, AttributeError):
            return 5, 60  # Default fallback
    
    def get_cache_key(self, request, view):
        """
        Generate unique cache key for rate limiting
        """
        if self.key == 'ip':
            ident = self.get_client_ip(request)
        elif self.key == 'user':
            ident = request.user.pk if request.user.is_authenticated else self.get_client_ip(request)
        else:
            ident = self.key
        
        # Include view name for more specific rate limiting
        view_name = view.__class__.__name__
        
        return f"rl:{view_name}:{ident}:{self.method}"
    
    def get_client_ip(self, request):
        """
        Get client IP address with proper header checking
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
        return ip
    
    def is_rate_limited(self, request, view):
        """
        Check if request is rate limited
        """
        cache_key = self.get_cache_key(request, view)
        num_requests, period = self.parse_rate(self.rate)
        
        # Get current count
        current = cache.get(cache_key, 0)
        
        if current >= num_requests:
            # Calculate wait time
            ttl = cache.ttl(cache_key)
            return True, ttl if ttl else period
        
        return False, 0
    
    def increment_counter(self, request, view):
        """
        Increment rate limit counter
        """
        cache_key = self.get_cache_key(request, view)
        num_requests, period = self.parse_rate(self.rate)
        
        # Use atomic increment
        try:
            current = cache.incr(cache_key)
        except ValueError:
            # Key doesn't exist, set it
            cache.set(cache_key, 1, period)
            current = 1
        
        return current

    
class SocialAuthThrottle:
    """
    Production social authentication rate limiter
    """
    
    def __init__(self):
        self.burst_limiter = ProductionRateLimit(rate='5/m')  # 5 attempts per minute
        self.sustained_limiter = ProductionRateLimit(rate='50/h')  # 50 attempts per hour
        self.daily_limiter = ProductionRateLimit(rate='200/d')  # 200 attempts per day
    
    def check_rate_limit(self, request, view):
        """
        Check all rate limit tiers
        """
        limits = [
            self.burst_limiter.is_rate_limited(request, view),
            self.sustained_limiter.is_rate_limited(request, view),
            self.daily_limiter.is_rate_limited(request, view)
        ]
        
        for is_limited, wait_time in limits:
            if is_limited:
                return True, wait_time
        
        return False, 0
    
    def increment_counters(self, request, view):
        """
        Increment all rate limit counters
        """
        self.burst_limiter.increment_counter(request, view)
        self.sustained_limiter.increment_counter(request, view)
        self.daily_limiter.increment_counter(request, view)

# Decorator for easy use
def rate_limit_view(rate='5/m', key='ip', method='POST'):
    """
    Decorator to apply rate limiting to views
    """
    def decorator(view_func):
        def wrapped(request, *args, **kwargs):
            limiter = ProductionRateLimit(key=key, rate=rate, method=method)
            
            is_limited, wait_time = limiter.is_rate_limited(request, wrapped)
            if is_limited:
                from rest_framework.response import Response
                from rest_framework import status
                return Response({
                    'error': 'Rate limit exceeded',
                    'wait_time': wait_time,
                    'retry_after': wait_time
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            
            # Increment counter
            limiter.increment_counter(request, wrapped)
            
            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator

class BurstSocialAuthThrottle(SocialAuthThrottle):
    """
    More restrictive throttling for burst attempts
    """
    def get_rate(self):
        return '5/minute'

class SustainedSocialAuthThrottle(SocialAuthThrottle):
    """
    Less restrictive throttling for sustained attempts
    """
    def get_rate(self):
        return '100/hour'