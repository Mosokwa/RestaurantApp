from django.contrib import admin
from django.urls import reverse
from django.utils import timezone
from django.db import models
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.utils.html import format_html
from django.contrib.auth.admin import UserAdmin
from .services.reservation_services import NotificationService
from .models import ComparativeAnalytics, CustomerLifetimeValue, DailySalesSnapshot, DishRating, DishReview, FinancialReport, MenuItemPerformance, OperationalEfficiency, RatingAggregate, Recommendation, RestaurantPerformanceMetrics, RestaurantRating, RestaurantReview, RestaurantReviewSettings, RestaurantSalesReport, ReviewReport, ReviewResponse, SimilarityMatrix, User, Cuisine, Address, Restaurant, Branch, Customer, RestaurantStaff, MenuCategory, MenuItem, ItemModifierGroup, ItemModifier, MenuItemModifier, SpecialOffer, Order, OrderItem, OrderItemModifier, Payment, OrderTracking, Cart, CartItem, CartItemModifier, UserBehavior, UserPreference, MultiRestaurantLoyaltyProgram, CustomerLoyalty, Reward, PointsTransaction, RewardRedemption, DiscountVoucher, GroupOrder, GroupOrderParticipant, ScheduledOrder, OrderTemplate, BulkOrder, BulkOrderItem, RestaurantLoyaltySettings, WebSocketConnection, Notification, NotificationPreference, LiveOrderTracking, RealTimeInventory, InventoryAlert,PushNotificationDevice, PushNotificationLog, PopularitySnapshot, ItemAssociation, Table, TimeSlot, Reservation

# Register your models here.
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name',  'last_name', 'user_type', 'is_staff', 'is_active', 'created_at')
    list_filter = ('user_type', 'is_staff', 'is_active', 'created_at')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-created_at',)
    fieldsets = UserAdmin.fieldsets + (
        ('custom Information', 
         {'fields':('user_type', 'phone_number', 'created_at')}),
                                       )
    readonly_fields = ('created_at',)

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('custom Information', {
            'fields': ('user_type', 'phone_number', 'email', 'first_name', 'last_name')
        }),
    )

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['customer_id', 'user', 'loyalty_points', 'newsletter_subscribed', 'created_at']
    list_select_related = ['user']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name']
    list_filter = ['newsletter_subscribed', 'marketing_emails', 'created_at']
    readonly_fields = ['customer_id', 'created_at', 'updated_at']

@admin.register(RestaurantStaff)
class RestaurantStaffAdmin(admin.ModelAdmin):
    list_display = ['staff_id', 'user', 'restaurant', 'role', 'is_active', 'hire_date']
    list_select_related = ['user', 'restaurant']
    search_fields = ['user__username', 'user__email', 'restaurant__name']
    list_filter = ['role', 'is_active', 'restaurant', 'hire_date']
    readonly_fields = ['staff_id', 'hire_date', 'created_at', 'updated_at']

@admin.register(Cuisine)
class CuisineAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['is_active']

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['street_address', 'city', 'state', 'country', 'postal_code']
    list_filter = ['city', 'state', 'country']
    search_fields = ['street_address', 'city', 'postal_code']

@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'status', 'overall_rating', 'is_featured', 'created_at']
    list_filter = ['status', 'is_featured', 'is_verified', 'created_at']
    search_fields = ['name', 'owner__username', 'email']
    filter_horizontal = ['cuisines']
    readonly_fields = ['overall_rating', 'total_reviews']

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ['restaurant', 'get_city', 'is_active', 'is_main_branch']
    list_filter = ['is_active', 'is_main_branch', 'restaurant']
    search_fields = ['restaurant__name', 'address__city']
    
    def get_city(self, obj):
        return obj.address.city
    get_city.short_description = 'City'

@admin.register(MenuCategory)
class MenuCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'restaurant', 'display_order', 'is_active', 'item_count']
    list_filter = ['is_active', 'restaurant', 'created_at']
    search_fields = ['name', 'restaurant__name']
    list_editable = ['display_order', 'is_active']
    
    def item_count(self, obj):
        return obj.menu_items.count()
    item_count.short_description = 'Items'

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'item_type', 'is_available', 'display_order']
    list_filter = ['item_type', 'is_available', 'is_vegetarian', 'is_vegan', 'category__restaurant']
    search_fields = ['name', 'description', 'category__name']
    list_editable = ['price', 'is_available', 'display_order']
    filter_horizontal = []  # For many-to-many if needed

