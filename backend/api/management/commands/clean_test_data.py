# management/commands/clean_test_data.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from api.models import *

User = get_user_model()

class Command(BaseCommand):
    help = 'Clean all test data'
    
    def handle(self, *args, **options):
        confirm = input('Are you sure you want to delete all test data? (yes/no): ')
        if confirm.lower() != 'yes':
            self.stdout.write(self.style.WARNING('Cancelled'))
            return
        
        # Delete in reverse order of dependencies
        models_to_clean = [
            # Analytics models
            'RestaurantSalesReport', 'DailySalesSnapshot', 'RestaurantPerformanceMetrics',
            'CustomerLifetimeValue', 'MenuItemPerformance', 'OperationalEfficiency',
            'FinancialReport', 'ComparativeAnalytics',
            
            # Real-time models
            'WebSocketConnection', 'Notification', 'NotificationPreference',
            'LiveOrderTracking', 'RealTimeInventory', 'InventoryAlert',
            
            # Order models
            'CartItemModifier', 'CartItem', 'Cart',
            'OrderItemModifier', 'OrderItem', 'OrderTracking', 'Payment', 'Order',
            
            # Advanced order models
            'GroupOrderParticipant', 'GroupOrder', 'ScheduledOrder', 'OrderTemplate',
            'BulkOrderItem', 'BulkOrder',
            
            # POS models
            'POSSyncLog', 'OrderItemPreparation', 'OrderPOSInfo', 'KitchenStation',
            'TableLayout', 'POSConnection',
            
            # Reservation models
            'TimeSlot', 'Reservation', 'Table',
            
            # Ratings and reviews
            'ReviewHelpfulVote', 'ReviewReport', 'ReviewResponse',
            'DishReview', 'RestaurantReview', 'RestaurantReviewSettings',
            'DishRating', 'RestaurantRating', 'RatingAggregate', 'OfferUsage',
            
            # Loyalty models
            'RewardRedemption', 'DiscountVoucher', 'Reward',
            'PointsTransaction', 'CustomerLoyalty', 'RestaurantLoyaltySettings',
            'MultiRestaurantLoyaltyProgram',
            
            # Personalization models
            'SimilarityMatrix', 'Recommendation', 'UserPreference', 'UserBehavior',
            
            # Referral models
            'Referral',
            
            # Push models
            'PushNotificationLog', 'PushNotificationDevice',
            
            # Menu models
            'MenuItemModifier', 'SpecialOffer', 'PopularCategory',
            'ItemModifier', 'ItemModifierGroup', 'MenuItem', 'MenuCategory',
            'ItemAssociation', 'PopularitySnapshot',
            
            # Restaurant models
            'Branch', 'Restaurant', 'Address',
            
            # User models
            'RestaurantOwnership', 'RestaurantStaff', 'Customer', 'User',
            
            # Menu models (cuisines last)
            'Cuisine',
        ]
        
        for model_name in models_to_clean:
            try:
                model = globals().get(model_name)
                if model:
                    count = model.objects.count()
                    model.objects.all().delete()
                    self.stdout.write(f'Deleted {count} {model_name}')
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Could not delete {model_name}: {str(e)}'))
        
        # Also delete test users by email pattern
        test_users = User.objects.filter(email__contains='@example.com')
        test_users_count = test_users.count()
        test_users.delete()
        
        self.stdout.write(self.style.SUCCESS(f'✅ Cleaned {test_users_count} test users'))
        self.stdout.write(self.style.SUCCESS('🎯 All test data cleaned successfully'))