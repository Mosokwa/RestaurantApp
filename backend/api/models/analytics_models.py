from datetime import timedelta
from django.db import models
from django.utils import timezone


class RestaurantSalesReport(models.Model):
    REPORT_PERIOD_CHOICES = (
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    )
    
    report_id = models.AutoField(primary_key=True)
    restaurant = models.ForeignKey(
        'api.Restaurant',
        on_delete=models.CASCADE,
        related_name='sales_reports'
    )
    period_type = models.CharField(max_length=10, choices=REPORT_PERIOD_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Sales metrics
    total_orders = models.IntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    average_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    completed_orders = models.IntegerField(default=0)
    cancelled_orders = models.IntegerField(default=0)
    
    # Customer metrics
    new_customers = models.IntegerField(default=0)
    returning_customers = models.IntegerField(default=0)
    
    # Popular items (stored as JSON)
    top_items = models.JSONField(default=dict)
    popular_categories = models.JSONField(default=dict)
    
    # Time-based metrics
    peak_hours = models.JSONField(default=dict)
    average_preparation_time = models.IntegerField(default=0)  # in minutes
    average_delivery_time = models.IntegerField(default=0)    # in minutes
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'restaurant_sales_reports'
        unique_together = ['restaurant', 'period_type', 'start_date']
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['restaurant', 'period_type']),
            models.Index(fields=['start_date', 'end_date']),
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.get_period_type_display()} Report ({self.start_date} to {self.end_date})"

class DailySalesSnapshot(models.Model):
    snapshot_id = models.AutoField(primary_key=True)
    restaurant = models.ForeignKey(
        'api.Restaurant',
        on_delete=models.CASCADE,
        related_name='daily_snapshots'
    )
    date = models.DateField()
    
    # Daily metrics
    orders_count = models.IntegerField(default=0)
    revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    completed_orders = models.IntegerField(default=0)
    cancelled_orders = models.IntegerField(default=0)
    
    # Hourly breakdown (stored as JSON)
    hourly_orders = models.JSONField(default=dict)
    hourly_revenue = models.JSONField(default=dict)
    
    # Popular items for the day
    daily_top_items = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'daily_sales_snapshots'
        unique_together = ['restaurant', 'date']
        ordering = ['-date']
        indexes = [
            models.Index(fields=['restaurant', 'date']),
        ]

    def __str__(self):
        return f"{self.restaurant.name} - Daily Snapshot ({self.date})"

class RestaurantPerformanceMetrics(models.Model):
    metrics_id = models.AutoField(primary_key=True)
    restaurant = models.OneToOneField(
        'api.Restaurant',
        on_delete=models.CASCADE,
        related_name='performance_metrics'
    )
    
    # Overall metrics
    lifetime_orders = models.IntegerField(default=0)
    lifetime_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    
    # Current period metrics (for quick access)
    today_orders = models.IntegerField(default=0)
    today_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    this_week_orders = models.IntegerField(default=0)
    this_week_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    this_month_orders = models.IntegerField(default=0)
    this_month_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # Performance indicators
    order_completion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)  # percentage
    average_preparation_time = models.IntegerField(default=0)  # in minutes
    customer_retention_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)  # percentage
    
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'restaurant_performance_metrics'
        ordering = ['-last_updated']

    def __str__(self):
        return f"{self.restaurant.name} - Performance Metrics"
    
# Update RestaurantPerformanceMetrics with additional fields

