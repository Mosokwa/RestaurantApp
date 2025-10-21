from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from decimal import Decimal
from api.models import Customer, Restaurant, MenuCategory, MenuItem, Order, Payment

User = get_user_model()

class PaymentTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Create test data
        self.customer_user = User.objects.create_user(
            username='customer',
            password='Testpass123!',
            user_type='customer',
            is_active=True
        )
        self.customer = Customer.objects.create(user=self.customer_user)
        
        self.owner_user = User.objects.create_user(
            username='owner',
            password='Testpass123!',
            user_type='owner',
            is_active=True
        )
        
        self.restaurant = Restaurant.objects.create(
            owner=self.owner_user,
            name='Test Restaurant',
            phone_number='+1234567890',
            email='test@example.com',
            status='active'
        )
        
        self.category = MenuCategory.objects.create(
            restaurant=self.restaurant,
            name='Main Course',
            display_order=1
        )
        
        self.menu_item = MenuItem.objects.create(
            category=self.category,
            name='Test Burger',
            description='Delicious test burger',
            price=Decimal('10.00'),
            is_available=True
        )
    
    def test_payment_creation(self):
        """Test successful payment creation"""
        self.client.force_authenticate(user=self.customer_user)
        
        # First create an order
        order_url = reverse('order_list')
        order_data = {
            'restaurant': self.restaurant.restaurant_id,
            'order_type': 'pickup',
            'items': [{'menu_item_id': self.menu_item.item_id, 'quantity': 1}]
        }
        
        order_response = self.client.post(order_url, order_data, format='json')
        order_id = order_response.data['order_id']
        order_total = order_response.data['total_amount']
        
        # Create payment
        payment_url = reverse('payment_create')
        payment_data = {
            'order': order_id,
            'payment_method': 'credit_card',
            'amount': order_total
        }
        
        response = self.client.post(payment_url, payment_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify payment was created
        payments = Payment.objects.filter(order_id=order_id)
        self.assertEqual(payments.count(), 1)
        
        payment = payments.first()
        self.assertEqual(payment.payment_status, 'completed')
        self.assertEqual(payment.amount, Decimal(order_total))
    
    def test_payment_permissions(self):
        """Test that users can only access their own payments"""
        # Create second customer
        customer2_user = User.objects.create_user(
            username='customer2',
            password='Testpass123!',
            user_type='customer',
            is_active=True
        )
        customer2 = Customer.objects.create(user=customer2_user)
        
        self.client.force_authenticate(user=self.customer_user)
        
        # Customer1 creates order and payment
        order_url = reverse('order_list')
        order_data = {
            'restaurant': self.restaurant.restaurant_id,
            'order_type': 'pickup',
            'items': [{'menu_item_id': self.menu_item.item_id, 'quantity': 1}]
        }
        
        order_response = self.client.post(order_url, order_data, format='json')
        order_id = order_response.data['order_id']
        
        payment_url = reverse('payment_create')
        payment_data = {'order': order_id, 'payment_method': 'credit_card'}
        payment_response = self.client.post(payment_url, payment_data, format='json')
        payment_id = payment_response.data['payment_id']
        
        # Switch to customer2 and try to access the payment
        self.client.force_authenticate(user=customer2_user)
        detail_url = reverse('payment_detail', kwargs={'pk': payment_id})
        response = self.client.get(detail_url)
        
        # Should not be able to access other user's payments
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_payment_amount_validation(self):
        """Test payment amount validation"""
        self.client.force_authenticate(user=self.customer_user)
        
        # Create order
        order_url = reverse('order_list')
        order_data = {
            'restaurant': self.restaurant.restaurant_id,
            'order_type': 'pickup',
            'items': [{'menu_item_id': self.menu_item.item_id, 'quantity': 1}]
        }
        
        order_response = self.client.post(order_url, order_data, format='json')
        order_id = order_response.data['order_id']
        
        # Try to pay with wrong amount
        payment_url = reverse('payment_create')
        payment_data = {
            'order': order_id,
            'payment_method': 'credit_card',
            'amount': '5.00'  # Incorrect amount
        }
        
        response = self.client.post(payment_url, payment_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('doesn\'t match', str(response.data))
    
    def test_payment_for_cancelled_order(self):
        """Test payment for cancelled order"""
        self.client.force_authenticate(user=self.customer_user)
        
        # Create order
        order_url = reverse('order_list')
        order_data = {
            'restaurant': self.restaurant.restaurant_id,
            'order_type': 'pickup',
            'items': [{'menu_item_id': self.menu_item.item_id, 'quantity': 1}]
        }
        
        order_response = self.client.post(order_url, order_data, format='json')
        order_id = order_response.data['order_id']
        
        # Cancel the order
        order = Order.objects.get(pk=order_id)
        order.status = 'cancelled'
        order.save()
        
        # Try to pay for cancelled order
        payment_url = reverse('payment_create')
        payment_data = {'order': order_id, 'payment_method': 'credit_card'}
        
        response = self.client.post(payment_url, payment_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('not in a payable state', str(response.data))