@admin.register(ItemModifierGroup)
class ItemModifierGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_required', 'min_selections', 'max_selections']
    list_filter = ['is_required']

@admin.register(ItemModifier)
class ItemModifierAdmin(admin.ModelAdmin):
    list_display = ['name', 'modifier_group', 'price_modifier', 'is_available']
    list_filter = ['modifier_group', 'is_available']
    list_editable = ['price_modifier', 'is_available']

@admin.register(MenuItemModifier)
class MenuItemModifierAdmin(admin.ModelAdmin):
    list_display = ['menu_item', 'modifier_group']
    list_filter = ['modifier_group']

@admin.register(SpecialOffer)
class SpecialOfferAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'restaurant', 'offer_type', 'discount_value', 
        'is_active', 'is_featured', 'is_valid', 'valid_days_display',
        'display_priority', 'current_usage'
    ]
    list_filter = [
        'is_active', 'is_featured', 'offer_type', 'restaurant',
        'valid_from', 'valid_until'
    ]
    search_fields = ['title', 'restaurant__name']
    filter_horizontal = ['applicable_items']
    readonly_fields = ['current_usage', 'created_at', 'updated_at', 'valid_days_display']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('restaurant', 'title', 'description', 'offer_type', 'discount_value')
        }),
        ('Visibility & Timing', {
            'fields': ('image', 'display_priority', 'is_active', 'is_featured', 
                      'valid_from', 'valid_until', 'valid_days', 'valid_days_display')
        }),
        ('Usage Limits', {
            'fields': ('min_order_amount', 'max_usage', 'max_usage_per_user', 'current_usage')
        }),
        ('Applicable Items', {
            'fields': ('applicable_items',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        })
    )
    
    def valid_days_display(self, obj):
        return obj.get_valid_days_display()
    valid_days_display.short_description = 'Valid Days'

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_uuid', 'customer', 'restaurant', 'status', 'order_type', 'total_amount', 'order_placed_at']
    list_filter = ['status', 'order_type', 'order_placed_at', 'restaurant']
    search_fields = ['order_uuid', 'customer__user__username', 'restaurant__name']
    readonly_fields = ['order_uuid', 'order_placed_at', 'total_amount']
    list_editable = ['status']

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'menu_item', 'quantity', 'unit_price', 'total_price']
    list_filter = ['order__restaurant']
    search_fields = ['order__order_uuid', 'menu_item__name']

@admin.register(OrderItemModifier)
class OrderItemModifierAdmin(admin.ModelAdmin):
    list_display = ['order_item', 'item_modifier', 'quantity', 'unit_price', 'total_price']
    list_filter = ['order_item__order__restaurant']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['order', 'payment_method', 'payment_status', 'amount', 'payment_initiated_at']
    list_filter = ['payment_status', 'payment_method', 'payment_initiated_at']
    search_fields = ['order__order_uuid', 'transaction_id']
    readonly_fields = ['payment_initiated_at']
    list_editable = ['payment_status']

