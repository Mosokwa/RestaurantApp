import json
from rest_framework.parsers import MultiPartParser, JSONParser
from rest_framework import status, generics, permissions, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from django.core.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from api.search_utils import SearchUtils
from ..models import RestaurantPerformanceMetrics, Cuisine, Restaurant, Branch, MenuCategory, ItemModifierGroup, MenuItemModifier
from ..serializers import (
    RestaurantSerializer, BranchSerializer, RestaurantCreateSerializer, BranchCreateSerializer, MenuCategorySerializer, MenuItemSerializer, RestaurantSearchSerializer, SpecialOfferSerializer
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

    @transaction.atomic
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
                    raise ValidationError("Invalid cuisine IDs format")
            
            # Validate cuisine IDs exist
            valid_cuisine_ids = Cuisine.objects.filter(
                cuisine_id__in=cuisines_data
            ).values_list('cuisine_id', flat=True)
            
            if len(valid_cuisine_ids) != len(cuisines_data):
                raise ValidationError("One or more cuisine IDs are invalid")
            
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
    """
    Comprehensive restaurant onboarding with proper file upload support
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, JSONParser]
    
    @transaction.atomic
    def post(self, request):
        try:
            data = request.data
            user = request.user
            
            print("📨 Received onboarding request from:", user.email)
            
            # Validate user can create restaurants
            if user.user_type != 'owner':
                return Response(
                    {'error': 'Only restaurant owners can create restaurants'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Parse JSON data from FormData
            data_str = data.get('data')
            if not data_str:
                return Response(
                    {'error': 'No data provided'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                json_data = json.loads(data_str)
                print("📝 Parsed JSON data successfully")
            except json.JSONDecodeError as e:
                return Response(
                    {'error': f'Invalid JSON data: {str(e)}'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check for duplicate restaurant
            restaurant_name = json_data.get('restaurant', {}).get('name', '').strip()
            if restaurant_name:
                existing_restaurant = Restaurant.objects.filter(
                    owner=user, 
                    name__iexact=restaurant_name,
                    status='active'
                ).first()
                
                if existing_restaurant:
                    return Response(
                        {'error': f'You already have a restaurant named "{restaurant_name}"'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # 1. Create Restaurant
            restaurant_data = json_data.get('restaurant', {})
            print("🏢 Processing restaurant:", restaurant_data.get('name'))
            
            # Add files to restaurant data
            restaurant_logo = request.FILES.get('restaurant_logo')
            restaurant_banner = request.FILES.get('restaurant_banner')
            
            if restaurant_logo:
                restaurant_data['logo'] = restaurant_logo
                print("📸 Added restaurant logo")
            if restaurant_banner:
                restaurant_data['banner_image'] = restaurant_banner
                print("📸 Added restaurant banner")
            
            restaurant_serializer = RestaurantCreateSerializer(
                data=restaurant_data,
                context={'request': request}
            )
            
            if not restaurant_serializer.is_valid():
                print("❌ Restaurant validation errors:", restaurant_serializer.errors)
                return Response(
                    {'error': 'Invalid restaurant data', 'details': restaurant_serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            restaurant = restaurant_serializer.save()
            print("✅ Restaurant created:", restaurant.restaurant_id, restaurant.name)
            
            # 2. Add Cuisines
            cuisine_ids = json_data.get('cuisines', [])
            print("🍽️ Adding cuisines:", cuisine_ids)
            
            for cuisine_id in cuisine_ids:
                try:
                    cuisine = Cuisine.objects.get(cuisine_id=cuisine_id, is_active=True)
                    restaurant.cuisines.add(cuisine)
                    print(f"✅ Added cuisine: {cuisine.name}")
                except Cuisine.DoesNotExist:
                    print(f"⚠️ Invalid cuisine ID: {cuisine_id}")
            
            # 3. Create Branches
            branches_data = json_data.get('branches', [])
            created_branches = []
            
            print("📍 Creating branches:", len(branches_data))
            
            for branch_index, branch_data in enumerate(branches_data):
                branch_data['restaurant'] = restaurant.restaurant_id
                branch_serializer = BranchCreateSerializer(
                    data=branch_data,
                    context={'request': request}
                )
                
                if not branch_serializer.is_valid():
                    print(f"❌ Branch {branch_index} errors:", branch_serializer.errors)
                    return Response(
                        {'error': f'Invalid branch data: {branch_serializer.errors}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                branch = branch_serializer.save()
                created_branches.append({
                    'branch_id': branch.branch_id,
                    'name': branch.name,
                    'address': str(branch.address)
                })
                print(f"✅ Branch created: {branch.name}")
            
            # Ensure at least one branch was created
            if not created_branches:
                return Response(
                    {'error': 'At least one branch is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 4. Create Menu Structure
            menu_data = json_data.get('menu', {})
            categories_data = menu_data.get('categories', [])
            created_menu_structure = {
                'categories': [],
                'items': 0
            }
            
            print("📋 Creating menu categories:", len(categories_data))
            
            # Create categories and items
            for category_index, category_data in enumerate(categories_data):
                category_data['restaurant'] = restaurant.restaurant_id
                category_serializer = MenuCategorySerializer(data=category_data)
                
                if not category_serializer.is_valid():
                    print(f"❌ Category {category_index} errors:", category_serializer.errors)
                    return Response(
                        {'error': f'Invalid category data: {category_serializer.errors}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                category = category_serializer.save()
                category_info = {
                    'category_id': category.category_id,
                    'name': category.name,
                    'items': []
                }
                
                # Create menu items for this category
                items_data = category_data.get('items', [])
                for item_index, item_data in enumerate(items_data):
                    item_data['category'] = category.category_id
                    
                    # Add menu item image if available
                    menu_item_image = request.FILES.get(f'menu_item_images[{category_index}][{item_index}]')
                    if menu_item_image:
                        item_data['image'] = menu_item_image
                        print(f"📸 Added image for menu item: {item_data.get('name')}")
                    
                    item_serializer = MenuItemSerializer(data=item_data)
                    
                    if not item_serializer.is_valid():
                        print(f"❌ Menu item {item_index} errors:", item_serializer.errors)
                        return Response(
                            {'error': f'Invalid menu item data: {item_serializer.errors}'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                    menu_item = item_serializer.save()
                    created_menu_structure['items'] += 1
                    
                    category_info['items'].append({
                        'item_id': menu_item.item_id,
                        'name': menu_item.name,
                        'price': str(menu_item.price)
                    })
                    print(f"✅ Menu item created: {menu_item.name} - ${menu_item.price}")
                
                created_menu_structure['categories'].append(category_info)
            
            # 5. Create performance metrics safely
            try:
                metrics, created = RestaurantPerformanceMetrics.objects.get_or_create(
                    restaurant=restaurant
                )
                if created:
                    print("✅ Created new performance metrics")
                else:
                    print("ℹ️ Performance metrics already exist")
            except Exception as e:
                print(f"⚠️ Performance metrics issue: {str(e)}")
                # Continue anyway - metrics are not critical for onboarding
            
            print("🎉 Onboarding completed successfully!")
            print(f"📊 Summary: {len(created_branches)} branches, {len(created_menu_structure['categories'])} categories, {created_menu_structure['items']} items")
            
            return Response({
                'message': 'Restaurant onboarding completed successfully',
                'restaurant_id': restaurant.restaurant_id,
                'is_first_restaurant': json_data.get('is_first_restaurant', False),
                'branches_created': len(created_branches),
                'menu_categories_created': len(created_menu_structure['categories']),
                'menu_items_created': created_menu_structure['items'],
                'cuisines_added': restaurant.cuisines.count(),
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            print("💥 Onboarding failed with exception:", str(e))
            import traceback
            traceback.print_exc()
            
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

    @transaction.atomic
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

    @transaction.atomic
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