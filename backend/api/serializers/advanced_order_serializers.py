from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.utils import timezone
from ..models import (
    GroupOrder, GroupOrderParticipant, ScheduledOrder, 
    OrderTemplate, BulkOrder, BulkOrderItem
)

class GroupOrderParticipantSerializer(serializers.ModelSerializer):
    customer_email = serializers.CharField(source='customer.user.email', read_only=True)
    customer_name = serializers.CharField(source='customer.user.get_full_name', read_only=True)
    order_status = serializers.CharField(source='order.status', read_only=True, allow_null=True)
    order_total = serializers.DecimalField(source='order.total_amount', read_only=True, max_digits=10, decimal_places=2, allow_null=True)
    
    class Meta:
        model = GroupOrderParticipant
        fields = [
            'participant_id', 'customer', 'customer_email', 'customer_name',
            'display_name', 'is_organizer', 'order', 'order_status', 'order_total',
            'joined_at', 'left_at'
        ]
        read_only_fields = ['participant_id', 'joined_at', 'left_at']

class GroupOrderSerializer(serializers.ModelSerializer):
    organizer_name = serializers.CharField(source='organizer.user.get_full_name', read_only=True)
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    participants = GroupOrderParticipantSerializer(many=True, read_only=True)
    participant_count = serializers.IntegerField(source='participants.count', read_only=True)
    is_joinable = serializers.BooleanField(read_only=True)
    time_remaining = serializers.SerializerMethodField()
    
    class Meta:
        model = GroupOrder
        fields = [
            'group_id', 'organizer', 'organizer_name', 'restaurant', 'restaurant_name',
            'name', 'description', 'share_code', 'status', 'allow_anyone_to_join',
            'max_participants', 'order_deadline', 'estimated_delivery_time',
            'subtotal', 'total_amount', 'participants', 'participant_count',
            'is_joinable', 'time_remaining', 'created_at', 'updated_at', 'closed_at'
        ]
        read_only_fields = [
            'group_id', 'share_code', 'subtotal', 'total_amount', 'created_at',
            'updated_at', 'closed_at'
        ]
    
    def get_time_remaining(self, obj):
        now = timezone.now()
        if obj.order_deadline > now:
            return obj.order_deadline - now
        return None
    
    def validate_order_deadline(self, value):
        if value <= timezone.now():
            raise ValidationError("Order deadline must be in the future")
        return value

class GroupOrderCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupOrder
        fields = [
            'restaurant', 'name', 'description', 'allow_anyone_to_join',
            'max_participants', 'order_deadline', 'estimated_delivery_time'
        ]
    
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['organizer'] = request.user.customer_profile
        return super().create(validated_data)

class JoinGroupOrderSerializer(serializers.Serializer):
    share_code = serializers.CharField(max_length=20, required=True)
    display_name = serializers.CharField(max_length=100, required=True)
    
    def validate(self, data):
        share_code = data['share_code']
        try:
            group_order = GroupOrder.objects.get(share_code=share_code)
            if not group_order.is_joinable():
                raise ValidationError("This group order is no longer accepting participants")
            
            # Check if user is already a participant
            request = self.context.get('request')
            if group_order.participants.filter(customer=request.user.customer_profile).exists():
                raise ValidationError("You have already joined this group order")
            
            data['group_order'] = group_order
        except GroupOrder.DoesNotExist:
            raise ValidationError("Invalid group order code")
        return data

class OrderTemplateSerializer(serializers.ModelSerializer):
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    delivery_address_text = serializers.CharField(source='delivery_address.get_full_address', read_only=True)
    
    class Meta:
        model = OrderTemplate
        fields = [
            'template_id', 'customer', 'restaurant', 'restaurant_name',
            'name', 'description', 'order_type', 'delivery_address',
            'delivery_address_text', 'special_instructions', 'items_configuration',
            'is_active', 'usage_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['template_id', 'usage_count', 'created_at', 'updated_at']
    
    def validate_items_configuration(self, value):
        if not isinstance(value, dict) or 'items' not in value:
            raise ValidationError("Items configuration must include 'items' array")
        
        for item in value['items']:
            if 'menu_item_id' not in item or 'quantity' not in item:
                raise ValidationError("Each item must include menu_item_id and quantity")
        
        return value

class ScheduledOrderSerializer(serializers.ModelSerializer):
    customer_email = serializers.CharField(source='customer.user.email', read_only=True)
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    template_name = serializers.CharField(source='order_template.name', read_only=True)
    
    class Meta:
        model = ScheduledOrder
        fields = [
            'schedule_id', 'customer', 'customer_email', 'restaurant', 'restaurant_name',
            'schedule_type', 'scheduled_for', 'timezone', 'order_template', 'template_name',
            'recurrence_end', 'recurrence_days', 'is_active', 'last_processed',
            'next_occurrence', 'created_at', 'updated_at'
        ]
        read_only_fields = ['schedule_id', 'last_processed', 'next_occurrence', 'created_at', 'updated_at']
    
    def validate_scheduled_for(self, value):
        if value <= timezone.now():
            raise ValidationError("Scheduled time must be in the future")
        return value

class BulkOrderItemSerializer(serializers.ModelSerializer):
    menu_item_name = serializers.CharField(source='menu_item.name', read_only=True)
    menu_item_description = serializers.CharField(source='menu_item.description', read_only=True, allow_null=True)
    
    class Meta:
        model = BulkOrderItem
        fields = [
            'bulk_item_id', 'menu_item', 'menu_item_name', 'menu_item_description',
            'quantity', 'unit_price', 'total_price', 'special_instructions'
        ]
        read_only_fields = ['bulk_item_id', 'total_price']

class BulkOrderSerializer(serializers.ModelSerializer):
    customer_email = serializers.CharField(source='customer.user.email', read_only=True)
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    delivery_address_text = serializers.CharField(source='delivery_address.get_full_address', read_only=True)
    items = BulkOrderItemSerializer(many=True, required=False)
    
    class Meta:
        model = BulkOrder
        fields = [
            'bulk_order_id', 'customer', 'customer_email', 'restaurant', 'restaurant_name',
            'event_type', 'event_name', 'event_description', 'event_date',
            'number_of_guests', 'contact_person', 'contact_phone', 'contact_email',
            'delivery_address', 'delivery_address_text', 'setup_requirements',
            'special_instructions', 'estimated_amount', 'deposit_amount',
            'final_amount', 'status', 'admin_notes', 'items', 'created_at', 'updated_at'
        ]
        read_only_fields = ['bulk_order_id', 'final_amount', 'created_at', 'updated_at']
    
    def validate_event_date(self, value):
        if value <= timezone.now():
            raise ValidationError("Event date must be in the future")
        return value

class CreateOrderFromTemplateSerializer(serializers.Serializer):
    template_id = serializers.IntegerField(required=True)
    
    def validate(self, data):
        template_id = data['template_id']
        request = self.context.get('request')
        
        try:
            template = OrderTemplate.objects.get(
                pk=template_id,
                customer=request.user.customer_profile,
                is_active=True
            )
            data['template'] = template
        except OrderTemplate.DoesNotExist:
            raise ValidationError("Order template not found or not accessible")
        return data