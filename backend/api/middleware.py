# middleware.py
import logging
from django.utils import timezone
from django.http import JsonResponse
from rest_framework import status

logger = logging.getLogger('api.auth')

class AuthLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Log authentication events
        if hasattr(request, 'user') and request.user.is_authenticated:
            if not hasattr(request, '_auth_logged'):
                logger.info(
                    f"User {request.user.username} ({request.user.id}) "
                    f"accessed {request.path} from {request.META.get('REMOTE_ADDR')} "
                    f"at {timezone.now()}"
                )
                request._auth_logged = True
        
        return response
    
    
class OwnerPermissionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Skip for non-owner routes
        if not request.path.startswith('/api/owner/'):
            return None
        
        # Check authentication
        if not request.user.is_authenticated:
            return JsonResponse(
                {'error': 'Authentication required'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Check if user is an owner
        if not request.user.user_type == 'owner':
            return JsonResponse(
                {'error': 'Access restricted to restaurant owners'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        return None