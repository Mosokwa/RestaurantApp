from rest_framework import status, generics, permissions, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from django.core.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from api.search_utils import SearchUtils
from ..models import RestaurantPerformanceMetrics, Cuisine, Restaurant, Branch, MenuCategory
from ..serializers import (
    RestaurantSerializer, BranchSerializer, RestaurantCreateSerializer, BranchCreateSerializer, MenuCategorySerializer, MenuItemSerializer, RestaurantSearchSerializer
)

#improved version of list views 
class EnhancedRestaurantListView(generics.ListAPIView):
    """
    Enhanced restaurant list view with geo-search capabilities
    """
    serializer_class = RestaurantSearchSerializer
    permission_classes = [permissions.AllowAny]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    def get_queryset(self):
        queryset = Restaurant.objects.filter(status='active').prefetch_related(
            'cuisines', 'branches', 'branches__address'
        )
        
        # Apply location filter if coordinates provided
        latitude = self.request.query_params.get('lat')
        longitude = self.request.query_params.get('lng')
        radius_km = float(self.request.query_params.get('radius', 10))
        
        if latitude and longitude:
            try:
                latitude = float(latitude)
                longitude = float(longitude)
                
                nearby_branches = SearchUtils.get_restaurant_branches_nearby(
                    latitude, longitude, radius_km
                )
                restaurant_ids = [branch.restaurant_id for branch in nearby_branches]
                queryset = queryset.filter(restaurant_id__in=restaurant_ids)
            except (ValueError, TypeError):
                pass  # Invalid coordinates, return all restaurants
        
        # Apply other filters
        cuisine = self.request.query_params.get('cuisine')
        if cuisine:
            queryset = queryset.filter(cuisines__name__icontains=cuisine)
        
        min_rating = self.request.query_params.get('min_rating')
        if min_rating:
            try:
                queryset = queryset.filter(overall_rating__gte=float(min_rating))
            except ValueError:
                pass
        
        return queryset.distinct()
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        
        # Add distance information if location provided
        latitude = request.query_params.get('lat')
        longitude = request.query_params.get('lng')
        
        if latitude and longitude:
            try:
                latitude = float(latitude)
                longitude = float(longitude)
                
                for i, restaurant_data in enumerate(response.data):
                    restaurant_id = restaurant_data['restaurant_id']
                    restaurant = Restaurant.objects.get(restaurant_id=restaurant_id)
                    
                    # Calculate distance to nearest branch
                    distances = []
                    for branch in restaurant.branches.all():
                        if branch.address.latitude and branch.address.longitude:
                            dist = SearchUtils.calculate_distance(
                                latitude, longitude,
                                float(branch.address.latitude), float(branch.address.longitude)
                            )
                            if dist is not None:
                                distances.append(dist)
                    
                    if distances:
                        restaurant_data['distance_km'] = round(min(distances), 2)
            except (ValueError, TypeError, Restaurant.DoesNotExist):
                pass
        
        return response

#older version of restaurant views
class RestaurantListView(generics.ListAPIView):
    serializer_class = RestaurantSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'is_featured', 'is_verified']
    search_fields = ['name', 'description', 'cuisines__name']
    ordering_fields = ['overall_rating', 'created_at', 'name']
    ordering = ['-overall_rating']

    def get_queryset(self):
        queryset = Restaurant.objects.filter(status='active').prefetch_related('cuisines')
        
        # Filter by cuisine
        cuisine = self.request.query_params.get('cuisine')
        if cuisine:
            queryset = queryset.filter(cuisines__name__icontains=cuisine)
        
        # Filter by city through branches
        city = self.request.query_params.get('city')
        if city:
            queryset = queryset.filter(branches__address__city__icontains=city)
        
        return queryset.distinct()

class RestaurantDetailView(generics.RetrieveAPIView):
    queryset = Restaurant.objects.all().prefetch_related('cuisines', 'branches')
    serializer_class = RestaurantSerializer
    permission_classes = [permissions.AllowAny]

class RestaurantCreateView(generics.CreateAPIView):
    queryset = Restaurant.objects.all()
    serializer_class = RestaurantCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class MyRestaurantsView(generics.ListAPIView):
    serializer_class = RestaurantSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Restaurant.objects.filter(owner=self.request.user).prefetch_related('cuisines')
    
class RestaurantUpdateView(generics.UpdateAPIView):
    queryset = Restaurant.objects.all()
    serializer_class = RestaurantSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Users can only update their own restaurants
        return Restaurant.objects.filter(owner=self.request.user)

    def perform_update(self, serializer):
        instance = self.get_object()
        if instance.owner != self.request.user:
            raise PermissionDenied("You can only update your own restaurants")
        
        # Handle cuisines separately if provided
        cuisines_data = self.request.data.get('cuisines')
        if cuisines_data is not None:
            # Convert to list of integers if it's a string
            if isinstance(cuisines_data, str):
                try:
                    cuisines_data = [int(id.strip()) for id in cuisines_data.split(',')]
                except ValueError:
                    raise serializers.ValidationError("Invalid cuisine IDs format")
            
            # Validate cuisine IDs exist
            valid_cuisine_ids = Cuisine.objects.filter(
                cuisine_id__in=cuisines_data
            ).values_list('cuisine_id', flat=True)
            
            if len(valid_cuisine_ids) != len(cuisines_data):
                raise serializers.ValidationError("One or more cuisine IDs are invalid")
            
            instance.cuisines.set(valid_cuisine_ids)

        serializer.save()

