from rest_framework import generics, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from django.core.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import ValidationError
from ..models import Cuisine, Restaurant, MenuCategory, MenuItem, SpecialOffer
from ..serializers import (
    CuisineSerializer, MenuCategorySerializer, MenuItemSerializer, SpecialOfferSerializer
)

class CuisineListView(generics.ListCreateAPIView):
    queryset = Cuisine.objects.filter(is_active=True)
    serializer_class = CuisineSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']

class CuisineDetailView(generics.RetrieveAPIView):
    queryset = Cuisine.objects.all()
    serializer_class = CuisineSerializer
    permission_classes = [permissions.IsAdminUser]
    
class CuisineCreateView(generics.CreateAPIView):  # ← Separate create view
    queryset = Cuisine.objects.all()
    serializer_class = CuisineSerializer
    permission_classes = [permissions.IsAdminUser]  # ← Only admins can create

class CuisineDeleteView(generics.DestroyAPIView):
    queryset = Cuisine.objects.all()
    permission_classes = [permissions.IsAdminUser]  # Only admins can delete cuisines

    def perform_destroy(self, instance):
        # Soft delete instead of actual deletion
        instance.is_active = False
        instance.save()

class CuisineUpdateView(generics.UpdateAPIView):  # ← Separate update view
    queryset = Cuisine.objects.all()
    serializer_class = CuisineSerializer
    permission_classes = [permissions.IsAdminUser]  # ← Only admins can update

class MenuCategoryListView(generics.ListAPIView):
    serializer_class = MenuCategorySerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description', 'restaurant__name']

    def get_queryset(self):
        restaurant_id = self.request.query_params.get('restaurant')
        queryset = MenuCategory.objects.filter(is_active=True).select_related('restaurant')
        
        if restaurant_id:
            queryset = queryset.filter(restaurant_id=restaurant_id)
        
        return queryset.prefetch_related('menu_items')

class RestaurantMenuView(generics.ListAPIView):
    serializer_class = MenuCategorySerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        restaurant_id = self.kwargs['restaurant_id']
        return MenuCategory.objects.filter(
            restaurant_id=restaurant_id,
            is_active=True
        ).select_related('restaurant').prefetch_related(
            'menu_items'
        ).order_by('display_order')

class MenuItemListView(generics.ListAPIView):
    serializer_class = MenuItemSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['item_type', 'is_available', 'is_vegetarian', 'is_vegan', 'is_gluten_free']
    search_fields = ['name', 'description', 'category__name']
    ordering_fields = ['price', 'name', 'display_order']
    ordering = ['display_order']

    def get_queryset(self):
        restaurant_id = self.request.query_params.get('restaurant')
        category_id = self.request.query_params.get('category')
        
        queryset = MenuItem.objects.filter(is_available=True).select_related('category__restaurant')
        
        if restaurant_id:
            queryset = queryset.filter(category__restaurant_id=restaurant_id)
        
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        return queryset.prefetch_related('menuitemmodifier_set__modifier_group__modifiers')

class MenuItemDetailView(generics.RetrieveAPIView):
    queryset = MenuItem.objects.all().select_related('category__restaurant').prefetch_related(
        'menuitemmodifier_set__modifier_group__modifiers'
    )
    serializer_class = MenuItemSerializer
    permission_classes = [AllowAny]


#SPECIAL OFFER VIEW

class SpecialOfferView(generics.ListAPIView):
    serializer_class = SpecialOfferSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        restaurant_id = self.request.query_params.get('restaurant')
        queryset = SpecialOffer.objects.filter(is_active=True).select_related('restaurant')
        
        if restaurant_id:
            queryset = queryset.filter(restaurant_id=restaurant_id)
        
        # Filter only valid offers
        return [offer for offer in queryset if offer.is_valid()]

# Admin views for restaurant owners
class MenuCategoryCreateView(generics.CreateAPIView):
    serializer_class = MenuCategorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Users can only manage categories for their own restaurants
        return MenuCategory.objects.filter(restaurant__owner=self.request.user)
    
    def perform_create(self, serializer):
        # Verify the restaurant belongs to the user
        restaurant_id = self.request.data.get('restaurant')
        print(restaurant_id)
        try:
            restaurant = Restaurant.objects.get(restaurant_id=restaurant_id, owner=self.request.user)
            serializer.save(restaurant=restaurant)
        except Restaurant.DoesNotExist:
            raise PermissionDenied("You can only create categories for your own restaurants")

class MenuItemCreateView(generics.CreateAPIView):
    serializer_class = MenuItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Users can only manage items for their own restaurants
        return MenuItem.objects.filter(category__restaurant__owner=self.request.user)
    
    def perform_create(self, serializer):
        # Verify the category belongs to user's restaurant
        category_id = self.request.data.get('category')
        if not category_id:
            raise ValidationError("Category is required")
        
        try:
            category = MenuCategory.objects.get(
                category_id=category_id,
                restaurant__owner=self.request.user
            )
            serializer.save(category=category)
        except MenuCategory.DoesNotExist:
            raise PermissionDenied("You can only create items for your own restaurants")