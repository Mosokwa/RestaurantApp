from rest_framework import generics, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.core.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from ..models import Customer, MenuItem, Cart, CartItem, SpecialOffer
from ..serializers import CartSerializer, CartItemSerializer, CartWithOffersSerializer


class CartDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        # Use enhanced serializer for offers when requested
        if self.request.query_params.get('with_offers') == 'true':
            return CartWithOffersSerializer
        return CartSerializer
    
    def get_object(self):
        if self.request.user.user_type != 'customer':
            raise PermissionDenied("Only customers can access cart")
        
        customer, created = Customer.objects.get_or_create(user = self.request.user)
        
        cart, created = Cart.objects.get_or_create(customer=customer)

        return cart

class CartItemView(generics.CreateAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def perform_create(self, serializer):
        if self.request.user.user_type != 'customer':
            raise PermissionDenied("Only customers can add to cart")
        
        customer, created = Customer.objects.get_or_create(user=self.request.user)

        cart, created = Cart.objects.get_or_create(customer=customer)
        
        # Save the cart first to ensure it has a primary key
        if created:
            cart.save()
        
        # Validate the menu item and get its restaurant
        menu_item_id = self.request.data.get('menu_item')
        try:
            menu_item = MenuItem.objects.get(pk=menu_item_id, is_available=True)
        except MenuItem.DoesNotExist:
            raise ValidationError("Menu item not available")
        
        # Check if cart already has items from a different restaurant
        if cart.cart_items.exists():
            existing_restaurant = cart.cart_items.first().menu_item.category.restaurant
            if existing_restaurant != menu_item.category.restaurant:
                raise ValidationError(
                    "Cannot add items from different restaurants to the same cart"
                )
        
        # Set cart restaurant if not set
        if not cart.restaurant:
            cart.restaurant = menu_item.category.restaurant
            cart.save()
        
        # Now create the cart item
        serializer.save(cart=cart, unit_price=menu_item.price)

# ADD NEW OFFER MANAGEMENT VIEWS
class CartApplyOfferView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, offer_id):
        if request.user.user_type != 'customer':
            raise PermissionDenied("Only customers can apply offers")
        
        customer, created = Customer.objects.get_or_create(user=request.user)
        cart = get_object_or_404(Cart, customer=customer)
        offer = get_object_or_404(SpecialOffer, offer_id=offer_id)
        
        try:
            success = cart.apply_offer(offer, customer)
            if success:
                serializer = CartWithOffersSerializer(cart, context={'request': request})
                return Response(serializer.data)
            else:
                return Response(
                    {'error': 'Failed to apply offer'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        except ValidationError as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

class CartRemoveOfferView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, offer_id):
        if request.user.user_type != 'customer':
            raise PermissionDenied("Only customers can remove offers")
        
        customer, created = Customer.objects.get_or_create(user=request.user)
        cart = get_object_or_404(Cart, customer=customer)
        offer = get_object_or_404(SpecialOffer, offer_id=offer_id)
        
        try:
            success = cart.remove_offer(offer)
            if success:
                serializer = CartWithOffersSerializer(cart, context={'request': request})
                return Response(serializer.data)
            else:
                return Response(
                    {'error': 'Offer not found in cart'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

class CartItemUpdateView(generics.UpdateAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.user_type != 'customer':
            return CartItem.objects.none()
        
        return CartItem.objects.filter(cart__customer__user=self.request.user)
    
    def perform_update(self, serializer):
        instance = serializer.save()
        # Recalculate cart totals
        instance.cart.save()

class CartItemDeleteView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.user_type != 'customer':
            return CartItem.objects.none()
        
        return CartItem.objects.filter(cart__customer__user=self.request.user)
    
    def perform_destroy(self, instance):
        cart = instance.cart
        instance.delete()
        # Recalculate cart totals
        cart.save()