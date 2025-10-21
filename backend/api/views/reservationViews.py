# views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.views import APIView
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta, datetime
from django.shortcuts import get_object_or_404

from ..models import Table, Reservation, TimeSlot, Restaurant, Branch
from ..serializers import (
    TableSerializer, ReservationSerializer, ReservationCreateSerializer,
    TimeSlotSerializer, AvailabilityCheckSerializer, RestaurantsSearchSerializer,
    RestaurantReservationConfigSerializer
)
from ..services.reservation_services import ReservationService, NotificationService

class RestaurantsSearchView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Search restaurants with availability filtering"""
        serializer = RestaurantsSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        date = data.get('date')
        time = data.get('time')
        party_size = data.get('party_size', 2)
        location = data.get('location')
        cuisine = data.get('cuisine')
        
        # Base queryset
        restaurants = Restaurant.objects.filter(
            reservation_enabled=True,
            status='active'
        ).prefetch_related('branches', 'branches__address', 'cuisines')
        
        # Apply filters
        if location:
            restaurants = restaurants.filter(
                Q(branches__address__city__icontains=location) |
                Q(branches__address__state__icontains=location) |
                Q(branches__address__postal_code__icontains=location)
            ).distinct()
        
        if cuisine:
            restaurants = restaurants.filter(cuisines__name__icontains=cuisine)
        
        # Check availability for each restaurant
        available_restaurants = []
        for restaurant in restaurants:
            has_availability = self.check_restaurant_availability(
                restaurant, date, time, party_size
            )
            
            if has_availability:
                restaurant_data = {
                    'id': restaurant.restaurant_id,
                    'name': restaurant.name,
                    'description': restaurant.description,
                    'overall_rating': float(restaurant.overall_rating),
                    'total_reviews': restaurant.total_reviews,
                    'logo': restaurant.logo.url if restaurant.logo else None,
                    'cuisines': [cuisine.name for cuisine in restaurant.cuisines.all()],
                    'branches': [
                        {
                            'id': branch.branch_id,
                            'address': str(branch.address),
                            'city': branch.address.city
                        }
                        for branch in restaurant.branches.filter(is_active=True)
                    ],
                    'has_availability': True
                }
                available_restaurants.append(restaurant_data)
        
        return Response({
            'count': len(available_restaurants),
            'restaurants': available_restaurants
        })
    
    def check_restaurant_availability(self, restaurant, date, time, party_size):
        """Check if restaurant has any availability for given criteria"""
        if not date or not time:
            return True  # If no specific time, just return all restaurants
        
        # Check each branch
        for branch in restaurant.branches.filter(is_active=True):
            available_tables = ReservationService.find_available_tables(
                restaurant, branch, date, time, 90, party_size  # Default 90min duration
            )
            if available_tables:
                return True
        return False

class RestaurantAvailabilityView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request, restaurant_id):
        """Get detailed availability for a specific restaurant"""
        restaurant = get_object_or_404(Restaurant, pk=restaurant_id)
        date_str = request.query_params.get('date')
        party_size = int(request.query_params.get('party_size', 2))
        
        if not date_str:
            return Response({'error': 'Date parameter is required'}, status=400)
        
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD'}, status=400)
        
        # Get availability for all branches
        branches_availability = []
        for branch in restaurant.branches.filter(is_active=True):
            time_slots = ReservationService.generate_time_slots(
                restaurant, branch, date, party_size
            )
            
            branches_availability.append({
                'branch_id': branch.branch_id,
                'branch_address': str(branch.address),
                'time_slots': time_slots
            })
        
        return Response({
            'restaurant': {
                'id': restaurant.restaurant_id,
                'name': restaurant.name,
                'reservation_rules': RestaurantReservationConfigSerializer(restaurant).data
            },
            'availability': branches_availability,
            'date': date_str,
            'party_size': party_size
        })

class ReservationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.user_type == 'customer':
            return Reservation.objects.filter(customer__user=user).select_related(
                'restaurant', 'branch', 'table', 'customer__user'
            )
        elif user.user_type == 'owner':
            return Reservation.objects.filter(restaurant__owner=user).select_related(
                'restaurant', 'branch', 'table', 'customer__user'
            )
        elif user.user_type == 'staff':
            # Staff can see reservations for their restaurant
            staff_profile = getattr(user, 'staff_profile', None)
            if staff_profile:
                return Reservation.objects.filter(restaurant=staff_profile.restaurant)
        elif user.user_type == 'admin':
            return Reservation.objects.all().select_related(
                'restaurant', 'branch', 'table', 'customer__user'
            )
        
        return Reservation.objects.none()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ReservationCreateSerializer
        return ReservationSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            reservation = self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            
            # Send confirmation notification
            NotificationService.send_reservation_confirmation(reservation)
            
            return Response(
                ReservationSerializer(reservation, context=self.get_serializer_context()).data,
                status=status.HTTP_201_CREATED,
                headers=headers
            )
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def perform_create(self, serializer):
        customer = self.request.user.customer_profile
        data = serializer.validated_data
        
        # Auto-assign table if enabled
        table = None
        if data['restaurant'].auto_assign_tables:
            table = ReservationService.auto_assign_table(
                data['restaurant'], data['branch'], data['reservation_date'],
                data['reservation_time'], data.get('duration_minutes', 90),
                data['party_size']
            )
        
        if not table:
            raise ValueError("No suitable table available for the reservation")
        
        # Create reservation
        reservation = serializer.save(
            customer=customer,
            table=table,
            status='confirmed' if not data['restaurant'].requires_confirmation else 'pending'
        )
        
        return reservation
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel reservation with reason"""
        reservation = self.get_object()
        reason = request.data.get('reason', '')
        
        if reservation.cancel(reason):
            # Send cancellation notification
            NotificationService.send_reservation_cancellation(reservation, reason)
            
            return Response({
                'status': 'Reservation cancelled successfully',
                'reservation_code': reservation.reservation_code
            })
        else:
            return Response(
                {'error': 'Reservation cannot be cancelled. It may be too close to the reservation time.'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Confirm a pending reservation (for restaurant owners)"""
        reservation = self.get_object()
        
        if reservation.status == 'pending' and reservation.confirm():
            NotificationService.send_reservation_confirmation(reservation)
            return Response({'status': 'Reservation confirmed'})
        else:
            return Response(
                {'error': 'Reservation cannot be confirmed'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def my_reservations(self, request):
        """Get current user's reservations with filtering"""
        status_filter = request.query_params.get('status')
        upcoming = request.query_params.get('upcoming')
        
        queryset = self.get_queryset()
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        if upcoming and upcoming.lower() == 'true':
            today = timezone.now().date()
            queryset = queryset.filter(
                Q(reservation_date__gt=today) |
                Q(reservation_date=today, reservation_time__gte=timezone.now().time())
            )
        
        queryset = queryset.order_by('-reservation_date', '-reservation_time')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class TableViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TableSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        restaurant_id = self.kwargs.get('restaurant_id')
        branch_id = self.request.query_params.get('branch_id')
        
        queryset = Table.objects.filter(restaurant_id=restaurant_id)
        
        if branch_id:
            queryset = queryset.filter(branch_id=branch_id)
        
        return queryset
    
    @action(detail=False, methods=['post'])
    def check_availability(self, request, restaurant_id=None):
        """Check table availability for specific criteria"""
        serializer = AvailabilityCheckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        restaurant = get_object_or_404(Restaurant, pk=restaurant_id)
        branch_id = data.get('branch_id')
        
        branches = restaurant.branches.filter(is_active=True)
        if branch_id:
            branches = branches.filter(branch_id=branch_id)
        
        availability_results = []
        for branch in branches:
            available_tables = ReservationService.find_available_tables(
                restaurant, branch, data['reservation_date'],
                data['reservation_time'], data['duration_minutes'], data['party_size']
            )
            
            availability_results.append({
                'branch': {
                    'id': branch.branch_id,
                    'address': str(branch.address)
                },
                'available_tables': TableSerializer(available_tables, many=True).data,
                'available_count': len(available_tables)
            })
        
        return Response({
            'restaurant_id': restaurant_id,
            'reservation_date': data['reservation_date'],
            'party_size': data['party_size'],
            'availability': availability_results
        })

class TimeSlotViewSet(viewsets.ModelViewSet):
    queryset = TimeSlot.objects.all()
    serializer_class = TimeSlotSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]