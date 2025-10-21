# throttles.py
from rest_framework.throttling import SimpleRateThrottle

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