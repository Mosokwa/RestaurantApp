from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from ..models import ComparativeAnalytics, CustomerLifetimeValue, DailySalesSnapshot, FinancialReport, MenuItemPerformance, OperationalEfficiency, RestaurantPerformanceMetrics, RestaurantSalesReport

class RestaurantSalesReportSerializer(serializers.ModelSerializer):
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    period_display = serializers.CharField(source='get_period_type_display', read_only=True)
    date_range = serializers.SerializerMethodField()
    order_completion_rate = serializers.SerializerMethodField()
    cancellation_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = RestaurantSalesReport
        fields = [
            'report_id', 'restaurant', 'restaurant_name', 'period_type', 'period_display',
            'start_date', 'end_date', 'date_range', 'total_orders', 'total_revenue',
            'average_order_value', 'completed_orders', 'cancelled_orders',
            'new_customers', 'returning_customers', 'top_items', 'popular_categories',
            'peak_hours', 'average_preparation_time', 'average_delivery_time',
            'order_completion_rate', 'cancellation_rate', 'created_at', 'updated_at'
        ]
        read_only_fields = ['report_id', 'created_at', 'updated_at']
    
    def get_date_range(self, obj):
        return f"{obj.start_date.strftime('%b %d')} - {obj.end_date.strftime('%b %d, %Y')}"
    
    def get_order_completion_rate(self, obj):
        if obj.total_orders > 0:
            return round((obj.completed_orders / obj.total_orders) * 100, 2)
        return 0.00
    
    def get_cancellation_rate(self, obj):
        if obj.total_orders > 0:
            return round((obj.cancelled_orders / obj.total_orders) * 100, 2)
        return 0.00

class RestaurantPerformanceMetricsSerializer(serializers.ModelSerializer):
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    today_avg_order_value = serializers.SerializerMethodField()
    week_avg_order_value = serializers.SerializerMethodField()
    month_avg_order_value = serializers.SerializerMethodField()
    
    class Meta:
        model = RestaurantPerformanceMetrics
        fields = [
            'metrics_id', 'restaurant', 'restaurant_name', 'lifetime_orders', 'lifetime_revenue',
            'average_rating', 'today_orders', 'today_revenue', 'today_avg_order_value',
            'this_week_orders', 'this_week_revenue', 'week_avg_order_value',
            'this_month_orders', 'this_month_revenue', 'month_avg_order_value',
            'order_completion_rate', 'average_preparation_time', 'customer_retention_rate',
            'last_updated', 'created_at'
        ]
        read_only_fields = ['metrics_id', 'last_updated', 'created_at']
    
    def get_today_avg_order_value(self, obj):
        if obj.today_orders > 0:
            return obj.today_revenue / obj.today_orders
        return 0.00
    
    def get_week_avg_order_value(self, obj):
        if obj.this_week_orders > 0:
            return obj.this_week_revenue / obj.this_week_orders
        return 0.00
    
    def get_month_avg_order_value(self, obj):
        if obj.this_month_orders > 0:
            return obj.this_month_revenue / obj.this_month_orders
        return 0.00

class SalesAnalyticsRequestSerializer(serializers.Serializer):
    period = serializers.ChoiceField(choices=[
        'today', 'yesterday', 'this_week', 'last_week', 
        'this_month', 'last_month', 'custom'
    ])
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    restaurant_id = serializers.IntegerField(required=False)
    
    def validate(self, data):
        if data.get('period') == 'custom' and (not data.get('start_date') or not data.get('end_date')):
            raise ValidationError("Start date and end date are required for custom period")
        return data
    