def update_comprehensive_metrics(self):
    """
    Comprehensive method to update all performance metrics for a restaurant
    This is the NEW detailed function
    """
    from django.db.models import Count, Sum, Avg, Q
    from decimal import Decimal
    from django.utils import timezone
    from datetime import timedelta
    from ..models import Order,RestaurantReview

    try:
        restaurant = self.restaurant
        today = timezone.now().date()
        
        # Calculate date ranges
        thirty_days_ago = today - timedelta(days=30)
        seven_days_ago = today - timedelta(days=7)
        month_start = today.replace(day=1)
        
        # TODAY'S METRICS
        today_orders = Order.objects.filter(
            restaurant=restaurant,
            order_placed_at__date=today
        )
        today_metrics = today_orders.aggregate(
            orders_count=Count('order_id'),
            revenue=Sum('total_amount', filter=Q(status='delivered'))
        )
        
        self.today_orders = today_metrics['orders_count'] or 0
        self.today_revenue = today_metrics['revenue'] or Decimal('0.00')
        
        # THIS WEEK'S METRICS
        week_orders = Order.objects.filter(
            restaurant=restaurant,
            order_placed_at__date__gte=seven_days_ago
        )
        week_metrics = week_orders.aggregate(
            orders_count=Count('order_id'),
            revenue=Sum('total_amount', filter=Q(status='delivered'))
        )
        
        self.this_week_orders = week_metrics['orders_count'] or 0
        self.this_week_revenue = week_metrics['revenue'] or Decimal('0.00')
        
        # THIS MONTH'S METRICS
        month_orders = Order.objects.filter(
            restaurant=restaurant,
            order_placed_at__date__gte=month_start
        )
        month_metrics = month_orders.aggregate(
            orders_count=Count('order_id'),
            revenue=Sum('total_amount', filter=Q(status='delivered'))
        )
        
        self.this_month_orders = month_metrics['orders_count'] or 0
        self.this_month_revenue = month_metrics['revenue'] or Decimal('0.00')
        
        # LIFETIME METRICS
        lifetime_metrics = Order.objects.filter(
            restaurant=restaurant,
            status='delivered'
        ).aggregate(
            total_orders=Count('order_id'),
            total_revenue=Sum('total_amount')
        )
        
        self.lifetime_orders = lifetime_metrics['total_orders'] or 0
        self.lifetime_revenue = lifetime_metrics['total_revenue'] or Decimal('0.00')
        
        # ORDER COMPLETION RATE (last 30 days)
        recent_orders = Order.objects.filter(
            restaurant=restaurant,
            order_placed_at__date__gte=thirty_days_ago
        )
        completed_recent = recent_orders.filter(status='delivered')
        
        if recent_orders.count() > 0:
            completion_rate = (completed_recent.count() / recent_orders.count()) * 100
            self.order_completion_rate = Decimal(str(round(completion_rate, 2)))
        else:
            self.order_completion_rate = Decimal('0.00')
        
        # AVERAGE PREPARATION TIME (simplified)
        self.average_preparation_time = 25  # Default, would need actual timing data
        
        # CUSTOMER RETENTION RATE
        try:
            sixty_days_ago = today - timedelta(days=60)
            recent_customers = Order.objects.filter(
                restaurant=restaurant,
                order_placed_at__date__gte=sixty_days_ago
            ).values('customer').distinct().count()
            
            returning_customers = Order.objects.filter(
                restaurant=restaurant,
                order_placed_at__date__gte=sixty_days_ago
            ).values('customer').annotate(
                order_count=Count('order_id')
            ).filter(order_count__gt=1).count()
            
            if recent_customers > 0:
                retention_rate = (returning_customers / recent_customers) * 100
                self.customer_retention_rate = Decimal(str(round(retention_rate, 2)))
            else:
                self.customer_retention_rate = Decimal('0.00')
        except Exception:
            self.customer_retention_rate = Decimal('0.00')
        
        # AVERAGE RATING
        try:
            rating_metrics = RestaurantReview.objects.filter(
                restaurant=restaurant,
                status='approved'
            ).aggregate(avg_rating=Avg('overall_rating'))
            
            self.average_rating = rating_metrics['avg_rating'] or Decimal('0.00')
        except Exception:
            self.average_rating = Decimal('0.00')
        
        self.save()
        return True
        
    except Exception as e:
        print(f"Error in update_comprehensive_metrics: {str(e)}")
        return False

# Add the method to RestaurantPerformanceMetrics
RestaurantPerformanceMetrics.update_comprehensive_metrics = update_comprehensive_metrics

# Add this signal to automatically create performance metrics when a restaurant is created
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender='api.Restaurant')
def create_restaurant_performance_metrics(sender, instance, created, **kwargs):
    if created:
        RestaurantPerformanceMetrics.objects.create(restaurant=instance)


class CustomerLifetimeValue(models.Model):
    """
    Track customer lifetime value and retention metrics
    """
    clv_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(
        'api.Customer',
        on_delete=models.CASCADE,
        related_name='lifetime_value'
    )
    restaurant = models.ForeignKey(
        'api.Restaurant',
        on_delete=models.CASCADE,
        related_name='customer_metrics'
    )
    
    # Customer metrics
    first_order_date = models.DateTimeField()
    last_order_date = models.DateTimeField()
    total_orders = models.IntegerField(default=0)
    total_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    average_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    order_frequency_days = models.IntegerField(default=0)  # Average days between orders
    
    # CLV calculations
    predicted_clv = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    customer_segment = models.CharField(max_length=20, choices=(
        ('high_value', 'High Value'),
        ('medium_value', 'Medium Value'),
        ('low_value', 'Low Value'),
        ('new', 'New Customer'),
    ), default='new')
    
    # Retention metrics
    is_active = models.BooleanField(default=True)
    days_since_last_order = models.IntegerField(default=0)
    churn_probability = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    calculated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'customer_lifetime_value'
        unique_together = ['customer', 'restaurant']
        indexes = [
            models.Index(fields=['restaurant', 'customer_segment']),
            models.Index(fields=['restaurant', 'is_active']),
        ]
    
    def __str__(self):
        return f"CLV - {self.customer.user.username} at {self.restaurant.name}"

