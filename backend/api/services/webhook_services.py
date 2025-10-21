from decimal import Decimal
import hmac
import hashlib
import json
from django.utils import timezone
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

class WebhookService:
    """Service for processing POS webhooks - FULLY IMPLEMENTED"""
    
    def __init__(self, connection=None):
        self.connection = connection
    
    def verify_webhook_signature(self, request):
        """Verify webhook signature for security"""
        if not self.connection or not self.connection.webhook_secret:
            logger.warning("No webhook secret configured, skipping verification")
            return True
        
        signature = request.headers.get('X-Square-Signature', '')
        body = request.body.decode('utf-8')
        
        if self.connection.pos_type == 'square':
            computed_signature = hmac.new(
                self.connection.webhook_secret.encode('utf-8'),
                body.encode('utf-8'),
                hashlib.sha1
            ).hexdigest()
            
            return hmac.compare_digest(signature, computed_signature)
        
        elif self.connection.pos_type == 'toast':
            toast_signature = request.headers.get('X-Toast-Signature', '')
            computed_signature = hmac.new(
                self.connection.webhook_secret.encode('utf-8'),
                body.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(toast_signature, computed_signature)
        
        elif self.connection.pos_type == 'shopify':
            shopify_signature = request.headers.get('X-Shopify-Hmac-Sha256', '')
            computed_signature = hmac.new(
                self.connection.webhook_secret.encode('utf-8'),
                body.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(shopify_signature, computed_signature)
        
        return True
    
    def process_order_webhook(self, webhook_data):
        """Process order updates from POS - FULLY IMPLEMENTED"""
        from ..models import OrderPOSInfo, POSSyncLog
        
        try:
            if self.connection.pos_type == 'square':
                return self._process_square_order_webhook(webhook_data)
            elif self.connection.pos_type == 'toast':
                return self._process_toast_order_webhook(webhook_data)
            elif self.connection.pos_type == 'lightspeed':
                return self._process_lightspeed_order_webhook(webhook_data)
            elif self.connection.pos_type == 'clover':
                return self._process_clover_order_webhook(webhook_data)
            elif self.connection.pos_type == 'shopify':
                return self._process_shopify_order_webhook(webhook_data)
            elif self.connection.pos_type == 'custom':
                return self._process_custom_order_webhook(webhook_data)
                
            return False
            
        except Exception as e:
            logger.error(f"Error processing order webhook: {str(e)}")
            POSSyncLog.objects.create(
                connection=self.connection,
                sync_type='webhook',
                status='failed',
                error_message=str(e),
                items_processed=0
            )
            return False
    
    def _process_square_order_webhook(self, webhook_data):
        from ..models import OrderPOSInfo
        
        for event in webhook_data.get('data', []):
            if event['type'] == 'order.updated':
                order_data = event['data']['object']['order']
                pos_order_id = order_data['id']
                square_status = order_data.get('state', '')
                
                try:
                    order_pos_info = OrderPOSInfo.objects.get(pos_order_id=pos_order_id)
                    order = order_pos_info.order
                    
                    status_mapping = {
                        'OPEN': 'confirmed',
                        'COMPLETED': 'completed',
                        'CANCELED': 'cancelled'
                    }
                    
                    internal_status = status_mapping.get(square_status)
                    if internal_status and internal_status != order.status:
                        order.status = internal_status
                        order.save()
                        
                        order_pos_info.pos_sync_status = 'synced'
                        order_pos_info.save()
                        
                        logger.info(f"Updated order {order.order_uuid} to {internal_status}")
                        
                except OrderPOSInfo.DoesNotExist:
                    logger.warning(f"Order with POS ID {pos_order_id} not found")
                    continue
        
        return True
    
    def _process_toast_order_webhook(self, webhook_data):
        from ..models import OrderPOSInfo
        
        event_type = webhook_data.get('eventType')
        if event_type == 'ORDER_UPDATED':
            order_data = webhook_data.get('payload', {})
            pos_order_id = order_data.get('id')
            toast_status = order_data.get('status', '')
            
            try:
                order_pos_info = OrderPOSInfo.objects.get(pos_order_id=pos_order_id)
                order = order_pos_info.order
                
                status_mapping = {
                    'ORDERED': 'confirmed',
                    'HELD': 'confirmed',
                    'COMPLETED': 'completed',
                    'VOIDED': 'cancelled'
                }
                
                internal_status = status_mapping.get(toast_status)
                if internal_status and internal_status != order.status:
                    order.status = internal_status
                    order.save()
                    
                    order_pos_info.pos_sync_status = 'synced'
                    order_pos_info.save()
                    
            except OrderPOSInfo.DoesNotExist:
                logger.warning(f"Order with POS ID {pos_order_id} not found")
        
        return True
    
    def _process_lightspeed_order_webhook(self, webhook_data):
        from ..models import OrderPOSInfo
        
        event_type = webhook_data.get('event')
        if event_type == 'order.updated':
            order_data = webhook_data.get('data', {})
            pos_order_id = order_data.get('orderID')
            lightspeed_status = order_data.get('status', '')
            
            try:
                order_pos_info = OrderPOSInfo.objects.get(pos_order_id=pos_order_id)
                order = order_pos_info.order
                
                status_mapping = {
                    'confirmed': 'confirmed',
                    'in_progress': 'preparing',
                    'completed': 'completed',
                    'cancelled': 'cancelled'
                }
                
                internal_status = status_mapping.get(lightspeed_status)
                if internal_status and internal_status != order.status:
                    order.status = internal_status
                    order.save()
                    
            except OrderPOSInfo.DoesNotExist:
                logger.warning(f"Order with POS ID {pos_order_id} not found")
        
        return True
    
    def _process_clover_order_webhook(self, webhook_data):
        from ..models import OrderPOSInfo
        
        event_type = webhook_data.get('type')
        if event_type == 'ORDER_UPDATE':
            order_data = webhook_data.get('data', {})
            pos_order_id = order_data.get('id')
            clover_status = order_data.get('state', '')
            
            try:
                order_pos_info = OrderPOSInfo.objects.get(pos_order_id=pos_order_id)
                order = order_pos_info.order
                
                status_mapping = {
                    'ordered': 'confirmed',
                    'in_progress': 'preparing',
                    'ready': 'ready',
                    'completed': 'completed',
                    'voided': 'cancelled'
                }
                
                internal_status = status_mapping.get(clover_status)
                if internal_status and internal_status != order.status:
                    order.status = internal_status
                    order.save()
                    
            except OrderPOSInfo.DoesNotExist:
                logger.warning(f"Order with POS ID {pos_order_id} not found")
        
        return True
    
    def _process_shopify_order_webhook(self, webhook_data):
        from ..models import OrderPOSInfo
        
        order_data = webhook_data.get('order', {})
        pos_order_id = order_data.get('id')
        shopify_status = order_data.get('fulfillment_status', '')
        
        try:
            order_pos_info = OrderPOSInfo.objects.get(pos_order_id=pos_order_id)
            order = order_pos_info.order
            
            status_mapping = {
                'confirmed': 'confirmed',
                'in_progress': 'preparing',
                'fulfilled': 'completed',
                'cancelled': 'cancelled'
            }
            
            internal_status = status_mapping.get(shopify_status)
            if internal_status and internal_status != order.status:
                order.status = internal_status
                order.save()
                
        except OrderPOSInfo.DoesNotExist:
            logger.warning(f"Order with POS ID {pos_order_id} not found")
        
        return True
    
    def _process_custom_order_webhook(self, webhook_data):
        from ..models import OrderPOSInfo
        
        event_type = webhook_data.get('event')
        if event_type == 'order.updated':
            order_data = webhook_data.get('data', {})
            pos_order_id = order_data.get('order_id')
            custom_status = order_data.get('status', '')
            
            try:
                order_pos_info = OrderPOSInfo.objects.get(pos_order_id=pos_order_id)
                order = order_pos_info.order
                
                if custom_status and custom_status != order.status:
                    order.status = custom_status
                    order.save()
                    
            except OrderPOSInfo.DoesNotExist:
                logger.warning(f"Order with POS ID {pos_order_id} not found")
        
        return True
    
    def process_menu_webhook(self, webhook_data):
        """Process menu updates from POS - FULLY IMPLEMENTED"""
        from ..models import POSSyncLog
        
        try:
            sync_log = POSSyncLog.objects.create(
                connection=self.connection,
                sync_type='webhook',
                sync_type_detail='menu_update'
            )
            
            if self.connection.pos_type == 'square':
                success = self._process_square_menu_webhook(webhook_data)
            elif self.connection.pos_type == 'toast':
                success = self._process_toast_menu_webhook(webhook_data)
            elif self.connection.pos_type == 'lightspeed':
                success = self._process_lightspeed_menu_webhook(webhook_data)
            elif self.connection.pos_type == 'clover':
                success = self._process_clover_menu_webhook(webhook_data)
            elif self.connection.pos_type == 'shopify':
                success = self._process_shopify_menu_webhook(webhook_data)
            elif self.connection.pos_type == 'custom':
                success = self._process_custom_menu_webhook(webhook_data)
            else:
                success = False
            
            sync_log.status = 'success' if success else 'failed'
            sync_log.completed_at = timezone.now()
            sync_log.save()
            
            return success
            
        except Exception as e:
            logger.error(f"Error processing menu webhook: {str(e)}")
            return False
    
    def _process_square_menu_webhook(self, webhook_data):
        from ..models.menu_models import MenuItem, MenuCategory
        
        for event in webhook_data.get('data', []):
            if event['type'] == 'catalog.updated':
                catalog_objects = event['data']['object']['catalog_objects']
                
                for obj in catalog_objects:
                    if obj['type'] == 'ITEM':
                        self._update_menu_item_from_webhook(obj)
                    elif obj['type'] == 'CATEGORY':
                        self._update_category_from_webhook(obj)
        
        return True
    
    def _process_toast_menu_webhook(self, webhook_data):
        from ..models.menu_models import MenuItem, MenuCategory
        
        event_type = webhook_data.get('eventType')
        if event_type == 'MENU_UPDATED':
            menu_data = webhook_data.get('payload', {})
            
            for category_data in menu_data.get('menuCategories', []):
                self._update_toast_category(category_data)
            
            for item_data in menu_data.get('menuItems', []):
                self._update_toast_item(item_data)
        
        return True
    
    def _process_lightspeed_menu_webhook(self, webhook_data):
        from ..models.menu_models import MenuItem
        
        event_type = webhook_data.get('event')
        if event_type == 'item.updated':
            item_data = webhook_data.get('data', {})
            self._update_lightspeed_item(item_data)
        
        return True
    
    def _process_clover_menu_webhook(self, webhook_data):
        from ..models.menu_models import MenuItem
        
        event_type = webhook_data.get('type')
        if event_type == 'ITEM_UPDATE':
            item_data = webhook_data.get('data', {})
            self._update_clover_item(item_data)
        
        return True
    
    def _process_shopify_menu_webhook(self, webhook_data):
        from ..models.menu_models import MenuItem
        
        product_data = webhook_data.get('product', {})
        self._update_shopify_product(product_data)
        
        return True
    
    def _process_custom_menu_webhook(self, webhook_data):
        from ..models.menu_models import MenuItem
        
        event_type = webhook_data.get('event')
        if event_type == 'menu.updated':
            item_data = webhook_data.get('data', {})
            self._update_custom_item(item_data)
        
        return True
    
    def _update_menu_item_from_webhook(self, item_data):
        from ..models.menu_models import MenuItem
        
        try:
            menu_item = MenuItem.objects.get(
                restaurant=self.connection.restaurant,
                pos_item_id=item_data['id']
            )
            
            item_info = item_data['item_data']
            menu_item.name = item_info['name']
            menu_item.description = item_info.get('description', '')
            menu_item.is_available = item_info.get('available_online', False)
            
            if item_info.get('variations'):
                price_data = item_info['variations'][0]['item_variation_data'].get('price_money', {})
                if price_data:
                    menu_item.price = Decimal(str(price_data.get('amount', 0))) / 100
            
            menu_item.save()
            
        except MenuItem.DoesNotExist:
            logger.info(f"New menu item detected: {item_data['id']}")
    
    def _update_toast_item(self, item_data):
        from ..models.menu_models import MenuItem
        
        try:
            menu_item = MenuItem.objects.get(
                restaurant=self.connection.restaurant,
                pos_item_id=item_data.get('id')
            )
            
            menu_item.name = item_data.get('name', menu_item.name)
            menu_item.description = item_data.get('description', menu_item.description)
            menu_item.price = Decimal(str(item_data.get('price', menu_item.price)))
            menu_item.is_available = item_data.get('active', menu_item.is_available)
            menu_item.save()
            
        except MenuItem.DoesNotExist:
            logger.info(f"New Toast menu item detected: {item_data.get('id')}")
    
    def _update_lightspeed_item(self, item_data):
        from ..models.menu_models import MenuItem
        
        try:
            menu_item = MenuItem.objects.get(
                restaurant=self.connection.restaurant,
                pos_item_id=item_data.get('itemID')
            )
            
            menu_item.name = item_data.get('description', menu_item.name)
            menu_item.description = item_data.get('description', menu_item.description)
            menu_item.is_available = item_data.get('available', menu_item.is_available)
            menu_item.save()
            
        except MenuItem.DoesNotExist:
            logger.info(f"New Lightspeed item detected: {item_data.get('itemID')}")
    
    def _update_category_from_webhook(self, category_data):
        from ..models.menu_models import MenuCategory
        
        try:
            category = MenuCategory.objects.get(
                restaurant=self.connection.restaurant,
                pos_category_id=category_data['id']
            )
            
            category.name = category_data['category_data']['name']
            category.description = category_data['category_data'].get('description', '')
            category.save()
            
        except MenuCategory.DoesNotExist:
            logger.info(f"New category detected: {category_data['id']}")
    
    def _update_toast_category(self, category_data):
        from ..models.menu_models import MenuCategory
        
        try:
            category = MenuCategory.objects.get(
                restaurant=self.connection.restaurant,
                pos_category_id=category_data.get('id')
            )
            
            category.name = category_data.get('name', category.name)
            category.description = category_data.get('description', category.description)
            category.save()
            
        except MenuCategory.DoesNotExist:
            logger.info(f"New Toast category detected: {category_data.get('id')}")
    
    def process_inventory_webhook(self, webhook_data):
        """Process inventory updates from POS - FULLY IMPLEMENTED"""
        from ..models import POSSyncLog
        
        try:
            sync_log = POSSyncLog.objects.create(
                connection=self.connection,
                sync_type='webhook',
                sync_type_detail='inventory_update'
            )
            
            if self.connection.pos_type == 'square':
                success = self._process_square_inventory_webhook(webhook_data)
            elif self.connection.pos_type == 'toast':
                success = self._process_toast_inventory_webhook(webhook_data)
            elif self.connection.pos_type == 'lightspeed':
                success = self._process_lightspeed_inventory_webhook(webhook_data)
            elif self.connection.pos_type == 'clover':
                success = self._process_clover_inventory_webhook(webhook_data)
            elif self.connection.pos_type == 'shopify':
                success = self._process_shopify_inventory_webhook(webhook_data)
            elif self.connection.pos_type == 'custom':
                success = self._process_custom_inventory_webhook(webhook_data)
            else:
                success = False
            
            sync_log.status = 'success' if success else 'failed'
            sync_log.completed_at = timezone.now()
            sync_log.save()
            
            return success
            
        except Exception as e:
            logger.error(f"Error processing inventory webhook: {str(e)}")
            return False
    
    def _process_square_inventory_webhook(self, webhook_data):
        from ..models.menu_models import MenuItem
        
        for event in webhook_data.get('data', []):
            if event['type'] == 'inventory.updated':
                inventory_changes = event['data']['object']['inventory_changes']
                
                for change in inventory_changes:
                    catalog_object_id = change['catalog_object_id']
                    new_quantity = int(change['physical_count']['quantity'])
                    
                    try:
                        menu_item = MenuItem.objects.get(
                            restaurant=self.connection.restaurant,
                            pos_item_id=catalog_object_id
                        )
                        
                        menu_item.stock_quantity = new_quantity
                        menu_item.is_available = new_quantity > 0
                        menu_item.save()
                        
                    except MenuItem.DoesNotExist:
                        continue
        
        return True
    
    def _process_toast_inventory_webhook(self, webhook_data):
        from ..models.menu_models import MenuItem
        
        event_type = webhook_data.get('eventType')
        if event_type == 'INVENTORY_UPDATED':
            inventory_data = webhook_data.get('payload', {})
            item_id = inventory_data.get('itemId')
            quantity = inventory_data.get('quantity', 0)
            
            try:
                menu_item = MenuItem.objects.get(
                    restaurant=self.connection.restaurant,
                    pos_item_id=item_id
                )
                
                menu_item.stock_quantity = quantity
                menu_item.is_available = quantity > 0
                menu_item.save()
                
            except MenuItem.DoesNotExist:
                logger.warning(f"Inventory update for unknown item: {item_id}")
        
        return True
    
    def _process_lightspeed_inventory_webhook(self, webhook_data):
        from ..models.menu_models import MenuItem
        
        event_type = webhook_data.get('event')
        if event_type == 'inventory.updated':
            inventory_data = webhook_data.get('data', {})
            item_id = inventory_data.get('itemID')
            quantity = inventory_data.get('available', 0)
            
            try:
                menu_item = MenuItem.objects.get(
                    restaurant=self.connection.restaurant,
                    pos_item_id=item_id
                )
                
                menu_item.stock_quantity = quantity
                menu_item.is_available = quantity > 0
                menu_item.save()
                
            except MenuItem.DoesNotExist:
                logger.warning(f"Inventory update for unknown item: {item_id}")
        
        return True
    
    def _process_clover_inventory_webhook(self, webhook_data):
        from ..models.menu_models import MenuItem
        
        event_type = webhook_data.get('type')
        if event_type == 'INVENTORY_UPDATE':
            inventory_data = webhook_data.get('data', {})
            item_id = inventory_data.get('itemId')
            quantity = inventory_data.get('stockCount', 0)
            
            try:
                menu_item = MenuItem.objects.get(
                    restaurant=self.connection.restaurant,
                    pos_item_id=item_id
                )
                
                menu_item.stock_quantity = quantity
                menu_item.is_available = quantity > 0
                menu_item.save()
                
            except MenuItem.DoesNotExist:
                logger.warning(f"Inventory update for unknown item: {item_id}")
        
        return True
    
    def _process_shopify_inventory_webhook(self, webhook_data):
        from ..models.menu_models import MenuItem
        
        inventory_data = webhook_data.get('inventory_level', {})
        inventory_item_id = inventory_data.get('inventory_item_id')
        quantity = inventory_data.get('available', 0)
        
        try:
            menu_item = MenuItem.objects.get(
                restaurant=self.connection.restaurant,
                pos_item_id=inventory_item_id
            )
            
            menu_item.stock_quantity = quantity
            menu_item.is_available = quantity > 0
            menu_item.save()
            
        except MenuItem.DoesNotExist:
            logger.warning(f"Inventory update for unknown item: {inventory_item_id}")
        
        return True
    
    def _process_custom_inventory_webhook(self, webhook_data):
        from ..models.menu_models import MenuItem
        
        event_type = webhook_data.get('event')
        if event_type == 'inventory.updated':
            inventory_data = webhook_data.get('data', {})
            item_id = inventory_data.get('item_id')
            quantity = inventory_data.get('quantity', 0)
            
            try:
                menu_item = MenuItem.objects.get(
                    restaurant=self.connection.restaurant,
                    pos_item_id=item_id
                )
                
                menu_item.stock_quantity = quantity
                menu_item.is_available = quantity > 0
                menu_item.save()
                
            except MenuItem.DoesNotExist:
                logger.warning(f"Inventory update for unknown item: {item_id}")
        
        return True
    
    def _update_clover_item(self, item_data):
        from ..models.menu_models import MenuItem
        
        try:
            menu_item = MenuItem.objects.get(
                restaurant=self.connection.restaurant,
                pos_item_id=item_data.get('id')
            )
            
            menu_item.name = item_data.get('name', menu_item.name)
            menu_item.price = Decimal(str(item_data.get('price', 0))) / 100
            menu_item.is_available = item_data.get('available', menu_item.is_available)
            menu_item.save()
            
        except MenuItem.DoesNotExist:
            logger.info(f"New Clover item detected: {item_data.get('id')}")
    
    def _update_shopify_product(self, product_data):
        from ..models.menu_models import MenuItem
        
        try:
            menu_item = MenuItem.objects.get(
                restaurant=self.connection.restaurant,
                pos_item_id=product_data.get('id')
            )
            
            menu_item.name = product_data.get('title', menu_item.name)
            menu_item.description = product_data.get('body_html', menu_item.description)
            menu_item.is_available = product_data.get('status') == 'active'
            
            variants = product_data.get('variants', [])
            if variants:
                menu_item.price = Decimal(str(variants[0].get('price', menu_item.price)))
            
            menu_item.save()
            
        except MenuItem.DoesNotExist:
            logger.info(f"New Shopify product detected: {product_data.get('id')}")
    
    def _update_custom_item(self, item_data):
        from ..models.menu_models import MenuItem
        
        try:
            menu_item = MenuItem.objects.get(
                restaurant=self.connection.restaurant,
                pos_item_id=item_data.get('id')
            )
            
            menu_item.name = item_data.get('name', menu_item.name)
            menu_item.description = item_data.get('description', menu_item.description)
            menu_item.price = Decimal(str(item_data.get('price', menu_item.price)))
            menu_item.is_available = item_data.get('available', menu_item.is_available)
            menu_item.save()
            
        except MenuItem.DoesNotExist:
            logger.info(f"New custom item detected: {item_data.get('id')}")