# management/commands/clean_db.py
from django.core.management.base import BaseCommand
from django.db import connection
from django.apps import apps
from django.core.management import call_command
import time

class Command(BaseCommand):
    help = 'Completely clean the database in the correct order (SQLite compatible)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm deletion (required to prevent accidental data loss)'
        )
        parser.add_argument(
            '--skip-input',
            action='store_true',
            help='Skip interactive confirmation prompt'
        )
        parser.add_argument(
            '--keep-superuser',
            action='store_true',
            default=True,
            help='Keep the superuser account'
        )
    
    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(self.style.ERROR('=' * 60))
            self.stdout.write(self.style.ERROR('⚠️  DANGER: This will delete ALL data in your database!'))
            self.stdout.write(self.style.ERROR('=' * 60))
            self.stdout.write('\nTo proceed, run with --confirm flag:')
            self.stdout.write('  python manage.py clean_db --confirm\n')
            return
        
        if not options['skip_input']:
            confirm = input('\n⚠️  Are you ABSOLUTELY sure? Type "DELETE ALL" to confirm: ')
            if confirm != 'DELETE ALL':
                self.stdout.write(self.style.WARNING('Operation cancelled.'))
                return
        
        start_time = time.time()
        
        self.stdout.write(self.style.WARNING('\n' + '=' * 60))
        self.stdout.write(self.style.WARNING('🗑️  CLEANING DATABASE (SQLite)...'))
        self.stdout.write(self.style.WARNING('=' * 60))
        
        # Define deletion order (from most dependent to least dependent)
        deletion_order = [
            # Real-time and tracking data
            'WebSocketConnection',
            'LiveOrderTracking',
            'InventoryAlert',
            'RealTimeInventory',
            
            # Loyalty and rewards
            'PointsTransaction',
            'RewardRedemption',
            'DiscountVoucher',
            'Referral',
            'OfferUsage',
            
            # Reviews and ratings
            'ReviewHelpfulVote',
            'ReviewReport',
            'ReviewResponse',
            'DishRating',
            'DishReview',
            'RestaurantRating',
            'RestaurantReview',
            
            # Orders and order items
            'OrderItemPreparation',
            'OrderPOSInfo',
            'OrderTracking',
            'Payment',
            'OrderItemModifier',
            'OrderItem',
            'Order',
            
            # Cart data
            'CartItemModifier',
            'CartItem',
            'Cart',
            
            # Reservations
            'Reservation',
            'TimeSlot',
            'Table',
            
            # Menu and offers
            'SpecialOffer',
            'MenuItemModifier',
            'ItemModifier',
            'ItemModifierGroup',
            'MenuItem',
            'MenuCategory',
            
            # Analytics
            'CustomerLifetimeValue',
            'FinancialReport',
            'OperationalEfficiency',
            'MenuItemPerformance',
            'RestaurantSalesReport',
            'DailySalesSnapshot',
            'ComparativeAnalytics',
            
            # Personalization
            'SimilarityMatrix',
            'Recommendation',
            'UserBehavior',
            'UserPreference',
            
            # Restaurant and branch data
            'RestaurantLoyaltySettings',
            'Branch',
            'POSConnection',
            'POSSyncLog',
            'KitchenStation',
            'TableLayout',
            
            # Customer and loyalty profiles
            'CustomerLoyalty',
            'Customer',
            
            # Staff and ownership
            'RestaurantStaff',
            'RestaurantOwnership',
            'RestaurantPerformanceMetrics',
            'RestaurantReviewSettings',
            'PopularCategory',
            'PopularitySnapshot',
            'ItemAssociation',
            'RatingAggregate',
            
            # Core restaurant data
            'Restaurant',
            'Address',
            
            # Users (keep superuser)
            'User',
            
            # Base data
            'MultiRestaurantLoyaltyProgram',
            'PushNotificationDevice',
            'PushNotificationLog',
            'Notification',
            'NotificationPreference',
            'Cuisine',
        ]
        
        deleted_counts = {}
        errors = []
        
        # Disable foreign key checks for SQLite
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA foreign_keys = OFF;")
        
        for model_name in deletion_order:
            try:
                # Try to get the model from api app
                try:
                    model = apps.get_model('api', model_name)
                except LookupError:
                    # Try with different app names if needed
                    model = None
                    for app in ['api', 'your_app_name']:  # Add your app name if different
                        try:
                            model = apps.get_model(app, model_name)
                            if model:
                                break
                        except LookupError:
                            continue
                
                if model:
                    count = model.objects.count()
                    if count > 0:
                        # For User model, exclude superuser if requested
                        if model_name == 'User' and options['keep_superuser']:
                            deleted, _ = model.objects.exclude(is_superuser=True).delete()
                            kept = model.objects.filter(is_superuser=True).count()
                            self.stdout.write(f"  Deleted {deleted} users, kept {kept} superuser(s)")
                            deleted_counts[model_name] = deleted
                        else:
                            deleted, _ = model.objects.all().delete()
                            self.stdout.write(f"  Deleted {deleted} {model_name}")
                            deleted_counts[model_name] = deleted
                    else:
                        self.stdout.write(f"  Skipped {model_name} (already empty)")
                else:
                    self.stdout.write(f"  ⚠️ Model not found: {model_name}")
                    
            except Exception as e:
                error_msg = f"Error deleting {model_name}: {str(e)}"
                self.stdout.write(self.style.ERROR(f"  ✗ {error_msg}"))
                errors.append(error_msg)
        
        # Re-enable foreign key checks
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA foreign_keys = ON;")
        
        # Reset SQLite auto-increment sequences
        self.stdout.write("\n🔄 Resetting auto-increment sequences...")
        try:
            with connection.cursor() as cursor:
                # Get all tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
                tables = cursor.fetchall()
                
                for table in tables:
                    table_name = table[0]
                    # Skip Django internal tables
                    if table_name.startswith('django_') or table_name.startswith('auth_'):
                        continue
                    try:
                        # Reset sequence for SQLite
                        cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table_name}';")
                    except Exception:
                        pass
            self.stdout.write("  Sequences reset successfully")
        except Exception as e:
            self.stdout.write(f"  ⚠️ Could not reset sequences: {str(e)}")
        
        elapsed_time = time.time() - start_time
        
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 60))
        self.stdout.write(self.style.SUCCESS('✅ DATABASE CLEANING COMPLETE!'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(f"\n📊 Summary:")
        total_deleted = 0
        for model_name, count in deleted_counts.items():
            if count > 0:
                self.stdout.write(f"  - {model_name}: {count} records deleted")
                total_deleted += count
        
        self.stdout.write(f"\n📊 Total records deleted: {total_deleted}")
        self.stdout.write(f"⏱️  Time taken: {elapsed_time:.2f} seconds")
        
        if errors:
            self.stdout.write(f"\n⚠️ Errors encountered: {len(errors)}")
            for error in errors[:5]:
                self.stdout.write(f"  - {error}")
        
        self.stdout.write(self.style.SUCCESS('\n✨ Database is now clean and ready for new data!'))
        self.stdout.write('\nTo repopulate, run:')
        self.stdout.write('  python manage.py populate_all')


class CommandFast(BaseCommand):
    """Alternative: Fast SQLite clean using raw SQL"""
    help = 'Fast clean using raw SQL (SQLite optimized)'
    
    def add_arguments(self, parser):
        parser.add_argument('--confirm', action='store_true', help='Confirm deletion')
        parser.add_argument('--keep-superuser', action='store_true', default=True)
    
    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(self.style.ERROR('⚠️  Use --confirm to proceed'))
            return
        
        from django.db import connection
        
        self.stdout.write(self.style.WARNING('\n🗑️  FAST CLEANING DATABASE (SQLite)...'))
        
        with connection.cursor() as cursor:
            # Disable foreign keys
            cursor.execute("PRAGMA foreign_keys = OFF;")
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name NOT LIKE 'django_%' AND name NOT LIKE 'auth_%';")
            tables = cursor.fetchall()
            
            deleted_totals = {}
            
            for table in tables:
                table_name = table[0]
                try:
                    if options['keep_superuser'] and table_name == 'users':
                        cursor.execute("DELETE FROM users WHERE is_superuser = 0;")
                    else:
                        cursor.execute(f"DELETE FROM {table_name};")
                    
                    deleted_totals[table_name] = cursor.rowcount
                    if cursor.rowcount > 0:
                        self.stdout.write(f"  Cleared {cursor.rowcount} rows from {table_name}")
                        
                except Exception as e:
                    self.stdout.write(f"  ⚠️ Could not clear {table_name}: {str(e)}")
            
            # Reset sequences
            cursor.execute("DELETE FROM sqlite_sequence;")
            
            # Re-enable foreign keys
            cursor.execute("PRAGMA foreign_keys = ON;")
        
        total_deleted = sum(deleted_totals.values())
        self.stdout.write(self.style.SUCCESS(f'\n✅ FAST CLEAN COMPLETE! {total_deleted} total records deleted'))