class MenuItemPerformance(models.Model):
    """
    Snapshot of menu item performance for analytics
    """
    performance_id = models.AutoField(primary_key=True)
    menu_item = models.ForeignKey(
        'api.MenuItem',
        on_delete=models.CASCADE,
        related_name='performance_snapshots'
    )
    restaurant = models.ForeignKey(
        'api.Restaurant',
        on_delete=models.CASCADE,
        related_name='menu_performance'
    )
    
    # Time period
    period_type = models.CharField(max_length=10, choices=(
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ))
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Sales metrics
    quantity_sold = models.IntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    average_selling_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Performance indicators
    profit_margin = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)  # Percentage
    popularity_rank = models.IntegerField(default=0)
    growth_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)  # Percentage
    
    # Customer behavior
    repeat_order_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    customer_rating_avg = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    
    # Cost analysis (if cost data is available)
    ingredient_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    preparation_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    gross_profit = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    metadata = models.JSONField(default=dict, blank=True)
    calculated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'menu_item_performance'
        unique_together = ['menu_item', 'period_type', 'start_date']
        indexes = [
            models.Index(fields=['restaurant', 'start_date']),
            models.Index(fields=['menu_item', 'period_type']),
        ]
    
    def __str__(self):
        return f"Performance - {self.menu_item.name} ({self.start_date} to {self.end_date})"

class OperationalEfficiency(models.Model):
    """
    Track operational metrics for restaurant efficiency
    """
    efficiency_id = models.AutoField(primary_key=True)
    restaurant = models.ForeignKey(
        'api.Restaurant',
        on_delete=models.CASCADE,
        related_name='operational_metrics'
    )
    branch = models.ForeignKey(
        'api.Branch',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='efficiency_metrics'
    )
    
    # Time period
    date = models.DateField()
    period_type = models.CharField(max_length=10, choices=(
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ), default='daily')
    
    # Order fulfillment metrics
    total_orders = models.IntegerField(default=0)
    completed_orders = models.IntegerField(default=0)
    cancelled_orders = models.IntegerField(default=0)
    fulfillment_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # Time metrics (in minutes)
    average_preparation_time = models.IntegerField(default=0)
    average_delivery_time = models.IntegerField(default=0)
    average_waiting_time = models.IntegerField(default=0)
    on_time_delivery_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # Staff efficiency
    orders_per_staff_hour = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    revenue_per_staff_hour = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    
    # Peak hours analysis
    peak_hours = models.JSONField(default=dict)  # {'14:00': 15, '19:00': 25}
    busy_periods = models.JSONField(default=dict)  # Peak order times
    
    # Resource utilization
    kitchen_utilization = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    delivery_utilization = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # Quality metrics
    order_accuracy_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    customer_satisfaction_score = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    
    calculated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'operational_efficiency'
        unique_together = ['restaurant', 'branch', 'date', 'period_type']
        indexes = [
            models.Index(fields=['restaurant', 'date']),
            models.Index(fields=['branch', 'date']),
        ]
    
    def __str__(self):
        branch_name = self.branch.address.city if self.branch else 'All Branches'
        return f"Efficiency - {self.restaurant.name} ({branch_name}) - {self.date}"

class FinancialReport(models.Model):
    """
    Comprehensive financial reporting
    """
    REPORT_TYPES = (
        ('profit_loss', 'Profit & Loss'),
        ('cash_flow', 'Cash Flow'),
        ('balance_sheet', 'Balance Sheet'),
        ('sales_summary', 'Sales Summary'),
    )
    
    report_id = models.AutoField(primary_key=True)
    restaurant = models.ForeignKey(
        'api.Restaurant',
        on_delete=models.CASCADE,
        related_name='financial_reports'
    )
    
    # Report details
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    period_type = models.CharField(max_length=10, choices=(
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ))
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Revenue breakdown
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    food_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    beverage_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    delivery_fee_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    other_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # Cost breakdown
    cost_of_goods_sold = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    labor_costs = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    operating_expenses = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    delivery_costs = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    marketing_costs = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # Profit metrics
    gross_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    operating_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    net_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # Margins
    gross_margin = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    operating_margin = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    net_margin = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # Financial ratios
    return_on_investment = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    break_even_point = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # Comparative data
    previous_period_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    revenue_growth = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    industry_benchmark = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    report_data = models.JSONField(default=dict)  # Detailed breakdown
    generated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'financial_reports'
        unique_together = ['restaurant', 'report_type', 'period_type', 'start_date']
        indexes = [
            models.Index(fields=['restaurant', 'report_type']),
            models.Index(fields=['start_date', 'end_date']),
        ]
    
    def __str__(self):
        return f"{self.get_report_type_display()} - {self.restaurant.name} ({self.start_date} to {self.end_date})"

