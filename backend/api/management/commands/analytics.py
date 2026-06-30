# management/commands/analytics.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
import random
from datetime import timedelta

class Command(BaseCommand):
    help = 'Populate analytics data: sales reports, performance metrics, etc.'
    
    def add_arguments(self, parser):
        parser.add_argument('--skip-existing', action='store_true')
        parser.add_argument('--clean', action='store_true')
    
    def handle(self, *args, **options):
        from api.models import (
            Restaurant, RestaurantSalesReport, DailySalesSnapshot,
            RestaurantPerformanceMetrics, MenuItemPerformance,
            OperationalEfficiency, FinancialReport, CustomerLifetimeValue,
            Order, Customer
        )
        
        if options['clean']:
            RestaurantSalesReport.objects.all().delete()
            DailySalesSnapshot.objects.all().delete()
            MenuItemPerformance.objects.all().delete()
            OperationalEfficiency.objects.all().delete()
            FinancialReport.objects.all().delete()
            CustomerLifetimeValue.objects.all().delete()
            self.stdout.write("  Cleaned existing analytics data")
        
        restaurants = list(Restaurant.objects.filter(status='active'))
        
        if not restaurants:
            self.stdout.write(self.style.ERROR("  No restaurants found! Run restaurants first."))
            return
        
        sales_reports_created = 0
        daily_snapshots_created = 0
        menu_performance_created = 0
        operational_metrics_created = 0
        financial_reports_created = 0
        clv_records_created = 0
        
        # For each restaurant, create historical data for last 3 months
        for restaurant in restaurants:
            # Generate daily sales snapshots for last 90 days
            for days_ago in range(1, 91):
                date = timezone.now().date() - timedelta(days=days_ago)
                
                # Simulate daily metrics based on day of week (weekends busier)
                is_weekend = date.weekday() >= 5
                base_orders = random.randint(10, 30) if is_weekend else random.randint(5, 20)
                base_revenue = base_orders * random.randint(15000, 35000)
                
                # Random variation
                orders_count = int(base_orders * random.uniform(0.8, 1.2))
                revenue = Decimal(str(int(base_revenue * random.uniform(0.8, 1.2))))
                
                # Hourly breakdown
                hourly_orders = {}
                hourly_revenue = {}
                for hour in range(10, 22):
                    hour_orders = random.randint(0, max(1, orders_count // 3))
                    hourly_orders[str(hour)] = hour_orders
                    hourly_revenue[str(hour)] = float(hour_orders * random.randint(10000, 25000))
                
                DailySalesSnapshot.objects.create(
                    restaurant=restaurant,
                    date=date,
                    orders_count=orders_count,
                    revenue=revenue,
                    completed_orders=int(orders_count * random.uniform(0.85, 0.98)),
                    cancelled_orders=int(orders_count * random.uniform(0.02, 0.15)),
                    hourly_orders=hourly_orders,
                    hourly_revenue=hourly_revenue,
                    daily_top_items={}
                )
                daily_snapshots_created += 1
            
            # Create weekly and monthly sales reports
            periods = [
                ('weekly', 7, 12),
                ('monthly', 30, 3),
            ]
            
            for period_type, days, count in periods:
                for i in range(count):
                    end_date = timezone.now().date() - timedelta(days=i * days)
                    start_date = end_date - timedelta(days=days - 1)
                    
                    snapshots = DailySalesSnapshot.objects.filter(
                        restaurant=restaurant,
                        date__gte=start_date,
                        date__lte=end_date
                    )
                    
                    if snapshots.exists():
                        total_orders = sum(s.orders_count for s in snapshots)
                        total_revenue = sum(s.revenue for s in snapshots)
                        
                        RestaurantSalesReport.objects.create(
                            restaurant=restaurant,
                            period_type=period_type,
                            start_date=start_date,
                            end_date=end_date,
                            total_orders=total_orders,
                            total_revenue=total_revenue,
                            average_order_value=total_revenue / max(1, total_orders) if total_orders > 0 else Decimal('0'),
                            completed_orders=int(total_orders * random.uniform(0.85, 0.95)),
                            cancelled_orders=int(total_orders * random.uniform(0.05, 0.15)),
                            new_customers=random.randint(5, 50),
                            returning_customers=random.randint(10, 100),
                            peak_hours={'12:00': 15, '13:00': 18, '19:00': 25},
                            average_preparation_time=random.randint(15, 35),
                            average_delivery_time=random.randint(25, 55)
                        )
                        sales_reports_created += 1
            
            # Update performance metrics
            try:
                perf_metrics = restaurant.performance_metrics
                perf_metrics.update_comprehensive_metrics()
            except Exception:
                RestaurantPerformanceMetrics.objects.create(restaurant=restaurant)
            
            # Create menu item performance snapshots
            menu_items = []
            if restaurant.menu_categories.exists():
                first_category = restaurant.menu_categories.first()
                menu_items = list(first_category.menu_items.all()[:10])
            
            for menu_item in menu_items:
                for period_type in ['weekly', 'monthly']:
                    if period_type == 'weekly':
                        days = 7
                        num_periods = 8
                    else:
                        days = 30
                        num_periods = 3
                    
                    for i in range(num_periods):
                        end_date = timezone.now().date() - timedelta(days=i * days)
                        start_date = end_date - timedelta(days=days - 1)
                        
                        quantity_sold = random.randint(5, 100)
                        total_revenue_val = quantity_sold * float(menu_item.price)
                        
                        MenuItemPerformance.objects.create(
                            menu_item=menu_item,
                            restaurant=restaurant,
                            period_type=period_type,
                            start_date=start_date,
                            end_date=end_date,
                            quantity_sold=quantity_sold,
                            total_revenue=Decimal(str(total_revenue_val)),
                            average_selling_price=menu_item.price,
                            profit_margin=Decimal(str(random.uniform(15, 40))),
                            popularity_rank=random.randint(1, 20),
                            growth_rate=Decimal(str(random.uniform(-10, 25))),
                            repeat_order_rate=Decimal(str(random.uniform(5, 35))),
                            customer_rating_avg=Decimal(str(random.uniform(3.5, 4.9))),
                            ingredient_cost=Decimal(str(float(menu_item.price) * random.uniform(0.3, 0.5))),
                            preparation_cost=Decimal(str(float(menu_item.price) * random.uniform(0.1, 0.2))),
                            gross_profit=Decimal(str(float(menu_item.price) * random.uniform(0.3, 0.5)))
                        )
                        menu_performance_created += 1
            
            # Create operational efficiency metrics
            for days_ago in range(1, 31):
                date = timezone.now().date() - timedelta(days=days_ago)
                total_orders_val = random.randint(10, 50)
                completed_orders_val = int(total_orders_val * random.uniform(0.85, 0.98))
                
                OperationalEfficiency.objects.create(
                    restaurant=restaurant,
                    date=date,
                    period_type='daily',
                    total_orders=total_orders_val,
                    completed_orders=completed_orders_val,
                    cancelled_orders=total_orders_val - completed_orders_val,
                    fulfillment_rate=Decimal(str(completed_orders_val / max(1, total_orders_val) * 100)),
                    average_preparation_time=random.randint(15, 35),
                    average_delivery_time=random.randint(25, 55),
                    average_waiting_time=random.randint(20, 45),
                    on_time_delivery_rate=Decimal(str(random.uniform(70, 95))),
                    orders_per_staff_hour=Decimal(str(random.uniform(2, 8))),
                    revenue_per_staff_hour=Decimal(str(random.uniform(50000, 200000))),
                    peak_hours={'12:00': 15, '13:00': 18, '19:00': 25},
                    kitchen_utilization=Decimal(str(random.uniform(40, 85))),
                    delivery_utilization=Decimal(str(random.uniform(30, 75))),
                    order_accuracy_rate=Decimal(str(random.uniform(85, 99))),
                    customer_satisfaction_score=Decimal(str(random.uniform(3.5, 4.9)))
                )
                operational_metrics_created += 1
            
            # Create financial reports
            for report_type in ['profit_loss', 'sales_summary']:
                for period_type in ['weekly', 'monthly']:
                    if period_type == 'weekly':
                        days = 7
                        num_periods = 8
                    else:
                        days = 30
                        num_periods = 3
                    
                    for i in range(num_periods):
                        end_date = timezone.now().date() - timedelta(days=i * days)
                        start_date = end_date - timedelta(days=days - 1)
                        
                        total_revenue_val = Decimal(str(random.uniform(5000000, 50000000)))
                        food_revenue_val = total_revenue_val * Decimal('0.7')
                        beverage_revenue_val = total_revenue_val * Decimal('0.2')
                        delivery_fee_revenue_val = total_revenue_val * Decimal('0.1')
                        
                        cost_of_goods_sold_val = total_revenue_val * Decimal('0.35')
                        labor_costs_val = total_revenue_val * Decimal('0.25')
                        operating_expenses_val = total_revenue_val * Decimal('0.15')
                        
                        gross_profit_val = total_revenue_val - cost_of_goods_sold_val
                        operating_profit_val = gross_profit_val - labor_costs_val - operating_expenses_val
                        net_profit_val = operating_profit_val * Decimal('0.85')
                        
                        FinancialReport.objects.create(
                            restaurant=restaurant,
                            report_type=report_type,
                            period_type=period_type,
                            start_date=start_date,
                            end_date=end_date,
                            total_revenue=total_revenue_val,
                            food_revenue=food_revenue_val,
                            beverage_revenue=beverage_revenue_val,
                            delivery_fee_revenue=delivery_fee_revenue_val,
                            cost_of_goods_sold=cost_of_goods_sold_val,
                            labor_costs=labor_costs_val,
                            operating_expenses=operating_expenses_val,
                            gross_profit=gross_profit_val,
                            operating_profit=operating_profit_val,
                            net_profit=net_profit_val,
                            gross_margin=(gross_profit_val / total_revenue_val * 100) if total_revenue_val > 0 else Decimal('0'),
                            operating_margin=(operating_profit_val / total_revenue_val * 100) if total_revenue_val > 0 else Decimal('0'),
                            net_margin=(net_profit_val / total_revenue_val * 100) if total_revenue_val > 0 else Decimal('0')
                        )
                        financial_reports_created += 1
        
        # Create Customer Lifetime Value records
        customers = list(Customer.objects.all()[:200])
        
        for customer in customers:
            orders = Order.objects.filter(customer=customer, status='delivered')
            if orders.exists():
                first_order = orders.order_by('order_placed_at').first()
                last_order = orders.order_by('-order_placed_at').first()
                total_orders = orders.count()
                total_spent = sum(o.total_amount for o in orders)
                avg_order_value = total_spent / total_orders if total_orders > 0 else Decimal('0')
                
                # Calculate average days between orders
                order_dates = list(orders.values_list('order_placed_at', flat=True))
                if len(order_dates) > 1:
                    diffs = [(order_dates[i] - order_dates[i-1]).days for i in range(1, len(order_dates))]
                    avg_frequency = sum(diffs) / len(diffs)
                else:
                    avg_frequency = 0
                
                # Determine segment based on total spent
                if total_spent > 500000:
                    segment = 'high_value'
                elif total_spent > 100000:
                    segment = 'medium_value'
                elif total_spent > 0:
                    segment = 'low_value'
                else:
                    segment = 'new'
                
                days_since_last = (timezone.now() - last_order.order_placed_at).days if last_order else 0
                
                # Calculate monthly orders as Decimal
                days_since_first = max(1, (timezone.now() - first_order.order_placed_at).days)
                months_since_first = Decimal(str(days_since_first / 30.0))
                monthly_orders = Decimal(str(total_orders)) / months_since_first if months_since_first > 0 else Decimal('1')
                
                # Predict CLV - all as Decimal to avoid type errors
                predicted_clv = avg_order_value * monthly_orders * Decimal('12')
                predicted_clv = min(predicted_clv, Decimal('5000000'))  # Cap at 5M
                
                CustomerLifetimeValue.objects.create(
                    customer=customer,
                    restaurant=random.choice(restaurants),
                    first_order_date=first_order.order_placed_at,
                    last_order_date=last_order.order_placed_at,
                    total_orders=total_orders,
                    total_spent=total_spent,
                    average_order_value=avg_order_value,
                    order_frequency_days=int(avg_frequency) if avg_frequency else 0,
                    predicted_clv=predicted_clv,
                    customer_segment=segment,
                    is_active=days_since_last < 30,
                    days_since_last_order=days_since_last,
                    churn_probability=Decimal(str(min(0.95, days_since_last / 90))) if days_since_last > 0 else Decimal('0.05')
                )
                clv_records_created += 1
        
        self.stdout.write(f"  ✅ Created {daily_snapshots_created} daily sales snapshots")
        self.stdout.write(f"  ✅ Created {sales_reports_created} sales reports")
        self.stdout.write(f"  ✅ Created {menu_performance_created} menu item performance records")
        self.stdout.write(f"  ✅ Created {operational_metrics_created} operational efficiency records")
        self.stdout.write(f"  ✅ Created {financial_reports_created} financial reports")
        self.stdout.write(f"  ✅ Created {clv_records_created} customer lifetime value records")