# pos_integration_models.py
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from encrypted_model_fields.fields import EncryptedCharField
import uuid

class POSConnection(models.Model):
    POS_TYPES = (
        ('square', 'Square'),
        ('toast', 'Toast'),
        ('lightspeed', 'Lightspeed'),
        ('clover', 'Clover'),
        ('shopify', 'Shopify'),
        ('custom', 'Custom POS'),
    )
    
    SYNC_STATUS_CHOICES = (
        ('syncing', 'Syncing'),
        ('connected', 'Connected'),
        ('error', 'Error'),
        ('disconnected', 'Disconnected'),
        ('pending', 'Pending Setup'),
    )
    
    connection_id = models.AutoField(primary_key=True)
    restaurant = models.ForeignKey(
        'api.Restaurant',
        on_delete=models.CASCADE,
        related_name='pos_connections'
    )
    pos_type = models.CharField(max_length=20, choices=POS_TYPES)
    connection_name = models.CharField(max_length=100, help_text="Friendly name for this connection")
    
    # API Credentials (encrypted)
    api_key = EncryptedCharField(max_length=500)
    api_secret = EncryptedCharField(max_length=500, blank=True, null=True)
    access_token = EncryptedCharField(max_length=1000, blank=True, null=True)
    refresh_token = EncryptedCharField(max_length=1000, blank=True, null=True)
    
    # Custom POS configuration
    base_url = models.URLField(blank=True, null=True, help_text="For custom POS systems")
    merchant_id = models.CharField(max_length=100, blank=True, null=True)
    location_id = models.CharField(max_length=100, blank=True, null=True)
    
    # Connection status
    is_active = models.BooleanField(default=True)
    sync_status = models.CharField(max_length=20, choices=SYNC_STATUS_CHOICES, default='pending')
    last_sync = models.DateTimeField(null=True, blank=True)
    last_successful_sync = models.DateTimeField(null=True, blank=True)
    
    # Sync settings
    auto_sync_menu = models.BooleanField(default=False)
    auto_sync_inventory = models.BooleanField(default=False)
    auto_sync_orders = models.BooleanField(default=True)
    sync_frequency = models.IntegerField(default=15, help_text="Sync frequency in minutes")
    
    # Error handling
    last_error = models.TextField(blank=True, null=True)
    error_count = models.IntegerField(default=0)
    retry_count = models.IntegerField(default=0)
    
    # Webhook configuration
    webhook_url = models.URLField(blank=True, null=True)
    webhook_secret = models.CharField(max_length=100, blank=True, null=True)
    webhook_registered = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'pos_connections'
        ordering = ['-is_active', '-created_at']
        unique_together = ['restaurant', 'pos_type']
        indexes = [
            models.Index(fields=['restaurant', 'is_active']),
            models.Index(fields=['sync_status', 'last_sync']),
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.get_pos_type_display()}"

    def save(self, *args, **kwargs):
        if not self.connection_name:
            self.connection_name = f"{self.get_pos_type_display()} - {self.restaurant.name}"
        super().save(*args, **kwargs)

    def get_active_service(self):
        """Get the active POS service instance"""
        from ..services.pos_services import POSServiceFactory
        return POSServiceFactory.get_service(self.pos_type, self)
    
    def can_sync(self):
        """Check if connection can perform sync operations"""
        return (self.is_active and 
                self.sync_status in ['connected', 'syncing'] and 
                self.last_error is None)

    def test_connection(self):
        """Test POS connection"""
        from ..services.pos_services import POSServiceFactory
        
        try:
            pos_service = POSServiceFactory.get_service(self.pos_type, self)
            success, message = pos_service.test_connection()
            
            if success:
                self.sync_status = 'connected'
                self.last_successful_sync = timezone.now()
                self.error_count = 0
            else:
                self.sync_status = 'error'
                self.last_error = message
                self.error_count += 1
            
            self.save()
            return success, message
            
        except Exception as e:
            self.sync_status = 'error'
            self.last_error = str(e)
            self.error_count += 1
            self.save()
            return False, str(e)

    def sync_menu_items(self):
        """Sync menu items from POS"""
        from ..services.pos_services import POSServiceFactory
        
        try:
            self.sync_status = 'syncing'
            self.save()
            
            pos_service = POSServiceFactory.get_service(self.pos_type, self)
            success, stats = pos_service.sync_menu_items()
            
            if success:
                self.sync_status = 'connected'
                self.last_successful_sync = timezone.now()
                self.last_sync = timezone.now()
                self.error_count = 0
            else:
                self.sync_status = 'error'
                self.error_count += 1
            
            self.save()
            return success, stats
            
        except Exception as e:
            self.sync_status = 'error'
            self.last_error = str(e)
            self.error_count += 1
            self.save()
            return False, {'error': str(e)}

    def sync_inventory(self):
        """Sync inventory from POS"""
        from ..services.pos_services import POSServiceFactory
        
        try:
            self.sync_status = 'syncing'
            self.save()
            
            pos_service = POSServiceFactory.get_service(self.pos_type, self)
            success, stats = pos_service.sync_inventory()
            
            if success:
                self.sync_status = 'connected'
                self.last_successful_sync = timezone.now()
                self.last_sync = timezone.now()
                self.error_count = 0
            else:
                self.sync_status = 'error'
                self.error_count += 1
            
            self.save()
            return success, stats
            
        except Exception as e:
            self.sync_status = 'error'
            self.last_error = str(e)
            self.error_count += 1
            self.save()
            return False, {'error': str(e)}

    def register_webhook(self):
        """Register webhook with POS system"""
        from ..services.pos_services import POSServiceFactory
        
        try:
            pos_service = POSServiceFactory.get_service(self.pos_type, self)
            success = pos_service.register_webhook()
            
            self.webhook_registered = success
            self.save()
            return success
            
        except Exception as e:
            self.last_error = f"Webhook registration failed: {str(e)}"
            self.save()
            return False

