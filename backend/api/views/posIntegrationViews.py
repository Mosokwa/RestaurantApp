# pos_integration_views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from ..models import (
    POSConnection, TableLayout, KitchenStation, 
    OrderPOSInfo, OrderItemPreparation, POSSyncLog
)
from ..serializers import (
    POSConnectionSerializer, TableLayoutSerializer, KitchenStationSerializer,
    OrderRoutingSerializer, OrderItemPreparationSerializer, POSSyncLogSerializer
)
from api.models import Order, OrderItem
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from api.permissions import IsRestaurantOwner, IsPOSWebhook

class POSConnectionViewSet(viewsets.ModelViewSet):
    queryset = POSConnection.objects.all()
    serializer_class = POSConnectionSerializer
    permission_classes = [IsAuthenticated, IsRestaurantOwner]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['restaurant', 'pos_type', 'is_active', 'sync_status']
    search_fields = ['connection_name', 'restaurant__name']
    ordering_fields = ['created_at', 'last_sync', 'sync_status']
    
    def get_queryset(self):
        # Restaurant owners can only see their own connections
        if self.request.user.user_type == 'owner':
            return POSConnection.objects.filter(
                restaurant__owner=self.request.user
            )
        return super().get_queryset()
    
    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """Test POS connection"""
        connection = self.get_object()
        success, message = connection.test_connection()
        
        return Response({
            'success': success,
            'message': message,
            'sync_status': connection.sync_status
        })
    
    @action(detail=True, methods=['post'])
    def sync_menu(self, request, pk=None):
        """Sync menu with POS"""
        connection = self.get_object()
        success, stats = connection.sync_menu_items()
        
        return Response({
            'success': success,
            'stats': stats
        })
    
    @action(detail=True, methods=['post'])
    def sync_inventory(self, request, pk=None):
        """Sync inventory with POS"""
        connection = self.get_object()
        success, stats = connection.sync_inventory()
        
        return Response({
            'success': success,
            'stats': stats
        })
    
    @action(detail=True, methods=['post'])
    def register_webhook(self, request, pk=None):
        """Register webhook with POS"""
        connection = self.get_object()
        success = connection.register_webhook()
        
        return Response({
            'success': success,
            'webhook_registered': connection.webhook_registered
        })

class TableLayoutViewSet(viewsets.ModelViewSet):
    queryset = TableLayout.objects.all()
    serializer_class = TableLayoutSerializer
    permission_classes = [IsAuthenticated, IsRestaurantOwner]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['restaurant', 'branch', 'layout_type', 'is_active']
    search_fields = ['layout_name', 'branch__address__city']
    
    def get_queryset(self):
        if self.request.user.user_type == 'owner':
            return TableLayout.objects.filter(
                restaurant__owner=self.request.user
            )
        return super().get_queryset()
    
    @action(detail=True, methods=['post'])
    def generate_qr_codes(self, request, pk=None):
        """Generate QR codes for table layout"""
        layout = self.get_object()
        success = layout.generate_qr_codes()
        
        return Response({
            'success': success,
            'qr_codes_generated': len(layout.qr_codes)
        })
    
    @action(detail=True, methods=['get'])
    def table_status(self, request, pk=None):
        """Get status of all tables in layout"""
        layout = self.get_object()
        table_statuses = {}
        
        for table_data in layout.layout_data.get('tables', []):
            table_number = table_data.get('number')
            if table_number:
                table_statuses[table_number] = layout.get_table_status(table_number)
        
        return Response(table_statuses)

class KitchenStationViewSet(viewsets.ModelViewSet):
    queryset = KitchenStation.objects.all()
    serializer_class = KitchenStationSerializer
    permission_classes = [IsAuthenticated, IsRestaurantOwner]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['restaurant', 'branch', 'station_type', 'is_available']
    search_fields = ['name', 'branch__address__city']
    
    def get_queryset(self):
        if self.request.user.user_type == 'owner':
            return KitchenStation.objects.filter(
                restaurant__owner=self.request.user
            )
        return super().get_queryset()
    
    @action(detail=True, methods=['get'])
    def workload(self, request, pk=None):
        """Get current workload for station"""
        station = self.get_object()
        workload = station.get_current_workload()
        
        return Response(workload)
    
    @action(detail=False, methods=['get'])
    def queue(self, request):
        """Get kitchen order queue"""
        restaurant_id = request.query_params.get('restaurant_id')
        branch_id = request.query_params.get('branch_id')
        
        queryset = self.get_queryset()
        if restaurant_id:
            queryset = queryset.filter(restaurant_id=restaurant_id)
        if branch_id:
            queryset = queryset.filter(branch_id=branch_id)
        
        stations_data = []
        for station in queryset:
            station_data = KitchenStationSerializer(station).data
            station_data['current_items'] = OrderItemPreparation.objects.filter(
                assigned_station=station,
                preparation_status__in=['pending', 'preparing']
            ).count()
            stations_data.append(station_data)
        
        return Response(stations_data)

class OrderRoutingViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = OrderPOSInfo.objects.all()
    serializer_class = OrderRoutingSerializer
    permission_classes = [IsAuthenticated, IsRestaurantOwner]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['order__restaurant', 'pos_sync_status', 'table_number']
    
    def get_queryset(self):
        if self.request.user.user_type == 'owner':
            return OrderPOSInfo.objects.filter(
                order__restaurant__owner=self.request.user
            )
        return super().get_queryset()
    
    @action(detail=True, methods=['post'])
    def route(self, request, pk=None):
        """Intelligent order routing to kitchen stations"""
        order_pos_info = self.get_object()
        order = order_pos_info.order
        
        # Implement order routing logic
        routing_result = self.route_order_to_stations(order)
        
        return Response(routing_result)
    
    def route_order_to_stations(self, order):
        """Route order items to appropriate kitchen stations"""
        from ..services.order_routing_service import OrderRoutingService
        
        routing_service = OrderRoutingService(order)
        routing_result = routing_service.route_order()
        
        return routing_result

class KitchenOrderViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def queue(self, request):
        """Get kitchen order queue"""
        restaurant_id = request.query_params.get('restaurant_id')
        branch_id = request.query_params.get('branch_id')
        
        # Get orders in preparation
        orders = Order.objects.filter(
            status__in=['confirmed', 'preparing']
        )
        
        if restaurant_id:
            orders = orders.filter(restaurant_id=restaurant_id)
        if branch_id:
            orders = orders.filter(branch_id=branch_id)
        
        queue_data = []
        for order in orders:
            order_data = {
                'order_id': order.order_uuid,
                'table_number': getattr(order.pos_info, 'table_number', None),
                'items': []
            }
            
            for item in order.order_items.all():
                prep_info = getattr(item, 'preparation_info', None)
                if prep_info:
                    order_data['items'].append({
                        'item_id': item.order_item_id,
                        'name': item.menu_item.name,
                        'station': prep_info.assigned_station.name if prep_info.assigned_station else None,
                        'status': prep_info.preparation_status,
                        'started_at': prep_info.preparation_started_at,
                        'estimated_completion': prep_info.estimated_completion_at
                    })
            
            queue_data.append(order_data)
        
        return Response(queue_data)

# Webhook endpoints
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

@api_view(['POST'])
@permission_classes([IsPOSWebhook])
def pos_order_webhook(request):
    """Handle POS order status updates"""
    from ..services.webhook_services import WebhookService
    
    try:
        webhook_service = WebhookService()
        result = webhook_service.process_order_webhook(request.data)
        
        return Response({'success': True, 'processed': result})
    
    except Exception as e:
        return Response(
            {'success': False, 'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['POST'])
@permission_classes([IsPOSWebhook])
def pos_menu_webhook(request):
    """Handle POS menu changes"""
    from ..services.webhook_services import WebhookService
    
    try:
        webhook_service = WebhookService()
        result = webhook_service.process_menu_webhook(request.data)
        
        return Response({'success': True, 'processed': result})
    
    except Exception as e:
        return Response(
            {'success': False, 'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['POST'])
@permission_classes([IsPOSWebhook])
def pos_inventory_webhook(request):
    """Handle POS inventory changes"""
    from ..services.webhook_services import WebhookService
    
    try:
        webhook_service = WebhookService()
        result = webhook_service.process_inventory_webhook(request.data)
        
        return Response({'success': True, 'processed': result})
    
    except Exception as e:
        return Response(
            {'success': False, 'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    
# Add these view functions
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsRestaurantOwner])
def route_order_to_kitchen(request, order_uuid):
    """Route order to kitchen stations"""
    from ..models import Order
    from ..services.order_routing_service import OrderRoutingService
    
    try:
        order = Order.objects.get(order_uuid=order_uuid, restaurant__owner=request.user)
        routing_service = OrderRoutingService(order)
        routing_result = routing_service.route_order()
        
        return Response({
            'success': True,
            'routing_result': routing_result
        })
        
    except Order.DoesNotExist:
        return Response({'success': False, 'error': 'Order not found'}, status=404)

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsRestaurantOwner])
def assign_order_station(request, order_uuid):
    """Assign specific station to order"""
    from ..models import Order, KitchenStation
    
    try:
        order = Order.objects.get(order_uuid=order_uuid, restaurant__owner=request.user)
        station_id = request.data.get('station_id')
        item_id = request.data.get('item_id')
        
        if not station_id or not item_id:
            return Response({'success': False, 'error': 'station_id and item_id required'}, status=400)
        
        station = KitchenStation.objects.get(station_id=station_id, restaurant=order.restaurant)
        order_item = order.order_items.get(order_item_id=item_id)
        
        if hasattr(order_item, 'preparation_info'):
            order_item.preparation_info.assign_to_station(station)
            
            return Response({
                'success': True,
                'message': f'Item assigned to {station.name}'
            })
        else:
            return Response({'success': False, 'error': 'Preparation info not found'}, status=400)
            
    except (Order.DoesNotExist, KitchenStation.DoesNotExist, OrderItem.DoesNotExist) as e:
        return Response({'success': False, 'error': str(e)}, status=404)

@api_view(['PUT'])
@permission_classes([IsAuthenticated, IsRestaurantOwner])
def update_preparation_status(request, order_uuid):
    """Update preparation status for order items"""
    from ..models import Order
    
    try:
        order = Order.objects.get(order_uuid=order_uuid, restaurant__owner=request.user)
        item_id = request.data.get('item_id')
        status = request.data.get('status')
        notes = request.data.get('notes', '')
        
        if not item_id or not status:
            return Response({'success': False, 'error': 'item_id and status required'}, status=400)
        
        success = order.update_kitchen_status(item_id, status, notes=notes)
        
        if success:
            return Response({
                'success': True,
                'message': f'Item status updated to {status}'
            })
        else:
            return Response({'success': False, 'error': 'Failed to update status'}, status=400)
            
    except Order.DoesNotExist:
        return Response({'success': False, 'error': 'Order not found'}, status=404)