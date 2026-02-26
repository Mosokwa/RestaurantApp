from rest_framework import routers
from django.urls import include, path

from .views import (
    UserProfileView, CurrentUserView, CustomerListView, CustomerDetailView, RestaurantStaffListView, RestaurantStaffDetailView, MyStaffProfileView, LoginView, SignupView, LogoutView, CSRFTokenView, JWTObtainPairView, PasswordResetView, PasswordResetConfirmView, EmailVerificationView, VerifyCodeView, ChangePasswordView, RefreshTokenView, UserBehaviorViewSet, UserPreferenceView, PersonalizedRecommendationView, TrendingRecommendationView, PopularRestaurantsView, TrendingDishesView, PersonalizedRecommendationsView, HomepageSpecialOffersView, CuisineListView, CuisineCreateView, CuisineDetailView, CuisineDeleteView, CuisineUpdateView, MenuCategoryListView, MenuCategoryCreateView, RestaurantMenuView, MenuItemListView, MenuItemDetailView, SpecialOfferView, MenuItemCreateView, EnhancedRestaurantListView, RestaurantListView, RestaurantDetailView, RestaurantCreateView, MyRestaurantsView, RestaurantUpdateView, RestaurantDeleteView, RestaurantOnboardingView, BranchCreateView, BranchListView, BranchDetailView, BranchUpdateView, BranchDeleteView, RestaurantBranchesView, ComprehensiveSearchView, SearchSuggestionsView, CombinedSuggestionsView, MenuItemSuggestionsView, RestaurantSuggestionsView, MenuItemSearchView, restaurant_search, nearby_restaurants, ItemModifierGroupListView, ItemModifierGroupDetailView, ItemModifierListView, ItemModifierDetailView, MenuItemModifierListView, MenuItemModifierDetailView, MenuItemModifiersView, BulkMenuItemModifiersView, OrderListView, OrderDetailView, OrderUpdateView, MyOrdersView, PaymentCreateView, PaymentDetailView, CartDetailView, CartItemView, CartItemUpdateView, CartItemDeleteView, RestaurantReviewListView, DishReviewListView, ReviewResponseView, ReviewHelpfulVoteView, ReviewReportView, RestaurantReviewAnalyticsView, UserReviewsView, ReviewModerationListView, ReviewModerationUpdateView, RestaurantRatingView, DishRatingView, QuickRatingView, RatingStatsView, BulkRatingView, UserRatingsView, OrderTrackingView, RestaurantSalesAnalyticsView, DailySalesReportView, MonthlySalesReportView, RestaurantPerformanceMetricsView, SalesTrendsView, CustomerInsightsView, OperationalMetricsView, FinancialReportsView, ComparativeAnalyticsView, ExportAnalyticsView, DashboardMetricsView, SimilarItemsView, TrackUserBehaviorView, MultiRestaurantLoyaltyViewSet, RewardViewSet, RestaurantLoyaltySettingsViewSet, RestaurantRewardViewSet, OwnerLoyaltyDashboardViewSet, GroupOrderViewSet, OrderTemplateViewSet, ScheduledOrderViewSet, BulkOrderViewSet, AdvancedOrderViewSet, CartApplyOfferView, CartRemoveOfferView, RestaurantHomepageRecommendationsView, RestaurantPopularItemsView, RestaurantSimilarItemsView, RestaurantTrendingItemsView, ReservationViewSet, TableViewSet, TimeSlotViewSet, RestaurantsSearchView, RestaurantAvailabilityView, RestaurantHomepageViewSet, POSConnectionViewSet, TableLayoutViewSet, KitchenStationViewSet,
    OrderRoutingViewSet, KitchenOrderViewSet, pos_order_webhook, pos_menu_webhook, pos_inventory_webhook, route_order_to_kitchen, assign_order_station, update_preparation_status, OwnerLoginView, OwnerRegisterView, OwnerProfileView, OwnerRestaurantsView, StaffInviteView, OwnerEmailVerificationView, OwnerVerifyCodeView, health_check, GoogleAuthView, AppleAuthView, SocialAuthHealthView, EnhancedMenuPerformanceView, CategoryAnalyticsView, ItemAssociationsView, BulkMenuOperationsView, RealTimeMenuMetricsView, QuickCategoriesView, NewRestaurantsView, UserFavoritesView, 
    DietaryPicksView, RecentlyViewedView, TimeBasedRecommendationsView, RestaurantsYouMightLikeView, FastDeliveryRestaurantsView, PriceRangeFilterView, LocalFavoritesView, TrendingTodayView, ExploreOtherCitiesView, RestaurantStoriesView, AnonymousTrackUserBehaviorView
)
from rest_framework_simplejwt.views import TokenRefreshView
from .two_factor_views import TwoFactorSetupView, TwoFactorVerifyView, TwoFactorDisableView