class TableLayout(models.Model):
    LAYOUT_TYPES = (
        ('main_dining', 'Main Dining'),
        ('outdoor', 'Outdoor'),
        ('private', 'Private Room'),
        ('bar', 'Bar Area'),
        ('custom', 'Custom'),
    )
    
    layout_id = models.AutoField(primary_key=True)
    restaurant = models.ForeignKey(
        'api.Restaurant',
        on_delete=models.CASCADE,
        related_name='table_layouts'
    )
    branch = models.ForeignKey(
        'api.Branch',
        on_delete=models.CASCADE,
        related_name='table_layouts',
        null=True,
        blank=True
    )
    
    # Layout details
    layout_name = models.CharField(max_length=100)
    layout_type = models.CharField(max_length=20, choices=LAYOUT_TYPES, default='main_dining')
    layout_data = models.JSONField(default=dict, help_text="Table positioning and metadata")
    
    # QR Code configuration
    qr_codes = models.JSONField(default=dict, help_text="Table number to QR code mapping")
    qr_base_url = models.URLField(help_text="Base URL for QR codes")
    
    # Status
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'table_layouts'
        ordering = ['branch', 'layout_name']
        unique_together = ['restaurant', 'layout_name']
        indexes = [
            models.Index(fields=['restaurant', 'is_active']),
            models.Index(fields=['branch', 'is_default']),
        ]

    def __str__(self):
        branch_name = f" - {self.branch.address.city}" if self.branch else ""
        return f"{self.layout_name}{branch_name} - {self.restaurant.name}"

    def save(self, *args, **kwargs):
        # Ensure only one default layout per branch
        if self.is_default and self.branch:
            TableLayout.objects.filter(
                branch=self.branch, 
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    def generate_qr_codes(self):
        """Generate QR codes for all tables in layout"""
        import qrcode
        from io import BytesIO
        from django.core.files.base import ContentFile
        from django.urls import reverse
        
        self.qr_codes = {}
        
        for table_data in self.layout_data.get('tables', []):
            table_number = table_data.get('number')
            if table_number:
                # Generate QR code data
                qr_data = f"{self.qr_base_url}?table={table_number}&layout={self.layout_id}"
                
                # Create QR code
                qr = qrcode.QRCode(version=1, box_size=10, border=5)
                qr.add_data(qr_data)
                qr.make(fit=True)
                
                img = qr.make_image(fill_color="black", back_color="white")
                
                # Save to buffer
                buffer = BytesIO()
                img.save(buffer, format='PNG')
                
                # Store in QR codes field
                self.qr_codes[table_number] = {
                    'data': qr_data,
                    'image_data': buffer.getvalue().hex()
                }
        
        self.save()
        return True
    
    def get_active_tables(self):
        """Get all active tables with current status"""
        tables_with_status = []
        for table_data in self.layout_data.get('tables', []):
            table_number = table_data.get('number')
            if table_number:
                status = self.get_table_status(table_number)
                tables_with_status.append({
                    **table_data,
                    'current_status': status
                })
        return tables_with_status
    
    def get_available_tables(self, party_size=None):
        """Get available tables filtered by party size"""
        available_tables = []
        for table_data in self.layout_data.get('tables', []):
            table_number = table_data.get('number')
            capacity = table_data.get('capacity', 0)
            
            if (table_number and 
                self.get_table_status(table_number).get('status') == 'available' and
                (party_size is None or capacity >= party_size)):
                
                available_tables.append(table_data)
        
        return available_tables

    def get_table_status(self, table_number):
        """Get current status of a specific table"""
        from .reservation_models import Reservation
        from django.utils import timezone
        
        now = timezone.now()
        current_time = now.time()
        today = now.date()
        
        # Check for active reservations
        active_reservation = Reservation.objects.filter(
            table__table_number=table_number,
            reservation_date=today,
            status__in=['confirmed', 'seated'],
            reservation_time__lte=current_time
        ).first()
        
        if active_reservation:
            return {
                'status': 'occupied',
                'reservation': active_reservation.reservation_code,
                'party_size': active_reservation.party_size,
                'estimated_end': active_reservation.end_time
            }
        
        # Check for upcoming reservations
        upcoming_reservation = Reservation.objects.filter(
            table__table_number=table_number,
            reservation_date=today,
            status='confirmed',
            reservation_time__gt=current_time,
            reservation_time__lte=(now + timezone.timedelta(hours=1)).time()
        ).first()
        
        if upcoming_reservation:
            return {
                'status': 'reserved',
                'reservation': upcoming_reservation.reservation_code,
                'party_size': upcoming_reservation.party_size,
                'reservation_time': upcoming_reservation.reservation_time
            }
        
        return {'status': 'available'}

class KitchenStation(models.Model):
    STATION_TYPES = (
        ('grill', 'Grill Station'),
        ('fryer', 'Fryer Station'),
        ('salad', 'Salad Station'),
        ('pizza', 'Pizza Station'),
        ('dessert', 'Dessert Station'),
        ('beverage', 'Beverage Station'),
        ('expediter', 'Expediter Station'),
        ('general', 'General Kitchen'),
    )
    
    station_id = models.AutoField(primary_key=True)
    restaurant = models.ForeignKey(
        'api.Restaurant',
        on_delete=models.CASCADE,
        related_name='kitchen_stations'
    )
    branch = models.ForeignKey(
        'api.Branch',
        on_delete=models.CASCADE,
        related_name='kitchen_stations',
        null=True,
        blank=True
    )
    
    # Station details
    name = models.CharField(max_length=100)
    station_type = models.CharField(max_length=20, choices=STATION_TYPES)
    description = models.TextField(blank=True, null=True)
    
    # Capacity and timing
    max_concurrent_items = models.IntegerField(default=5, help_text="Maximum items station can handle simultaneously")
    avg_prep_time = models.IntegerField(default=15, help_text="Average preparation time in minutes")
    is_available = models.BooleanField(default=True)
    
    # Staff assignment
    assigned_staff = models.ManyToManyField(
        'api.RestaurantStaff',
        related_name='kitchen_stations',
        blank=True
    )
    
    # Menu items this station handles
    assigned_categories = models.ManyToManyField(
        'api.MenuCategory',
        related_name='kitchen_stations',
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'kitchen_stations'
        ordering = ['branch', 'station_type', 'name']
        indexes = [
            models.Index(fields=['restaurant', 'is_available']),
            models.Index(fields=['branch', 'station_type']),
        ]

    def __str__(self):
        branch_name = f" - {self.branch.address.city}" if self.branch else ""
        return f"{self.name}{branch_name} - {self.restaurant.name}"
    
    def get_active_items(self):
        """Get currently active items at this station"""
        from .pos_integration_models import OrderItemPreparation
        return OrderItemPreparation.objects.filter(
            assigned_station=self,
            preparation_status__in=['pending', 'preparing']
        ).select_related('order_item__order', 'order_item__menu_item')
    
    def get_completion_rate(self):
        """Get historical completion rate for this station"""
        from .pos_integration_models import OrderItemPreparation
        from django.db.models import Count, Q
        
        stats = OrderItemPreparation.objects.filter(
            assigned_station=self
        ).aggregate(
            total=Count('id'),
            completed=Count('id', filter=Q(preparation_status='ready')),
            failed=Count('id', filter=Q(preparation_status='cancelled'))
        )
        
        total = stats['total'] or 1
        completed = stats['completed'] or 0
        
        return {
            'completion_rate': (completed / total) * 100,
            'total_items': total,
            'completed_items': completed,
            'failed_items': stats['failed'] or 0
        }

    def get_current_workload(self):
        """Get current workload for this station"""
        from .order_models import OrderItem
        from django.utils import timezone
        
        # Count active items assigned to this station
        active_items = OrderItem.objects.filter(
            order__restaurant=self.restaurant,
            order__status__in=['confirmed', 'preparing'],
            station_assignments__station=self
        ).count()
        
        workload_percentage = (active_items / self.max_concurrent_items) * 100
        return {
            'active_items': active_items,
            'max_capacity': self.max_concurrent_items,
            'workload_percentage': workload_percentage,
            'status': 'overloaded' if workload_percentage > 90 else 
                     'busy' if workload_percentage > 70 else 
                     'moderate' if workload_percentage > 40 else 'available'
        }

    def can_accept_item(self, menu_item):
        """Check if station can accept a new menu item"""
        workload = self.get_current_workload()
        
        # Check if station handles this item type
        item_categories = menu_item.categories.all()
        station_categories = self.assigned_categories.all()
        
        category_match = any(cat in station_categories for cat in item_categories)
        
        return (workload['status'] != 'overloaded' and 
                self.is_available and 
                category_match)

# Enhanced Order model (add these fields to existing Order model)
class OrderPOSInfo(models.Model):
    """Extended POS information for orders"""
    order = models.OneToOneField(
        'api.Order',
        on_delete=models.CASCADE,
        related_name='pos_info'
    )
    
    # POS integration fields
    pos_order_id = models.CharField(max_length=100, blank=True, null=True, help_text="POS system's order reference")
    pos_location_id = models.CharField(max_length=100, blank=True, null=True)
    pos_employee_id = models.CharField(max_length=100, blank=True, null=True)
    
    # Enhanced dine-in information
    table_number = models.CharField(max_length=20, blank=True, null=True)
    table_layout = models.ForeignKey(
        TableLayout,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )
    
    # Kitchen routing
    station_assignments = models.JSONField(
        default=dict,
        help_text="Kitchen station assignments: {station_id: [item_ids]}"
    )
    
    # Enhanced preparation tracking
    preparation_started_at = models.DateTimeField(null=True, blank=True)
    estimated_ready_at = models.DateTimeField(null=True, blank=True)
    actual_ready_at = models.DateTimeField(null=True, blank=True)
    
    # POS sync status
    pos_sync_status = models.CharField(
        max_length=20,
        choices=(
            ('pending', 'Pending Sync'),
            ('synced', 'Synced to POS'),
            ('failed', 'Sync Failed'),
            ('not_required', 'Not Required'),
        ),
        default='pending'
    )
    last_sync_attempt = models.DateTimeField(null=True, blank=True)
    sync_errors = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'order_pos_info'
        indexes = [
            models.Index(fields=['pos_order_id']),
            models.Index(fields=['pos_sync_status']),
            models.Index(fields=['table_number']),
        ]

    def __str__(self):
        return f"POS Info - Order #{self.order.order_uuid}"

    def sync_to_pos(self):
        """Sync order to POS system"""
        from ..services.pos_services import POSServiceFactory
        
        try:
            active_connection = self.order.restaurant.pos_connections.filter(
                is_active=True, 
                sync_status='connected'
            ).first()
            
            if not active_connection:
                self.pos_sync_status = 'not_required'
                self.save()
                return True, "No active POS connection"
            
            pos_service = POSServiceFactory.get_service(active_connection.pos_type, active_connection)
            success, pos_order_id = pos_service.create_order(self.order)
            
            if success:
                self.pos_order_id = pos_order_id
                self.pos_sync_status = 'synced'
                self.last_sync_attempt = timezone.now()
            else:
                self.pos_sync_status = 'failed'
                self.sync_errors.append({
                    'timestamp': timezone.now().isoformat(),
                    'error': "Failed to sync order to POS"
                })
                self.last_sync_attempt = timezone.now()
            
            self.save()
            return success, pos_order_id if success else "Sync failed"
            
        except Exception as e:
            self.pos_sync_status = 'failed'
            self.sync_errors.append({
                'timestamp': timezone.now().isoformat(),
                'error': str(e)
            })
            self.last_sync_attempt = timezone.now()
            self.save()
            return False, str(e)
        
    def get_kitchen_status(self):
        """Get comprehensive kitchen status for this order"""
        items = self.order.order_items.all()
        status_summary = {
            'pending': 0,
            'preparing': 0,
            'ready': 0,
            'served': 0,
            'cancelled': 0,
            'total': items.count()
        }
        
        for item in items:
            if hasattr(item, 'preparation_info'):
                status = item.preparation_info.preparation_status
                status_summary[status] = status_summary.get(status, 0) + 1
        
        status_summary['completion_percentage'] = (
            (status_summary['ready'] + status_summary['served']) / status_summary['total'] * 100
            if status_summary['total'] > 0 else 0
        )
        
        return status_summary
    
    def get_station_assignments_detail(self):
        """Get detailed station assignments"""
        from .pos_integration_models import KitchenStation
        detailed_assignments = {}
        
        for station_id, item_ids in self.station_assignments.items():
            try:
                station = KitchenStation.objects.get(station_id=station_id)
                items = self.order.order_items.filter(order_item_id__in=item_ids)
                
                detailed_assignments[station.name] = {
                    'station': {
                        'id': station.station_id,
                        'name': station.name,
                        'type': station.station_type
                    },
                    'items': [
                        {
                            'id': item.order_item_id,
                            'name': item.menu_item.name,
                            'quantity': item.quantity,
                            'status': item.preparation_info.preparation_status if hasattr(item, 'preparation_info') else 'pending'
                        }
                        for item in items
                    ],
                    'item_count': len(item_ids)
                }
            except KitchenStation.DoesNotExist:
                continue
        
        return detailed_assignments

# Enhanced OrderItem model (add these fields)
class OrderItemPreparation(models.Model):
    """Extended preparation information for order items"""
    order_item = models.OneToOneField(
        'api.OrderItem',
        on_delete=models.CASCADE,
        related_name='preparation_info'
    )
    
    # Station assignment
    assigned_station = models.ForeignKey(
        KitchenStation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_items'
    )
    
    # Preparation tracking
    preparation_status = models.CharField(
        max_length=20,
        choices=(
            ('pending', 'Pending'),
            ('preparing', 'Preparing'),
            ('ready', 'Ready'),
            ('served', 'Served'),
        ),
        default='pending'
    )
    preparation_started_at = models.DateTimeField(null=True, blank=True)
    estimated_completion_at = models.DateTimeField(null=True, blank=True)
    actual_completion_at = models.DateTimeField(null=True, blank=True)
    
    # Quality control
    quality_check_passed = models.BooleanField(null=True, blank=True)
    quality_notes = models.TextField(blank=True, null=True)
    checked_by = models.ForeignKey(
        'api.RestaurantStaff',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'order_item_preparation'
        indexes = [
            models.Index(fields=['preparation_status']),
            models.Index(fields=['assigned_station', 'preparation_status']),
        ]

    def __str__(self):
        return f"Prep - {self.order_item.menu_item.name} - Order #{self.order_item.order.order_uuid}"

    def assign_to_station(self, station):
        """Assign item to kitchen station"""
        from django.utils import timezone
        from datetime import timedelta
        
        self.assigned_station = station
        self.preparation_status = 'preparing'
        self.preparation_started_at = timezone.now()
        self.estimated_completion_at = timezone.now() + timedelta(
            minutes=station.avg_prep_time
        )
        self.save()
        
        # Update order's station assignments
        pos_info, created = OrderPOSInfo.objects.get_or_create(order=self.order_item.order)
        station_assignments = pos_info.station_assignments
        
        if str(station.station_id) not in station_assignments:
            station_assignments[str(station.station_id)] = []
        
        if self.order_item.order_item_id not in station_assignments[str(station.station_id)]:
            station_assignments[str(station.station_id)].append(self.order_item.order_item_id)
        
        pos_info.station_assignments = station_assignments
        pos_info.save()

    def mark_ready(self, quality_notes=None, checked_by=None):
        """Mark item as ready for serving"""
        from django.utils import timezone
        
        self.preparation_status = 'ready'
        self.actual_completion_at = timezone.now()
        self.quality_notes = quality_notes
        self.checked_by = checked_by
        
        if quality_notes:
            self.quality_check_passed = True
        
        self.save()
        
        # Check if all items in order are ready
        all_items_ready = not self.order_item.order.order_items.filter(
            preparation_info__preparation_status__in=['pending', 'preparing']
        ).exists()
        
        if all_items_ready:
            pos_info = getattr(self.order_item.order, 'pos_info', None)
            if pos_info:
                pos_info.actual_ready_at = timezone.now()
                pos_info.save()

class POSSyncLog(models.Model):
    """Log for POS synchronization activities"""
    log_id = models.AutoField(primary_key=True)
    connection = models.ForeignKey(
        POSConnection,
        on_delete=models.CASCADE,
        related_name='sync_logs'
    )
    
    # Sync details
    sync_type = models.CharField(
        max_length=20,
        choices=(
            ('menu', 'Menu Sync'),
            ('inventory', 'Inventory Sync'),
            ('order', 'Order Sync'),
            ('customer', 'Customer Sync'),
            ('webhook', 'Webhook Processing'),
        )
    )
    status = models.CharField(
        max_length=20,
        choices=(
            ('success', 'Success'),
            ('partial', 'Partial Success'),
            ('failed', 'Failed'),
        )
    )
    
    # Statistics
    items_processed = models.IntegerField(default=0)
    items_created = models.IntegerField(default=0)
    items_updated = models.IntegerField(default=0)
    items_failed = models.IntegerField(default=0)
    
    # Error details
    error_message = models.TextField(blank=True, null=True)
    stack_trace = models.TextField(blank=True, null=True)
    
    # Timing
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = 'pos_sync_logs'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['connection', 'sync_type']),
            models.Index(fields=['started_at']),
        ]

    def __str__(self):
        return f"{self.get_sync_type_display()} - {self.connection} - {self.started_at}"

    def save(self, *args, **kwargs):
        if self.completed_at and self.started_at:
            self.duration_seconds = (self.completed_at - self.started_at).total_seconds()
        super().save(*args, **kwargs)