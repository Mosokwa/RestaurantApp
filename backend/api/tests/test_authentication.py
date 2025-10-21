from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from django.core import mail
from api.models import Customer

User = get_user_model()

class AuthenticationTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.signup_url = reverse('signup')
        self.login_url = reverse('login')
        self.current_user_url = reverse('current_user')
        
    def test_user_registration_success(self):
        """Test successful user registration"""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'StrongPass123!',
            'password_confirm': 'StrongPass123!',
            'first_name': 'New',
            'last_name': 'User',
            'user_type': 'customer'
        }
        
        response = self.client.post(self.signup_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='newuser').exists())
        
        # Verify customer profile was created
        user = User.objects.get(username='newuser')
        self.assertTrue(hasattr(user, 'customer_profile'))
    
    def test_user_registration_password_mismatch(self):
        """Test registration with mismatched passwords"""
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'Password123!',
            'password_confirm': 'DifferentPassword123!',
            'user_type': 'customer'
        }
        
        response = self.client.post(self.signup_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('passwords don\'t match', str(response.data))
    
    def test_user_login_success(self):
        """Test successful user login"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='Testpass123!',
            user_type='customer',
            is_active=True
        )
        
        data = {
            'username': 'testuser',
            'password': 'Testpass123!'
        }
        
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])
        self.assertEqual(response.data['user']['username'], 'testuser')
    
    def test_user_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        data = {
            'username': 'nonexistent',
            'password': 'wrongpassword'
        }
        
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_access_protected_endpoint_without_auth(self):
        """Test accessing protected endpoint without authentication"""
        response = self.client.get(self.current_user_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_access_protected_endpoint_with_auth(self):
        """Test accessing protected endpoint with authentication"""
        user = User.objects.create_user(
            username='authuser',
            password='Testpass123!',
            user_type='customer',
            is_active=True
        )
        
        # Login to get token
        login_data = {'username': 'authuser', 'password': 'Testpass123!'}
        login_response = self.client.post(self.login_url, login_data, format='json')
        access_token = login_response.data['tokens']['access']
        
        # Access protected endpoint with token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get(self.current_user_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'authuser')
    
    def test_password_reset_flow(self):
        """Test password reset functionality"""
        user = User.objects.create_user(
            username='resetuser',
            email='reset@example.com',
            password='OldPassword123!',
            user_type='customer',
            is_active=True
        )
        
        reset_url = reverse('password_reset')
        data = {'email': 'reset@example.com'}
        
        response = self.client.post(reset_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Password Reset', mail.outbox[0].subject)
    
    def test_jwt_token_refresh(self):
        """Test JWT token refresh functionality"""
        user = User.objects.create_user(
            username='refreshuser',
            password='Testpass123!',
            user_type='customer',
            is_active=True
        )
        
        # Login to get tokens
        login_data = {'username': 'refreshuser', 'password': 'Testpass123!'}
        login_response = self.client.post(self.login_url, login_data, format='json')
        refresh_token = login_response.data['tokens']['refresh']
        
        # Refresh token
        refresh_url = reverse('token_refresh')
        refresh_data = {'refresh': refresh_token}
        refresh_response = self.client.post(refresh_url, refresh_data, format='json')
        
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', refresh_response.data)