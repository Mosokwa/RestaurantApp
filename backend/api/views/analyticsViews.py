import csv
from datetime import date, datetime, timedelta
from decimal import Decimal
from io import BytesIO
from django.forms import DurationField
import numpy as np
from django.db.models import Value
from django.db.models.functions import Coalesce
from xhtml2pdf import pisa
import pandas as pd
from django.http import Http404, HttpResponse
from django.utils import timezone 
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models.functions import ExtractHour, ExtractWeekDay, TruncDate
from django.db.models import ExpressionWrapper, Q
from django.template.loader import render_to_string
from django.db.models import Avg, Count, Sum, F
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
import calendar
from ..models import CustomerLifetimeValue, RestaurantPerformanceMetrics, Restaurant, MenuItem, Order, OrderItem,  OrderTracking, MenuCategory, PopularitySnapshot
from ..serializers import (
    AnalyticsPeriodSerializer, ExportRequestSerializer, RestaurantPerformanceMetricsSerializer, SalesAnalyticsRequestSerializer, SalesTrendSerializer, OrderTrackingSerializer, EnhancedMenuPerformanceSerializer, CategoryAnalyticsSerializer, ItemAnalyticsSerializer
)

class OrderTrackingView(generics.ListAPIView):
    serializer_class = OrderTrackingSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        order_id = self.kwargs['order_id']
        
        # Verify user has permission to view this order's tracking
        order = get_object_or_404(Order, pk=order_id)
        user = self.request.user
        
        if user.user_type == 'customer' and order.customer.user != user:
            raise PermissionDenied("You can only view tracking for your own orders")
        
        elif user.user_type in ['owner', 'staff']:
            if user.user_type == 'owner':
                restaurant_ids = Restaurant.objects.filter(owner=user).values_list('restaurant_id', flat=True)
            else:
                restaurant_ids = [user.staff_profile.restaurant.restaurant_id]
            
            if order.restaurant.restaurant_id not in restaurant_ids:
                raise PermissionDenied("You can only view tracking for your restaurant's orders")
        
        return OrderTracking.objects.filter(order=order).order_by('created_at')
    
class RestaurantSalesAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        serializer = SalesAnalyticsRequestSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        period = data.get('period', 'this_week')
        restaurant_id = data.get('restaurant_id')
        
        # Get restaurants user has access to
        if request.user.user_type == 'customer':
            return Response(
                {'error': 'Only restaurant owners and staff can access sales analytics'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if request.user.user_type == 'owner':
            restaurants = Restaurant.objects.filter(owner=request.user)
        elif request.user.user_type == 'staff':
            restaurants = Restaurant.objects.filter(staff_members__user=request.user)
        else:  # admin
            restaurants = Restaurant.objects.all()
        
        if restaurant_id:
            restaurants = restaurants.filter(restaurant_id=restaurant_id)
        
        if not restaurants.exists():
            return Response({'error': 'No restaurants found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Calculate date range based on period
        today = timezone.now().date()
        start_date, end_date = self._get_date_range(period, data.get('start_date'), data.get('end_date'))
        
        analytics_data = []
        for restaurant in restaurants:
            restaurant_data = self._get_restaurant_analytics(restaurant, start_date, end_date)
            analytics_data.append(restaurant_data)
        
        return Response({
            'period': period,
            'start_date': start_date,
            'end_date': end_date,
            'analytics': analytics_data
        })
    
    def _get_date_range(self, period, custom_start=None, custom_end=None):
        today = timezone.now().date()
        
        if period == 'today':
            return today, today
        elif period == 'yesterday':
            yesterday = today - timedelta(days=1)
            return yesterday, yesterday
        elif period == 'this_week':
            start = today - timedelta(days=today.weekday())
            return start, today
        elif period == 'last_week':
            start = today - timedelta(days=today.weekday() + 7)
            end = start + timedelta(days=6)
            return start, end
        elif period == 'this_month':
            start = today.replace(day=1)
            return start, today
        elif period == 'last_month':
            first_day_this_month = today.replace(day=1)
            last_day_last_month = first_day_this_month - timedelta(days=1)
            start = last_day_last_month.replace(day=1)
            return start, last_day_last_month
        elif period == 'custom' and custom_start and custom_end:
            return custom_start, custom_end
        else:
            # Default to this week
            start = today - timedelta(days=today.weekday())
            return start, today
    
    def _get_restaurant_analytics(self, restaurant, start_date, end_date):
        # Get orders in the date range
        orders = Order.objects.filter(
            restaurant=restaurant,
            order_placed_at__date__range=[start_date, end_date]
        )
        
        completed_orders = orders.filter(status='delivered')
        cancelled_orders = orders.filter(status='cancelled')
        
        # Calculate metrics
        total_orders = orders.count()
        total_revenue = completed_orders.aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        
        avg_order_value = total_revenue / completed_orders.count() if completed_orders.exists() else 0
        
        # Get top items
        top_items = self._get_top_items(restaurant, start_date, end_date)
        
        # Get hourly distribution
        hourly_data = self._get_hourly_distribution(completed_orders)
        
        return {
            'restaurant_id': restaurant.restaurant_id,
            'restaurant_name': restaurant.name,
            'period': f"{start_date} to {end_date}",
            'total_orders': total_orders,
            'completed_orders': completed_orders.count(),
            'cancelled_orders': cancelled_orders.count(),
            'total_revenue': float(total_revenue),
            'average_order_value': float(avg_order_value),
            'completion_rate': round((completed_orders.count() / total_orders * 100), 2) if total_orders > 0 else 0,
            'cancellation_rate': round((cancelled_orders.count() / total_orders * 100), 2) if total_orders > 0 else 0,
            'top_items': top_items[:5],  # Top 5 items
            'hourly_distribution': hourly_data
        }
    
    def _get_top_items(self, restaurant, start_date, end_date):
        # Get top selling items with revenue
        top_items = OrderItem.objects.filter(
            order__restaurant=restaurant,
            order__status='delivered',
            order__order_placed_at__date__range=[start_date, end_date]
        ).values(
            'menu_item__item_id',
            'menu_item__name',
            'menu_item__category__name'
        ).annotate(
            quantity_sold=Sum('quantity'),
            revenue=Sum(F('quantity') * F('unit_price'))
        ).order_by('-revenue')[:10]
        
        return [
            {
                'item_id': item['menu_item__item_id'],
                'name': item['menu_item__name'],
                'category': item['menu_item__category__name'],
                'quantity_sold': item['quantity_sold'] or 0,
                'revenue': float(item['revenue'] or 0)
            }
            for item in top_items
        ]
    
    def _get_hourly_distribution(self, orders):
        hourly_data = {hour: {'orders': 0, 'revenue': 0} for hour in range(24)}
        
        for order in orders:
            hour = order.order_placed_at.hour
            hourly_data[hour]['orders'] += 1
            hourly_data[hour]['revenue'] += float(order.total_amount)
        
        return [
            {
                'hour': f"{hour:02d}:00",
                'orders': data['orders'],
                'revenue': data['revenue']
            }
            for hour, data in hourly_data.items()
        ]

class DailySalesReportView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, restaurant_id=None):
        # Get date from query params, default to today
        report_date = request.query_params.get('date', timezone.now().date().isoformat())
        
        try:
            report_date = datetime.strptime(report_date, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get restaurant(s) user has access to
        if request.user.user_type == 'customer':
            return Response(
                {'error': 'Only restaurant owners and staff can access sales reports'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if request.user.user_type == 'owner':
            restaurants = Restaurant.objects.filter(owner=request.user)
        elif request.user.user_type == 'staff':
            restaurants = Restaurant.objects.filter(staff_members__user=request.user)
        else:  # admin
            restaurants = Restaurant.objects.all()
        
        if restaurant_id:
            restaurants = restaurants.filter(restaurant_id=restaurant_id)
        
        if not restaurants.exists():
            return Response({'error': 'No restaurants found'}, status=status.HTTP_404_NOT_FOUND)
        
        reports = []
        for restaurant in restaurants:
            report = self._generate_daily_report(restaurant, report_date)
            reports.append(report)
        
        return Response({
            'date': report_date,
            'reports': reports
        })
    
    def _generate_daily_report(self, restaurant, report_date):
        # Get orders for the day
        orders = Order.objects.filter(
            restaurant=restaurant,
            order_placed_at__date=report_date
        )
        
        completed_orders = orders.filter(status='delivered')
        cancelled_orders = orders.filter(status='cancelled')
        
        # Calculate metrics
        total_orders = orders.count()
        total_revenue = completed_orders.aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        
        # Get previous day for comparison
        prev_day = report_date - timedelta(days=1)
        prev_day_orders = Order.objects.filter(
            restaurant=restaurant,
            order_placed_at__date=prev_day,
            status='delivered'
        )
        prev_day_revenue = prev_day_orders.aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        
        # Calculate growth
        revenue_growth = 0
        if prev_day_revenue > 0:
            revenue_growth = ((total_revenue - prev_day_revenue) / prev_day_revenue) * 100
        
        # Get top items
        top_items = self._get_daily_top_items(restaurant, report_date)
        
        # Get hourly breakdown
        hourly_breakdown = self._get_hourly_breakdown(completed_orders)
        
        return {
            'restaurant_id': restaurant.restaurant_id,
            'restaurant_name': restaurant.name,
            'date': report_date,
            'total_orders': total_orders,
            'completed_orders': completed_orders.count(),
            'cancelled_orders': cancelled_orders.count(),
            'total_revenue': float(total_revenue),
            'revenue_growth_percent': round(revenue_growth, 2),
            'average_order_value': float(total_revenue / completed_orders.count()) if completed_orders.exists() else 0,
            'completion_rate': round((completed_orders.count() / total_orders * 100), 2) if total_orders > 0 else 0,
            'top_items': top_items,
            'hourly_breakdown': hourly_breakdown
        }
    
    def _get_daily_top_items(self, restaurant, report_date):
        return OrderItem.objects.filter(
            order__restaurant=restaurant,
            order__status='delivered',
            order__order_placed_at__date=report_date
        ).values(
            'menu_item__item_id',
            'menu_item__name',
            'menu_item__category__name'
        ).annotate(
            quantity_sold=Sum('quantity'),
            revenue=Sum(F('quantity') * F('unit_price'))
        ).order_by('-revenue')[:5]
    
    def _get_hourly_breakdown(self, orders):
        hourly_data = {hour: {'orders': 0, 'revenue': 0} for hour in range(24)}
        
        for order in orders:
            hour = order.order_placed_at.hour
            hourly_data[hour]['orders'] += 1
            hourly_data[hour]['revenue'] += float(order.total_amount)
        
        return [
            {
                'hour': f"{hour:02d}:00",
                'orders': data['orders'],
                'revenue': float(data['revenue'])
            }
            for hour, data in hourly_data.items()
            if data['orders'] > 0  # Only include hours with orders
        ]

class MonthlySalesReportView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, restaurant_id=None):
        # Get year and month from query params, default to current
        year = int(request.query_params.get('year', timezone.now().year))
        month = int(request.query_params.get('month', timezone.now().month))
        
        # Get restaurant(s) user has access to
        if request.user.user_type == 'customer':
            return Response(
                {'error': 'Only restaurant owners and staff can access sales reports'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if request.user.user_type == 'owner':
            restaurants = Restaurant.objects.filter(owner=request.user)
        elif request.user.user_type == 'staff':
            restaurants = Restaurant.objects.filter(staff_members__user=request.user)
        else:  # admin
            restaurants = Restaurant.objects.all()
        
        if restaurant_id:
            restaurants = restaurants.filter(restaurant_id=restaurant_id)
        
        if not restaurants.exists():
            return Response({'error': 'No restaurants found'}, status=status.HTTP_404_NOT_FOUND)
        
        reports = []
        for restaurant in restaurants:
            report = self._generate_monthly_report(restaurant, year, month)
            reports.append(report)
        
        return Response({
            'year': year,
            'month': month,
            'month_name': calendar.month_name[month],
            'reports': reports
        })
    
    def _generate_monthly_report(self, restaurant, year, month):
        # Calculate date range for the month
        start_date = date(year, month, 1)
        end_date = date(year, month, calendar.monthrange(year, month)[1])
        
        # Get orders for the month
        orders = Order.objects.filter(
            restaurant=restaurant,
            order_placed_at__date__range=[start_date, end_date]
        )
        
        completed_orders = orders.filter(status='delivered')
        cancelled_orders = orders.filter(status='cancelled')
        
        # Calculate metrics
        total_orders = orders.count()
        total_revenue = completed_orders.aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        
        # Get previous month for comparison
        prev_month = start_date - timedelta(days=1)
        prev_start = prev_month.replace(day=1)
        prev_end = prev_month
        prev_month_orders = Order.objects.filter(
            restaurant=restaurant,
            order_placed_at__date__range=[prev_start, prev_end],
            status='delivered'
        )
        prev_month_revenue = prev_month_orders.aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        
        # Calculate growth
        revenue_growth = 0
        if prev_month_revenue > 0:
            revenue_growth = ((total_revenue - prev_month_revenue) / prev_month_revenue) * 100
        
        # Get daily trends
        daily_trends = self._get_daily_trends(restaurant, start_date, end_date)
        
        # Get top items and categories
        top_items = self._get_monthly_top_items(restaurant, start_date, end_date)
        top_categories = self._get_monthly_top_categories(restaurant, start_date, end_date)
        
        return {
            'restaurant_id': restaurant.restaurant_id,
            'restaurant_name': restaurant.name,
            'year': year,
            'month': month,
            'month_name': calendar.month_name[month],
            'total_orders': total_orders,
            'completed_orders': completed_orders.count(),
            'cancelled_orders': cancelled_orders.count(),
            'total_revenue': float(total_revenue),
            'revenue_growth_percent': round(revenue_growth, 2),
            'average_order_value': float(total_revenue / completed_orders.count()) if completed_orders.exists() else 0,
            'completion_rate': round((completed_orders.count() / total_orders * 100), 2) if total_orders > 0 else 0,
            'daily_trends': daily_trends,
            'top_items': top_items[:5],
            'top_categories': top_categories[:5]
        }
    
    def _get_daily_trends(self, restaurant, start_date, end_date):
        daily_data = {}
        current_date = start_date
        
        while current_date <= end_date:
            daily_data[current_date] = {'orders': 0, 'revenue': 0}
            current_date += timedelta(days=1)
        
        orders = Order.objects.filter(
            restaurant=restaurant,
            status='delivered',
            order_placed_at__date__range=[start_date, end_date]
        )
        
        for order in orders:
            order_date = order.order_placed_at.date()
            if order_date in daily_data:
                daily_data[order_date]['orders'] += 1
                daily_data[order_date]['revenue'] += float(order.total_amount)
        
        return [
            {
                'date': date.strftime('%Y-%m-%d'),
                'day_name': date.strftime('%A'),
                'orders': data['orders'],
                'revenue': data['revenue']
            }
            for date, data in daily_data.items()
        ]
    
    def _get_monthly_top_items(self, restaurant, start_date, end_date):
        return OrderItem.objects.filter(
            order__restaurant=restaurant,
            order__status='delivered',
            order__order_placed_at__date__range=[start_date, end_date]
        ).values(
            'menu_item__item_id',
            'menu_item__name',
            'menu_item__category__name'
        ).annotate(
            quantity_sold=Sum('quantity'),
            revenue=Sum(F('quantity') * F('unit_price'))
        ).order_by('-revenue')[:10]
    
    def _get_monthly_top_categories(self, restaurant, start_date, end_date):
        return OrderItem.objects.filter(
            order__restaurant=restaurant,
            order__status='delivered',
            order__order_placed_at__date__range=[start_date, end_date]
        ).values(
            'menu_item__category__category_id',
            'menu_item__category__name'
        ).annotate(
            quantity_sold=Sum('quantity'),
            revenue=Sum(F('quantity') * F('unit_price'))
        ).order_by('-revenue')[:10]

class RestaurantPerformanceMetricsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, restaurant_id=None):
        # Get restaurant(s) user has access to
        if request.user.user_type == 'customer':
            return Response(
                {'error': 'Only restaurant owners and staff can access performance metrics'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if request.user.user_type == 'owner':
            restaurants = Restaurant.objects.filter(owner=request.user)
        elif request.user.user_type == 'staff':
            restaurants = Restaurant.objects.filter(staff_members__user=request.user)
        else:  # admin
            restaurants = Restaurant.objects.all()
        
        if restaurant_id:
            restaurants = restaurants.filter(restaurant_id=restaurant_id)
        
        if not restaurants.exists():
            return Response({'error': 'No restaurants found'}, status=status.HTTP_404_NOT_FOUND)
        
        metrics = []
        for restaurant in restaurants:
            try:
                performance_metrics = RestaurantPerformanceMetrics.objects.get(restaurant=restaurant)
                serializer = RestaurantPerformanceMetricsSerializer(performance_metrics)
                metrics.append(serializer.data)
            except RestaurantPerformanceMetrics.DoesNotExist:
                # Create metrics if they don't exist
                performance_metrics = RestaurantPerformanceMetrics.objects.create(restaurant=restaurant)
                serializer = RestaurantPerformanceMetricsSerializer(performance_metrics)
                metrics.append(serializer.data)
        
        return Response({'metrics': metrics})

class SalesTrendsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, restaurant_id):
        # Get date range from query params (default to last 30 days)
        days = int(request.query_params.get('days', 30))
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days-1)
        
        try:
            restaurant = Restaurant.objects.get(restaurant_id=restaurant_id)
        except Restaurant.DoesNotExist:
            return Response(
                {'error': 'Restaurant not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if user has access to this restaurant
        if not self._has_access(request.user, restaurant):
            return Response(
                {'error': 'Access denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        trends = self._get_sales_trends(restaurant, start_date, end_date)
        
        return Response({
            'restaurant_id': restaurant_id,
            'restaurant_name': restaurant.name,
            'start_date': start_date,
            'end_date': end_date,
            'trends': trends
        })
    
    def _has_access(self, user, restaurant):
        if user.user_type == 'admin':
            return True
        elif user.user_type == 'owner':
            return restaurant.owner == user
        elif user.user_type == 'staff':
            return restaurant.staff_members.filter(user=user).exists()
        return False
    
    def _get_sales_trends(self, restaurant, start_date, end_date):
        trends = []
        current_date = start_date
        
        # Initialize all dates in range
        while current_date <= end_date:
            trends.append({
                'date': current_date,
                'orders': 0,
                'revenue': 0,
                'avg_order_value': 0
            })
            current_date += timedelta(days=1)
        
        # Get actual order data
        orders = Order.objects.filter(
            restaurant=restaurant,
            status='delivered',
            order_placed_at__date__range=[start_date, end_date]
        )
        
        # Aggregate data by date
        daily_data = orders.values('order_placed_at__date').annotate(
            orders_count=Count('order_id'),
            total_revenue=Sum('total_amount'),
            avg_order_value=Avg('total_amount')
        )
        
        # Update trends with actual data
        for data in daily_data:
            date_key = data['order_placed_at__date']
            for trend in trends:
                if trend['date'] == date_key:
                    trend['orders'] = data['orders_count']
                    trend['revenue'] = float(data['total_revenue'] or 0)
                    trend['avg_order_value'] = float(data['avg_order_value'] or 0)
                    break
        
        # Serialize the data
        serializer = SalesTrendSerializer(trends, many=True)
        return serializer.data

#ENHANCED ANALYTICS FOR OWNERS VIEWS
class AnalyticsBaseView(APIView):
    """
    Base class for analytics views with common functionality
    """
    permission_classes = [IsAuthenticated]
    
    def _get_restaurant_access(self, restaurant_id=None):
        """Get restaurants user has access to"""
        user = self.request.user
        
        if user.user_type == 'customer':
            raise PermissionDenied("Only restaurant owners and staff can access analytics")
        
        if user.user_type == 'owner':
            restaurants = Restaurant.objects.filter(owner=user)
        elif user.user_type == 'staff':
            restaurants = Restaurant.objects.filter(staff_members__user=user)
        else:  # admin
            restaurants = Restaurant.objects.all()
        
        if restaurant_id:
            restaurants = restaurants.filter(restaurant_id=restaurant_id)
        
        if not restaurants.exists():
            raise Http404("No restaurants found")
        
        return restaurants
    
    def _get_date_range(self, period, custom_start=None, custom_end=None):
        """Calculate date range based on period"""
        today = timezone.now().date()
        
        date_ranges = {
            'today': (today, today),
            'yesterday': (today - timedelta(days=1), today - timedelta(days=1)),
            'this_week': (today - timedelta(days=today.weekday()), today),
            'last_week': (today - timedelta(days=today.weekday() + 7), 
                         today - timedelta(days=today.weekday() + 1)),
            'this_month': (today.replace(day=1), today),
            'last_month': ((today.replace(day=1) - timedelta(days=1)).replace(day=1),
                         today.replace(day=1) - timedelta(days=1)),
            'last_3_months': (today - timedelta(days=90), today),
            'last_6_months': (today - timedelta(days=180), today),
            'this_year': (today.replace(month=1, day=1), today),
        }
        
        if period == 'custom' and custom_start and custom_end:
            return custom_start, custom_end
        else:
            return date_ranges.get(period, (today - timedelta(days=30), today))

class CustomerInsightsView(AnalyticsBaseView):
    """
    Comprehensive customer analytics endpoint
    """
    
    def get(self, request, restaurant_id=None):
        serializer = AnalyticsPeriodSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        period = data.get('period', 'this_month')
        start_date, end_date = self._get_date_range(
            period, data.get('start_date'), data.get('end_date')
        )
        
        restaurants = self._get_restaurant_access(restaurant_id)
        
        insights_data = []
        for restaurant in restaurants:
            restaurant_insights = self._get_restaurant_customer_insights(
                restaurant, start_date, end_date
            )
            insights_data.append(restaurant_insights)
        
        return Response({
            'period': period,
            'start_date': start_date,
            'end_date': end_date,
            'insights': insights_data
        })
    
    def _get_restaurant_customer_insights(self, restaurant, start_date, end_date):
        """Get comprehensive customer insights for a restaurant"""
        
        # Customer acquisition metrics
        new_customers = Order.objects.filter(
            restaurant=restaurant,
            order_placed_at__date__range=[start_date, end_date]
        ).values('customer').distinct().count()
        
        # Customer retention metrics
        returning_customers = self._get_returning_customers(restaurant, start_date, end_date)
        retention_rate = self._calculate_retention_rate(restaurant, start_date, end_date)
        
        # Customer value metrics
        clv_data = CustomerLifetimeValue.objects.filter(
            restaurant=restaurant,
            last_order_date__date__range=[start_date, end_date]
        ).aggregate(
            avg_clv=Avg('predicted_clv'),
            avg_order_frequency=Avg('order_frequency_days'),
            churn_rate=Avg('churn_probability')
        )
        
        # Customer segmentation
        segments = self._get_customer_segments(restaurant)
        
        # Behavioral analysis
        behavior_metrics = self._get_customer_behavior_metrics(restaurant, start_date, end_date)
        
        return {
            'restaurant_id': restaurant.restaurant_id,
            'restaurant_name': restaurant.name,
            'period': f"{start_date} to {end_date}",
            'customer_metrics': {
                'total_customers': new_customers + returning_customers,
                'new_customers': new_customers,
                'returning_customers': returning_customers,
                'retention_rate': round(retention_rate, 2),
                'churn_rate': round(clv_data['churn_rate'] or 0, 2),
            },
            'value_metrics': {
                'average_clv': float(clv_data['avg_clv'] or 0),
                'average_order_frequency': clv_data['avg_order_frequency'] or 0,
                'customer_acquisition_cost': self._calculate_cac(restaurant, start_date, end_date),
            },
            'segmentation': segments,
            'behavior_analysis': behavior_metrics,
            'recommendations': self._generate_customer_recommendations(restaurant, segments)
        }
    
    def _get_returning_customers(self, restaurant, start_date, end_date):
        """Calculate returning customers"""
        # Customers who ordered before the period and during the period
        previous_customers = Order.objects.filter(
            restaurant=restaurant,
            order_placed_at__date__lt=start_date
        ).values('customer').distinct()
        
        returning = Order.objects.filter(
            restaurant=restaurant,
            customer_id__in=previous_customers,
            order_placed_at__date__range=[start_date, end_date]
        ).values('customer').distinct().count()
        
        return returning
    
    def _calculate_retention_rate(self, restaurant, start_date, end_date):
        """Calculate customer retention rate"""
        # This is a simplified calculation - in production, use cohort analysis
        previous_period_end = start_date - timedelta(days=1)
        previous_period_start = start_date - timedelta(days=30)
        
        previous_customers = Order.objects.filter(
            restaurant=restaurant,
            order_placed_at__date__range=[previous_period_start, previous_period_end]
        ).values('customer').distinct().count()
        
        if previous_customers == 0:
            return 0
        
        retained_customers = Order.objects.filter(
            restaurant=restaurant,
            order_placed_at__date__range=[start_date, end_date],
            customer_id__in=Order.objects.filter(
                restaurant=restaurant,
                order_placed_at__date__range=[previous_period_start, previous_period_end]
            ).values('customer')
        ).values('customer').distinct().count()
        
        return (retained_customers / previous_customers) * 100
    
    def _get_customer_segments(self, restaurant):
        """Segment customers by value and behavior"""
        segments = CustomerLifetimeValue.objects.filter(restaurant=restaurant).values(
            'customer_segment'
        ).annotate(
            count=Count('customer_id'),
            avg_orders=Avg('total_orders'),
            avg_spent=Avg('total_spent')
        )
        
        return {
            segment['customer_segment']: {
                'count': segment['count'],
                'average_orders': segment['avg_orders'],
                'average_spent': float(segment['avg_spent'] or 0)
            }
            for segment in segments
        }
    
    def _calculate_cac(self, restaurant, start_date, end_date):
        """Calculate customer acquisition cost (simplified)"""
        # In production, integrate with marketing spend data
        marketing_orders = Order.objects.filter(
            restaurant=restaurant,
            order_placed_at__date__range=[start_date, end_date]
        ).count()
        
        # Placeholder - replace with actual marketing spend
        estimated_marketing_spend = marketing_orders * 5  # $5 per acquisition estimate
        
        return float(estimated_marketing_spend / marketing_orders) if marketing_orders > 0 else 0
    
    def _get_customer_behavior_metrics(self, restaurant, start_date, end_date):
        """Analyze customer behavior patterns"""
        orders = Order.objects.filter(
            restaurant=restaurant,
            order_placed_at__date__range=[start_date, end_date],
            status='delivered'
        )
        
        # Preferred order times
        order_times = orders.annotate(
            hour=ExtractHour('order_placed_at')
        ).values('hour').annotate(
            count=Count('order_id')
        ).order_by('-count')
        
        # Average order value by customer segment
        segment_values = CustomerLifetimeValue.objects.filter(
            restaurant=restaurant
        ).values('customer_segment').annotate(
            avg_order_value=Avg('average_order_value')
        )
        
        return {
            'preferred_order_times': list(order_times[:5]),
            'segment_order_values': {
                seg['customer_segment']: float(seg['avg_order_value'] or 0)
                for seg in segment_values
            },
            'repeat_order_patterns': self._analyze_repeat_patterns(restaurant)
        }
    
    def _generate_customer_recommendations(self, restaurant, segments):
        """Generate actionable recommendations based on customer insights"""
        recommendations = []
        
        high_value_count = segments.get('high_value', {}).get('count', 0)
        retention_rate = segments.get('retention_rate', 0)
        
        if high_value_count < 10:
            recommendations.append({
                'type': 'acquisition',
                'priority': 'high',
                'message': 'Focus on acquiring high-value customers through targeted marketing',
                'action': 'Implement customer referral program and premium offerings'
            })
        
        if retention_rate < 60:
            recommendations.append({
                'type': 'retention',
                'priority': 'high',
                'message': 'Improve customer retention through loyalty programs',
                'action': 'Launch loyalty program with points and exclusive offers'
            })
        
        return recommendations

class OperationalMetricsView(AnalyticsBaseView):
    """
    Operational efficiency and performance metrics
    """
    
    def get(self, request, restaurant_id=None):
        serializer = AnalyticsPeriodSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        period = data.get('period', 'this_month')
        branch_id = data.get('branch_id')
        start_date, end_date = self._get_date_range(
            period, data.get('start_date'), data.get('end_date')
        )
        
        restaurants = self._get_restaurant_access(restaurant_id)
        
        operational_data = []
        for restaurant in restaurants:
            metrics = self._get_operational_metrics(
                restaurant, branch_id, start_date, end_date
            )
            operational_data.append(metrics)
        
        return Response({
            'period': period,
            'start_date': start_date,
            'end_date': end_date,
            'operational_metrics': operational_data
        })
    
    def _get_operational_metrics(self, restaurant, branch_id, start_date, end_date):
        """Get comprehensive operational metrics"""
        
        # Base query
        orders_query = Order.objects.filter(
            restaurant=restaurant,
            order_placed_at__date__range=[start_date, end_date]
        )
        
        if branch_id:
            orders_query = orders_query.filter(branch_id=branch_id)
        
        # Order fulfillment metrics
        fulfillment_metrics = self._calculate_fulfillment_metrics(orders_query)
        
        # Time efficiency metrics
        time_metrics = self._calculate_time_metrics(orders_query)
        
        # Staff efficiency
        staff_metrics = self._calculate_staff_efficiency(restaurant, branch_id, start_date, end_date)
        
        # Peak hours analysis
        peak_hours = self._analyze_peak_hours(orders_query)
        
        # Quality metrics
        quality_metrics = self._calculate_quality_metrics(orders_query)
        
        return {
            'restaurant_id': restaurant.restaurant_id,
            'restaurant_name': restaurant.name,
            'branch_id': branch_id,
            'period': f"{start_date} to {end_date}",
            'fulfillment_metrics': fulfillment_metrics,
            'time_efficiency': time_metrics,
            'staff_efficiency': staff_metrics,
            'peak_analysis': peak_hours,
            'quality_metrics': quality_metrics,
            'overall_efficiency_score': self._calculate_overall_efficiency(
                fulfillment_metrics, time_metrics, quality_metrics
            ),
            'recommendations': self._generate_operational_recommendations(
                fulfillment_metrics, time_metrics, peak_hours
            )
        }
    
    def _calculate_fulfillment_metrics(self, orders_query):
        """Calculate order fulfillment rates"""
        total_orders = orders_query.count()
        completed_orders = orders_query.filter(status='delivered').count()
        cancelled_orders = orders_query.filter(status='cancelled').count()
        
        fulfillment_rate = (completed_orders / total_orders * 100) if total_orders > 0 else 0
        cancellation_rate = (cancelled_orders / total_orders * 100) if total_orders > 0 else 0
        
        return {
            'total_orders': total_orders,
            'completed_orders': completed_orders,
            'cancelled_orders': cancelled_orders,
            'fulfillment_rate': round(fulfillment_rate, 2),
            'cancellation_rate': round(cancellation_rate, 2)
        }
    
    def _calculate_time_metrics(self, orders_query):
        """Calculate time-based efficiency metrics"""
        delivered_orders = orders_query.filter(status='delivered')
        
        # Average preparation time
        prep_times = delivered_orders.annotate(
            prep_time=ExpressionWrapper(
                F('preparation_completed_at') - F('order_placed_at'),
                output_field=DurationField()
            )
        ).aggregate(avg_prep_time=Avg('prep_time'))
        
        avg_prep_minutes = prep_times['avg_prep_time'].total_seconds() / 60 if prep_times['avg_prep_time'] else 0
        
        # On-time delivery rate (within estimated time)
        on_time_deliveries = delivered_orders.filter(
            delivered_at__lte=F('estimated_delivery_time')
        ).count()
        
        on_time_rate = (on_time_deliveries / delivered_orders.count() * 100) if delivered_orders.count() > 0 else 0
        
        return {
            'average_preparation_time_minutes': round(avg_prep_minutes, 2),
            'on_time_delivery_rate': round(on_time_rate, 2),
            'average_order_duration_minutes': self._calculate_average_order_duration(delivered_orders)
        }
    
    def _calculate_staff_efficiency(self, restaurant, branch_id, start_date, end_date):
        """Calculate staff efficiency metrics"""
        # Placeholder - integrate with staff scheduling system
        # For now, use estimated staff hours based on order volume
        
        orders_count = Order.objects.filter(
            restaurant=restaurant,
            order_placed_at__date__range=[start_date, end_date],
            status='delivered'
        ).count()
        
        # Estimate staff hours (simplified)
        estimated_staff_hours = max(orders_count * 0.1, 1)  # 6 minutes per order
        
        orders_per_hour = orders_count / estimated_staff_hours if estimated_staff_hours > 0 else 0
        
        return {
            'estimated_staff_hours': round(estimated_staff_hours, 2),
            'orders_per_staff_hour': round(orders_per_hour, 2),
            'efficiency_rating': 'high' if orders_per_hour > 5 else 'medium' if orders_per_hour > 3 else 'low'
        }
    
    def _analyze_peak_hours(self, orders_query):
        """Analyze peak ordering hours and patterns"""
        peak_data = orders_query.annotate(
            order_hour=ExtractHour('order_placed_at'),
            order_day=ExtractWeekDay('order_placed_at')
        ).values('order_hour').annotate(
            order_count=Count('order_id'),
            avg_prep_time=Avg(
                ExpressionWrapper(
                    F('preparation_completed_at') - F('order_placed_at'),
                    output_field=DurationField()
                )
            )
        ).order_by('-order_count')
        
        return {
            'peak_hours': [
                {
                    'hour': f"{data['order_hour']}:00",
                    'order_count': data['order_count'],
                    'average_prep_time_minutes': round(
                        data['avg_prep_time'].total_seconds() / 60 if data['avg_prep_time'] else 0, 2
                    )
                }
                for data in peak_data[:8]  # Top 8 hours
            ],
            'busiest_hour': peak_data[0] if peak_data else None
        }
    
    def _calculate_quality_metrics(self, orders_query):
        """Calculate quality and accuracy metrics"""
        delivered_orders = orders_query.filter(status='delivered')
        
        # Customer satisfaction (from ratings)
        avg_rating = delivered_orders.aggregate(
            avg_rating=Avg('rating__rating')
        )['avg_rating'] or 0
        
        # Order accuracy (placeholder - integrate with complaint/refund data)
        # For now, estimate based on rating
        accuracy_rate = (avg_rating / 5) * 100
        
        return {
            'average_rating': round(float(avg_rating), 2),
            'order_accuracy_rate': round(accuracy_rate, 2),
            'customer_satisfaction_score': round((avg_rating / 5) * 100, 2)
        }
    
    def _calculate_overall_efficiency(self, fulfillment, time, quality):
        """Calculate overall operational efficiency score"""
        weights = {
            'fulfillment_rate': 0.3,
            'on_time_delivery_rate': 0.3,
            'average_preparation_time': 0.2,
            'customer_satisfaction_score': 0.2
        }
        
        # Normalize preparation time (lower is better)
        prep_time_score = max(0, 100 - (time['average_preparation_time_minutes'] * 2))
        
        score = (
            fulfillment['fulfillment_rate'] * weights['fulfillment_rate'] +
            time['on_time_delivery_rate'] * weights['on_time_delivery_rate'] +
            prep_time_score * weights['average_preparation_time'] +
            quality['customer_satisfaction_score'] * weights['customer_satisfaction_score']
        )
        
        return round(score, 2)

class FinancialReportsView(AnalyticsBaseView):
    """
    Comprehensive financial reporting and analytics
    """
    
    def get(self, request, restaurant_id=None):
        serializer = AnalyticsPeriodSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        period = data.get('period', 'this_month')
        start_date, end_date = self._get_date_range(
            period, data.get('start_date'), data.get('end_date')
        )
        
        restaurants = self._get_restaurant_access(restaurant_id)
        
        financial_data = []
        for restaurant in restaurants:
            report = self._generate_financial_report(restaurant, start_date, end_date, period)
            financial_data.append(report)
        
        return Response({
            'period': period,
            'start_date': start_date,
            'end_date': end_date,
            'financial_reports': financial_data
        })
    
    def _generate_financial_report(self, restaurant, start_date, end_date, period_type):
        """Generate comprehensive financial report"""
        
        # Revenue analysis
        revenue_data = self._analyze_revenue(restaurant, start_date, end_date)
        
        # Cost analysis
        cost_data = self._analyze_costs(restaurant, start_date, end_date)
        
        # Profitability analysis
        profitability = self._analyze_profitability(revenue_data, cost_data)
        
        # Comparative analysis
        comparative_data = self._get_comparative_analysis(restaurant, start_date, end_date, period_type)
        
        # Financial health assessment
        health_assessment = self._assess_financial_health(profitability)
        
        return {
            'restaurant_id': restaurant.restaurant_id,
            'restaurant_name': restaurant.name,
            'report_period': f"{start_date} to {end_date}",
            'period_type': period_type,
            'revenue_analysis': revenue_data,
            'cost_analysis': cost_data,
            'profitability_analysis': profitability,
            'comparative_analysis': comparative_data,
            'financial_health': health_assessment,
            'key_metrics': self._calculate_key_metrics(revenue_data, cost_data, profitability),
            'recommendations': self._generate_financial_recommendations(profitability, health_assessment)
        }
    
    def _analyze_revenue(self, restaurant, start_date, end_date):
        """Analyze revenue streams"""
        orders = Order.objects.filter(
            restaurant=restaurant,
            order_placed_at__date__range=[start_date, end_date],
            status='delivered'
        )
        
        total_revenue = orders.aggregate(total=Sum('total_amount'))['total'] or 0
        
        # Revenue by category (simplified)
        category_revenue = OrderItem.objects.filter(
            order__in=orders
        ).values(
            'menu_item__category__name'
        ).annotate(
            revenue=Sum(F('quantity') * F('price_at_time'))
        ).order_by('-revenue')
        
        # Revenue trends (daily/weekly)
        daily_revenue = orders.annotate(
            date=TruncDate('order_placed_at')
        ).values('date').annotate(
            daily_revenue=Sum('total_amount')
        ).order_by('date')
        
        return {
            'total_revenue': float(total_revenue),
            'average_daily_revenue': float(total_revenue / max((end_date - start_date).days, 1)),
            'revenue_by_category': [
                {
                    'category': item['menu_item__category__name'] or 'Uncategorized',
                    'revenue': float(item['revenue'] or 0),
                    'percentage': round((item['revenue'] or 0) / total_revenue * 100, 2) if total_revenue > 0 else 0
                }
                for item in category_revenue
            ],
            'revenue_trends': [
                {
                    'date': item['date'].strftime('%Y-%m-%d'),
                    'revenue': float(item['daily_revenue'] or 0)
                }
                for item in daily_revenue
            ]
        }
    
    def _analyze_costs(self, restaurant, start_date, end_date):
        """Analyze costs and expenses"""
        # Placeholder - integrate with actual cost accounting system
        orders = Order.objects.filter(
            restaurant=restaurant,
            order_placed_at__date__range=[start_date, end_date],
            status='delivered'
        )
        
        total_revenue = orders.aggregate(total=Sum('total_amount'))['total'] or 0
        
        # Estimated costs (in production, use actual cost data)
        cogs = total_revenue * Decimal('0.35')  # 35% COGS estimate
        labor_costs = total_revenue * Decimal('0.25')  # 25% labor estimate
        operating_costs = total_revenue * Decimal('0.15')  # 15% operating expenses
        delivery_costs = total_revenue * Decimal('0.05')  # 5% delivery costs
        
        total_costs = cogs + labor_costs + operating_costs + delivery_costs
        
        return {
            'cost_of_goods_sold': float(cogs),
            'labor_costs': float(labor_costs),
            'operating_expenses': float(operating_costs),
            'delivery_costs': float(delivery_costs),
            'total_costs': float(total_costs),
            'cost_breakdown': {
                'cogs_percentage': 35.0,
                'labor_percentage': 25.0,
                'operating_percentage': 15.0,
                'delivery_percentage': 5.0
            }
        }
    
    def _analyze_profitability(self, revenue, costs):
        """Calculate profitability metrics"""
        gross_profit = revenue['total_revenue'] - costs['cost_of_goods_sold']
        operating_profit = gross_profit - costs['labor_costs'] - costs['operating_expenses']
        net_profit = operating_profit - costs['delivery_costs']
        
        gross_margin = (gross_profit / revenue['total_revenue'] * 100) if revenue['total_revenue'] > 0 else 0
        operating_margin = (operating_profit / revenue['total_revenue'] * 100) if revenue['total_revenue'] > 0 else 0
        net_margin = (net_profit / revenue['total_revenue'] * 100) if revenue['total_revenue'] > 0 else 0
        
        return {
            'gross_profit': gross_profit,
            'operating_profit': operating_profit,
            'net_profit': net_profit,
            'gross_margin': round(gross_margin, 2),
            'operating_margin': round(operating_margin, 2),
            'net_margin': round(net_margin, 2)
        }
    
    def _assess_financial_health(self, profitability):
        """Assess overall financial health"""
        net_margin = profitability['net_margin']
        
        if net_margin > 15:
            return {'status': 'excellent', 'color': 'green', 'score': 90}
        elif net_margin > 10:
            return {'status': 'good', 'color': 'blue', 'score': 75}
        elif net_margin > 5:
            return {'status': 'fair', 'color': 'yellow', 'score': 60}
        elif net_margin > 0:
            return {'status': 'poor', 'color': 'orange', 'score': 40}
        else:
            return {'status': 'critical', 'color': 'red', 'score': 20}

class ComparativeAnalyticsView(AnalyticsBaseView):
    """
    Comparative analytics against benchmarks and similar restaurants
    """
    
    def get(self, request, restaurant_id=None):
        serializer = AnalyticsPeriodSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        period = data.get('period', 'this_month')
        start_date, end_date = self._get_date_range(
            period, data.get('start_date'), data.get('end_date')
        )
        
        restaurants = self._get_restaurant_access(restaurant_id)
        
        comparative_data = []
        for restaurant in restaurants:
            analysis = self._generate_comparative_analysis(restaurant, start_date, end_date)
            comparative_data.append(analysis)
        
        return Response({
            'period': period,
            'start_date': start_date,
            'end_date': end_date,
            'comparative_analytics': comparative_data
        })
    
    def _generate_comparative_analysis(self, restaurant, start_date, end_date):
        """Generate comparative analysis against benchmarks"""
        
        # Get restaurant performance data
        restaurant_performance = self._get_restaurant_performance(restaurant, start_date, end_date)
        
        # Get industry benchmarks (placeholder - in production, use real benchmark data)
        industry_benchmarks = self._get_industry_benchmarks(restaurant)
        
        # Calculate comparative metrics
        comparative_metrics = self._calculate_comparative_metrics(
            restaurant_performance, industry_benchmarks
        )
        
        # SWOT analysis
        swot_analysis = self._perform_swot_analysis(comparative_metrics)
        
        # Competitive positioning
        competitive_position = self._determine_competitive_position(comparative_metrics)
        
        return {
            'restaurant_id': restaurant.restaurant_id,
            'restaurant_name': restaurant.name,
            'analysis_period': f"{start_date} to {end_date}",
            'restaurant_performance': restaurant_performance,
            'industry_benchmarks': industry_benchmarks,
            'comparative_metrics': comparative_metrics,
            'swot_analysis': swot_analysis,
            'competitive_position': competitive_position,
            'growth_opportunities': self._identify_growth_opportunities(comparative_metrics, swot_analysis)
        }
    
    def _get_restaurant_performance(self, restaurant, start_date, end_date):
        """Get key performance metrics for the restaurant"""
        orders = Order.objects.filter(
            restaurant=restaurant,
            order_placed_at__date__range=[start_date, end_date],
            status='delivered'
        )
        
        total_revenue = orders.aggregate(total=Sum('total_amount'))['total'] or 0
        total_orders = orders.count()
        avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
        
        # Customer metrics
        customer_count = orders.values('customer').distinct().count()
        retention_rate = self._calculate_simple_retention_rate(restaurant, start_date, end_date)
        
        return {
            'total_revenue': float(total_revenue),
            'total_orders': total_orders,
            'average_order_value': float(avg_order_value),
            'customer_count': customer_count,
            'retention_rate': retention_rate,
            'daily_revenue': float(total_revenue / max((end_date - start_date).days, 1))
        }
    
    def _get_industry_benchmarks(self, restaurant):
        """Get industry benchmark data (placeholder)"""
        # In production, integrate with industry data sources
        # These are sample benchmarks for a typical restaurant
        return {
            'average_daily_revenue': 1500.00,
            'average_order_value': 35.00,
            'customer_retention_rate': 65.0,
            'order_volume_per_day': 45,
            'net_profit_margin': 12.0
        }
    
    def _calculate_comparative_metrics(self, performance, benchmarks):
        """Calculate how the restaurant compares to benchmarks"""
        metrics = {}
        
        for key, benchmark in benchmarks.items():
            if key in performance:
                actual = performance[key]
                if isinstance(actual, (int, float)) and isinstance(benchmark, (int, float)) and benchmark != 0:
                    percentage_of_benchmark = (actual / benchmark) * 100
                    difference = actual - benchmark
                    
                    metrics[key] = {
                        'actual': actual,
                        'benchmark': benchmark,
                        'percentage_of_benchmark': round(percentage_of_benchmark, 2),
                        'difference': round(difference, 2),
                        'performance': 'above' if actual > benchmark else 'below'
                    }
        
        return metrics

class ExportAnalyticsView(AnalyticsBaseView):
    """
    Export analytics data to various formats
    """
    
    def post(self, request):
        serializer = ExportRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        report_type = data['report_type']
        export_format = data['format']
        period = data['period']
        
        restaurants = self._get_restaurant_access()
        
        # Generate export data
        export_data = self._generate_export_data(report_type, restaurants, period)
        
        # Create response based on format
        if export_format == 'csv':
            return self._export_to_csv(export_data, report_type)
        elif export_format == 'pdf':
            return self._export_to_pdf(export_data, report_type)
        elif export_format == 'excel':
            return self._export_to_excel(export_data, report_type)
        
        return Response({'error': 'Invalid export format'}, status=status.HTTP_400_BAD_REQUEST)
    
    def _generate_export_data(self, report_type, restaurants, period):
        """Generate data for export based on report type"""
        start_date, end_date = self._get_date_range(period)
        
        export_data = []
        for restaurant in restaurants:
            if report_type == 'customer_insights':
                data = self._get_restaurant_customer_insights(restaurant, start_date, end_date)
            elif report_type == 'menu_performance':
                data = self._get_restaurant_menu_performance(restaurant, start_date, end_date)
            # Add other report types...
            
            export_data.append(data)
        
        return export_data
    
    def _export_to_csv(self, data, report_type):
        """Export data to CSV format"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{report_type}_{datetime.now().strftime("%Y%m%d")}.csv"'
        
        writer = csv.writer(response)
        # Add CSV header and data based on report type
        # Implementation depends on specific report structure
        
        return response
    
    def _export_to_pdf(self, data, report_type):
        """Export data to PDF format using xhtml2pdf"""
        try:
            template_path = f'analytics/{report_type}_pdf.html'
            html_string = render_to_string(template_path, {'data': data})
            
            result = BytesIO()
            pdf = pisa.pisaDocument(BytesIO(html_string.encode("UTF-8")), result)
            
            if not pdf.err:
                response = HttpResponse(
                    result.getvalue(), 
                    content_type='application/pdf'
                )
                response['Content-Disposition'] = (
                    f'attachment; filename="{report_type}_'
                    f'{datetime.now().strftime("%Y%m%d")}.pdf"'
                )
                return response
            else:
                return Response(
                    {'error': 'PDF generation failed'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            return Response(
                {'error': f'PDF export error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _export_to_excel(self, data, report_type):
        """Export data to Excel format"""
        df = pd.DataFrame(data)
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=report_type, index=False)
        
        output.seek(0)
        
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{report_type}_{datetime.now().strftime("%Y%m%d")}.xlsx"'
        
        return response

class DashboardMetricsView(AnalyticsBaseView):
    """
    Real-time dashboard with key metrics
    """
    
    def get(self, request, restaurant_id=None):
        restaurants = self._get_restaurant_access(restaurant_id)
        
        dashboard_data = []
        for restaurant in restaurants:
            metrics = self._get_dashboard_metrics(restaurant)
            dashboard_data.append(metrics)
        
        return Response({
            'timestamp': timezone.now(),
            'dashboard_metrics': dashboard_data
        })
    
    def _get_dashboard_metrics(self, restaurant):
        """Get real-time dashboard metrics"""
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        # Today's metrics
        today_orders = Order.objects.filter(
            restaurant=restaurant,
            order_placed_at__date=today
        )
        today_revenue = today_orders.filter(status='delivered').aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        
        # Yesterday's metrics for comparison
        yesterday_orders = Order.objects.filter(
            restaurant=restaurant,
            order_placed_at__date=yesterday
        )
        yesterday_revenue = yesterday_orders.filter(status='delivered').aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        
        # Growth calculation
        revenue_growth = self._calculate_growth(today_revenue, yesterday_revenue)
        
        return {
            'restaurant_id': restaurant.restaurant_id,
            'restaurant_name': restaurant.name,
            'today': {
                'revenue': float(today_revenue),
                'orders': today_orders.count(),
                'completed_orders': today_orders.filter(status='delivered').count(),
                'average_order_value': float(
                    today_revenue / today_orders.filter(status='delivered').count()
                ) if today_orders.filter(status='delivered').count() > 0 else 0
            },
            'comparison': {
                'revenue_growth': revenue_growth,
                'order_growth': self._calculate_growth(
                    today_orders.count(), yesterday_orders.count()
                )
            },
            'live_metrics': {
                'orders_in_progress': today_orders.filter(
                    status__in=['preparing', 'ready_for_pickup', 'out_for_delivery']
                ).count(),
                'current_hour_orders': today_orders.filter(
                    order_placed_at__hour=timezone.now().hour
                ).count()
            }
        }
    
    def _calculate_growth(self, current, previous):
        """Calculate growth percentage"""
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        return round(((current - previous) / previous) * 100, 2)
    
# ==================== ENHANCED MENU ANALYTICS VIEWS ====================

class EnhancedMenuPerformanceView(APIView):
    """
    Comprehensive menu performance analytics with BCG matrix and profitability analysis
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        restaurant_id = request.GET.get('restaurant_id')
        days = int(request.GET.get('days', 30))
        
        if not restaurant_id:
            return Response({'error': 'restaurant_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not self._has_restaurant_access(request.user, restaurant_id):
            return Response({'error': 'Access denied to this restaurant'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            analytics = self._calculate_comprehensive_analytics(restaurant_id, days)
            serializer = EnhancedMenuPerformanceSerializer(analytics)
            return Response({
                'data': serializer.data,
                'pagination': None,
                'status': status.HTTP_200_OK,
                'success': True
            })
        except Exception as e:
            return Response({
                'error': f'Analytics calculation failed: {str(e)}',
                'status': status.HTTP_500_INTERNAL_SERVER_ERROR,
                'success': False
            })
    
    def _has_restaurant_access(self, user, restaurant_id):
        """Verify user has access to this restaurant"""
        if user.user_type == 'owner':
            return Restaurant.objects.filter(
                restaurant_id=restaurant_id, 
                owner=user
            ).exists()
        elif user.user_type == 'staff':
            return Restaurant.objects.filter(
                restaurant_id=restaurant_id,
                staff_members__user=user
            ).exists()
        elif user.user_type == 'admin':
            return True
        return False
    
    def _calculate_comprehensive_analytics(self, restaurant_id, days):
        """Calculate comprehensive menu performance metrics"""
        from django.db.models import Sum, Avg, Count, F, Q, Value, FloatField
        from django.db.models.functions import Coalesce
        from datetime import timedelta
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Get all menu items with their categories
        menu_items = MenuItem.objects.filter(
            category__restaurant_id=restaurant_id
        ).select_related('category').prefetch_related('order_items')
        
        # Calculate item performance
        item_performance = []
        for item in menu_items:
            # Get sales data for the period
            order_items = item.order_items.filter(
                order__status='delivered',
                order__order_placed_at__date__range=[start_date, end_date]
            )
            
            quantity_sold = order_items.aggregate(
                total=Coalesce(Sum('quantity'), Value(0))
            )['total']
            
            revenue = order_items.aggregate(
                total=Coalesce(Sum(F('quantity') * F('price_at_time')), Value(0.0))
            )['total']
            
            # Calculate profitability (simplified - 30% food cost)
            food_cost = revenue * 0.3
            gross_profit = revenue - food_cost
            profit_margin = (gross_profit / revenue * 100) if revenue > 0 else 0
            
            # Get ratings
            ratings = item.ratings.aggregate(
                avg_rating=Coalesce(Avg('rating'), Value(0.0)),
                count=Count('rating_id')
            )
            
            item_performance.append({
                'item_id': item.item_id,
                'name': item.name,
                'category_id': item.category_id,
                'category_name': item.category.name,
                'price': float(item.price),
                'is_available': item.is_available,
                'quantity_sold': quantity_sold,
                'revenue': float(revenue),
                'food_cost': float(food_cost),
                'gross_profit': float(gross_profit),
                'profit_margin': round(profit_margin, 2),
                'avg_rating': float(ratings['avg_rating']),
                'rating_count': ratings['count'],
                'popularity_score': item.popularity_score,
                'preparation_time': item.preparation_time
            })
        
        # Calculate category performance
        categories = MenuCategory.objects.filter(restaurant_id=restaurant_id)
        category_performance = []
        
        for category in categories:
            category_items = [item for item in item_performance if item['category_id'] == category.category_id]
            category_revenue = sum(item['revenue'] for item in category_items)
            category_items_sold = sum(item['quantity_sold'] for item in category_items)
            category_profit = sum(item['gross_profit'] for item in category_items)
            
            category_performance.append({
                'category_id': category.category_id,
                'name': category.name,
                'display_color': category.display_color,
                'display_order': category.display_order,
                'is_active': category.is_active,
                'total_items': len(category_items),
                'active_items': len([item for item in category_items if item['is_available']]),
                'items_sold': category_items_sold,
                'revenue': category_revenue,
                'gross_profit': category_profit,
                'profit_margin': (category_profit / category_revenue * 100) if category_revenue > 0 else 0,
                'avg_rating': np.mean([item['avg_rating'] for item in category_items]) if category_items else 0
            })
        
        # Calculate BCG Matrix
        bcg_matrix = self._calculate_bcg_matrix(item_performance)
        
        # Calculate popularity trends
        popularity_trends = self._get_popularity_trends(restaurant_id, days)
        
        # Overall summary metrics
        summary_metrics = self._calculate_summary_metrics(item_performance, category_performance)
        
        return {
            'restaurant_id': restaurant_id,
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': days
            },
            'summary_metrics': summary_metrics,
            'item_performance': item_performance,
            'category_performance': category_performance,
            'bcg_matrix': bcg_matrix,
            'popularity_trends': popularity_trends,
            'calculated_at': timezone.now().isoformat()
        }
    
    def _calculate_bcg_matrix(self, item_performance):
        """Calculate BCG matrix classification for menu items"""
        if not item_performance:
            return []
        
        # Filter out items with no sales
        active_items = [item for item in item_performance if item['quantity_sold'] > 0]
        if not active_items:
            return []
        
        # Calculate averages for segmentation
        avg_popularity = np.mean([item['popularity_score'] for item in active_items])
        avg_profit_margin = np.mean([item['profit_margin'] for item in active_items])
        
        bcg_matrix = []
        for item in active_items:
            if item['popularity_score'] >= avg_popularity and item['profit_margin'] >= avg_profit_margin:
                category = 'stars'
                recommendation = 'Promote and feature prominently'
            elif item['popularity_score'] >= avg_popularity and item['profit_margin'] < avg_profit_margin:
                category = 'plow_horses'
                recommendation = 'Optimize costs or increase price'
            elif item['popularity_score'] < avg_popularity and item['profit_margin'] >= avg_profit_margin:
                category = 'puzzles'
                recommendation = 'Increase marketing and visibility'
            else:
                category = 'dogs'
                recommendation = 'Consider removal or recipe improvement'
            
            bcg_matrix.append({
                **item,
                'bcg_category': category,
                'recommendation': recommendation,
                'relative_popularity': item['popularity_score'] / avg_popularity if avg_popularity > 0 else 0,
                'relative_profitability': item['profit_margin'] / avg_profit_margin if avg_profit_margin > 0 else 0
            })
        
        return bcg_matrix
    
    def _get_popularity_trends(self, restaurant_id, days):
        """Get popularity trends over time"""
        from datetime import datetime, timedelta
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Get daily popularity snapshots
        snapshots = PopularitySnapshot.objects.filter(
            menu_item__category__restaurant_id=restaurant_id,
            date_recorded__range=[start_date, end_date]
        ).values('date_recorded').annotate(
            avg_score=Avg('score'),
            total_items=Count('menu_item_id')
        ).order_by('date_recorded')
        
        return [
            {
                'date': snapshot['date_recorded'].strftime('%Y-%m-%d'),
                'avg_popularity': float(snapshot['avg_score'] or 0),
                'items_tracked': snapshot['total_items']
            }
            for snapshot in snapshots
        ]
    
    def _calculate_summary_metrics(self, item_performance, category_performance):
        """Calculate high-level summary metrics"""
        total_revenue = sum(item['revenue'] for item in item_performance)
        total_items_sold = sum(item['quantity_sold'] for item in item_performance)
        total_profit = sum(item['gross_profit'] for item in item_performance)
        
        active_items = [item for item in item_performance if item['is_available']]
        inactive_items = [item for item in item_performance if not item['is_available']]
        
        high_performers = [item for item in item_performance if item['profit_margin'] > 30 and item['quantity_sold'] > 10]
        low_performers = [item for item in item_performance if item['profit_margin'] < 10 or item['quantity_sold'] == 0]
        
        return {
            'total_revenue': float(total_revenue),
            'total_items_sold': total_items_sold,
            'total_gross_profit': float(total_profit),
            'overall_profit_margin': (total_profit / total_revenue * 100) if total_revenue > 0 else 0,
            'active_menu_items': len(active_items),
            'inactive_menu_items': len(inactive_items),
            'total_categories': len(category_performance),
            'high_performing_items': len(high_performers),
            'low_performing_items': len(low_performers),
            'menu_health_score': self._calculate_menu_health_score(item_performance)
        }
    
    def _calculate_menu_health_score(self, item_performance):
        """Calculate overall menu health score (0-100)"""
        if not item_performance:
            return 0
        
        # Score based on various factors
        availability_score = len([item for item in item_performance if item['is_available']]) / len(item_performance) * 30
        profitability_score = min(np.mean([item['profit_margin'] for item in item_performance]) / 50 * 40, 40)
        popularity_score = min(np.mean([item['popularity_score'] for item in item_performance]) / 100 * 30, 30)
        
        return round(availability_score + profitability_score + popularity_score, 2)


class CategoryAnalyticsView(APIView):
    """Detailed category-level analytics with trends"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        restaurant_id = request.GET.get('restaurant_id')
        
        if not restaurant_id:
            return Response({
                'error': 'restaurant_id is required',
                'status': status.HTTP_400_BAD_REQUEST,
                'success': False
            })
        
        if not self._has_restaurant_access(request.user, restaurant_id):
            return Response({
                'error': 'access denied',
                'status': status.HTTP_403_FORBIDDEN,
                'success': False
            })
        
        try:
            category_data = self._get_category_analytics(restaurant_id)
            serializer = CategoryAnalyticsSerializer(category_data, many=True)
            return Response({
                'data': serializer.data,
                'pagination': None,
                'status': status.HTTP_200_OK,
                'success': True
            })
        except Exception as e:
            return Response({
                'error': f'Category analytics failed: {str(e)}',
                'status': status.HTTP_500_INTERNAL_SERVER_ERROR,
                'success': False
            })
    
    def _get_category_analytics(self, restaurant_id):
        """Get comprehensive category analytics"""
        from django.db.models import Count, Sum, Avg, F, Q
        from datetime import timedelta
        
        thirty_days_ago = timezone.now() - timedelta(days=30)
        seven_days_ago = timezone.now() - timedelta(days=7)
        
        categories = MenuCategory.objects.filter(
            restaurant_id=restaurant_id
        ).annotate(
            # Basic counts
            total_items=Count('menu_items'),
            active_items=Count('menu_items', filter=Q(menu_items__is_available=True)),
            
            # Sales metrics (last 30 days)
            items_sold_30d=Coalesce(Sum(
                'menu_items__order_items__quantity',
                filter=Q(
                    menu_items__order_items__order__status='delivered',
                    menu_items__order_items__order__order_placed_at__gte=thirty_days_ago
                )
            ), Value(0)),
            
            revenue_30d=Coalesce(Sum(
                F('menu_items__order_items__quantity') * F('menu_items__order_items__price_at_time'),
                filter=Q(
                    menu_items__order_items__order__status='delivered',
                    menu_items__order_items__order__order_placed_at__gte=thirty_days_ago
                )
            ), Value(0.0)),
            
            # Recent sales (last 7 days)
            items_sold_7d=Coalesce(Sum(
                'menu_items__order_items__quantity',
                filter=Q(
                    menu_items__order_items__order__status='delivered',
                    menu_items__order_items__order__order_placed_at__gte=seven_days_ago
                )
            ), Value(0)),
            
            # Performance metrics
            avg_rating=Coalesce(Avg('menu_items__ratings__rating'), Value(0.0)),
            avg_prep_time=Coalesce(Avg('menu_items__preparation_time'), Value(0)),
            
            # Growth calculation (compare last 7 days vs previous 7 days)
            previous_period_revenue=Coalesce(Sum(
                F('menu_items__order_items__quantity') * F('menu_items__order_items__price_at_time'),
                filter=Q(
                    menu_items__order_items__order__status='delivered',
                    menu_items__order_items__order__order_placed_at__range=[
                        thirty_days_ago - timedelta(days=7),
                        thirty_days_ago
                    ]
                )
            ), Value(0.0))
        ).values(
            'category_id', 'name', 'display_color', 'display_order', 'is_active',
            'total_items', 'active_items', 'items_sold_30d', 'revenue_30d',
            'items_sold_7d', 'avg_rating', 'avg_prep_time', 'previous_period_revenue'
        )
        
        # Calculate growth rates
        category_data = []
        for category in categories:
            revenue_growth = 0
            if category['previous_period_revenue'] > 0:
                revenue_growth = ((category['revenue_30d'] - category['previous_period_revenue']) / 
                                category['previous_period_revenue'] * 100)
            
            category_data.append({
                **category,
                'revenue_30d': float(category['revenue_30d']),
                'previous_period_revenue': float(category['previous_period_revenue']),
                'revenue_growth': round(revenue_growth, 2),
                'performance_score': self._calculate_category_performance_score(category)
            })
        
        return category_data
    
    def _calculate_category_performance_score(self, category):
        """Calculate performance score for category (0-100)"""
        score = 0
        
        # Revenue contribution (max 40 points)
        if category['revenue_30d'] > 1000:
            score += 40
        elif category['revenue_30d'] > 500:
            score += 30
        elif category['revenue_30d'] > 100:
            score += 20
        else:
            score += 10
        
        # Growth (max 20 points)
        if category['revenue_growth'] > 20:
            score += 20
        elif category['revenue_growth'] > 10:
            score += 15
        elif category['revenue_growth'] > 0:
            score += 10
        else:
            score += 5
        
        # Item utilization (max 20 points)
        utilization = (category['active_items'] / category['total_items']) * 100 if category['total_items'] > 0 else 0
        if utilization > 80:
            score += 20
        elif utilization > 60:
            score += 15
        elif utilization > 40:
            score += 10
        else:
            score += 5
        
        # Rating (max 20 points)
        if category['avg_rating'] > 4.0:
            score += 20
        elif category['avg_rating'] > 3.0:
            score += 15
        elif category['avg_rating'] > 2.0:
            score += 10
        else:
            score += 5
        
        return min(score, 100)


class ItemAssociationsView(APIView):
    """Get items frequently bought together with confidence scores"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, item_id):
        if not self._has_item_access(request.user, item_id):
            return Response({'error': 'Access denied to this item'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            associations = self._calculate_item_associations(item_id)
            return Response(associations)
        except Exception as e:
            return Response(
                {'error': f'Association calculation failed: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _has_item_access(self, user, item_id):
        """Verify user has access to this menu item"""
        try:
            item = MenuItem.objects.get(item_id=item_id)
            if user.user_type == 'owner':
                return item.category.restaurant.owner == user
            elif user.user_type == 'staff':
                return item.category.restaurant.staff_members.filter(user=user).exists()
            elif user.user_type == 'admin':
                return True
            return False
        except MenuItem.DoesNotExist:
            return False
    
    def _calculate_item_associations(self, item_id):
        """Calculate items frequently bought together with the given item"""
        from collections import Counter
        
        # Get all orders that contain the target item
        target_orders = OrderItem.objects.filter(
            menu_item_id=item_id,
            order__status='delivered'
        ).values_list('order_id', flat=True).distinct()
        
        if not target_orders:
            return []
        
        # Find other items in those orders
        associated_items = OrderItem.objects.filter(
            order_id__in=target_orders
        ).exclude(menu_item_id=item_id).select_related('menu_item')
        
        # Count co-occurrences
        item_counter = Counter()
        for order_item in associated_items:
            item_counter[order_item.menu_item_id] += 1
        
        total_orders_with_target = len(target_orders)
        
        # Calculate association metrics
        associations = []
        for menu_item_id, count in item_counter.most_common(10):  # Top 10 associations
            try:
                menu_item = MenuItem.objects.get(item_id=menu_item_id)
                confidence = (count / total_orders_with_target) * 100
                support = count
                
                associations.append({
                    'item_id': menu_item.item_id,
                    'name': menu_item.name,
                    'price': float(menu_item.price),
                    'category': menu_item.category.name,
                    'confidence': round(confidence, 2),
                    'support': support,
                    'lift': self._calculate_lift(item_id, menu_item_id, count, total_orders_with_target)
                })
            except MenuItem.DoesNotExist:
                continue
        
        return associations
    
    def _calculate_lift(self, item_a_id, item_b_id, co_occurrence, total_orders_with_a):
        """Calculate lift metric for association rules"""
        from django.db.models import Count
        
        # Total number of orders
        total_orders = Order.objects.filter(status='delivered').count()
        if total_orders == 0:
            return 1.0
        
        # Number of orders containing item B
        orders_with_b = OrderItem.objects.filter(
            menu_item_id=item_b_id,
            order__status='delivered'
        ).values('order_id').distinct().count()
        
        if orders_with_b == 0:
            return 1.0
        
        # Calculate lift: P(A&B) / (P(A) * P(B))
        prob_a_and_b = co_occurrence / total_orders
        prob_a = total_orders_with_a / total_orders
        prob_b = orders_with_b / total_orders
        
        if prob_a * prob_b == 0:
            return 1.0
        
        lift = prob_a_and_b / (prob_a * prob_b)
        return round(lift, 3)


class BulkMenuOperationsView(APIView):
    """Handle bulk operations on menu items and categories"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        operation_type = request.data.get('operation_type')
        restaurant_id = request.data.get('restaurant_id')
        items = request.data.get('items', [])
        
        if not restaurant_id or not operation_type:
            return Response(
                {'error': 'restaurant_id and operation_type are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not self._has_restaurant_access(request.user, restaurant_id):
            return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            if operation_type == 'update_prices':
                result = self._bulk_update_prices(restaurant_id, items)
            elif operation_type == 'update_availability':
                result = self._bulk_update_availability(restaurant_id, items)
            elif operation_type == 'update_categories':
                result = self._bulk_update_categories(restaurant_id, items)
            else:
                return Response({'error': 'Invalid operation type'}, status=status.HTTP_400_BAD_REQUEST)
            
            return Response(result)
            
        except Exception as e:
            return Response(
                {'error': f'Bulk operation failed: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _bulk_update_prices(self, restaurant_id, items):
        """Bulk update menu item prices"""
        from django.db import transaction
        
        updated_count = 0
        with transaction.atomic():
            for item_data in items:
                item_id = item_data.get('item_id')
                new_price = item_data.get('new_price')
                
                if not item_id or new_price is None:
                    continue
                
                try:
                    menu_item = MenuItem.objects.get(
                        item_id=item_id,
                        category__restaurant_id=restaurant_id
                    )
                    menu_item.price = new_price
                    menu_item.save()
                    updated_count += 1
                except MenuItem.DoesNotExist:
                    continue
        
        return {
            'operation': 'update_prices',
            'updated_count': updated_count,
            'total_items': len(items)
        }
    
    def _bulk_update_availability(self, restaurant_id, items):
        """Bulk update menu item availability"""
        from django.db import transaction
        
        updated_count = 0
        with transaction.atomic():
            for item_data in items:
                item_id = item_data.get('item_id')
                is_available = item_data.get('is_available')
                
                if not item_id or is_available is None:
                    continue
                
                try:
                    menu_item = MenuItem.objects.get(
                        item_id=item_id,
                        category__restaurant_id=restaurant_id
                    )
                    menu_item.is_available = is_available
                    menu_item.save()
                    updated_count += 1
                except MenuItem.DoesNotExist:
                    continue
        
        return {
            'operation': 'update_availability',
            'updated_count': updated_count,
            'total_items': len(items)
        }
    
    def _bulk_update_categories(self, restaurant_id, items):
        """Bulk update menu item categories"""
        from django.db import transaction
        
        updated_count = 0
        with transaction.atomic():
            for item_data in items:
                item_id = item_data.get('item_id')
                category_id = item_data.get('category_id')
                
                if not item_id or not category_id:
                    continue
                
                try:
                    # Verify both item and category belong to the same restaurant
                    menu_item = MenuItem.objects.get(
                        item_id=item_id,
                        category__restaurant_id=restaurant_id
                    )
                    new_category = MenuCategory.objects.get(
                        category_id=category_id,
                        restaurant_id=restaurant_id
                    )
                    
                    menu_item.category = new_category
                    menu_item.save()
                    updated_count += 1
                except (MenuItem.DoesNotExist, MenuCategory.DoesNotExist):
                    continue
        
        return {
            'operation': 'update_categories',
            'updated_count': updated_count,
            'total_items': len(items)
        }


class RealTimeMenuMetricsView(APIView):
    """Real-time metrics for menu performance"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, restaurant_id):
        if not self._has_restaurant_access(request.user, restaurant_id):
            return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            metrics = self._get_real_time_metrics(restaurant_id)
            return Response(metrics)
        except Exception as e:
            return Response(
                {'error': f'Real-time metrics failed: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_real_time_metrics(self, restaurant_id):
        """Get real-time menu performance metrics"""
        from datetime import datetime, timedelta
        
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        current_hour = now.replace(minute=0, second=0, microsecond=0)
        
        # Today's metrics
        today_orders = Order.objects.filter(
            restaurant_id=restaurant_id,
            order_placed_at__gte=today_start,
            status='delivered'
        )
        
        today_metrics = today_orders.aggregate(
            total_orders=Count('order_id'),
            total_revenue=Coalesce(Sum('total_amount'), Value(0.0)),
            avg_order_value=Coalesce(Avg('total_amount'), Value(0.0))
        )
        
        # Current hour metrics
        current_hour_orders = Order.objects.filter(
            restaurant_id=restaurant_id,
            order_placed_at__gte=current_hour,
            status='delivered'
        )
        
        current_hour_metrics = current_hour_orders.aggregate(
            orders_count=Count('order_id'),
            revenue=Coalesce(Sum('total_amount'), Value(0.0))
        )
        
        # Active preparations
        active_preparations = Order.objects.filter(
            restaurant_id=restaurant_id,
            status__in=['preparing', 'ready_for_pickup'],
            order_placed_at__gte=today_start
        ).count()
        
        # Low stock alerts (simplified - based on popularity and recent sales)
        popular_items = MenuItem.objects.filter(
            category__restaurant_id=restaurant_id,
            is_available=True
        ).annotate(
            recent_orders=Count('order_items', filter=Q(
                order_items__order__order_placed_at__gte=today_start - timedelta(days=7)
            ))
        ).order_by('-recent_orders')[:10]
        
        low_stock_alerts = []
        for item in popular_items:
            # Simplified stock alert logic
            if item.recent_orders > 20:  # High demand items
                low_stock_alerts.append({
                    'item_id': item.item_id,
                    'name': item.name,
                    'alert_level': 'high' if item.recent_orders > 50 else 'medium',
                    'message': f'High demand item - monitor stock levels'
                })
        
        return {
            'timestamp': now.isoformat(),
            'today_metrics': {
                'total_orders': today_metrics['total_orders'],
                'total_revenue': float(today_metrics['total_revenue']),
                'average_order_value': float(today_metrics['avg_order_value'])
            },
            'current_hour_metrics': {
                'orders_count': current_hour_metrics['orders_count'],
                'revenue': float(current_hour_metrics['revenue'])
            },
            'operational_metrics': {
                'active_preparations': active_preparations,
                'kitchen_load': min(active_preparations * 10, 100),  # Simplified load calculation
                'low_stock_alerts': len(low_stock_alerts)
            },
            'alerts': low_stock_alerts
        }