from rest_framework import generics, filters
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from ..models import Restaurant, Order, OrderTracking
from ..serializers import (
    OrderSerializer, OrderCreateSerializer, OrderWithOffersSerializer
)

class OrderListView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return OrderCreateSerializer
        # Use enhanced serializer when offers are requested
        elif self.request.query_params.get('with_offers') == 'true':
            return OrderWithOffersSerializer
        return OrderSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        if user.user_type == 'customer':
            return Order.objects.filter(customer__user=user).select_related(
                'customer__user', 'restaurant', 'branch', 'delivery_address'
            ).prefetch_related('order_items', 'tracking_history', 'applied_offers').order_by('-order_placed_at')
        
        elif user.user_type in ['owner', 'staff']:
            # Restaurant staff can see orders for their restaurant
            if user.user_type == 'owner':
                restaurant_ids = Restaurant.objects.filter(owner=user).values_list('restaurant_id', flat=True)
            else:
                restaurant_ids = [user.staff_profile.restaurant.restaurant_id]
            
            return Order.objects.filter(restaurant_id__in=restaurant_ids).select_related(
                'customer__user', 'restaurant', 'branch', 'delivery_address'
            ).prefetch_related('order_items', 'tracking_history', 'applied_offers').order_by('-order_placed_at')
        
        elif user.user_type == 'admin':
            return Order.objects.all().select_related(
                'customer__user', 'restaurant', 'branch', 'delivery_address'
            ).prefetch_related('order_items', 'tracking_history', 'applied_offers').order_by('-order_placed_at')
        
        return Order.objects.none()
    
    @transaction.atomic
    def perform_create(self, serializer):
        serializer.save()

class OrderDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        # Use enhanced serializer for offer details when requested
        if self.request.query_params.get('with_offers') == 'true':
            return OrderWithOffersSerializer
        return OrderSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        if user.user_type == 'customer':
            return Order.objects.filter(customer__user=user)
        
        elif user.user_type in ['owner', 'staff']:
            if user.user_type == 'owner':
                restaurant_ids = Restaurant.objects.filter(owner=user).values_list('restaurant_id', flat=True)
            else:
                restaurant_ids = [user.staff_profile.restaurant.restaurant_id]
            
            return Order.objects.filter(restaurant_id__in=restaurant_ids)
        
        elif user.user_type == 'admin':
            return Order.objects.all()
        
        return Order.objects.none()

class OrderUpdateView(generics.UpdateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['patch']  # Only allow PATCH for partial updates
    
    def get_queryset(self):
        user = self.request.user
        
        # Only restaurant staff and owners can update orders
        if user.user_type in ['owner', 'staff']:
            if user.user_type == 'owner':
                restaurant_ids = Restaurant.objects.filter(owner=user).values_list('restaurant_id', flat=True)
            else:
                restaurant_ids = [user.staff_profile.restaurant.restaurant_id]
            
            return Order.objects.filter(restaurant_id__in=restaurant_ids)
        
        return Order.objects.none()
    
    @transaction.atomic
    def perform_update(self, serializer):
        old_status = self.get_object().status
        new_status = serializer.validated_data.get('status', old_status)
        
        instance = serializer.save()
        
        # Use the enhanced real-time method
        description = f"Order status changed from {old_status} to {new_status}"
        instance.update_status_with_realtime(
            new_status, 
            self.request.user, 
            description
        )

class MyOrdersView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'order_type']
    ordering_fields = ['order_placed_at', 'total_amount']
    ordering = ['-order_placed_at']
    
    def get_queryset(self):
        if self.request.user.user_type != 'customer':
            raise PermissionDenied("Only customers can view their orders")
        
        return Order.objects.filter(customer__user=self.request.user).select_related(
            'restaurant', 'branch', 'delivery_address'
        ).prefetch_related('order_items')