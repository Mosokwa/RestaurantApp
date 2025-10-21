from django.utils import timezone 
import uuid
from rest_framework import generics
from django.db import transaction
from django.core.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from ..models import Restaurant, Payment
from ..serializers import PaymentSerializer


class PaymentCreateView(generics.CreateAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def perform_create(self, serializer):
        order = serializer.validated_data['order']
        
        # Verify order belongs to authenticated customer
        if order.customer.user != self.request.user:
            raise PermissionDenied("You can only pay for your own orders")
        
        # Verify order is in payable state
        if order.status != 'pending':
            raise ValidationError("Order is not in a payable state")
        
        # Create payment with initial processing status
        payment = serializer.save(
            amount=order.total_amount,
            payment_status='processing'
        )
        
        # Here you would integrate with your payment gateway (Stripe, PayPal, etc.)
        # For now, we'll simulate successful payment
        self._process_payment(payment)
    
    def _process_payment(self, payment):
        """Simulate payment processing - Replace with actual payment gateway integration"""
        try:
            # Simulate payment processing
            payment.transaction_id = f"txn_{uuid.uuid4().hex[:16]}"
            payment.payment_status = 'completed'
            payment.payment_completed_at = timezone.now()
            payment.save()
            
            # Update order status
            payment.order.update_status('confirmed')
            
        except Exception as e:
            payment.payment_status = 'failed'
            payment.payment_failed_at = timezone.now()
            payment.save()
            raise ValidationError(f"Payment processing failed: {str(e)}")

class PaymentDetailView(generics.RetrieveAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.user_type == 'customer':
            return Payment.objects.filter(order__customer__user=user)
        
        elif user.user_type in ['owner', 'staff']:
            if user.user_type == 'owner':
                restaurant_ids = Restaurant.objects.filter(owner=user).values_list('restaurant_id', flat=True)
            else:
                restaurant_ids = [user.staff_profile.restaurant.restaurant_id]
            
            return Payment.objects.filter(order__restaurant_id__in=restaurant_ids)
        
        elif user.user_type == 'admin':
            return Payment.objects.all()
        
        return Payment.objects.none()