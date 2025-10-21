# pos_integration_serializers.py
from rest_framework import serializers
from ..models import (
    POSConnection, TableLayout, KitchenStation, 
    OrderPOSInfo, OrderItemPreparation, POSSyncLog
)
from api.models import Order, OrderItem

class POSConnectionSerializer(serializers.ModelSerializer):
    pos_type_display = serializers.CharField(source='get_pos_type_display', read_only=True)
    sync_status_display = serializers.CharField(source='get_sync_status_display', read_only=True)
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    
    class Meta:
        model = POSConnection
        fields = [
            'connection_id', 'restaurant', 'restaurant_name', 'pos_type', 'pos_type_display',
            'connection_name', 'is_active', 'sync_status', 'sync_status_display',
            'last_sync', 'last_successful_sync', 'auto_sync_menu', 'auto_sync_inventory',
            'auto_sync_orders', 'sync_frequency', 'last_error', 'error_count',
            'webhook_registered', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'connection_id', 'last_sync', 'last_successful_sync', 'last_error',
            'error_count', 'webhook_registered', 'created_at', 'updated_at'
        ]
    
    def validate(self, data):
        # Validate custom POS requires base_url
        if data.get('pos_type') == 'custom' and not data.get('base_url'):
            raise serializers.ValidationError({
                'base_url': 'Custom POS systems require a base URL'
            })
        return data

class TableLayoutSerializer(serializers.ModelSerializer):
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    branch_city = serializers.CharField(source='branch.address.city', read_only=True)
    table_count = serializers.SerializerMethodField()
    
    class Meta:
        model = TableLayout
        fields = [
            'layout_id', 'restaurant', 'restaurant_name', 'branch', 'branch_city',
            'layout_name', 'layout_type', 'layout_data', 'qr_codes', 'qr_base_url',
            'is_active', 'is_default', 'table_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['layout_id', 'created_at', 'updated_at']
    
    def get_table_count(self, obj):
        return len(obj.layout_data.get('tables', []))

class KitchenStationSerializer(serializers.ModelSerializer):
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    branch_city = serializers.CharField(source='branch.address.city', read_only=True)
    station_type_display = serializers.CharField(source='get_station_type_display', read_only=True)
    current_workload = serializers.SerializerMethodField()
    assigned_staff_count = serializers.SerializerMethodField()
    
    class Meta:
        model = KitchenStation
        fields = [
            'station_id', 'restaurant', 'restaurant_name', 'branch', 'branch_city',
            'name', 'station_type', 'station_type_display', 'description',
            'max_concurrent_items', 'avg_prep_time', 'is_available',
            'assigned_staff', 'assigned_categories', 'current_workload',
            'assigned_staff_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['station_id', 'created_at', 'updated_at']
    
    def get_current_workload(self, obj):
        return obj.get_current_workload()
    
    def get_assigned_staff_count(self, obj):
        return obj.assigned_staff.count()

class OrderRoutingSerializer(serializers.ModelSerializer):
    order_uuid = serializers.UUIDField(source='order.order_uuid', read_only=True)
    customer_name = serializers.CharField(source='order.customer.user.get_full_name', read_only=True)
    table_number = serializers.CharField(read_only=True)
    station_assignments = serializers.JSONField(read_only=True)
    
    class Meta:
        model = OrderPOSInfo
        fields = [
            'order', 'order_uuid', 'customer_name', 'pos_order_id',
            'table_number', 'station_assignments', 'preparation_started_at',
            'estimated_ready_at', 'actual_ready_at', 'pos_sync_status'
        ]

class OrderItemPreparationSerializer(serializers.ModelSerializer):
    menu_item_name = serializers.CharField(source='order_item.menu_item.name', read_only=True)
    station_name = serializers.CharField(source='assigned_station.name', read_only=True)
    preparation_status_display = serializers.CharField(
        source='get_preparation_status_display', 
        read_only=True
    )
    
    class Meta:
        model = OrderItemPreparation
        fields = [
            'id', 'order_item', 'menu_item_name', 'assigned_station', 'station_name',
            'preparation_status', 'preparation_status_display', 'preparation_started_at',
            'estimated_completion_at', 'actual_completion_at', 'quality_check_passed',
            'quality_notes', 'checked_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class POSSyncLogSerializer(serializers.ModelSerializer):
    connection_name = serializers.CharField(source='connection.connection_name', read_only=True)
    sync_type_display = serializers.CharField(source='get_sync_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = POSSyncLog
        fields = [
            'log_id', 'connection', 'connection_name', 'sync_type', 'sync_type_display',
            'status', 'status_display', 'items_processed', 'items_created',
            'items_updated', 'items_failed', 'error_message', 'started_at',
            'completed_at', 'duration_seconds'
        ]
        read_only_fields = fields