from rest_framework import status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, GenericViewSet
# from rest_framework.mixins import (
#     ListModelMixin, RetrieveModelMixin, UpdateModelMixin, CreateModelMixin
# )
from django.db import transaction
from ..models import RestaurantLoyaltySettings, Reward, Restaurant
from ..serializers import (
    RestaurantLoyaltySettingsSerializer, RestaurantLoyaltySettingsCreateSerializer,
    RestaurantRewardSerializer, ToggleLoyaltySerializer
)

class RestaurantLoyaltySettingsViewSet(ModelViewSet):
    """
    ViewSet for restaurant owners to manage loyalty program settings
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = RestaurantLoyaltySettingsSerializer
    
    def get_queryset(self):
        # Owners can only see settings for their own restaurants
        return RestaurantLoyaltySettings.objects.filter(
            restaurant__owner=self.request.user
        ).select_related('restaurant')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return RestaurantLoyaltySettingsCreateSerializer
        return RestaurantLoyaltySettingsSerializer
    
    def perform_create(self, serializer):
        # Ensure the restaurant belongs to the current user
        restaurant = serializer.validated_data['restaurant']
        if restaurant.owner != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only create settings for your own restaurants")
        
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def toggle_loyalty(self, request, pk=None):
        """
        Quickly enable/disable loyalty program for this restaurant
        """
        try:
            loyalty_settings = self.get_object()
            
            serializer = ToggleLoyaltySerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            loyalty_settings = serializer.update(loyalty_settings, serializer.validated_data)
            
            response_serializer = RestaurantLoyaltySettingsSerializer(loyalty_settings)
            return Response(response_serializer.data)
        
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """
        Get loyalty program statistics for this restaurant
        """
        try:
            loyalty_settings = self.get_object()
            restaurant = loyalty_settings.restaurant
            
            # Calculate basic statistics
            from django.db.models import Sum, Count
            from ..models import PointsTransaction, RewardRedemption
            
            points_given = PointsTransaction.objects.filter(
                restaurant=restaurant,
                transaction_type='earned'
            ).aggregate(total_points=Sum('points'))['total_points'] or 0
            
            points_redeemed = PointsTransaction.objects.filter(
                restaurant=restaurant,
                transaction_type='redeemed'
            ).aggregate(total_points=Sum('points'))['total_points'] or 0
            
            redemptions_count = RewardRedemption.objects.filter(
                restaurant=restaurant,
                status='completed'
            ).count()
            
            active_customers = PointsTransaction.objects.filter(
                restaurant=restaurant
            ).values('customer_loyalty').distinct().count()
            
            return Response({
                'restaurant_id': restaurant.restaurant_id,
                'restaurant_name': restaurant.name,
                'is_loyalty_enabled': loyalty_settings.is_loyalty_enabled,
                'points_given': points_given,
                'points_redeemed': abs(points_redeemed),  # Make positive
                'net_points': points_given - abs(points_redeemed),
                'redemptions_count': redemptions_count,
                'active_customers': active_customers,
                'effective_points_rate': float(loyalty_settings.effective_points_rate)
            })
        
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class RestaurantRewardViewSet(ModelViewSet):
    """
    ViewSet for restaurant owners to manage their custom rewards
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = RestaurantRewardSerializer
    
    def get_queryset(self):
        # Owners can only see rewards for their own restaurants
        return Reward.objects.filter(
            restaurant__owner=self.request.user
        ).select_related('restaurant')
    
    def perform_create(self, serializer):
        restaurant_id = self.request.data.get('restaurant')
        if not restaurant_id:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("Restaurant is required")
        
        try:
            restaurant = Restaurant.objects.get(
                pk=restaurant_id,
                owner=self.request.user
            )
            
            # Get the active loyalty program
            from ..models import LoyaltyProgram
            program = LoyaltyProgram.objects.filter(is_active=True).first()
            if not program:
                from rest_framework.exceptions import ValidationError
                raise ValidationError("No active loyalty program found")
            
            serializer.save(restaurant=restaurant, program=program)
        
        except Restaurant.DoesNotExist:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only create rewards for your own restaurants")

class OwnerLoyaltyDashboardViewSet(GenericViewSet):
    """
    Dashboard for restaurant owners to manage loyalty programs
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def overview(self, request):
        """
        Get loyalty program overview for all owner's restaurants
        """
        try:
            restaurants = Restaurant.objects.filter(owner=request.user)
            
            results = []
            for restaurant in restaurants:
                try:
                    loyalty_settings = restaurant.loyalty_settings
                    settings_data = RestaurantLoyaltySettingsSerializer(loyalty_settings).data
                    settings_data['has_custom_settings'] = True
                except RestaurantLoyaltySettings.DoesNotExist:
                    settings_data = {
                        'restaurant_id': restaurant.restaurant_id,
                        'restaurant_name': restaurant.name,
                        'is_loyalty_enabled': True,  # Default
                        'has_custom_settings': False,
                        'is_loyalty_active': True
                    }
                
                results.append(settings_data)
            
            return Response(results)
        
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def bulk_toggle(self, request):
        """
        Bulk enable/disable loyalty for multiple restaurants
        """
        try:
            restaurant_ids = request.data.get('restaurant_ids', [])
            enable_loyalty = request.data.get('enable', True)
            
            if not restaurant_ids:
                return Response({
                    'error': 'restaurant_ids is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            restaurants = Restaurant.objects.filter(
                restaurant_id__in=restaurant_ids,
                owner=request.user
            )
            
            updated_count = 0
            with transaction.atomic():
                for restaurant in restaurants:
                    # Get or create settings for each restaurant
                    loyalty_settings, created = RestaurantLoyaltySettings.objects.get_or_create(
                        restaurant=restaurant,
                        defaults={'is_loyalty_enabled': enable_loyalty}
                    )
                    
                    if not created:
                        loyalty_settings.is_loyalty_enabled = enable_loyalty
                        loyalty_settings.save()
                    
                    updated_count += 1
            
            return Response({
                'message': f'Successfully updated loyalty settings for {updated_count} restaurants',
                'updated_count': updated_count,
                'enable_loyalty': enable_loyalty
            })
        
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)