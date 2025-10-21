from rest_framework import permissions
from rest_framework.permissions import BasePermission

class CanReviewRestaurant(permissions.BasePermission):
    """
    Permission to check if user can review a restaurant
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        if not hasattr(request.user, 'customer_profile'):
            return False
        
        return True

class IsRestaurantOwnerOrStaff(permissions.BasePermission):
    """
    Permission to check if user is restaurant owner or staff
    """
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'restaurant'):
            restaurant = obj.restaurant
        else:
            restaurant = obj
        
        return (request.user == restaurant.owner or 
                restaurant.staff_members.filter(user=request.user).exists())

class CanModerateReviews(permissions.BasePermission):
    """
    Permission to check if user can moderate reviews
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        restaurant_id = view.kwargs.get('restaurant_id')
        if not restaurant_id:
            return False
        
        try:
            from .models import Restaurant
            restaurant = Restaurant.objects.get(pk=restaurant_id)
            
            return (request.user == restaurant.owner or 
                    restaurant.staff_members.filter(
                        user=request.user, 
                        can_manage_orders=True
                    ).exists())
        except Restaurant.DoesNotExist:
            return False

class HasOrderedFromRestaurant(permissions.BasePermission):
    """
    Permission to check if user has ordered from the restaurant
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated or not hasattr(request.user, 'customer_profile'):
            return False
        
        restaurant_id = view.kwargs.get('restaurant_id')
        if restaurant_id:
            from .models import Order
            customer = request.user.customer_profile
            return Order.objects.filter(
                customer=customer,
                restaurant_id=restaurant_id,
                status='delivered'
            ).exists()
        
        return True
    
class IsRestaurantOwner(BasePermission):
    """
    Custom permission to only allow restaurant owners to access their data.
    """
    
    def has_permission(self, request, view):
        # Check if user is authenticated and is a restaurant owner
        return (request.user and 
                request.user.is_authenticated and 
                request.user.user_type == 'owner')
    
    def has_object_permission(self, request, view, obj):
        """
        Check if the user is the owner of the restaurant related to the object.
        """
        # Handle different object types
        if hasattr(obj, 'restaurant'):
            # Object has a direct restaurant relationship (Order, Table, etc.)
            return obj.restaurant.owner == request.user
        
        elif hasattr(obj, 'owner'):
            # Object is a Restaurant itself
            return obj.owner == request.user
        
        elif hasattr(obj, 'organized_group_orders'):
            # Object is a Customer but we're checking their organized orders
            # This is handled in the view's get_queryset
            return True
        
        # Default deny
        return False

class IsCustomer(BasePermission):
    """
    Custom permission to only allow customers to access their data.
    """
    
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                request.user.user_type == 'customer')
    
    def has_object_permission(self, request, view, obj):
        # For orders, reservations, etc. owned by the customer
        if hasattr(obj, 'customer'):
            return obj.customer.user == request.user
        
        # For customer profile itself
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False

class IsStaffMember(BasePermission):
    """
    Custom permission for restaurant staff members.
    """
    
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                request.user.user_type == 'staff')
    
    def has_object_permission(self, request, view, obj):
        # Staff can access data for restaurants they work at
        if hasattr(obj, 'restaurant'):
            # Check if staff member works at this restaurant
            from .models import RestaurantStaff
            return RestaurantStaff.objects.filter(
                user=request.user,
                restaurant=obj.restaurant
            ).exists()
        
        return False

class IsOwnerOrStaff(BasePermission):
    """
    Permission for both restaurant owners and their staff.
    """
    
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                request.user.user_type in ['owner', 'staff'])
    
    def has_object_permission(self, request, view, obj):
        # Restaurant owner has full access
        if hasattr(obj, 'restaurant'):
            if obj.restaurant.owner == request.user:
                return True
            
            # Staff members can access if they work at the restaurant
            if request.user.user_type == 'staff':
                from .models import RestaurantStaff
                return RestaurantStaff.objects.filter(
                    user=request.user,
                    restaurant=obj.restaurant
                ).exists()
        
        return False

class IsKitchenStaff(BasePermission):
    """
    Permission specifically for kitchen staff to update preparation status.
    """
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Kitchen staff can be either staff users or owners
        if request.user.user_type == 'owner':
            return True
        
        if request.user.user_type == 'staff':
            # Check if staff is assigned to any kitchen station
            from .models import KitchenStation
            return KitchenStation.objects.filter(
                assigned_staff__user=request.user
            ).exists()
        
        return False
    
    def has_object_permission(self, request, view, obj):
        # For order items, check if staff is assigned to the station
        if hasattr(obj, 'preparation_info') and obj.preparation_info.assigned_station:
            station = obj.preparation_info.assigned_station
            return station.assigned_staff.filter(user=request.user).exists()
        
        # For stations themselves
        if hasattr(obj, 'assigned_staff'):
            return obj.assigned_staff.filter(user=request.user).exists()
        
        return False

class IsPOSWebhook(permissions.BasePermission):
    """
    Permission for POS webhook endpoints - no authentication required but signature verification.
    """
    
    def has_permission(self, request, view):
        # Webhook endpoints should verify signatures instead of using traditional auth
        return True

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permission for admin users to have write access, others read-only.
    """
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner` attribute.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Instance must have an attribute named `owner`.
        return obj.owner == request.user