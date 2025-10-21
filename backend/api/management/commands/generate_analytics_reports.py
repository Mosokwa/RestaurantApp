from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Count, Sum, Avg, F, Q
from decimal import Decimal
import logging
from django.db.models.functions import ExtractHour

from api.models import (
    CustomerLifetimeValue, MenuItemPerformance, OperationalEfficiency,
    FinancialReport, ComparativeAnalytics, RestaurantPerformanceMetrics,
    RestaurantSalesReport, DailySalesSnapshot, Restaurant, Order, OrderItem,
    Customer, MenuItem
)

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Generate automated analytics reports'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--report-type',
            type=str,
            choices=['daily', 'weekly', 'monthly', 'all'],
            default='daily',
            help='Type of report to generate'
        )
        parser.add_argument(
            '--restaurant-id',
            type=int,
            help='Specific restaurant ID to generate reports for'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force regeneration of existing reports'
        )

    def handle(self, *args, **options):
        report_type = options['report_type']
        restaurant_id = options['restaurant_id']
        force = options['force']
        
        self.stdout.write(f'Generating {report_type} analytics reports...')
        
        # Get restaurants to process
        restaurants = Restaurant.objects.filter(status='active')
        if restaurant_id:
            restaurants = restaurants.filter(restaurant_id=restaurant_id)
        
        if not restaurants.exists():
            self.stdout.write(self.style.ERROR('No restaurants found to process'))
            return
        
        try:
            if report_type in ['daily', 'all']:
                self.generate_daily_reports(restaurants, force)
            
            if report_type in ['weekly', 'all']:
                self.generate_weekly_reports(restaurants, force)
            
            if report_type in ['monthly', 'all']:
                self.generate_monthly_reports(restaurants, force)
            
            # Update performance metrics
            self.update_performance_metrics(restaurants)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully generated {report_type} reports for {restaurants.count()} restaurants'
                )
            )
            
        except Exception as e:
            logger.error(f"Failed to generate reports: {str(e)}")
            self.stdout.write(self.style.ERROR(f'Report generation failed: {str(e)}'))

    def generate_daily_reports(self, restaurants, force=False):
        """Generate daily operational and performance reports"""
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        self.stdout.write(f'Generating daily reports for {yesterday}...')
        
        for restaurant in restaurants:
            # Check if report already exists
            if not force and DailySalesSnapshot.objects.filter(
                restaurant=restaurant, date=yesterday
            ).exists():
                self.stdout.write(f'Daily report already exists for {restaurant.name} - {yesterday}')
                continue
            
            try:
                # Get orders for yesterday
                orders = Order.objects.filter(
                    restaurant=restaurant,
                    order_placed_at__date=yesterday
                )
                
                completed_orders = orders.filter(status='delivered')
                cancelled_orders = orders.filter(status='cancelled')
                
                # Calculate metrics
                total_revenue = completed_orders.aggregate(
                    total=Sum('total_amount')
                )['total'] or Decimal('0.00')
                
                # Get previous day for growth calculation
                day_before = yesterday - timedelta(days=1)
                prev_day_orders = Order.objects.filter(
                    restaurant=restaurant,
                    order_placed_at__date=day_before,
                    status='delivered'
                )
                prev_day_revenue = prev_day_orders.aggregate(
                    total=Sum('total_amount')
                )['total'] or Decimal('0.00')
                
                # Calculate growth rate
                growth_rate = Decimal('0.00')
                if prev_day_revenue > 0:
                    growth_rate = ((total_revenue - prev_day_revenue) / prev_day_revenue) * 100
                
                # Get hourly breakdown
                hourly_orders = {}
                hourly_revenue = {}
                for hour in range(24):
                    hour_orders = orders.filter(
                        order_placed_at__hour=hour
                    )
                    hour_revenue = hour_orders.filter(
                        status='delivered'
                    ).aggregate(
                        total=Sum('total_amount')
                    )['total'] or Decimal('0.00')
                    
                    hourly_orders[f"{hour:02d}:00"] = hour_orders.count()
                    hourly_revenue[f"{hour:02d}:00"] = float(hour_revenue)
                
                # Get top items for the day
                top_items = OrderItem.objects.filter(
                    order__in=completed_orders
                ).values(
                    'menu_item__item_id', 'menu_item__name'
                ).annotate(
                    quantity_sold=Sum('quantity')
                ).order_by('-quantity_sold')[:5]
                
                daily_top_items = {
                    item['menu_item__name']: item['quantity_sold']
                    for item in top_items
                }
                
                # Create daily snapshot
                snapshot, created = DailySalesSnapshot.objects.get_or_create(
                    restaurant=restaurant,
                    date=yesterday,
                    defaults={
                        'orders_count': orders.count(),
                        'revenue': total_revenue,
                        'completed_orders': completed_orders.count(),
                        'cancelled_orders': cancelled_orders.count(),
                        'hourly_orders': hourly_orders,
                        'hourly_revenue': hourly_revenue,
                        'daily_top_items': daily_top_items,
                    }
                )
                
                if not created:
                    # Update existing snapshot
                    snapshot.orders_count = orders.count()
                    snapshot.revenue = total_revenue
                    snapshot.completed_orders = completed_orders.count()
                    snapshot.cancelled_orders = cancelled_orders.count()
                    snapshot.hourly_orders = hourly_orders
                    snapshot.hourly_revenue = hourly_revenue
                    snapshot.daily_top_items = daily_top_items
                    snapshot.save()
                
                # Generate operational efficiency report
                self.generate_operational_efficiency(restaurant, yesterday, 'daily')
                
                # Generate menu item performance
                self.generate_menu_performance(restaurant, yesterday, yesterday, 'daily')
                
                self.stdout.write(
                    self.style.SUCCESS(f'Created daily report for {restaurant.name} - {yesterday}')
                )
                
            except Exception as e:
                logger.error(f"Failed to generate daily report for {restaurant.name}: {str(e)}")
                self.stdout.write(
                    self.style.ERROR(f'Failed for {restaurant.name}: {str(e)}')
                )

    def generate_weekly_reports(self, restaurants, force=False):
        """Generate weekly comprehensive reports"""
        today = timezone.now().date()
        start_of_week = today - timedelta(days=today.weekday() + 7)  # Last week
        end_of_week = start_of_week + timedelta(days=6)
        
        self.stdout.write(f'Generating weekly reports for {start_of_week} to {end_of_week}...')
        
        for restaurant in restaurants:
            if not force and RestaurantSalesReport.objects.filter(
                restaurant=restaurant,
                period_type='weekly',
                start_date=start_of_week
            ).exists():
                self.stdout.write(f'Weekly report already exists for {restaurant.name}')
                continue
            
            try:
                self.generate_sales_report(
                    restaurant, 'weekly', start_of_week, end_of_week
                )
                self.generate_financial_report(
                    restaurant, 'weekly', start_of_week, end_of_week
                )
                self.generate_menu_performance(
                    restaurant, start_of_week, end_of_week, 'weekly'
                )
                
                self.stdout.write(
                    self.style.SUCCESS(f'Created weekly report for {restaurant.name}')
                )
                
            except Exception as e:
                logger.error(f"Failed to generate weekly report for {restaurant.name}: {str(e)}")
                self.stdout.write(
                    self.style.ERROR(f'Failed for {restaurant.name}: {str(e)}')
                )

    def generate_monthly_reports(self, restaurants, force=False):
        """Generate monthly financial and performance reports"""
        today = timezone.now().date()
        first_day_last_month = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
        last_day_last_month = today.replace(day=1) - timedelta(days=1)
        
        self.stdout.write(
            f'Generating monthly reports for {first_day_last_month} to {last_day_last_month}...'
        )
        
        for restaurant in restaurants:
            if not force and RestaurantSalesReport.objects.filter(
                restaurant=restaurant,
                period_type='monthly',
                start_date=first_day_last_month
            ).exists():
                self.stdout.write(f'Monthly report already exists for {restaurant.name}')
                continue
            
            try:
                self.generate_sales_report(
                    restaurant, 'monthly', first_day_last_month, last_day_last_month
                )
                self.generate_financial_report(
                    restaurant, 'monthly', first_day_last_month, last_day_last_month
                )
                self.generate_comparative_analytics(
                    restaurant, 'monthly', first_day_last_month, last_day_last_month
                )
                self.generate_customer_analytics(
                    restaurant, first_day_last_month, last_day_last_month
                )
                
                self.stdout.write(
                    self.style.SUCCESS(f'Created monthly report for {restaurant.name}')
                )
                
            except Exception as e:
                logger.error(f"Failed to generate monthly report for {restaurant.name}: {str(e)}")
                self.stdout.write(
                    self.style.ERROR(f'Failed for {restaurant.name}: {str(e)}')
                )

    def generate_sales_report(self, restaurant, period_type, start_date, end_date):
        """Generate sales report for a period"""
        orders = Order.objects.filter(
            restaurant=restaurant,
            order_placed_at__date__range=[start_date, end_date]
        )
        
        completed_orders = orders.filter(status='delivered')
        cancelled_orders = orders.filter(status='cancelled')
        
        # Calculate metrics
        total_revenue = completed_orders.aggregate(
            total=Sum('total_amount')
        )['total'] or Decimal('0.00')
        
        avg_order_value = completed_orders.aggregate(
            avg=Avg('total_amount')
        )['avg'] or Decimal('0.00')
        
        # Customer metrics
        new_customers = orders.values('customer').distinct().count()
        
        # Get top items
        top_items = OrderItem.objects.filter(
            order__in=completed_orders
        ).values(
            'menu_item__name'
        ).annotate(
            quantity=Sum('quantity')
        ).order_by('-quantity')[:10]
        
        top_items_dict = {
            item['menu_item__name']: item['quantity']
            for item in top_items
        }
        
        # Get popular categories
        popular_categories = OrderItem.objects.filter(
            order__in=completed_orders
        ).values(
            'menu_item__category__name'
        ).annotate(
            count=Count('menu_item_id')
        ).order_by('-count')[:5]
        
        popular_categories_dict = {
            item['menu_item__category__name']: item['count']
            for item in popular_categories
        }
        
        # Peak hours analysis
        peak_hours = orders.annotate(
            hour=ExtractHour('order_placed_at')
        ).values('hour').annotate(
            count=Count('order_id')
        ).order_by('-count')[:6]
        
        peak_hours_dict = {
            f"{item['hour']:02d}:00": item['count']
            for item in peak_hours
        }
        
        # Create or update sales report
        report, created = RestaurantSalesReport.objects.update_or_create(
            restaurant=restaurant,
            period_type=period_type,
            start_date=start_date,
            defaults={
                'end_date': end_date,
                'total_orders': orders.count(),
                'total_revenue': total_revenue,
                'average_order_value': avg_order_value,
                'completed_orders': completed_orders.count(),
                'cancelled_orders': cancelled_orders.count(),
                'new_customers': new_customers,
                'returning_customers': 0,  # This would need more complex calculation
                'top_items': top_items_dict,
                'popular_categories': popular_categories_dict,
                'peak_hours': peak_hours_dict,
                'average_preparation_time': 25,  # Placeholder
                'average_delivery_time': 45,     # Placeholder
            }
        )
        
        return report

    def generate_financial_report(self, restaurant, period_type, start_date, end_date):
        """Generate financial report for a period"""
        completed_orders = Order.objects.filter(
            restaurant=restaurant,
            order_placed_at__date__range=[start_date, end_date],
            status='delivered'
        )
        
        total_revenue = completed_orders.aggregate(
            total=Sum('total_amount')
        )['total'] or Decimal('0.00')
        
        # Calculate estimated costs (in production, use actual cost data)
        cogs = total_revenue * Decimal('0.35')  # 35% COGS
        labor_costs = total_revenue * Decimal('0.25')  # 25% labor
        operating_costs = total_revenue * Decimal('0.15')  # 15% operating
        delivery_costs = total_revenue * Decimal('0.05')  # 5% delivery
        
        gross_profit = total_revenue - cogs
        operating_profit = gross_profit - labor_costs - operating_costs
        net_profit = operating_profit - delivery_costs
        
        # Calculate margins
        gross_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0
        operating_margin = (operating_profit / total_revenue * 100) if total_revenue > 0 else 0
        net_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0
        
        # Get previous period for comparison
        if period_type == 'monthly':
            prev_start = (start_date.replace(day=1) - timedelta(days=1)).replace(day=1)
            prev_end = start_date - timedelta(days=1)
        else:  # weekly
            prev_start = start_date - timedelta(days=7)
            prev_end = start_date - timedelta(days=1)
        
        prev_revenue = Order.objects.filter(
            restaurant=restaurant,
            order_placed_at__date__range=[prev_start, prev_end],
            status='delivered'
        ).aggregate(
            total=Sum('total_amount')
        )['total'] or Decimal('0.00')
        
        revenue_growth = Decimal('0.00')
        if prev_revenue > 0:
            revenue_growth = ((total_revenue - prev_revenue) / prev_revenue) * 100
        
        # Create financial report
        report, created = FinancialReport.objects.update_or_create(
            restaurant=restaurant,
            report_type='profit_loss',
            period_type=period_type,
            start_date=start_date,
            defaults={
                'end_date': end_date,
                'total_revenue': total_revenue,
                'food_revenue': total_revenue * Decimal('0.85'),  # Estimate
                'beverage_revenue': total_revenue * Decimal('0.15'),  # Estimate
                'cost_of_goods_sold': cogs,
                'labor_costs': labor_costs,
                'operating_expenses': operating_costs,
                'delivery_costs': delivery_costs,
                'gross_profit': gross_profit,
                'operating_profit': operating_profit,
                'net_profit': net_profit,
                'gross_margin': gross_margin,
                'operating_margin': operating_margin,
                'net_margin': net_margin,
                'previous_period_revenue': prev_revenue,
                'revenue_growth': revenue_growth,
                'industry_benchmark': Decimal('12.00'),  # Placeholder
            }
        )
        
        return report

    def generate_operational_efficiency(self, restaurant, date, period_type):
        """Generate operational efficiency report"""
        orders = Order.objects.filter(
            restaurant=restaurant,
            order_placed_at__date=date
        )
        
        completed_orders = orders.filter(status='delivered')
        
        # Calculate metrics
        fulfillment_rate = (completed_orders.count() / orders.count() * 100) if orders.count() > 0 else 0
        
        # Placeholder calculations - in production, use actual timing data
        avg_prep_time = 25  # minutes
        avg_delivery_time = 45  # minutes
        on_time_rate = 85  # percentage
        
        # Peak hours analysis
        peak_hours = orders.annotate(
            hour=ExtractHour('order_placed_at')
        ).values('hour').annotate(
            count=Count('order_id')
        ).order_by('-count')[:8]
        
        peak_hours_dict = {
            f"{item['hour']:02d}:00": item['count']
            for item in peak_hours
        }
        
        # Create operational efficiency record
        efficiency, created = OperationalEfficiency.objects.update_or_create(
            restaurant=restaurant,
            date=date,
            period_type=period_type,
            defaults={
                'total_orders': orders.count(),
                'completed_orders': completed_orders.count(),
                'cancelled_orders': orders.filter(status='cancelled').count(),
                'fulfillment_rate': fulfillment_rate,
                'average_preparation_time': avg_prep_time,
                'average_delivery_time': avg_delivery_time,
                'on_time_delivery_rate': on_time_rate,
                'orders_per_staff_hour': Decimal('2.5'),  # Placeholder
                'revenue_per_staff_hour': Decimal('85.00'),  # Placeholder
                'peak_hours': peak_hours_dict,
                'kitchen_utilization': Decimal('75.0'),  # Placeholder
                'delivery_utilization': Decimal('65.0'),  # Placeholder
                'order_accuracy_rate': Decimal('95.0'),  # Placeholder
                'customer_satisfaction_score': Decimal('4.2'),  # Placeholder
            }
        )
        
        return efficiency

    def generate_menu_performance(self, restaurant, start_date, end_date, period_type):
        """Generate menu item performance reports"""
        completed_orders = Order.objects.filter(
            restaurant=restaurant,
            order_placed_at__date__range=[start_date, end_date],
            status='delivered'
        )
        
        # Get all menu items for the restaurant
        menu_items = MenuItem.objects.filter(category__restaurant=restaurant)
        
        for menu_item in menu_items:
            # Get sales data for this item
            item_orders = OrderItem.objects.filter(
                menu_item=menu_item,
                order__in=completed_orders
            )
            
            quantity_sold = item_orders.aggregate(
                total=Sum('quantity')
            )['total'] or 0
            
            total_revenue = item_orders.aggregate(
                total=Sum(F('quantity') * F('unit_price'))
            )['total'] or Decimal('0.00')
            
            avg_selling_price = (total_revenue / quantity_sold) if quantity_sold > 0 else Decimal('0.00')
            
            # Calculate profitability (simplified)
            cost_per_item = menu_item.price * Decimal('0.3')  # 30% COGS estimate
            total_cost = cost_per_item * quantity_sold
            gross_profit = total_revenue - total_cost
            profit_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0
            
            # Create performance record
            performance, created = MenuItemPerformance.objects.update_or_create(
                menu_item=menu_item,
                period_type=period_type,
                start_date=start_date,
                defaults={
                    'restaurant': restaurant,
                    'end_date': end_date,
                    'quantity_sold': quantity_sold,
                    'total_revenue': total_revenue,
                    'average_selling_price': avg_selling_price,
                    'profit_margin': profit_margin,
                    'popularity_rank': 0,  # Would need to calculate based on all items
                    'growth_rate': Decimal('0.00'),  # Would need historical data
                    'ingredient_cost': cost_per_item * Decimal('0.7'),  # Estimate
                    'preparation_cost': cost_per_item * Decimal('0.3'),  # Estimate
                    'total_cost': total_cost,
                    'gross_profit': gross_profit,
                }
            )

    def generate_comparative_analytics(self, restaurant, period_type, start_date, end_date):
        """Generate comparative analytics against benchmarks"""
        # Placeholder implementation - in production, integrate with real benchmark data
        comparative, created = ComparativeAnalytics.objects.update_or_create(
            restaurant=restaurant,
            comparison_type='industry',
            period_type=period_type,
            start_date=start_date,
            defaults={
                'end_date': end_date,
                'revenue_comparison': {
                    'your_value': 10000,
                    'benchmark': 12000,
                    'percentile': 75
                },
                'order_volume_comparison': {
                    'your_value': 250,
                    'benchmark': 300,
                    'percentile': 70
                },
                'market_share': Decimal('8.5'),
                'competitive_position': 'strong',
                'strengths': ['High customer satisfaction', 'Efficient operations'],
                'weaknesses': ['Lower than average order volume', 'Limited delivery range'],
                'opportunities': ['Expand delivery area', 'Introduce loyalty program'],
                'threats': ['New competitors in area', 'Rising ingredient costs']
            }
        )
        
        return comparative

    def generate_customer_analytics(self, restaurant, start_date, end_date):
        """Generate customer lifetime value and analytics"""
        customers = Customer.objects.filter(
            orders__restaurant=restaurant,
            orders__order_placed_at__date__range=[start_date, end_date]
        ).distinct()
        
        for customer in customers:
            customer_orders = Order.objects.filter(
                restaurant=restaurant,
                customer=customer,
                order_placed_at__date__range=[start_date, end_date],
                status='delivered'
            )
            
            if not customer_orders.exists():
                continue
            
            total_orders = customer_orders.count()
            total_spent = customer_orders.aggregate(
                total=Sum('total_amount')
            )['total'] or Decimal('0.00')
            
            avg_order_value = total_spent / total_orders if total_orders > 0 else Decimal('0.00')
            
            first_order = customer_orders.earliest('order_placed_at')
            last_order = customer_orders.latest('order_placed_at')
            
            # Calculate order frequency
            if total_orders > 1:
                date_range = (last_order.order_placed_at - first_order.order_placed_at).days
                order_frequency = date_range / (total_orders - 1)
            else:
                order_frequency = 0
            
            # Simple CLV calculation
            predicted_clv = avg_order_value * 12  # Annual estimate
            
            # Determine customer segment
            if total_spent > 500:
                segment = 'high_value'
            elif total_spent > 200:
                segment = 'medium_value'
            else:
                segment = 'low_value'
            
            # Create or update CLV record
            clv, created = CustomerLifetimeValue.objects.update_or_create(
                customer=customer,
                restaurant=restaurant,
                defaults={
                    'first_order_date': first_order.order_placed_at,
                    'last_order_date': last_order.order_placed_at,
                    'total_orders': total_orders,
                    'total_spent': total_spent,
                    'average_order_value': avg_order_value,
                    'order_frequency_days': order_frequency,
                    'predicted_clv': predicted_clv,
                    'customer_segment': segment,
                    'is_active': True,
                    'days_since_last_order': (
                        timezone.now().date() - last_order.order_placed_at.date()
                    ).days,
                    'churn_probability': max(0, min(100, (90 - order_frequency) * 10))  # Simple heuristic
                }
            )

    def update_performance_metrics(self, restaurants):
        """Update restaurant performance metrics"""
        for restaurant in restaurants:
            metrics, created = RestaurantPerformanceMetrics.objects.get_or_create(
                restaurant=restaurant
            )
            
            # Update with latest data
            today = timezone.now().date()
            
            # Today's metrics
            today_orders = Order.objects.filter(
                restaurant=restaurant,
                order_placed_at__date=today
            )
            today_revenue = today_orders.filter(status='delivered').aggregate(
                total=Sum('total_amount')
            )['total'] or Decimal('0.00')
            
            # This week's metrics
            start_of_week = today - timedelta(days=today.weekday())
            week_orders = Order.objects.filter(
                restaurant=restaurant,
                order_placed_at__date__range=[start_of_week, today]
            )
            week_revenue = week_orders.filter(status='delivered').aggregate(
                total=Sum('total_amount')
            )['total'] or Decimal('0.00')
            
            # This month's metrics
            start_of_month = today.replace(day=1)
            month_orders = Order.objects.filter(
                restaurant=restaurant,
                order_placed_at__date__range=[start_of_month, today]
            )
            month_revenue = month_orders.filter(status='delivered').aggregate(
                total=Sum('total_amount')
            )['total'] or Decimal('0.00')
            
            # Lifetime metrics
            lifetime_orders = Order.objects.filter(restaurant=restaurant).count()
            lifetime_revenue = Order.objects.filter(
                restaurant=restaurant, status='delivered'
            ).aggregate(
                total=Sum('total_amount')
            )['total'] or Decimal('0.00')
            
            # Update metrics
            metrics.today_orders = today_orders.count()
            metrics.today_revenue = today_revenue
            metrics.this_week_orders = week_orders.count()
            metrics.this_week_revenue = week_revenue
            metrics.this_month_orders = month_orders.count()
            metrics.this_month_revenue = month_revenue
            metrics.lifetime_orders = lifetime_orders
            metrics.lifetime_revenue = lifetime_revenue
            
            # Calculate completion rate
            total_orders = Order.objects.filter(restaurant=restaurant).count()
            completed_orders = Order.objects.filter(
                restaurant=restaurant, status='delivered'
            ).count()
            
            metrics.order_completion_rate = (
                (completed_orders / total_orders * 100) if total_orders > 0 else 0
            )
            
            metrics.save()