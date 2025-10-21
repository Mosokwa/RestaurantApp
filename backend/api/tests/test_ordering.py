from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from decimal import Decimal
from api.models import Customer, Restaurant, MenuCategory, MenuItem, Branch, Address, Order, Cart, CartItem

User = get_user_model()

class OrderingFlowTests(APITestCase):
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
            price=Decimal('12.99'),
            is_available=True
        )
        
        self.address = Address.objects.create(
            street_address='123 Test St',
            city='Test City',
            state='TS',
            postal_code='12345',
            country='USA'
        )
        
        self.branch = Branch.objects.create(
            restaurant=self.restaurant,
            address=self.address,
            is_active=True
        )
    
    def test_add_item_to_cart(self):
        """Test adding item to cart"""
        self.client.force_authenticate(user=self.customer_user)
        
        url = reverse('cart_item_add')
        data = {
            'menu_item': self.menu_item.item_id,
            'quantity': 2
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify cart item was created
        cart = Cart.objects.get(customer=self.customer)
        cart_items = CartItem.objects.filter(cart=cart)
        self.assertEqual(cart_items.count(), 1)
        self.assertEqual(cart_items[0].quantity, 2)
    
    def test_view_cart_contents(self):
        """Test viewing cart contents"""
        self.client.force_authenticate(user=self.customer_user)
        
        # First add item to cart
        add_url = reverse('cart_item_add')
        add_data = {'menu_item': self.menu_item.item_id, 'quantity': 1}
        self.client.post(add_url, add_data, format='json')
        
        # Then view cart
        view_url = reverse('cart_detail')
        response = self.client.get(view_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_items'], 1)
        self.assertEqual(Decimal(response.data['subtotal']), self.menu_item.price)
    
    def test_create_order_from_cart(self):
        """Test creating order from cart items"""
        self.client.force_authenticate(user=self.customer_user)
        
        # Add item to cart
        cart_url = reverse('cart_item_add')
        cart_data = {'menu_item': self.menu_item.item_id, 'quantity': 2}
        self.client.post(cart_url, cart_data, format='json')
        
        # Create order
        order_url = reverse('order_list')
        order_data = {
            'restaurant': self.restaurant.restaurant_id,
            'branch': self.branch.branch_id,
            'order_type': 'delivery',
            'delivery_address': self.address.address_id,
            'items': [
                {
                    'menu_item_id': self.menu_item.item_id,
                    'quantity': 2,
                    'modifiers': []
                }
            ]
        }
        
        response = self.client.post(order_url, order_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify order was created
        orders = Order.objects.filter(customer=self.customer)
        self.assertEqual(orders.count(), 1)
        
        order = orders.first()
        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.total_amount, Decimal('28.58'))  # (12.99 * 2) * 1.1 + 5.00
    
    def test_order_status_workflow(self):
        """Test order status changes"""
        self.client.force_authenticate(user=self.customer_user)
        
        # Create order
        order_url = reverse('order_list')
        order_data = {
            'restaurant': self.restaurant.restaurant_id,
            'branch': self.branch.branch_id,
            'order_type': 'pickup',
            'items': [{'menu_item_id': self.menu_item.item_id, 'quantity': 1}]
        }
        
        order_response = self.client.post(order_url, order_data, format='json')
        order_id = order_response.data['order_id']
        
        # Switch to staff user to update status
        staff_user = User.objects.create_user(
            username='staffuser',
            password='Testpass123!',
            user_type='staff',
            is_active=True
        )
        
        self.client.force_authenticate(user=staff_user)
        
        # Update order status
        update_url = reverse('order_update', kwargs={'pk': order_id})
        update_data = {'status': 'confirmed'}
        
        response = self.client.patch(update_url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'confirmed')
        
        # Verify status was updated in database
        order = Order.objects.get(pk=order_id)
        self.assertEqual(order.status, 'confirmed')
        self.assertIsNotNone(order.confirmed_at)
    
    def test_order_tracking_history(self):
        """Test order tracking history"""
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
        
        # Check tracking
        tracking_url = reverse('order_tracking', kwargs={'order_id': order_id})
        response = self.client.get(tracking_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)
        self.assertEqual(response.data[0]['status'], 'pending')