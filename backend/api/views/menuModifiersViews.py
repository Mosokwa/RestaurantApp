from rest_framework import status, generics, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from django.core.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import ValidationError
from ..models import ItemModifier, ItemModifierGroup, MenuItemModifier, Restaurant, MenuItem
from ..serializers import (
    ItemModifierGroupSerializer, ItemModifierSerializer, MenuItemModifierSerializer
)

class ItemModifierGroupListView(generics.ListCreateAPIView):
    serializer_class = ItemModifierGroupSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']

    def get_queryset(self):
        user = self.request.user
        
        # Restaurant owners/staff can see modifier groups for their restaurants
        if user.user_type in ['owner', 'staff']:
            if user.user_type == 'owner':
                restaurant_ids = Restaurant.objects.filter(owner=user).values_list('restaurant_id', flat=True)
            else:
                restaurant_ids = [user.staff_profile.restaurant.restaurant_id]
            
            # Get modifier groups used by menu items in user's restaurants
            return ItemModifierGroup.objects.filter(
                menuitemmodifier__menu_item__category__restaurant_id__in=restaurant_ids
            ).distinct()
        
        # Admins can see all modifier groups
        elif user.user_type == 'admin':
            return ItemModifierGroup.objects.all()
        
        return ItemModifierGroup.objects.none()

    def perform_create(self, serializer):
        # Any authenticated user can create modifier groups (they'll be linked via menu items)
        serializer.save()

class ItemModifierGroupDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ItemModifierGroup.objects.all()
    serializer_class = ItemModifierGroupSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        
        if user.user_type in ['owner', 'staff']:
            if user.user_type == 'owner':
                restaurant_ids = Restaurant.objects.filter(owner=user).values_list('restaurant_id', flat=True)
            else:
                restaurant_ids = [user.staff_profile.restaurant.restaurant_id]
            
            return ItemModifierGroup.objects.filter(
                menuitemmodifier__menu_item__category__restaurant_id__in=restaurant_ids
            ).distinct()
        
        elif user.user_type == 'admin':
            return ItemModifierGroup.objects.all()
        
        return ItemModifierGroup.objects.none()
    
class ItemModifierListView(generics.ListCreateAPIView):
    serializer_class = ItemModifierSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['name', 'description']
    filterset_fields = ['modifier_group', 'is_available']

    def get_queryset(self):
        user = self.request.user
        modifier_group_id = self.request.query_params.get('modifier_group')
        
        queryset = ItemModifier.objects.select_related('modifier_group')
        
        if user.user_type in ['owner', 'staff']:
            if user.user_type == 'owner':
                restaurant_ids = Restaurant.objects.filter(owner=user).values_list('restaurant_id', flat=True)
            else:
                restaurant_ids = [user.staff_profile.restaurant.restaurant_id]
            
            # Filter modifiers that belong to groups used in user's restaurants
            queryset = queryset.filter(
                modifier_group__menuitemmodifier__menu_item__category__restaurant_id__in=restaurant_ids
            ).distinct()
        
        elif user.user_type != 'admin':
            queryset = ItemModifier.objects.none()
        
        # Filter by modifier group if provided
        if modifier_group_id:
            queryset = queryset.filter(modifier_group_id=modifier_group_id)
        
        return queryset

    def perform_create(self, serializer):
        modifier_group_id = self.request.data.get('modifier_group')
        
        if modifier_group_id:
            try:
                modifier_group = ItemModifierGroup.objects.get(pk=modifier_group_id)
                # Validate user has access to this modifier group's restaurant
                user = self.request.user
                if user.user_type in ['owner', 'staff']:
                    if user.user_type == 'owner':
                        has_access = modifier_group.menuitemmodifier.filter(
                            menu_item__category__restaurant__owner=user
                        ).exists()
                    else:
                        has_access = modifier_group.menuitemmodifier.filter(
                            menu_item__category__restaurant=user.staff_profile.restaurant
                        ).exists()
                    
                    if not has_access and user.user_type != 'admin':
                        raise PermissionDenied("You don't have permission to add modifiers to this group")
                
                serializer.save(modifier_group=modifier_group)
                return
            except ItemModifierGroup.DoesNotExist:
                raise ValidationError("Modifier group not found")
        
        raise ValidationError("Modifier group is required")

class ItemModifierDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ItemModifierSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        
        if user.user_type in ['owner', 'staff']:
            if user.user_type == 'owner':
                restaurant_ids = Restaurant.objects.filter(owner=user).values_list('restaurant_id', flat=True)
            else:
                restaurant_ids = [user.staff_profile.restaurant.restaurant_id]
            
            return ItemModifier.objects.filter(
                modifier_group__menuitemmodifier__menu_item__category__restaurant_id__in=restaurant_ids
            ).distinct()
        
        elif user.user_type == 'admin':
            return ItemModifier.objects.all()
        
        return ItemModifier.objects.none()
    
