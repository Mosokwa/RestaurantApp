from decimal import Decimal
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.db import transaction
from ..models import Customer, MenuItem, Order, OrderItem, OrderItemModifier, OrderTracking, ItemModifier

class OrderItemModifierSerializer(serializers.ModelSerializer):
    modifier_name = serializers.CharField(source='item_modifier.name', read_only=True)
    modifier_group = serializers.CharField(source='item_modifier.modifier_group.name', read_only=True)
    
    class Meta:
        model = OrderItemModifier
        fields = [
            'order_item_modifier_id', 'item_modifier', 'modifier_name', 'modifier_group',
            'quantity', 'unit_price', 'total_price'
        ]
        read_only_fields = ['order_item_modifier_id', 'total_price']

class OrderItemSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='menu_item.name', read_only=True)
    modifiers = OrderItemModifierSerializer(many=True, read_only=True)
    dietary_info = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderItem
        fields = [
            'order_item_id', 'menu_item', 'item_name', 'quantity', 'unit_price',
            'total_price', 'special_instructions', 'modifiers', 'dietary_info'
        ]
        read_only_fields = ['order_item_id', 'total_price']
    
    def get_dietary_info(self, obj):
        return {
            'vegetarian': obj.menu_item.is_vegetarian,
            'vegan': obj.menu_item.is_vegan,
            'gluten_free': obj.menu_item.is_gluten_free
        }

class OrderTrackingSerializer(serializers.ModelSerializer):
    updated_by_username = serializers.CharField(source='updated_by.username', read_only=True)
    
    class Meta:
        model = OrderTracking
        fields = [
            'tracking_id', 'status', 'description', 'updated_by', 'updated_by_username', 'created_at'
        ]
        read_only_fields = ['tracking_id', 'created_at']

class OrderSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.user.get_full_name', read_only=True)
    customer_email = serializers.CharField(source='customer.user.email', read_only=True)
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    branch_address = serializers.SerializerMethodField(read_only=True)
    order_items = OrderItemSerializer(many=True, read_only=True)
    tracking_history = OrderTrackingSerializer(many=True, read_only=True)
    estimated_delivery_minutes = serializers.SerializerMethodField()
    applied_offers_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'order_id', 'order_uuid', 'customer', 'customer_name', 'customer_email',
            'restaurant', 'restaurant_name', 'branch', 'branch_address',
            'order_type', 'status', 'special_instructions',
            'subtotal', 'tax_amount', 'delivery_fee', 'discount_amount', 'total_amount',
            'delivery_address', 'estimated_delivery_time', 'estimated_delivery_minutes',
            'table_number', 'order_placed_at', 'confirmed_at', 'preparation_started_at',
            'ready_at', 'delivered_at', 'cancelled_at', 'order_items', 'tracking_history', 'applied_offers_info'
        ]
        read_only_fields = [
            'order_id', 'order_uuid', 'subtotal', 'tax_amount', 'delivery_fee',
            'discount_amount', 'total_amount', 'order_placed_at', 'confirmed_at',
            'preparation_started_at', 'ready_at', 'delivered_at', 'cancelled_at'
        ]
    
    def get_branch_address(self, obj):
        if obj.branch and obj.branch.address:
            return str(obj.branch.address)
        return None
    
    def get_estimated_delivery_minutes(self, obj):
        if obj.estimated_delivery_time and obj.order_placed_at:
            delta = obj.estimated_delivery_time - obj.order_placed_at
            return int(delta.total_seconds() / 60)
        return None
    
    def get_applied_offers_info(self, obj):  # ADDED
        """Get applied offers information"""
        if hasattr(obj, 'get_applied_offers_info'):
            return obj.get_applied_offers_info()
        return []