router = routers.DefaultRouter()
# Register the ViewSet with a base name
router.register(r'user-behaviors', UserBehaviorViewSet, basename='userbehavior')

# Multi-Restaurant Loyalty Routes
router.register(r'loyalty', MultiRestaurantLoyaltyViewSet, basename='loyalty')
router.register(r'rewards', RewardViewSet, basename='rewards')
router.register(r'restaurant-loyalty-settings', RestaurantLoyaltySettingsViewSet, basename='restaurant-loyalty-settings')
router.register(r'restaurant-rewards', RestaurantRewardViewSet, basename='restaurant-rewards')
router.register(r'owner-loyalty-dashboard', OwnerLoyaltyDashboardViewSet, basename='owner-loyalty-dashboard')

# Advanced Ordering Routes
router.register(r'group-orders', GroupOrderViewSet, basename='group-orders')
router.register(r'order-templates', OrderTemplateViewSet, basename='order-templates')
router.register(r'scheduled-orders', ScheduledOrderViewSet, basename='scheduled-orders')
router.register(r'bulk-orders', BulkOrderViewSet, basename='bulk-orders')
router.register(r'advanced-orders', AdvancedOrderViewSet, basename='advanced-orders')

# Reservations routes
router.register(r'reservations', ReservationViewSet, basename='reservations')
router.register(r'timeslots', TimeSlotViewSet, basename='timeslots')

# Dedicated restaurant homepage viewset
router.register(r'restaurants', RestaurantHomepageViewSet, basename='restaurant')

# POS Integration Routes
router.register(r'pos/connections', POSConnectionViewSet, basename='posconnection')
router.register(r'tables/layouts', TableLayoutViewSet, basename='tablelayout')
router.register(r'kitchen/stations', KitchenStationViewSet, basename='kitchenstation')
router.register(r'orders/routing', OrderRoutingViewSet, basename='orderrouting')
router.register(r'kitchen/orders', KitchenOrderViewSet, basename='kitchenorder')