class DailySalesSnapshotSerializer(serializers.ModelSerializer):
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    date_formatted = serializers.SerializerMethodField()
    growth_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = DailySalesSnapshot
        fields = [
            'snapshot_id', 'restaurant', 'restaurant_name', 'date', 'date_formatted',
            'orders_count', 'revenue', 'completed_orders', 'cancelled_orders',
            'hourly_orders', 'hourly_revenue', 'daily_top_items', 'growth_rate',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['snapshot_id', 'created_at', 'updated_at']
    
    def get_date_formatted(self, obj):
        return obj.date.strftime('%Y-%m-%d')
    
    def get_growth_rate(self, obj):
        # Calculate growth rate compared to previous day
        previous_day = DailySalesSnapshot.objects.filter(
            restaurant=obj.restaurant,
            date__lt=obj.date
        ).order_by('-date').first()
        
        if previous_day and previous_day.revenue > 0:
            growth = ((obj.revenue - previous_day.revenue) / previous_day.revenue) * 100
            return round(float(growth), 2)
        return 0.00
    
class TopItemsSerializer(serializers.Serializer):
    item_id = serializers.IntegerField()
    item_name = serializers.CharField()
    quantity_sold = serializers.IntegerField()
    revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    category = serializers.CharField()

class SalesTrendSerializer(serializers.Serializer):
    date = serializers.DateField()
    orders = serializers.IntegerField()
    revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    avg_order_value = serializers.DecimalField(max_digits=10, decimal_places=2)

class CustomerLifetimeValueSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.user.get_full_name', read_only=True)
    customer_email = serializers.CharField(source='customer.user.email', read_only=True)
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    
    class Meta:
        model = CustomerLifetimeValue
        fields = [
            'clv_id', 'customer', 'customer_name', 'customer_email', 'restaurant', 'restaurant_name',
            'first_order_date', 'last_order_date', 'total_orders', 'total_spent', 'average_order_value',
            'order_frequency_days', 'predicted_clv', 'customer_segment', 'is_active',
            'days_since_last_order', 'churn_probability', 'calculated_at', 'created_at'
        ]
        read_only_fields = ['clv_id', 'calculated_at', 'created_at']

class MenuItemPerformanceSerializer(serializers.ModelSerializer):
    menu_item_name = serializers.CharField(source='menu_item.name', read_only=True)
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    category_name = serializers.CharField(source='menu_item.category.name', read_only=True)
    profitability = serializers.SerializerMethodField()
    
    class Meta:
        model = MenuItemPerformance
        fields = [
            'performance_id', 'menu_item', 'menu_item_name', 'restaurant', 'restaurant_name',
            'category_name', 'period_type', 'start_date', 'end_date', 'quantity_sold',
            'total_revenue', 'average_selling_price', 'profit_margin', 'popularity_rank',
            'growth_rate', 'repeat_order_rate', 'customer_rating_avg', 'ingredient_cost',
            'preparation_cost', 'total_cost', 'gross_profit', 'profitability', 'metadata',
            'calculated_at'
        ]
        read_only_fields = ['performance_id', 'calculated_at']
    
    def get_profitability(self, obj):
        if obj.total_revenue > 0:
            return (obj.gross_profit / obj.total_revenue) * 100
        return 0.00

class OperationalEfficiencySerializer(serializers.ModelSerializer):
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    branch_name = serializers.SerializerMethodField()
    efficiency_score = serializers.SerializerMethodField()
    
    class Meta:
        model = OperationalEfficiency
        fields = [
            'efficiency_id', 'restaurant', 'restaurant_name', 'branch', 'branch_name',
            'date', 'period_type', 'total_orders', 'completed_orders', 'cancelled_orders',
            'fulfillment_rate', 'average_preparation_time', 'average_delivery_time',
            'average_waiting_time', 'on_time_delivery_rate', 'orders_per_staff_hour',
            'revenue_per_staff_hour', 'peak_hours', 'busy_periods', 'kitchen_utilization',
            'delivery_utilization', 'order_accuracy_rate', 'customer_satisfaction_score',
            'efficiency_score', 'calculated_at'
        ]
        read_only_fields = ['efficiency_id', 'calculated_at']
    
    def get_branch_name(self, obj):
        return obj.branch.address.city if obj.branch else 'All Branches'
    
    def get_efficiency_score(self, obj):
        # Calculate overall efficiency score (0-100)
        score = 0
        if obj.fulfillment_rate > 0:
            score += obj.fulfillment_rate * 0.3  # 30% weight
        if obj.on_time_delivery_rate > 0:
            score += obj.on_time_delivery_rate * 0.3  # 30% weight
        if obj.customer_satisfaction_score > 0:
            score += float(obj.customer_satisfaction_score) * 20 * 0.2  # 20% weight (convert 5-star to 100)
        if obj.order_accuracy_rate > 0:
            score += obj.order_accuracy_rate * 0.2  # 20% weight
        return round(score, 2)

class FinancialReportSerializer(serializers.ModelSerializer):
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    period_display = serializers.SerializerMethodField()
    financial_health = serializers.SerializerMethodField()
    
    class Meta:
        model = FinancialReport
        fields = [
            'report_id', 'restaurant', 'restaurant_name', 'report_type', 'period_type',
            'period_display', 'start_date', 'end_date', 'total_revenue', 'food_revenue',
            'beverage_revenue', 'delivery_fee_revenue', 'other_revenue', 'cost_of_goods_sold',
            'labor_costs', 'operating_expenses', 'delivery_costs', 'marketing_costs',
            'gross_profit', 'operating_profit', 'net_profit', 'gross_margin', 'operating_margin',
            'net_margin', 'return_on_investment', 'break_even_point', 'previous_period_revenue',
            'revenue_growth', 'industry_benchmark', 'financial_health', 'report_data',
            'generated_at', 'created_at'
        ]
        read_only_fields = ['report_id', 'generated_at', 'created_at']
    
    def get_period_display(self, obj):
        return f"{obj.start_date.strftime('%b %d, %Y')} to {obj.end_date.strftime('%b %d, %Y')}"
    
    def get_financial_health(self, obj):
        if obj.net_margin > 15:
            return 'excellent'
        elif obj.net_margin > 10:
            return 'good'
        elif obj.net_margin > 5:
            return 'fair'
        else:
            return 'poor'

class ComparativeAnalyticsSerializer(serializers.ModelSerializer):
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    performance_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = ComparativeAnalytics
        fields = [
            'comparison_id', 'restaurant', 'restaurant_name', 'comparison_type', 'period_type',
            'start_date', 'end_date', 'revenue_comparison', 'order_volume_comparison',
            'average_order_value_comparison', 'customer_satisfaction_comparison',
            'market_share', 'competitive_position', 'growth_rate_comparison',
            'customer_acquisition_comparison', 'strengths', 'weaknesses', 'opportunities',
            'threats', 'performance_summary', 'calculated_at', 'created_at'
        ]
        read_only_fields = ['comparison_id', 'calculated_at', 'created_at']
    
    def get_performance_summary(self, obj):
        revenue_percentile = obj.revenue_comparison.get('percentile', 50)
        if revenue_percentile >= 80:
            return 'outperforming'
        elif revenue_percentile >= 60:
            return 'above_average'
        elif revenue_percentile >= 40:
            return 'average'
        else:
            return 'below_average'

# Analytics Request Serializers
class AnalyticsPeriodSerializer(serializers.Serializer):
    period = serializers.ChoiceField(choices=[
        'today', 'yesterday', 'this_week', 'last_week', 
        'this_month', 'last_month', 'last_3_months', 'last_6_months', 'this_year', 'custom'
    ])
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    branch_id = serializers.IntegerField(required=False)
    
    def validate(self, data):
        if data.get('period') == 'custom' and (not data.get('start_date') or not data.get('end_date')):
            raise ValidationError("Start date and end date are required for custom period")
        return data

class ExportRequestSerializer(serializers.Serializer):
    report_type = serializers.ChoiceField(choices=[
        'customer_insights', 'menu_performance', 'operational_metrics', 
        'financial_report', 'comparative_analytics'
    ])
    format = serializers.ChoiceField(choices=['csv', 'pdf', 'excel'])
    period = serializers.ChoiceField(choices=[
        'this_week', 'this_month', 'last_month', 'last_3_months'
    ])
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)

class DashboardMetricsSerializer(serializers.Serializer):
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_orders = serializers.IntegerField()
    average_order_value = serializers.DecimalField(max_digits=10, decimal_places=2)
    customer_count = serializers.IntegerField()
    completion_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    growth_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    
class CustomerInsightsSerializer(serializers.Serializer):
    new_customers = serializers.IntegerField()
    returning_customers = serializers.IntegerField()
    retention_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    average_clv = serializers.DecimalField(max_digits=10, decimal_places=2)
    churn_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    customer_segments = serializers.JSONField()