@admin.register(OrderTracking)
class OrderTrackingAdmin(admin.ModelAdmin):
    list_display = ['order', 'status', 'updated_by', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order__order_uuid']
    readonly_fields = ['created_at']

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['customer', 'restaurant', 'total_items', 'subtotal', 'updated_at']
    search_fields = ['customer__user__username', 'restaurant__name']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['cart', 'menu_item', 'quantity', 'unit_price', 'total_price']
    search_fields = ['cart__customer__user__username', 'menu_item__name']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(CartItemModifier)
class CartItemModifierAdmin(admin.ModelAdmin):
    list_display = ['cart_item', 'item_modifier', 'quantity', 'unit_price', 'total_price']
    search_fields = ['cart_item__menu_item__name', 'item_modifier__name']

@admin.register(RestaurantSalesReport)
class RestaurantSalesReportAdmin(admin.ModelAdmin):
    list_display = [
        'restaurant', 'period_type', 'start_date', 'end_date',
        'total_orders', 'total_revenue', 'order_completion_rate_display'
    ]
    list_filter = ['period_type', 'restaurant', 'start_date']
    search_fields = ['restaurant__name']
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 20
    date_hierarchy = 'start_date'
    
    def order_completion_rate_display(self, obj):
        if obj.total_orders > 0:
            rate = (obj.completed_orders / obj.total_orders) * 100
            return f"{rate:.1f}%"
        return "0%"
    order_completion_rate_display.short_description = 'Completion Rate'

@admin.register(DailySalesSnapshot)
class DailySalesSnapshotAdmin(admin.ModelAdmin):
    list_display = [
        'restaurant', 'date', 'orders_count', 'revenue', 
        'completed_orders', 'cancelled_orders', 'growth_rate_display'
    ]
    list_filter = ['restaurant', 'date']
    search_fields = ['restaurant__name']
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 20
    date_hierarchy = 'date'
    
    def growth_rate_display(self, obj):
        return f"{obj.growth_rate}%" if hasattr(obj, 'growth_rate') else "N/A"
    growth_rate_display.short_description = 'Growth Rate'


@admin.register(RestaurantPerformanceMetrics)
class RestaurantPerformanceMetricsAdmin(admin.ModelAdmin):
    list_display = [
        'restaurant', 'lifetime_orders', 'lifetime_revenue', 'average_rating',
        'today_orders', 'today_revenue', 'order_completion_rate', 'last_updated'
    ]
    list_filter = ['restaurant']
    search_fields = ['restaurant__name']
    readonly_fields = ['last_updated', 'created_at']
    list_per_page = 20
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('restaurant')

@admin.register(UserBehavior)
class UserBehaviorAdmin(admin.ModelAdmin):
    list_display = ['user', 'behavior_type', 'restaurant', 'menu_item', 'created_at']
    list_filter = ['behavior_type', 'created_at']
    search_fields = ['user__username', 'user__email', 'restaurant__name']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at']

@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'last_calculated', 'avg_order_value']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['last_calculated', 'created_at']
    
    def avg_order_value(self, obj):
        return f"${obj.avg_order_value}"
    avg_order_value.short_description = 'Avg Order Value'