class RestaurantDeleteView(generics.DestroyAPIView):
    queryset = Restaurant.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Users can only delete their own restaurants
        return Restaurant.objects.filter(owner=self.request.user)

    def perform_destroy(self, instance):
        if instance.owner != self.request.user:
            raise PermissionDenied("You can only delete your own restaurants")
        # Soft delete by changing status instead of actual deletion
        instance.status = 'inactive'
        instance.save()

# =============================================================================
# VIEW FOR WHEN OWNERS ARE TO CREATE A NEW RESTAURANT
# =============================================================================

class RestaurantOnboardingView(APIView):
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def post(self, request):
        try:
            data = request.data
            
            # 1. Create Restaurant
            restaurant_serializer = RestaurantCreateSerializer(
                data=data.get('restaurant'),
                context={'request': request}
            )
            if not restaurant_serializer.is_valid():
                return Response(
                    {'error': 'Invalid restaurant data', 'details': restaurant_serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            restaurant = restaurant_serializer.save()
            
            # 2. Create Branch
            branch_data = data.get('branch', {})
            branch_data['restaurant'] = restaurant.restaurant_id
            
            branch_serializer = BranchCreateSerializer(
                data=branch_data,
                context={'request': request}
            )
            if not branch_serializer.is_valid():
                return Response(
                    {'error': 'Invalid branch data', 'details': branch_serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            branch = branch_serializer.save()
            
            # 3. Add Cuisines
            cuisine_ids = data.get('cuisines', [])
            for cuisine_id in cuisine_ids:
                try:
                    cuisine = Cuisine.objects.get(cuisine_id=cuisine_id)
                    restaurant.cuisines.add(cuisine)
                except Cuisine.DoesNotExist:
                    continue
            
            # 4. Create Menu Categories and Items
            menu_data = data.get('menu', {})
            categories_data = menu_data.get('categories', [])
            items_data = menu_data.get('items', [])
            
            # Create categories
            for category_data in categories_data:
                category_data['restaurant'] = restaurant.restaurant_id
                category_serializer = MenuCategorySerializer(data=category_data)
                if category_serializer.is_valid():
                    category_serializer.save()
            
            # Create menu items
            for item_data in items_data:
                # Ensure category exists for this restaurant
                category_id = item_data.get('category')
                try:
                    category = MenuCategory.objects.get(
                        category_id=category_id,
                        restaurant=restaurant
                    )
                    item_data['category'] = category.category_id
                    item_serializer = MenuItemSerializer(data=item_data)
                    if item_serializer.is_valid():
                        item_serializer.save()
                except MenuCategory.DoesNotExist:
                    continue
            
            # 5. Create initial performance metrics
            RestaurantPerformanceMetrics.objects.create(restaurant=restaurant)
            
            return Response({
                'message': 'Restaurant onboarding completed successfully',
                'restaurant_id': restaurant.restaurant_id,
                'branch_id': branch.branch_id
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': f'Onboarding failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
# =============================================================================
# BRANCH VIEWS
# =============================================================================

class BranchListView(generics.ListAPIView):
    serializer_class = BranchSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        restaurant_id = self.request.query_params.get('restaurant')
        queryset = Branch.objects.select_related('restaurant', 'address')
        
        if restaurant_id:
            queryset = queryset.filter(restaurant_id=restaurant_id)
        
        return queryset

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return BranchCreateSerializer
        return BranchSerializer

class BranchDetailView(generics.RetrieveAPIView):
    queryset = Branch.objects.select_related('restaurant', 'address')
    serializer_class = BranchSerializer
    permission_classes = [permissions.AllowAny]

class BranchCreateView(generics.CreateAPIView):
    serializer_class = BranchCreateSerializer
    permission_classes = [IsAuthenticated]  # ← Only authenticated users can create

    def perform_create(self, serializer):
        # Get restaurant from context or validate the provided one
        restaurant_id = self.request.data.get('restaurant')

        
        if not restaurant_id:
            raise ValidationError("Restaurant ID is required")
        
        try:
            restaurant = Restaurant.objects.select_related('owner').get(
                restaurant_id=restaurant_id,
                owner=self.request.user  # Ensure user owns the restaurant
            )
        except Restaurant.DoesNotExist:
            raise PermissionDenied("You don't have permission to add branches to this restaurant")
    
        serializer.save(restaurant=restaurant)


class BranchUpdateView(generics.UpdateAPIView):
    queryset = Branch.objects.select_related('restaurant', 'address')
    serializer_class = BranchCreateSerializer
    permission_classes = [IsAuthenticated]  # ← Only restaurant owners can update

    def get_queryset(self):
        # Users can only update branches of their own restaurants
        return Branch.objects.filter(restaurant__owner=self.request.user)

    def perform_update(self, serializer):
        instance = self.get_object()
        if instance.restaurant.owner != self.request.user:
            raise PermissionDenied("You can only update branches of your own restaurants")
        serializer.save()

class BranchDeleteView(generics.DestroyAPIView):
    queryset = Branch.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Users can only delete branches of their own restaurants
        return Branch.objects.filter(restaurant__owner=self.request.user)

    def perform_destroy(self, instance):
        if instance.restaurant.owner != self.request.user:
            raise PermissionDenied("You can only delete branches of your own restaurants")
        # Soft delete by deactivating instead of actual deletion
        instance.is_active = False
        instance.save()

class RestaurantBranchesView(generics.ListAPIView):
    serializer_class = BranchSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        restaurant_id = self.kwargs['restaurant_id']
        return Branch.objects.filter(
            restaurant_id=restaurant_id, 
            is_active=True
        ).select_related('address')