class OrderCreateSerializer(serializers.ModelSerializer):
    items = serializers.JSONField(write_only=True)  # Format: [{"menu_item_id": 1, "quantity": 2, "modifiers": [{"modifier_id": 1, "quantity": 1}]}]
    applied_offer_ids = serializers.ListField(  # ADDED
        child=serializers.IntegerField(),
        required=False,
        default=[],
        write_only=True
    )
    
    class Meta:
        model = Order
        fields = [
            'restaurant', 'branch', 'order_type', 'special_instructions',
            'delivery_address', 'table_number', 'items', 'applied_offer_ids'
        ]
    
    def validate(self, data):
        # Validate that branch belongs to restaurant
        if data['branch'].restaurant != data['restaurant']:
            raise ValidationError("Branch must belong to the selected restaurant")
        
        # Validate order type requirements
        if data['order_type'] == 'delivery' and not data.get('delivery_address'):
            raise ValidationError("Delivery address is required for delivery orders")
        
        if data['order_type'] == 'dine_in' and not data.get('table_number'):
            raise ValidationError("Table number is required for dine-in orders")
        
        # Validate applied offers
        offer_ids = data.get('applied_offer_ids', [])
        if offer_ids:
            from ..models import SpecialOffer
            valid_offers = SpecialOffer.objects.filter(
                offer_id__in=offer_ids,
                restaurant=data['restaurant'],
                is_active=True
            )
            if valid_offers.count() != len(offer_ids):
                raise ValidationError("Some offers are not valid")
        
        return data
    
    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        applied_offer_ids = validated_data.pop('applied_offer_ids', [])
        customer, created = Customer.objects.get_or_create(user = self.context['request'].user)
        
        # Create order first
        order = Order.objects.create(
            customer=customer,
            **validated_data
        )

        # Apply offers if any
        if applied_offer_ids:
            from ..models import SpecialOffer
            offers = SpecialOffer.objects.filter(offer_id__in=applied_offer_ids)
            for offer in offers:
                if offer.is_valid() and offer.can_user_use(self.context['request'].user):
                    order.apply_special_offer(offer, customer.customer_profile)
        
        # Then create order items
        subtotal = Decimal('0')
        for item_data in items_data:
            order_item = self._create_order_item(order, item_data)
            subtotal += Decimal(str(order_item.total_price))
        
        # Set order totals
        order.subtotal = subtotal
        order.tax_amount = subtotal * Decimal('0.1')  # Example: 10% tax
        order.delivery_fee = Decimal('5.00') if order.order_type == 'delivery' else Decimal('0')
        order.total_amount = order.subtotal + order.tax_amount + order.delivery_fee
        order.save()
        
        # Create initial tracking
        OrderTracking.objects.create(
            order=order,
            status='pending',
            description='Order placed successfully',
            updated_by=self.context['request'].user
        )
        
        return order
    
    def _create_order_item(self, order, item_data):
        try:
            menu_item = MenuItem.objects.get(pk=item_data['menu_item_id'], is_available=True)
        except MenuItem.DoesNotExist:
            raise ValidationError(f"Menu item {item_data['menu_item_id']} not available")
        
        order_item = OrderItem.objects.create(
            order=order,
            menu_item=menu_item,
            quantity=item_data['quantity'],
            unit_price=menu_item.price,
            special_instructions=item_data.get('special_instructions', '')
        )
        
        # Add modifiers if any
        for modifier_data in item_data.get('modifiers', []):
            self._create_order_item_modifier(order_item, modifier_data)

        
        # Update order subtotal - convert to Decimal for consistency
        from decimal import Decimal
        order.subtotal += Decimal(str(order_item.total_price))

        return order_item
    
    def _create_order_item_modifier(self, order_item, modifier_data):  # ADDED MISSING METHOD
        """Create order item modifier"""
        try:
            item_modifier = ItemModifier.objects.get(
                pk=modifier_data['modifier_id'],
                is_available=True
            )
        except ItemModifier.DoesNotExist:
            raise ValidationError(f"Modifier {modifier_data['modifier_id']} not available")
        
        OrderItemModifier.objects.create(
            order_item=order_item,
            item_modifier=item_modifier,
            quantity=modifier_data.get('quantity', 1),
            unit_price=item_modifier.price_modifier
        )
    

#enhanced order with offer serializer
class OrderWithOffersSerializer(OrderSerializer):
    """
    Enhanced order serializer with complete offer functionality
    Extends OrderSerializer to maintain all existing fields
    """
    payment_status = serializers.CharField(source='payment.payment_status', read_only=True)
    available_offers_at_time = serializers.SerializerMethodField()
    
    class Meta(OrderSerializer.Meta):
        fields = OrderSerializer.Meta.fields + [
            'payment_status', 'available_offers_at_time', 'loyalty_points_earned'
        ]
    
    def get_available_offers_at_time(self, obj):
        """Get offers that were available when order was placed"""
        from ..serializers import EnhancedSpecialOfferSerializer
        try:
            # Get offers that were valid at order placement time
            valid_offers = obj.restaurant.special_offers.filter(
                is_active=True,
                valid_from__lte=obj.order_placed_at,
                valid_until__gte=obj.order_placed_at
            )
            return EnhancedSpecialOfferSerializer(
                valid_offers, 
                many=True, 
                context=self.context
            ).data
        except:
            return []