@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ['user', 'recommendation_type', 'is_active', 'generated_at', 'expires_at']
    list_filter = ['recommendation_type', 'is_active', 'generated_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['generated_at']
    filter_horizontal = ['recommended_restaurants', 'recommended_menu_items']
    
    def has_expired(self, obj):
        return obj.is_expired()
    has_expired.boolean = True
    has_expired.short_description = 'Expired'

@admin.register(SimilarityMatrix)
class SimilarityMatrixAdmin(admin.ModelAdmin):
    list_display = ['matrix_type', 'item_a_id', 'item_b_id', 'similarity_score', 'calculated_at']
    list_filter = ['matrix_type', 'calculated_at']
    search_fields = ['matrix_type']
    readonly_fields = ['calculated_at']

@admin.register(RestaurantReview)
class RestaurantReviewAdmin(admin.ModelAdmin):
    list_display = ['review_id', 'restaurant', 'customer', 'overall_rating', 'status', 'created_at']
    list_filter = ['status', 'overall_rating', 'created_at', 'restaurant']
    search_fields = ['restaurant__name', 'customer__user__username', 'title', 'comment']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['approve_reviews', 'reject_reviews']

    def approve_reviews(self, request, queryset):
        queryset.update(status='approved', approved_at=timezone.now())
        self.message_user(request, f"{queryset.count()} reviews approved")
    approve_reviews.short_description = "Approve selected reviews"

    def reject_reviews(self, request, queryset):
        queryset.update(status='rejected')
        self.message_user(request, f"{queryset.count()} reviews rejected")
    reject_reviews.short_description = "Reject selected reviews"

@admin.register(DishReview)
class DishReviewAdmin(admin.ModelAdmin):
    list_display = ['dish_review_id', 'menu_item', 'customer', 'rating', 'status', 'created_at']
    list_filter = ['status', 'rating', 'created_at']
    search_fields = ['menu_item__name', 'customer__user__username', 'comment']

@admin.register(ReviewResponse)
class ReviewResponseAdmin(admin.ModelAdmin):
    list_display = ['response_id', 'review', 'responder', 'created_at']
    search_fields = ['review__title', 'responder__username']

@admin.register(ReviewReport)
class ReviewReportAdmin(admin.ModelAdmin):
    list_display = ['report_id', 'review', 'reporter', 'reason', 'status', 'created_at']
    list_filter = ['reason', 'status', 'created_at']
    actions = ['resolve_reports']

    def resolve_reports(self, request, queryset):
        queryset.update(status='resolved', resolved_by=request.user, resolved_at=timezone.now())
        self.message_user(request, f"{queryset.count()} reports resolved")
    resolve_reports.short_description = "Resolve selected reports"

@admin.register(RestaurantReviewSettings)
class RestaurantReviewSettingsAdmin(admin.ModelAdmin):
    list_display = ['restaurant', 'auto_approve_reviews', 'require_order_verification']
    list_filter = ['auto_approve_reviews', 'require_order_verification']

@admin.register(RestaurantRating)
class RestaurantRatingAdmin(admin.ModelAdmin):
    list_display = ['rating_id', 'restaurant', 'customer', 'overall_rating', 'is_quick_rating', 'created_at']
    list_filter = ['is_quick_rating', 'created_at', 'restaurant']
    search_fields = ['restaurant__name', 'customer__user__username']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(DishRating)
class DishRatingAdmin(admin.ModelAdmin):
    list_display = ['dish_rating_id', 'menu_item', 'customer', 'rating', 'is_quick_rating', 'created_at']
    list_filter = ['is_quick_rating', 'created_at']
    search_fields = ['menu_item__name', 'customer__user__username']

@admin.register(RatingAggregate)
class RatingAggregateAdmin(admin.ModelAdmin):
    list_display = ['aggregate_id', 'content_type', 'object_id', 'total_ratings', 'average_rating']
    list_filter = ['content_type']
    readonly_fields = ['last_calculated', 'created_at']

@admin.register(CustomerLifetimeValue)
class CustomerLifetimeValueAdmin(admin.ModelAdmin):
    list_display = [
        'customer', 'restaurant', 'total_orders', 'total_spent', 
        'customer_segment', 'is_active', 'calculated_at'
    ]
    list_filter = ['customer_segment', 'is_active', 'restaurant', 'calculated_at']
    search_fields = ['customer__user__username', 'customer__user__email', 'restaurant__name']
    readonly_fields = ['calculated_at', 'created_at']
    list_per_page = 20
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('customer__user', 'restaurant')

@admin.register(MenuItemPerformance)
class MenuItemPerformanceAdmin(admin.ModelAdmin):
    list_display = [
        'menu_item', 'restaurant', 'period_type', 'start_date', 'end_date',
        'quantity_sold', 'total_revenue', 'profit_margin', 'popularity_rank'
    ]
    list_filter = ['period_type', 'restaurant', 'start_date']
    search_fields = ['menu_item__name', 'restaurant__name']
    readonly_fields = ['calculated_at']
    list_per_page = 20
    date_hierarchy = 'start_date'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('menu_item', 'restaurant')

@admin.register(OperationalEfficiency)
class OperationalEfficiencyAdmin(admin.ModelAdmin):
    list_display = [
        'restaurant', 'branch_display', 'date', 'period_type',
        'fulfillment_rate', 'average_preparation_time', 'efficiency_score'
    ]
    list_filter = ['period_type', 'restaurant', 'date']
    search_fields = ['restaurant__name']
    readonly_fields = ['calculated_at']
    list_per_page = 20
    date_hierarchy = 'date'
    
    def branch_display(self, obj):
        return obj.branch.address.city if obj.branch else 'All Branches'
    branch_display.short_description = 'Branch'
    
    def efficiency_score(self, obj):
        # Calculate efficiency score for admin display
        score = (obj.fulfillment_rate * 0.3 + 
                (obj.on_time_delivery_rate or 0) * 0.3 +
                (obj.customer_satisfaction_score * 20) * 0.2 +
                (obj.order_accuracy_rate or 0) * 0.2)
        return f"{score:.1f}%"
    efficiency_score.short_description = 'Efficiency Score'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('restaurant', 'branch', 'branch__address')

@admin.register(FinancialReport)
class FinancialReportAdmin(admin.ModelAdmin):
    list_display = [
        'restaurant', 'report_type', 'period_type', 'start_date', 'end_date',
        'total_revenue', 'net_profit', 'net_margin', 'financial_health'
    ]
    list_filter = ['report_type', 'period_type', 'restaurant', 'start_date']
    search_fields = ['restaurant__name']
    readonly_fields = ['generated_at', 'created_at']
    list_per_page = 20
    date_hierarchy = 'start_date'
    
    def financial_health(self, obj):
        if obj.net_margin > 15:
            return "🟢 Excellent"
        elif obj.net_margin > 10:
            return "🔵 Good"
        elif obj.net_margin > 5:
            return "🟡 Fair"
        else:
            return "🔴 Poor"
    financial_health.short_description = 'Financial Health'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('restaurant')

@admin.register(ComparativeAnalytics)
class ComparativeAnalyticsAdmin(admin.ModelAdmin):
    list_display = [
        'restaurant', 'comparison_type', 'period_type', 'start_date', 'end_date',
        'market_share', 'competitive_position', 'calculated_at'
    ]
    list_filter = ['comparison_type', 'period_type', 'competitive_position', 'restaurant']
    search_fields = ['restaurant__name']
    readonly_fields = ['calculated_at', 'created_at']
    list_per_page = 20
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('restaurant')

@admin.register(MultiRestaurantLoyaltyProgram)
class MultiRestaurantLoyaltyProgramAdmin(admin.ModelAdmin):
    list_display = ['name', 'program_type', 'is_active', 'default_points_per_dollar', 'get_restaurant_count']
    list_filter = ['program_type', 'is_active']
    filter_horizontal = ['participating_restaurants']
    search_fields = ['name']
    
    def get_restaurant_count(self, obj):
        if obj.program_type == 'global':
            return "All Restaurants"
        return obj.participating_restaurants.count()
    get_restaurant_count.short_description = 'Restaurants'

@admin.register(RestaurantLoyaltySettings)
class RestaurantLoyaltySettingsAdmin(admin.ModelAdmin):
    list_display = ['restaurant', 'is_loyalty_enabled', 'effective_points_rate', 'allow_point_redemption']
    list_filter = ['is_loyalty_enabled', 'allow_point_redemption', 'allow_reward_redemption']
    search_fields = ['restaurant__name']
    readonly_fields = ['effective_points_rate']

@admin.register(CustomerLoyalty)
class CustomerLoyaltyAdmin(admin.ModelAdmin):
    list_display = ['customer', 'program', 'tier', 'current_points', 'total_orders']
    list_filter = ['tier', 'program']
    search_fields = ['customer__user__email', 'customer__user__first_name']
    readonly_fields = ['joined_at', 'tier_updated_at']

@admin.register(PointsTransaction)
class PointsTransactionAdmin(admin.ModelAdmin):
    list_display = ['customer_loyalty', 'points', 'transaction_type', 'restaurant', 'transaction_date']
    list_filter = ['transaction_type', 'is_active']
    search_fields = ['customer_loyalty__customer__user__email', 'reason']
    readonly_fields = ['transaction_date']
    date_hierarchy = 'transaction_date'

@admin.register(Reward)
class RewardAdmin(admin.ModelAdmin):
    list_display = ['name', 'restaurant', 'reward_type', 'points_required', 'min_tier_required', 'is_active']
    list_filter = ['reward_type', 'min_tier_required', 'is_active', 'restaurant']
    search_fields = ['name', 'description']

@admin.register(RewardRedemption)
class RewardRedemptionAdmin(admin.ModelAdmin):
    list_display = ['customer_loyalty', 'reward', 'status', 'points_used', 'created_at']
    list_filter = ['status']
    search_fields = ['customer_loyalty__customer__user__email', 'reward__name']
    readonly_fields = ['redemption_code']

@admin.register(DiscountVoucher)
class DiscountVoucherAdmin(admin.ModelAdmin):
    list_display = ['code', 'restaurant', 'discount_type', 'discount_value', 'is_used', 'valid_until']
    list_filter = ['discount_type', 'is_used']
    search_fields = ['code']
    readonly_fields = ['code']

@admin.register(GroupOrder)
class GroupOrderAdmin(admin.ModelAdmin):
    list_display = ['name', 'organizer', 'restaurant', 'status', 'order_deadline']
    list_filter = ['status', 'restaurant']
    search_fields = ['name', 'organizer__user__email']
    readonly_fields = ['share_code', 'created_at']

@admin.register(OrderTemplate)
class OrderTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'customer', 'restaurant', 'usage_count', 'is_active']
    list_filter = ['is_active', 'restaurant']
    search_fields = ['name', 'customer__user__email']

@admin.register(ScheduledOrder)
class ScheduledOrderAdmin(admin.ModelAdmin):
    list_display = ['customer', 'restaurant', 'schedule_type', 'scheduled_for', 'is_active']
    list_filter = ['schedule_type', 'is_active']
    search_fields = ['customer__user__email', 'restaurant__name']

@admin.register(BulkOrder)
class BulkOrderAdmin(admin.ModelAdmin):
    list_display = ['event_name', 'customer', 'restaurant', 'event_type', 'status', 'event_date']
    list_filter = ['event_type', 'status']
    search_fields = ['event_name', 'customer__user__email']

# Register other models
admin.site.register(GroupOrderParticipant)
admin.site.register(BulkOrderItem)

# Custom filter for stock status
class StockStatusFilter(admin.SimpleListFilter):
    title = 'stock status'
    parameter_name = 'stock_status'
    
    def lookups(self, request, model_admin):
        return (
            ('out_of_stock', 'Out of Stock'),
            ('low_stock', 'Low Stock'),
            ('in_stock', 'In Stock'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'out_of_stock':
            return queryset.filter(current_stock__lte=models.F('out_of_stock_threshold'))
        elif self.value() == 'low_stock':
            return queryset.filter(
                current_stock__lte=models.F('low_stock_threshold'),
                current_stock__gt=models.F('out_of_stock_threshold')
            )
        elif self.value() == 'in_stock':
            return queryset.filter(current_stock__gt=models.F('low_stock_threshold'))
        return queryset

@admin.register(WebSocketConnection)
class WebSocketConnectionAdmin(admin.ModelAdmin):
    list_display = ['connection_id_short', 'user', 'connection_type', 'is_active', 'connected_at']
    list_filter = ['connection_type', 'is_active', 'connected_at']
    search_fields = ['user__username', 'connection_id']
    readonly_fields = ['connection_id', 'connected_at', 'last_activity']
    
    def connection_id_short(self, obj):
        return str(obj.connection_id)[:8] + '...'
    connection_id_short.short_description = 'Connection ID'

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title_short', 'user', 'type', 'is_read', 'is_sent', 'created_at']
    list_filter = ['type', 'is_read', 'is_sent', 'created_at']
    search_fields = ['user__username', 'title']
    readonly_fields = ['notification_id', 'created_at']
    actions = ['mark_as_read']
    
    def title_short(self, obj):
        return obj.title[:50] + '...' if len(obj.title) > 50 else obj.title
    title_short.short_description = 'Title'
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True, read_at=timezone.now())
        self.message_user(request, f'{updated} notifications marked as read.')

@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'enable_websocket', 'enable_push', 'enable_email']
    list_filter = ['enable_websocket', 'enable_push', 'enable_email']
    search_fields = ['user__username']

@admin.register(LiveOrderTracking)
class LiveOrderTrackingAdmin(admin.ModelAdmin):
    list_display = ['order', 'preparation_progress', 'delivery_progress', 'delivery_person']
    list_filter = ['delivery_person']
    search_fields = ['order__order_uuid']
    readonly_fields = ['tracking_id']

# FIXED: RealTimeInventoryAdmin
@admin.register(RealTimeInventory)
class RealTimeInventoryAdmin(admin.ModelAdmin):
    list_display = ['menu_item', 'branch', 'current_stock', 'low_stock_threshold', 'stock_status', 'last_updated']
    list_filter = [StockStatusFilter, 'branch', 'auto_restock_enabled']  # FIXED: Using custom filter
    search_fields = ['menu_item__name']
    list_editable = ['current_stock']
    
    def stock_status(self, obj):
        if obj.is_out_of_stock:
            return format_html('<span style="color: red;">● Out of Stock</span>')
        elif obj.is_low_stock:
            return format_html('<span style="color: orange;">● Low Stock</span>')
        else:
            return format_html('<span style="color: green;">● In Stock</span>')
    stock_status.short_description = 'Status'

@admin.register(InventoryAlert)
class InventoryAlertAdmin(admin.ModelAdmin):
    list_display = ['inventory', 'alert_type', 'is_resolved', 'created_at']
    list_filter = ['alert_type', 'is_resolved', 'created_at']
    search_fields = ['inventory__menu_item__name']
    actions = ['mark_as_resolved']
    
    def mark_as_resolved(self, request, queryset):
        updated = queryset.update(is_resolved=True, resolved_at=timezone.now(), resolved_by=request.user)
        self.message_user(request, f'{updated} alerts marked as resolved.')