class MenuItemModifierListView(generics.ListCreateAPIView):
    serializer_class = MenuItemModifierSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        menu_item_id = self.request.query_params.get('menu_item')
        modifier_group_id = self.request.query_params.get('modifier_group')
        
        queryset = MenuItemModifier.objects.select_related('menu_item', 'modifier_group')
        
        # Filter by user's restaurants
        user = self.request.user
        if user.user_type in ['owner', 'staff']:
            if user.user_type == 'owner':
                restaurant_ids = Restaurant.objects.filter(owner=user).values_list('restaurant_id', flat=True)
            else:
                restaurant_ids = [user.staff_profile.restaurant.restaurant_id]
            
            queryset = queryset.filter(
                menu_item__category__restaurant_id__in=restaurant_ids
            )
        
        elif user.user_type != 'admin':
            queryset = MenuItemModifier.objects.none()
        
        if menu_item_id:
            queryset = queryset.filter(menu_item_id=menu_item_id)
        
        if modifier_group_id:
            queryset = queryset.filter(modifier_group_id=modifier_group_id)
        
        return queryset

    def perform_create(self, serializer):
        menu_item_id = self.request.data.get('menu_item')
        modifier_group_id = self.request.data.get('modifier_group')
        
        if not menu_item_id or not modifier_group_id:
            raise ValidationError("Both menu_item and modifier_group are required")
        
        try:
            menu_item = MenuItem.objects.get(pk=menu_item_id)
            modifier_group = ItemModifierGroup.objects.get(pk=modifier_group_id)
            
            # Validate user has access to the menu item's restaurant
            user = self.request.user
            if user.user_type in ['owner', 'staff']:
                if user.user_type == 'owner':
                    has_access = menu_item.category.restaurant.owner == user
                else:
                    has_access = menu_item.category.restaurant == user.staff_profile.restaurant
                
                if not has_access and user.user_type != 'admin':
                    raise PermissionDenied("You don't have permission to modify this menu item")
            
            # Check if association already exists
            if MenuItemModifier.objects.filter(menu_item=menu_item, modifier_group=modifier_group).exists():
                raise ValidationError("This modifier group is already assigned to the menu item")
            
            serializer.save(menu_item=menu_item, modifier_group=modifier_group)
            
        except MenuItem.DoesNotExist:
            raise ValidationError("Menu item not found")
        except ItemModifierGroup.DoesNotExist:
            raise ValidationError("Modifier group not found")

class MenuItemModifierDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = MenuItemModifierSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        
        if user.user_type in ['owner', 'staff']:
            if user.user_type == 'owner':
                restaurant_ids = Restaurant.objects.filter(owner=user).values_list('restaurant_id', flat=True)
            else:
                restaurant_ids = [user.staff_profile.restaurant.restaurant_id]
            
            return MenuItemModifier.objects.filter(
                menu_item__category__restaurant_id__in=restaurant_ids
            )
        
        elif user.user_type == 'admin':
            return MenuItemModifier.objects.all()
        
        return MenuItemModifier.objects.none()

class MenuItemModifiersView(APIView):
    """View to get all modifiers for a specific menu item"""
    permission_classes = [AllowAny]
    
    def get(self, request, menu_item_id):
        try:
            menu_item = MenuItem.objects.get(pk=menu_item_id, is_available=True)
            
            # Get all modifier groups assigned to this menu item
            modifier_groups = ItemModifierGroup.objects.filter(
                menuitemmodifier__menu_item=menu_item
            ).prefetch_related('modifiers').distinct()
            
            result = []
            for group in modifier_groups:
                group_data = ItemModifierGroupSerializer(group).data
                # Only include available modifiers
                group_data['modifiers'] = [
                    modifier for modifier in group_data['modifiers'] 
                    if modifier['is_available']
                ]
                result.append(group_data)
            
            return Response(result)
            
        except MenuItem.DoesNotExist:
            return Response(
                {'error': 'Menu item not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

class BulkMenuItemModifiersView(APIView):
    """View to bulk assign/remove modifier groups from menu items"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        menu_item_id = request.data.get('menu_item_id')
        modifier_group_ids = request.data.get('modifier_group_ids', [])
        action = request.data.get('action', 'assign')  # 'assign' or 'remove'
        
        if not menu_item_id:
            return Response(
                {'error': 'menu_item_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            menu_item = MenuItem.objects.get(pk=menu_item_id)
            
            # Validate user has access
            user = request.user
            if user.user_type in ['owner', 'staff']:
                if user.user_type == 'owner':
                    has_access = menu_item.category.restaurant.owner == user
                else:
                    has_access = menu_item.category.restaurant == user.staff_profile.restaurant
                
                if not has_access and user.user_type != 'admin':
                    raise PermissionDenied("You don't have permission to modify this menu item")
            
            with transaction.atomic():
                if action == 'assign':
                    # Assign modifier groups
                    for group_id in modifier_group_ids:
                        try:
                            modifier_group = ItemModifierGroup.objects.get(pk=group_id)
                            MenuItemModifier.objects.get_or_create(
                                menu_item=menu_item,
                                modifier_group=modifier_group
                            )
                        except ItemModifierGroup.DoesNotExist:
                            continue
                    
                    message = f"Successfully assigned {len(modifier_group_ids)} modifier groups to menu item"
                
                elif action == 'remove':
                    # Remove modifier groups
                    removed_count = MenuItemModifier.objects.filter(
                        menu_item=menu_item,
                        modifier_group_id__in=modifier_group_ids
                    ).delete()[0]
                    
                    message = f"Successfully removed {removed_count} modifier groups from menu item"
                
                else:
                    return Response(
                        {'error': 'Invalid action. Use "assign" or "remove"'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            return Response({'message': message})
            
        except MenuItem.DoesNotExist:
            return Response(
                {'error': 'Menu item not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )