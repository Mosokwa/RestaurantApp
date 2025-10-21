from .models import Customer

def create_user_profile(backend, user, response, *args, **kwargs):
    """
    Pipeline function to create user profile after social authentication
    """
    if backend.name == 'google-oauth2':
        # Handle Google authentication
        if user.user_type == 'customer' and not hasattr(user, 'customer_profile'):
            Customer.objects.create(user=user)
    
    elif backend.name == 'facebook':
        # Handle Facebook authentication
        if user.user_type == 'customer' and not hasattr(user, 'customer_profile'):
            Customer.objects.create(user=user)
    
    return {'user': user}