@admin.register(PushNotificationDevice)
class PushNotificationDeviceAdmin(admin.ModelAdmin):
    list_display = ['user', 'platform', 'is_active', 'last_active']
    list_filter = ['platform', 'is_active']
    search_fields = ['user__username']
    readonly_fields = ['last_active']

@admin.register(PushNotificationLog)
class PushNotificationLogAdmin(admin.ModelAdmin):
    list_display = ['notification', 'device', 'success', 'sent_at']
    list_filter = ['success', 'sent_at']
    search_fields = ['notification__title']
    readonly_fields = ['sent_at']

@admin.register(PopularitySnapshot)
class PopularitySnapshotAdmin(admin.ModelAdmin):
    list_display = ['menu_item', 'score', 'rank', 'date_recorded']
    list_filter = ['date_recorded', 'menu_item__category__restaurant']
    readonly_fields = ['score', 'rank', 'date_recorded']
    search_fields = ['menu_item__name']

@admin.register(ItemAssociation)
class ItemAssociationAdmin(admin.ModelAdmin):
    list_display = ['source_item', 'target_item', 'confidence', 'support']
    list_filter = ['source_item__category__restaurant']
    readonly_fields = ['confidence', 'support']
    search_fields = ['source_item__name', 'target_item__name']

@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ['table_number', 'table_name', 'restaurant', 'branch', 'capacity', 'table_type', 'is_available', 'upcoming_reservations']
    list_filter = ['restaurant', 'branch', 'table_type', 'is_available']
    search_fields = ['table_number', 'table_name', 'restaurant__name']
    readonly_fields = ['created_at', 'updated_at']
    list_select_related = ['restaurant', 'branch']
    
    def upcoming_reservations(self, obj):
        count = obj.reservations.filter(
            reservation_date__gte=timezone.now().date(),
            status__in=['confirmed', 'pending']
        ).count()
        return count
    upcoming_reservations.short_description = 'Upcoming'

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ['reservation_code', 'customer_name', 'restaurant', 'reservation_date', 'reservation_time', 'party_size', 'status', 'is_upcoming', 'admin_actions']
    list_filter = ['status', 'restaurant', 'reservation_date', 'special_occasion', 'branch']
    search_fields = ['reservation_code', 'customer__user__email', 'customer__user__first_name', 'customer__user__last_name']
    readonly_fields = ['reservation_code', 'created_at', 'updated_at']
    list_select_related = ['customer__user', 'restaurant', 'branch', 'table']
    date_hierarchy = 'reservation_date'
    
    # ✅ CORRECT: List of method names as strings
    actions = ['confirm_selected_reservations', 'cancel_selected_reservations']
    
    def customer_name(self, obj):
        return obj.customer.user.get_full_name() or obj.customer.user.username
    customer_name.short_description = 'Customer'
    
    def is_upcoming(self, obj):
        return obj.is_upcoming
    is_upcoming.boolean = True
    
    def admin_actions(self, obj):
        """Display action buttons in list view"""
        if obj.status in ['pending', 'confirmed']:
            return format_html(
                '<a class="button" href="{}">Confirm</a> '
                '<a class="button" href="{}" style="background-color: #ba2121; color: white;">Cancel</a>',
                reverse('admin:reservation_reservation_confirm', args=[obj.pk]),
                reverse('admin:reservation_reservation_cancel', args=[obj.pk])
            )
        return "-"
    admin_actions.short_description = 'Actions'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.user_type == 'owner':
            return qs.filter(restaurant__owner=request.user)
        return qs
    
    # ✅ CORRECT: Admin actions as methods
    @admin.action(description="Confirm selected reservations")
    def confirm_selected_reservations(self, request, queryset):
        updated = queryset.filter(status='pending').update(status='confirmed')
        for reservation in queryset.filter(status='confirmed'):
            try:
                NotificationService.send_reservation_confirmation(reservation)
            except Exception as e:
                self.message_user(request, f"Failed to send confirmation for {reservation.reservation_code}: {str(e)}", messages.ERROR)
        self.message_user(request, f'{updated} reservations confirmed.', messages.SUCCESS)
    
    @admin.action(description="Cancel selected reservations")
    def cancel_selected_reservations(self, request, queryset):
        updated = queryset.filter(status__in=['pending', 'confirmed']).update(status='cancelled')
        for reservation in queryset.filter(status='cancelled'):
            try:
                NotificationService.send_reservation_cancellation(reservation, "Cancelled by admin")
            except Exception as e:
                self.message_user(request, f"Failed to send cancellation for {reservation.reservation_code}: {str(e)}", messages.ERROR)
        self.message_user(request, f'{updated} reservations cancelled.', messages.SUCCESS)
    
    # Custom admin views for individual actions
    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/confirm/', self.admin_site.admin_view(self.confirm_reservation), name='reservation_reservation_confirm'),
            path('<path:object_id>/cancel/', self.admin_site.admin_view(self.cancel_reservation), name='reservation_reservation_cancel'),
        ]
        return custom_urls + urls
    
    def confirm_reservation(self, request, object_id):
        """Confirm a single reservation"""
        reservation = self.get_object(request, object_id)
        if reservation and reservation.status == 'pending':
            reservation.status = 'confirmed'
            reservation.save()
            try:
                NotificationService.send_reservation_confirmation(reservation)
                self.message_user(request, f'Reservation {reservation.reservation_code} confirmed.', messages.SUCCESS)
            except Exception as e:
                self.message_user(request, f'Reservation confirmed but failed to send email: {str(e)}', messages.WARNING)
        else:
            self.message_user(request, 'Reservation could not be confirmed.', messages.ERROR)
        
        return HttpResponseRedirect(reverse('admin:reservation_reservation_changelist'))
    
    def cancel_reservation(self, request, object_id):
        """Cancel a single reservation"""
        reservation = self.get_object(request, object_id)
        if reservation and reservation.status in ['pending', 'confirmed']:
            reservation.status = 'cancelled'
            reservation.save()
            try:
                NotificationService.send_reservation_cancellation(reservation, "Cancelled by admin")
                self.message_user(request, f'Reservation {reservation.reservation_code} cancelled.', messages.SUCCESS)
            except Exception as e:
                self.message_user(request, f'Reservation cancelled but failed to send email: {str(e)}', messages.WARNING)
        else:
            self.message_user(request, 'Reservation could not be cancelled.', messages.ERROR)
        
        return HttpResponseRedirect(reverse('admin:reservation_reservation_changelist'))

@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ['date', 'start_time', 'end_time', 'restaurant', 'branch', 'max_capacity', 'reserved_count', 'available_capacity', 'is_available']
    list_filter = ['restaurant', 'branch', 'date', 'is_available']
    readonly_fields = ['created_at', 'updated_at']
    list_select_related = ['restaurant', 'branch']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.user_type == 'owner':
            return qs.filter(restaurant__owner=request.user)
        return qs
