from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from ..models import Payment, Cart, CartItem, CartItemModifier
from .restaurantsHomepageSerializers import EnhancedSpecialOfferSerializer

class PaymentSerializer(serializers.ModelSerializer):
    order_uuid = serializers.CharField(source='order.order_uuid', read_only=True)
    customer_email = serializers.CharField(source='order.customer.user.email', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'payment_id', 'order', 'order_uuid', 'payment_method', 'payment_status',
            'amount', 'transaction_id', 'customer_email', 'payment_initiated_at',
            'payment_completed_at', 'refund_amount', 'refund_reason'
        ]
        read_only_fields = [
            'payment_id', 'payment_status', 'amount', 'transaction_id',
            'payment_initiated_at', 'payment_completed_at', 'refund_amount'
        ]
    
    def validate(self, data):
        order = data['order']
        
        # Validate order belongs to customer
        if self.context['request'].user != order.customer.user:
            raise ValidationError("You can only pay for your own orders")
        
        # Validate order status
        if order.status != 'pending':
            raise ValidationError("Order is not in a payable state")
        
        # Validate payment amount matches order total
        if data.get('amount') and float(data['amount']) != float(order.total_amount):
            raise ValidationError("Payment amount doesn't match order total")
        
        return data
    
# Cart serializers
class CartItemModifierSerializer(serializers.ModelSerializer):
    modifier_name = serializers.CharField(source='item_modifier.name', read_only=True)
    
    class Meta:
        model = CartItemModifier
        fields = ['cart_item_modifier_id', 'item_modifier', 'modifier_name', 'quantity', 'unit_price', 'total_price']
        read_only_fields = ['cart_item_modifier_id', 'total_price']

class CartItemSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='menu_item.name', read_only=True)
    item_price = serializers.DecimalField(source='menu_item.price', read_only=True, max_digits=10, decimal_places=2)
    modifiers = CartItemModifierSerializer(many=True, read_only=True)
    
    class Meta:
        model = CartItem
        fields = [
            'cart_item_id', 'menu_item', 'item_name', 'item_price', 'quantity',
            'unit_price', 'total_price', 'special_instructions', 'modifiers'
        ]
        read_only_fields = ['cart_item_id', 'total_price', 'created_at', 'updated_at']
    
    def validate_menu_item(self, value):
        """Validate that menu item is available"""
        if not value.is_available:
            raise ValidationError("This menu item is not available")
        return value
    
    def validate(self, data):
        """Validate cart item consistency"""
        menu_item = data.get('menu_item')
        cart = self.context.get('cart')
        
        if cart and menu_item:
            # Check if item belongs to cart's restaurant
            if cart.restaurant != menu_item.category.restaurant:
                raise ValidationError(
                    "Cannot add items from different restaurants to the same cart"
                )
        
        return data

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    
    class Meta:
        model = Cart
        fields = ['cart_id', 'restaurant', 'restaurant_name', 'items', 'subtotal', 'total_items', 'updated_at']
        read_only_fields = ['cart_id', 'subtotal', 'total_items', 'updated_at']


#enhanced cart serializer with offers
class CartWithOffersSerializer(CartSerializer):
    """
    Enhanced cart serializer with special offers functionality
    Use this when you need to show applied offers and discounts
    """
    applied_offers = serializers.SerializerMethodField()
    available_offers = serializers.SerializerMethodField()
    discount_amount = serializers.SerializerMethodField()
    total_with_discount = serializers.SerializerMethodField()
    
    class Meta(CartSerializer.Meta):
        fields = CartSerializer.Meta.fields + [
            'applied_offers', 'available_offers', 'discount_amount', 'total_with_discount'
        ]
    
    def get_applied_offers(self, obj):
        """Get applied offers with details"""
        offers = obj.applied_offers.filter(is_active=True)
        return EnhancedSpecialOfferSerializer(
            offers, 
            many=True, 
            context=self.context
        ).data
    
    def get_available_offers(self, obj):
        """Get available offers that can be applied to this cart"""
        request = self.context.get('request')
        
        if request and request.user.is_authenticated and hasattr(request.user, 'customer_profile'):
            offers = obj.get_available_offers(request.user.customer_profile)
            return EnhancedSpecialOfferSerializer(
                offers, 
                many=True, 
                context=self.context
            ).data
        return []
    
    def get_discount_amount(self, obj):
        return float(obj.discount_amount)
    
    def get_total_with_discount(self, obj):
        return float(obj.total_with_discount)

class CartItemWithOffersSerializer(CartItemSerializer):
    """
    Enhanced cart item serializer for when offer details are needed
    """
    is_eligible_for_offers = serializers.SerializerMethodField()
    
    class Meta(CartItemSerializer.Meta):
        fields = CartItemSerializer.Meta.fields + ['is_eligible_for_offers']
    
    def get_is_eligible_for_offers(self, obj):
        """Check if this item is eligible for any current offers"""
        cart = obj.cart
        if not cart.applied_offers.exists():
            return True
        
        # Check if this item is part of any applied offers
        for offer in cart.applied_offers.all():
            if offer.applicable_items.exists():
                if obj.menu_item in offer.applicable_items.all():
                    return True
        return True  # Default to True if no item-specific offers