urlpatterns = [
    # Include router URLs
    path('routes/', include(router.urls)),

    # database check
    path('health/', health_check, name='health_check'),

    #authentication
    path('auth/signup/', SignupView.as_view(), name='signup'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/me/', CurrentUserView.as_view(), name='current_user'),
    path('auth/profile/', UserProfileView.as_view(), name='user_profile'),
    path('auth/csrf/', CSRFTokenView.as_view(), name='csrf_token'),
    path('auth/verify-code/', VerifyCodeView.as_view(), name='verify_code'),

    # Owner authentication and management
     path('owner/auth/login/', OwnerLoginView.as_view(), name='owner_login'),
     path('owner/auth/register/', OwnerRegisterView.as_view(), name='owner_register'),
     path('owner/auth/verify-email/', OwnerEmailVerificationView.as_view(), name='owner-verify-email'),
     path('owner/auth/verify-code/', OwnerVerifyCodeView.as_view(), name='owner-verify-code'),
     path('owner/auth/me/', OwnerProfileView.as_view(), name='owner_profile'),
     path('owner/restaurants/', OwnerRestaurantsView.as_view(), name='owner_restaurants'),
     path('owner/staff/invite/', StaffInviteView.as_view(), name='staff_invite'),


    # Social authentication
    path('auth/google/login/', GoogleAuthView.as_view(), name='google_login'),
    path('auth/apple/login/', AppleAuthView.as_view(), name='apple_login'),
    path('auth/health/social/', SocialAuthHealthView.as_view(), name='social_auth_health'),
    
    #JWT Tokens
    path('auth/token/', JWTObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/token/custom-refresh/', RefreshTokenView.as_view(), name='custom_token_refresh'),
    
    # Password Management
    path('auth/password/reset/', PasswordResetView.as_view(), name='password_reset'),
    path('auth/password/reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('auth/password/change/', ChangePasswordView.as_view(), name='change_password'),
    
    # Email Verification
    path('auth/verify-email/', EmailVerificationView.as_view(), name='verify_email'),

    # 2FA endpoints
    path('auth/2fa/setup/', TwoFactorSetupView.as_view(), name='2fa_setup'),
    path('auth/2fa/verify/', TwoFactorVerifyView.as_view(), name='2fa_verify'),
    path('auth/2fa/disable/', TwoFactorDisableView.as_view(), name='2fa_disable'),

    # Customer endpoints
    path('customers/', CustomerListView.as_view(), name='customer_list'),
    path('customers/me/', CustomerDetailView.as_view(), name='customer_me'),
    path('customers/<int:pk>/', CustomerDetailView.as_view(), name='customer_detail'),
    
    # Staff endpoints
    path('staff/', RestaurantStaffListView.as_view(), name='staff_list'),
    path('staff/me/', MyStaffProfileView.as_view(), name='staff_me'),
    path('staff/<int:pk>/', RestaurantStaffDetailView.as_view(), name='staff_detail'),

     # Cuisine endpoints
    path('cuisines/', CuisineListView.as_view(), name='cuisine_list'),
    path('cuisines/create/', CuisineCreateView.as_view(), name='cuisine_create'),
    path('cuisines/<int:pk>/', CuisineDetailView.as_view(), name='cuisine_detail'),
    path('cuisines/<int:pk>/update/', CuisineUpdateView.as_view(), name='cuisine_update'),
    path('cuisines/<int:pk>/delete/', CuisineDeleteView.as_view(), name='cuisine_delete'),
    
    #Homepage endpoints
    path('homepage/popular-restaurants/', PopularRestaurantsView.as_view(), name='popular_restaurants'),
    path('homepage/trending-dishes/', TrendingDishesView.as_view(), name='trending_dishes'),
    path('homepage/personalized-recommendations/', PersonalizedRecommendationsView.as_view(), name='personalized_recommendations'),
    path('homepage/special-offers/', HomepageSpecialOffersView.as_view(), name='homepage_special_offers'),

    # Enhanced homepage endpoints
    path('homepage/quick-categories/', QuickCategoriesView.as_view(), name='quick_categories'),
    path('homepage/new-restaurants/', NewRestaurantsView.as_view(), name='new_restaurants'),
    path('homepage/user-favorites/', UserFavoritesView.as_view(), name='user_favorites'),
    path('homepage/dietary-picks/', DietaryPicksView.as_view(), name='dietary_picks'),
    path('homepage/recently-viewed/', RecentlyViewedView.as_view(), name='recently_viewed'),

    path('homepage/time-based-recommendations/', TimeBasedRecommendationsView.as_view(), name='time_based_recommendations'),
    path('homepage/restaurants-you-might-like/', RestaurantsYouMightLikeView.as_view(), name='restaurants_you_might_like'),
    path('homepage/fast-delivery/', FastDeliveryRestaurantsView.as_view(), name='fast_delivery'),
    path('homepage/price-ranges/', PriceRangeFilterView.as_view(), name='price_ranges'),

    path('homepage/local-favorites/', LocalFavoritesView.as_view(), name='local_favorites'),
    path('homepage/trending-today/', TrendingTodayView.as_view(), name='trending_today'),
    path('homepage/explore-cities/', ExploreOtherCitiesView.as_view(), name='explore_cities'),
    path('homepage/restaurant-stories/', RestaurantStoriesView.as_view(), name='restaurant_stories'),

    #personalized recommendations endpoints
    path('recommendations/personalized/', PersonalizedRecommendationView.as_view(), name='personalized-recommendations'),
    path('user/preferences/', UserPreferenceView.as_view(), name='user-preferences'),
    path('recommendations/trending/', TrendingRecommendationView.as_view(), name='trending-recommendations'),
    path('recommendations/<int:item_id>/similar/', SimilarItemsView.as_view(), name='similar-items'),
    path('user/track-behavior/', TrackUserBehaviorView.as_view(), name='track-behavior'),
    path('user/track-anonymous/', AnonymousTrackUserBehaviorView.as_view(), name='track-anonymous'),

    # Restaurant-specific recommendation endpoints
    path('restaurants/<int:restaurant_id>/homepage-recommendations/', RestaurantHomepageRecommendationsView.as_view(), name='restaurant-homepage-recommendations'),
    path('restaurants/<int:restaurant_id>/popular-items/', RestaurantPopularItemsView.as_view(), name='restaurant-popular-items'),
    path('restaurants/<int:restaurant_id>/similar-items/<int:item_id>/', RestaurantSimilarItemsView.as_view(), name='restaurant-similar-items'),
    path('restaurants/<int:restaurant_id>/trending-items/', RestaurantTrendingItemsView.as_view(), name='restaurant-trending-items'),

    #restaurant list (has no geo-search)
    path('restaurants/', RestaurantListView.as_view(), name='restaurant_list'),

    # Updated restaurant list with geo-search
    path('restaurants/enhanced/', EnhancedRestaurantListView.as_view(), name='enhanced_restaurant_list'),

    # Restaurant endpoints
    path('restaurants/onboarding/', RestaurantOnboardingView.as_view(), name='restaurant_onboarding'),
    path('restaurants/create/', RestaurantCreateView.as_view(), name='restaurant_create'),
    path('restaurants/<int:pk>/', RestaurantDetailView.as_view(), name='restaurant_detail'),
    path('restaurants/<int:pk>/update/', RestaurantUpdateView.as_view(), name='restaurant_update'),
    path('restaurants/<int:pk>/delete/', RestaurantDeleteView.as_view(), name='restaurant_delete'),
    path('restaurants/my/', MyRestaurantsView.as_view(), name='my_restaurants'),
    path('restaurants/<int:restaurant_id>/branches/', RestaurantBranchesView.as_view(), name='restaurant_branches'),
    path('restaurants/<int:restaurant_id>/branches/create/', BranchCreateView.as_view(), name='branch_create_for_restaurant'),
    
    # Branch endpoints
    path('branches/', BranchListView.as_view(), name='branch_list'),
    path('branches/create/', BranchCreateView.as_view(), name='branch_create'),
    path('branches/<int:pk>/', BranchDetailView.as_view(), name='branch_detail'),
    path('branches/<int:pk>/update/', BranchUpdateView.as_view(), name='branch_update'),
    path('branches/<int:pk>/delete/', BranchDeleteView.as_view(), name='branch_delete'),
    
    # Search endpoints (public)
    path('search/restaurants/', restaurant_search, name='restaurant_search'),
    path('search/nearby/', nearby_restaurants, name='nearby_restaurants'),

    # Enhanced Search endpoints(private)
    path('search/comprehensive/', ComprehensiveSearchView.as_view(), name='comprehensive_search'),
    path('search/suggestions/', SearchSuggestionsView.as_view(), name='search_suggestions'),  # Keep original for backward compatibility
    path('search/suggestions/restaurants/', RestaurantSuggestionsView.as_view(), name='restaurant_suggestions'),
    path('search/suggestions/menu-items/', MenuItemSuggestionsView.as_view(), name='menu_item_suggestions'),
    path('search/suggestions/combined/', CombinedSuggestionsView.as_view(), name='combined_suggestions'),
    path('search/menu-items/', MenuItemSearchView.as_view(), name='menu_item_search'),

     # Menu endpoints
    path('menu/categories/', MenuCategoryListView.as_view(), name='menu_category_list'),
    path('menu/categories/create/', MenuCategoryCreateView.as_view(), name='menu_category_create'),
    path('menu/items/', MenuItemListView.as_view(), name='menu_item_list'),
    path('menu/items/create/', MenuItemCreateView.as_view(), name='menu_item_create'),
    path('menu/items/<int:pk>/', MenuItemDetailView.as_view(), name='menu_item_detail'),
    path('menu/restaurant/<int:restaurant_id>/', RestaurantMenuView.as_view(), name='restaurant_menu'),
    path('menu/special-offers/', SpecialOfferView.as_view(), name='special_offers'),

    # Modifier Group endpoints
    path('modifier-groups/', ItemModifierGroupListView.as_view(), name='modifier_group_list'),
    path('modifier-groups/create/', ItemModifierGroupListView.as_view(), name='modifier_group_create'),
    path('modifier-groups/<int:pk>/', ItemModifierGroupDetailView.as_view(), name='modifier_group_detail'),
    path('modifier-groups/<int:pk>/update/', ItemModifierGroupDetailView.as_view(), name='modifier_group_update'),
    path('modifier-groups/<int:pk>/delete/', ItemModifierGroupDetailView.as_view(), name='modifier_group_delete'),

    # Item Modifier endpoints
    path('modifiers/', ItemModifierListView.as_view(), name='modifier_list'),
    path('modifiers/create/', ItemModifierListView.as_view(), name='modifier_create'),
    path('modifiers/<int:pk>/', ItemModifierDetailView.as_view(), name='modifier_detail'),
    path('modifiers/<int:pk>/update/', ItemModifierDetailView.as_view(), name='modifier_update'),
    path('modifiers/<int:pk>/delete/', ItemModifierDetailView.as_view(), name='modifier_delete'),

    # Menu Item Modifier endpoints
    path('menu-item-modifiers/', MenuItemModifierListView.as_view(), name='menu_item_modifier_list'),
    path('menu-item-modifiers/create/', MenuItemModifierListView.as_view(), name='menu_item_modifier_create'),
    path('menu-item-modifiers/<int:pk>/', MenuItemModifierDetailView.as_view(), name='menu_item_modifier_detail'),
    path('menu-item-modifiers/<int:pk>/delete/', MenuItemModifierDetailView.as_view(), name='menu_item_modifier_delete'),

    # Enhanced Menu Analytics URLs
    path('analytics/enhanced-menu-performance/', EnhancedMenuPerformanceView.as_view(), name='enhanced-menu-performance'),
    path('analytics/category-analytics/', CategoryAnalyticsView.as_view(), name='category-analytics'),
    path('analytics/item-associations/<int:item_id>/', ItemAssociationsView.as_view(), name='item-associations'),
    path('analytics/bulk-menu-operations/', BulkMenuOperationsView.as_view(), name='bulk-menu-operations'),
    path('analytics/real-time-metrics/<int:restaurant_id>/', RealTimeMenuMetricsView.as_view(), name='real-time-metrics'),
    # Special modifier endpoints
    path('menu-items/<int:menu_item_id>/modifiers/', MenuItemModifiersView.as_view(), name='menu_item_modifiers'),
    path('menu-items/bulk-modifiers/', BulkMenuItemModifiersView.as_view(), name='bulk_menu_item_modifiers'),

    # Review and Rating endpoints
    path('restaurants/<int:restaurant_id>/reviews/', RestaurantReviewListView.as_view(), name='restaurant_reviews'),
    path('menu-items/<int:menu_item_id>/reviews/', DishReviewListView.as_view(), name='dish_reviews'),
    path('reviews/<int:review_id>/response/', ReviewResponseView.as_view(), name='review_response'),
    path('reviews/<int:review_id>/helpful-vote/', ReviewHelpfulVoteView.as_view(), name='review_helpful_vote'),
    path('reviews/<int:review_id>/report/', ReviewReportView.as_view(), name='review_report'),
    path('restaurants/<int:restaurant_id>/review-analytics/', RestaurantReviewAnalyticsView.as_view(), name='review_analytics'),
    path('user/reviews/', UserReviewsView.as_view(), name='user_reviews'),
    path('restaurants/<int:restaurant_id>/moderation/reviews/', ReviewModerationListView.as_view(), name='review_moderation_list'),
    path('reviews/<int:review_id>/moderate/', ReviewModerationUpdateView.as_view(), name='review_moderate'),

    # Restaurant rating endpoints
    path('restaurants/<int:restaurant_id>/rate/', RestaurantRatingView.as_view(), name='restaurant_rate'),
    path('restaurants/<int:restaurant_id>/quick-rate/', QuickRatingView.as_view(), name='restaurant_quick_rate'),

    # Dish rating endpoints
    path('menu-items/<int:menu_item_id>/rate/', DishRatingView.as_view(), name='dish_rate'),

    # Rating statistics
    path('ratings/stats/', RatingStatsView.as_view(), name='rating_stats'),

    # Bulk rating operations
    path('ratings/bulk/', BulkRatingView.as_view(), name='bulk_rating'),

    # User ratings
    path('user/ratings/', UserRatingsView.as_view(), name='user_ratings'),

    # Order endpoints
    path('orders/', OrderListView.as_view(), name='order_list'),
    path('orders/my/', MyOrdersView.as_view(), name='my_orders'),
    path('orders/<int:pk>/update/', OrderUpdateView.as_view(), name='order_update'),
    path('orders/<int:order_id>/tracking/', OrderTrackingView.as_view(), name='order_tracking'),
    
    # New order endpoints with offers
    path('orders/with-offers/', OrderListView.as_view(), name='order-list-with-offers'),
    path('orders/<uuid:order_uuid>/', OrderDetailView.as_view(), name='order-detail'),
    path('orders/<uuid:order_uuid>/with-offers/', OrderDetailView.as_view(), name='order-detail-with-offers'),

    # Multi-Restaurant Loyalty Endpoints
    path('loyalty/restaurant-status/', MultiRestaurantLoyaltyViewSet.as_view({'get': 'restaurant_status'}), name='restaurant-loyalty-status'),
    path('loyalty/enroll/', MultiRestaurantLoyaltyViewSet.as_view({'post': 'enroll'}), name='enroll-loyalty'),
    path('loyalty/restaurant-rewards/', MultiRestaurantLoyaltyViewSet.as_view({'get': 'restaurant_rewards'}), name='restaurant-rewards'),
    path('loyalty/my-restaurants/', MultiRestaurantLoyaltyViewSet.as_view({'get': 'my_restaurants'}), name='my-loyalty-restaurants'),
    path('loyalty/redeem-restaurant/', MultiRestaurantLoyaltyViewSet.as_view({'post': 'redeem_at_restaurant'}), name='redeem-at-restaurant'),
    path('loyalty/validate-redemption/', MultiRestaurantLoyaltyViewSet.as_view({'post': 'validate_redemption'}), name='validate-redemption'),
    
    # Customer Loyalty Endpoints
    path('loyalty/points/', MultiRestaurantLoyaltyViewSet.as_view({'get': 'points'}), name='loyalty-points'),
    path('loyalty/transactions/', MultiRestaurantLoyaltyViewSet.as_view({'get': 'transactions'}), name='loyalty-transactions'),
    path('loyalty/redemptions/', MultiRestaurantLoyaltyViewSet.as_view({'get': 'redemptions'}), name='loyalty-redemptions'),
    path('loyalty/referral/', MultiRestaurantLoyaltyViewSet.as_view({'post': 'referral'}), name='customer-referral'),
    path('loyalty/referral-stats/', MultiRestaurantLoyaltyViewSet.as_view({'get': 'referral_stats'}), name='referral-stats'),
    path('loyalty/referral-history/', MultiRestaurantLoyaltyViewSet.as_view({'get': 'referral_history'}), name='referral-history'),
    
    # Advanced Ordering Endpoints
    path('orders/group/', GroupOrderViewSet.as_view({'post': 'create'}), name='create-group-order'),
    path('orders/group/join/', GroupOrderViewSet.as_view({'post': 'join'}), name='join-group-order'),
    path('orders/schedule/', ScheduledOrderViewSet.as_view({'post': 'create'}), name='schedule-order'),
    path('orders/template/create-order/', AdvancedOrderViewSet.as_view({'post': 'create_from_template'}), name='create-order-from-template'),
    
    # Restaurant Owner Management
    path('owner/loyalty/overview/', OwnerLoyaltyDashboardViewSet.as_view({'get': 'overview'}), name='owner-loyalty-overview'),
    path('owner/loyalty/bulk-toggle/',OwnerLoyaltyDashboardViewSet.as_view({'post': 'bulk_toggle'}), name='bulk-toggle-loyalty'),
    
    # Payment endpoints
    path('payments/create/', PaymentCreateView.as_view(), name='payment_create'),
    path('payments/<int:pk>/', PaymentDetailView.as_view(), name='payment_detail'),
    
    # Cart endpoints
    path('cart/', CartDetailView.as_view(), name='cart_detail'),
    path('cart/items/', CartItemView.as_view(), name='cart_item_add'),
    path('cart/items/<int:pk>/', CartItemUpdateView.as_view(), name='cart_item_update'),
    path('cart/items/<int:pk>/delete/', CartItemDeleteView.as_view(), name='cart_item_delete'),

    # New offer endpoints
    path('cart/apply-offer/<int:offer_id>/', CartApplyOfferView.as_view(), name='apply-offer'),
    path('cart/remove-offer/<int:offer_id>/', CartRemoveOfferView.as_view(), name='remove-offer'),
    path('cart/with-offers/', CartDetailView.as_view(), name='cart-with-offers'),

    # Sales Analytics URLs
    path('sales/analytics/', RestaurantSalesAnalyticsView.as_view(), name='sales-analytics'),
    path('sales/daily-report/', DailySalesReportView.as_view(), name='daily-sales-report'),
    path('sales/daily-report/<int:restaurant_id>/', DailySalesReportView.as_view(), name='daily-sales-report-restaurant'),
    path('sales/monthly-report/', MonthlySalesReportView.as_view(), name='monthly-sales-report'),
    path('sales/monthly-report/<int:restaurant_id>/', MonthlySalesReportView.as_view(), name='monthly-sales-report-restaurant'),
    path('sales/performance-metrics/', RestaurantPerformanceMetricsView.as_view(), name='performance-metrics'),
    path('sales/performance-metrics/<int:restaurant_id>/', RestaurantPerformanceMetricsView.as_view(), name='performance-metrics-restaurant'),
    path('sales/trends/<int:restaurant_id>/', SalesTrendsView.as_view(), name='sales-trends'),

    # Analytics endpoints
    path('analytics/customer-insights/<int:restaurant_id>/', CustomerInsightsView.as_view(), name='customer-insights'),
    path('analytics/customer-insights/', CustomerInsightsView.as_view(), name='customer-insights-all'),
    
    path('analytics/operational-metrics/<int:restaurant_id>/', OperationalMetricsView.as_view(), name='operational-metrics'),
    path('analytics/operational-metrics/', OperationalMetricsView.as_view(), name='operational-metrics-all'),
    
    path('analytics/financial-reports/<int:restaurant_id>/', FinancialReportsView.as_view(), name='financial-reports'),
    path('analytics/financial-reports/', FinancialReportsView.as_view(), name='financial-reports-all'),
    
    path('analytics/comparative/<int:restaurant_id>/', ComparativeAnalyticsView.as_view(), name='comparative-analytics'),
    path('analytics/comparative/', ComparativeAnalyticsView.as_view(), name='comparative-analytics-all'),
    
    path('analytics/export/', ExportAnalyticsView.as_view(), name='export-analytics'),
    
    path('analytics/dashboard/<int:restaurant_id>/', DashboardMetricsView.as_view(), name='dashboard-metrics'),
    path('analytics/dashboard/', DashboardMetricsView.as_view(), name='dashboard-metrics-all'),

    # Restaurant discovery and search
    path('restaurants/search/', RestaurantsSearchView.as_view(), name='restaurant-search'),
    path('restaurants/<int:restaurant_id>/availability/', RestaurantAvailabilityView.as_view(), name='restaurant-availability'),
    
    # Restaurant-specific tables
    path('restaurants/<int:restaurant_id>/tables/', 
         TableViewSet.as_view({'get': 'list'}), 
         name='restaurant-tables'),
    path('restaurants/<int:restaurant_id>/tables/check-availability/', 
         TableViewSet.as_view({'post': 'check_availability'}), 
         name='check-availability'),
    
    # Customer reservation management
    path('reservations/my/', 
         ReservationViewSet.as_view({'get': 'my_reservations'}), 
         name='my-reservations'),

    #============POS Integration Endpoints================#  
      
    # Webhook endpoints
    path('webhooks/pos/order-update/', pos_order_webhook, name='pos-order-webhook'),
    path('webhooks/pos/menu-update/', pos_menu_webhook, name='pos-menu-webhook'),
    path('webhooks/pos/inventory-update/', pos_inventory_webhook, name='pos-inventory-webhook'),

    # Additional endpoints
    path('owner/tables/status/', TableLayoutViewSet.as_view({'get': 'table_status'}), name='tables-status'),
    path('owner/kitchen/queue/', KitchenOrderViewSet.as_view({'get': 'queue'}), name='kitchen-queue'),
    path('owner/pos/sync/menu/', POSConnectionViewSet.as_view({'post': 'sync_menu'}), name='pos-sync-menu'),
    path('owner/pos/sync/inventory/', POSConnectionViewSet.as_view({'post': 'sync_inventory'}), name='pos-sync-inventory'),

    # Real-time endpoints
    path('owner/orders/<uuid:order_uuid>/route/', route_order_to_kitchen, name='route-order'),
    path('owner/orders/<uuid:order_uuid>/assign-station/', assign_order_station, name='assign-station'),
    path('owner/orders/<uuid:order_uuid>/preparation-status/', update_preparation_status, name='update-preparation-status'),

    #============end POS Integration Endpoints================# 

    # Add real-time HTTP APIs
    path('realtime/', include('api.realtime_urls')),
]


