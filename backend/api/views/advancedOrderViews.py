from rest_framework import status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.mixins import (
    CreateModelMixin, ListModelMixin, RetrieveModelMixin, DestroyModelMixin
)
from django.db import transaction, models
from django.utils import timezone
from django.shortcuts import get_object_or_404
from ..models import (
    GroupOrder, GroupOrderParticipant, ScheduledOrder, 
    OrderTemplate, BulkOrder, CustomerLoyalty
)
from ..serializers import (
    GroupOrderSerializer, GroupOrderCreateSerializer, JoinGroupOrderSerializer,
    OrderTemplateSerializer, ScheduledOrderSerializer, BulkOrderSerializer,
    CreateOrderFromTemplateSerializer
)

class GroupOrderViewSet(CreateModelMixin, ListModelMixin, RetrieveModelMixin, GenericViewSet):
    """
    ViewSet for group order operations
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return GroupOrder.objects.filter(
            models.Q(organizer=self.request.user.customer_profile) |
            models.Q(participants__customer=self.request.user.customer_profile)
        ).distinct()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return GroupOrderCreateSerializer
        return GroupOrderSerializer
    
    def create(self, request, *args, **kwargs):
        """
        Create a new group order
        """
        try:
            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            with transaction.atomic():
                group_order = serializer.save()
                
                # Add organizer as first participant
                GroupOrderParticipant.objects.create(
                    group_order=group_order,
                    customer=request.user.customer_profile,
                    display_name=request.user.get_full_name() or request.user.email.split('@')[0],
                    is_organizer=True
                )
            
            full_serializer = GroupOrderSerializer(group_order, context={'request': request})
            return Response(full_serializer.data, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def join(self, request):
        """
        Join an existing group order
        """
        try:
            serializer = JoinGroupOrderSerializer(data=request.data, context={'request': request})
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            group_order = serializer.validated_data['group_order']
            display_name = serializer.validated_data['display_name']
            
            with transaction.atomic():
                participant = GroupOrderParticipant.objects.create(
                    group_order=group_order,
                    customer=request.user.customer_profile,
                    display_name=display_name,
                    is_organizer=False
                )
            
            # Return group order details
            group_serializer = GroupOrderSerializer(group_order, context={'request': request})
            return Response(group_serializer.data)
        
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        """
        Close a group order (organizer only)
        """
        try:
            group_order = self.get_object()
            
            # Check if user is the organizer
            if group_order.organizer != request.user.customer_profile:
                return Response({
                    'error': 'Only the organizer can close the group order'
                }, status=status.HTTP_403_FORBIDDEN)
            
            if group_order.status != 'active':
                return Response({
                    'error': 'Group order is not active'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            group_order.status = 'closed'
            group_order.closed_at = timezone.now()
            group_order.save()
            
            serializer = self.get_serializer(group_order)
            return Response(serializer.data)
        
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def participants(self, request, pk=None):
        """
        Get list of participants for a group order
        """
        try:
            group_order = self.get_object()
            participants = group_order.participants.all()
            
            from ..serializers import GroupOrderParticipantSerializer
            serializer = GroupOrderParticipantSerializer(participants, many=True)
            return Response(serializer.data)
        
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class OrderTemplateViewSet(ModelViewSet):
    """
    ViewSet for order template operations
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OrderTemplateSerializer
    
    def get_queryset(self):
        return OrderTemplate.objects.filter(customer=self.request.user.customer_profile, is_active=True)
    
    def perform_create(self, serializer):
        serializer.save(customer=self.request.user.customer_profile)
    
    @action(detail=True, methods=['post'])
    def create_order(self, request, pk=None):
        """
        Create an order from this template
        """
        try:
            template = self.get_object()
            
            with transaction.atomic():
                order = template.create_order_from_template()
                
                # Add loyalty points if applicable
                try:
                    loyalty_profile = request.user.customer_profile.loyalty_profile
                    points_to_add = int(order.subtotal * float(loyalty_profile.program.points_per_dollar))
                    if points_to_add > 0:
                        loyalty_profile.add_points(
                            points_to_add,
                            reason=f"Order from template: {template.name}",
                            order=order
                        )
                except CustomerLoyalty.DoesNotExist:
                    pass  # No loyalty profile, skip points
            
            from ..serializers import OrderSerializer
            order_serializer = OrderSerializer(order, context={'request': request})
            return Response(order_serializer.data, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ScheduledOrderViewSet(ModelViewSet):
    """
    ViewSet for scheduled order operations
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ScheduledOrderSerializer
    
    def get_queryset(self):
        return ScheduledOrder.objects.filter(customer=self.request.user.customer_profile)
    
    def perform_create(self, serializer):
        serializer.save(customer=self.request.user.customer_profile)
    
    @action(detail=True, methods=['post'])
    def skip(self, request, pk=None):
        """
        Skip the next occurrence of a scheduled order
        """
        try:
            scheduled_order = self.get_object()
            
            if not scheduled_order.is_active:
                return Response({
                    'error': 'Scheduled order is not active'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Calculate next occurrence after skipping
            if scheduled_order.schedule_type == 'once':
                scheduled_order.is_active = False
            elif scheduled_order.schedule_type == 'daily':
                scheduled_order.next_occurrence += timezone.timedelta(days=1)
            # Add logic for weekly/monthly as needed
            
            scheduled_order.save()
            
            serializer = self.get_serializer(scheduled_order)
            return Response(serializer.data)
        
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel a scheduled order
        """
        try:
            scheduled_order = self.get_object()
            scheduled_order.is_active = False
            scheduled_order.save()
            
            serializer = self.get_serializer(scheduled_order)
            return Response(serializer.data)
        
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class BulkOrderViewSet(ModelViewSet):
    """
    ViewSet for bulk order operations
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BulkOrderSerializer
    
    def get_queryset(self):
        return BulkOrder.objects.filter(customer=self.request.user.customer_profile)
    
    def perform_create(self, serializer):
        serializer.save(customer=self.request.user.customer_profile)
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """
        Confirm a bulk order (move from inquiry to confirmed)
        """
        try:
            bulk_order = self.get_object()
            
            if bulk_order.status != 'quoted':
                return Response({
                    'error': 'Bulk order must be in quoted status to confirm'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            bulk_order.status = 'confirmed'
            bulk_order.save()
            
            serializer = self.get_serializer(bulk_order)
            return Response(serializer.data)
        
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AdvancedOrderViewSet(GenericViewSet):
    """
    Combined ViewSet for advanced order features
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def create_from_template(self, request):
        """
        Create order from template (alternative endpoint)
        """
        try:
            serializer = CreateOrderFromTemplateSerializer(data=request.data, context={'request': request})
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            template = serializer.validated_data['template']
            
            with transaction.atomic():
                order = template.create_order_from_template()
                
                # Add loyalty points
                try:
                    loyalty_profile = request.user.customer_profile.loyalty_profile
                    points_to_add = int(order.subtotal * float(loyalty_profile.program.points_per_dollar))
                    if points_to_add > 0:
                        loyalty_profile.add_points(
                            points_to_add,
                            reason=f"Order from template: {template.name}",
                            order=order
                        )
                except CustomerLoyalty.DoesNotExist:
                    pass
            
            from ..serializers import OrderSerializer
            order_serializer = OrderSerializer(order, context={'request': request})
            return Response(order_serializer.data, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
