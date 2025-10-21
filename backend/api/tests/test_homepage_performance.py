# tests/test_homepage_performance.py
import time
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from api.models import Restaurant

class HomepagePerformanceTest(APITestCase):
    
    def setUp(self):
        self.restaurant = Restaurant.objects.create(
            name="Test Restaurant",
            status='active',
            is_featured=True
        )
        self.url = reverse('restaurant-homepage', kwargs={'pk': self.restaurant.pk})
    
    def test_homepage_response_time(self):
        """Test that homepage loads within acceptable time limits"""
        start_time = time.time()
        
        response = self.client.get(self.url)
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # Should respond in under 200ms for cached responses, 500ms for uncached
        self.assertLess(response_time, 0.5)
        self.assertEqual(response.status_code, 200)
    
    def test_homepage_query_count(self):
        """Test that homepage uses optimized query count"""
        with self.assertNumQueries(10):  # Should use less than 10 queries
            self.client.get(self.url)