class ComparativeAnalytics(models.Model):
    """
    Comparative analytics against similar restaurants or industry benchmarks
    """
    comparison_id = models.AutoField(primary_key=True)
    restaurant = models.ForeignKey(
        'api.Restaurant',
        on_delete=models.CASCADE,
        related_name='comparative_analytics'
    )
    
    # Comparison parameters
    comparison_type = models.CharField(max_length=20, choices=(
        ('industry', 'Industry Benchmark'),
        ('similar_size', 'Similar Size Restaurants'),
        ('same_cuisine', 'Same Cuisine Type'),
        ('geographic', 'Geographic Area'),
    ))
    period_type = models.CharField(max_length=10, choices=(
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
    ))
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Key metrics comparison
    revenue_comparison = models.JSONField(default=dict)  # {'your_value': 10000, 'benchmark': 12000, 'percentile': 75}
    order_volume_comparison = models.JSONField(default=dict)
    average_order_value_comparison = models.JSONField(default=dict)
    customer_satisfaction_comparison = models.JSONField(default=dict)
    
    # Performance rankings
    market_share = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    competitive_position = models.CharField(max_length=20, choices=(
        ('leader', 'Market Leader'),
        ('strong', 'Strong Competitor'),
        ('average', 'Average Performer'),
        ('weak', 'Weak Performer'),
    ), default='average')
    
    # Growth comparison
    growth_rate_comparison = models.JSONField(default=dict)
    customer_acquisition_comparison = models.JSONField(default=dict)
    
    # Strengths and weaknesses
    strengths = models.JSONField(default=list)
    weaknesses = models.JSONField(default=list)
    opportunities = models.JSONField(default=list)
    threats = models.JSONField(default=list)
    
    calculated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'comparative_analytics'
        indexes = [
            models.Index(fields=['restaurant', 'comparison_type']),
            models.Index(fields=['start_date', 'end_date']),
        ]
    
    def __str__(self):
        return f"Comparative Analytics - {self.restaurant.name} vs {self.get_comparison_type_display()}"


def update_restaurant_performance_metrics(self):
    """Enhanced method to update all performance metrics"""
    from django.db.models import Count, Avg, Sum, F, Q
    from decimal import Decimal
    
    # Calculate comprehensive metrics
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    # Customer metrics
    customer_metrics = CustomerLifetimeValue.objects.filter(
        restaurant=self.restaurant
    ).aggregate(
        total_customers=Count('customer_id'),
        active_customers=Count('customer_id', filter=Q(is_active=True)),
        avg_clv=Avg('predicted_clv'),
        avg_order_frequency=Avg('order_frequency_days')
    )
    
    # Order metrics
    from ..models import Order
    order_metrics = Order.objects.filter(
        restaurant=self.restaurant,
        order_placed_at__gte=thirty_days_ago
    ).aggregate(
        total_orders=Count('order_id'),
        completed_orders=Count('order_id', filter=Q(status='delivered')),
        total_revenue=Sum('total_amount', filter=Q(status='delivered')),
        avg_order_value=Avg('total_amount', filter=Q(status='delivered'))
    )
    
    # Update the metrics
    self.total_customers = customer_metrics['total_customers'] or 0
    self.active_customers = customer_metrics['active_customers'] or 0
    self.customer_retention_rate = Decimal('0.00')  # Will be calculated separately
    
    if order_metrics['total_orders'] > 0:
        self.order_completion_rate = (
            Decimal(order_metrics['completed_orders'] or 0) / 
            Decimal(order_metrics['total_orders']) * 100
        )
        self.avg_order_value = order_metrics['avg_order_value'] or Decimal('0.00')
    else:
        self.order_completion_rate = Decimal('0.00')
        self.avg_order_value = Decimal('0.00')
    
    self.save()