import logging
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone
from django.db import models
from ..models import RealTimeInventory, InventoryAlert, RestaurantStaff
from .websocket_services import WebSocketService
from .notification_service import NotificationService

logger = logging.getLogger(__name__)

class InventoryService:
    """
    Service for real-time inventory management
    """
    
    @staticmethod
    def update_inventory(menu_item_id, branch_id, new_quantity, reason="", user=None):
        """Update inventory quantity and trigger notifications"""
        try:
            inventory = RealTimeInventory.objects.get(
                menu_item_id=menu_item_id,
                branch_id=branch_id
            )
            
            old_quantity = inventory.current_stock
            inventory.current_stock = new_quantity
            inventory.save()
            
            # Handle stock change events
            InventoryService.handle_stock_change(inventory, old_quantity, new_quantity, reason, user)
            
            # Broadcast inventory update
            InventoryService.broadcast_inventory_update(inventory)
            
            return inventory
            
        except RealTimeInventory.DoesNotExist:
            logger.error(f"Inventory record not found for menu_item {menu_item_id}, branch {branch_id}")
            return None
    
    @staticmethod
    def handle_stock_change(inventory, old_quantity, new_quantity, reason, user):
        """Handle inventory change events and trigger notifications"""
        # Check for stockout
        if old_quantity > 0 and new_quantity <= 0:
            InventoryService.trigger_stockout_alert(inventory, user)
        
        # Check for low stock
        elif old_quantity > inventory.low_stock_threshold and new_quantity <= inventory.low_stock_threshold:
            InventoryService.trigger_low_stock_alert(inventory, user)
        
        # Check for restock
        elif old_quantity <= 0 and new_quantity > 0:
            InventoryService.trigger_restock_notification(inventory, user)
        
        # Create alert record
        alert_type = None
        if new_quantity <= 0:
            alert_type = 'out_of_stock'
        elif new_quantity <= inventory.low_stock_threshold:
            alert_type = 'low_stock'
        
        if alert_type:
            InventoryAlert.objects.create(
                inventory=inventory,
                alert_type=alert_type,
                message=f"Stock changed from {old_quantity} to {new_quantity}. {reason}",
                previous_stock=old_quantity,
                current_stock=new_quantity
            )
    
    @staticmethod
    def trigger_stockout_alert(inventory, user):
        """Trigger notifications for stockout"""
        try:
            # Notify restaurant staff
            staff_members = RestaurantStaff.objects.filter(
                restaurant=inventory.branch.restaurant,
                is_active=True
            ).select_related('user')
            
            for staff in staff_members:
                NotificationService.create_notification(
                    user=staff.user,
                    notification_type='system',
                    title=f"Item Out of Stock",
                    message=f"{inventory.menu_item.name} is out of stock at {inventory.branch.address.city}",
                    restaurant=inventory.branch.restaurant,
                    priority='high',
                    data={
                        'menu_item_id': inventory.menu_item.item_id,
                        'menu_item_name': inventory.menu_item.name,
                        'branch_id': inventory.branch.branch_id,
                        'branch_name': f"{inventory.branch.restaurant.name} - {inventory.branch.address.city}",
                        'current_stock': inventory.current_stock,
                        'alert_type': 'stockout'
                    }
                )
            
            logger.info(f"Stockout alert triggered for {inventory.menu_item.name}")
            
        except Exception as e:
            logger.error(f"Error triggering stockout alert: {str(e)}")
    
    @staticmethod
    def trigger_low_stock_alert(inventory, user):
        """Trigger notifications for low stock"""
        try:
            # Notify restaurant staff
            staff_members = RestaurantStaff.objects.filter(
                restaurant=inventory.branch.restaurant,
                is_active=True
            ).select_related('user')
            
            for staff in staff_members:
                NotificationService.create_notification(
                    user=staff.user,
                    notification_type='system',
                    title=f"Low Stock Alert",
                    message=f"{inventory.menu_item.name} is running low at {inventory.branch.address.city}",
                    restaurant=inventory.branch.restaurant,
                    priority='medium',
                    data={
                        'menu_item_id': inventory.menu_item.item_id,
                        'menu_item_name': inventory.menu_item.name,
                        'branch_id': inventory.branch.branch_id,
                        'branch_name': f"{inventory.branch.restaurant.name} - {inventory.branch.address.city}",
                        'current_stock': inventory.current_stock,
                        'low_stock_threshold': inventory.low_stock_threshold,
                        'alert_type': 'low_stock'
                    }
                )
            
            logger.info(f"Low stock alert triggered for {inventory.menu_item.name}")
            
        except Exception as e:
            logger.error(f"Error triggering low stock alert: {str(e)}")
    
    @staticmethod
    def broadcast_inventory_update(inventory):
        """Broadcast inventory update to restaurant staff"""
        try:
            update_data = {
                'menu_item_id': inventory.menu_item.item_id,
                'branch_id': inventory.branch.branch_id,
                'current_stock': inventory.current_stock,
                'is_low_stock': inventory.is_low_stock,
                'is_out_of_stock': inventory.is_out_of_stock,
                'last_updated': inventory.last_updated.isoformat()
            }
            
            WebSocketService.broadcast_to_restaurant(
                inventory.branch.restaurant.restaurant_id,
                'inventory_update',
                update_data
            )
            
        except Exception as e:
            logger.error(f"Error broadcasting inventory update: {str(e)}")
    
    @staticmethod
    def get_branch_inventory(branch_id, low_stock_only=False):
        """Get inventory for a specific branch"""
        queryset = RealTimeInventory.objects.filter(branch_id=branch_id).select_related('menu_item')
        
        if low_stock_only:
            queryset = queryset.filter(current_stock__lte=models.F('low_stock_threshold'))
        
        return queryset
    
    @staticmethod
    def get_restaurant_inventory(restaurant_id, low_stock_only=False):
        """Get inventory for all branches of a restaurant"""
        queryset = RealTimeInventory.objects.filter(
            branch__restaurant_id=restaurant_id
        ).select_related('menu_item', 'branch')
        
        if low_stock_only:
            queryset = queryset.filter(current_stock__lte=models.F('low_stock_threshold'))
        
        return queryset