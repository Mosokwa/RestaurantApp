from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model

User = get_user_model()

class SecurityTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        
    def test_sql_injection_protection(self):
        """Test protection against SQL injection attacks"""
        search_url = reverse('restaurant_search')
        
        # Test various SQL injection attempts
        injection_attempts = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "'; EXEC xp_cmdshell('format c:'); --",
            "UNION SELECT password FROM users"
        ]
        
        for attempt in injection_attempts:
            response = self.client.get(search_url, {'q': attempt})
            # Should not crash - return either 200 or 400
            self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])
    
    def test_xss_protection(self):
        """Test protection against XSS attacks"""
        # Create a user first
        user = User.objects.create_user(
            username='xssuser',
            password='Testpass123!',
            user_type='customer',
            is_active=True
        )
        
        self.client.force_authenticate(user=user)
        
        profile_url = reverse('user_profile')
        xss_payloads = [
            '<script>alert("XSS")</script>',
            '<img src=x onerror=alert("XSS")>',
            'javascript:alert("XSS")'
        ]
        
        for payload in xss_payloads:
            response = self.client.put(profile_url, {'first_name': payload}, format='json')
            
            # Should either reject or sanitize the input
            if response.status_code == status.HTTP_200_OK:
                # If accepted, verify it was sanitized
                self.assertNotIn('<script>', response.data['first_name'])
                self.assertNotIn('javascript:', response.data['first_name'])
    
    def test_rate_limiting(self):
        """Test rate limiting on authentication endpoints"""
        login_url = reverse('login')
        reset_url = reverse('password_reset')
        
        # Test login rate limiting
        for i in range(15):
            data = {'username': f'user{i}', 'password': 'wrongpassword'}
            response = self.client.post(login_url, data, format='json')
            
            if i >= 10:  # Should be rate limited after certain attempts
                self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        
        # Test password reset rate limiting
        for i in range(15):
            data = {'email': f'user{i}@example.com'}
            response = self.client.post(reset_url, data, format='json')
            
            if i >= 5:  # Stricter limit for password reset
                self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
    
    def test_jwt_token_security(self):
        """Test JWT token security features"""
        user = User.objects.create_user(
            username='tokenuser',
            password='Testpass123!',
            user_type='customer',
            is_active=True
        )
        
        # Get valid token
        login_url = reverse('login')
        login_data = {'username': 'tokenuser', 'password': 'Testpass123!'}
        login_response = self.client.post(login_url, login_data, format='json')
        valid_token = login_response.data['tokens']['access']
        
        # Test with invalid token
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token')
        protected_url = reverse('current_user')
        response = self.client.get(protected_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test with valid token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {valid_token}')
        response = self.client.get(protected_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)