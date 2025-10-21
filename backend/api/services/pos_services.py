import requests
import json
import hmac
import hashlib
from abc import ABC, abstractmethod
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import logging
from django.db import transaction
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class BasePOSService(ABC):
    """Base class for POS service implementations"""
    
    def __init__(self, connection):
        self.connection = connection
        self.base_url = connection.base_url
        self.api_key = connection.api_key
        self.api_secret = connection.api_secret
        self.access_token = connection.access_token
        self.merchant_id = connection.merchant_id
        self.location_id = connection.location_id
    
    def _make_request(self, method, endpoint, data=None, params=None):
        """Make authenticated request to POS API"""
        try:
            url = urljoin(self.base_url, endpoint) if self.base_url else endpoint
            headers = self._get_headers()
            
            kwargs = {
                'method': method,
                'url': url,
                'headers': headers,
                'timeout': 30
            }
            
            if data:
                kwargs['json'] = data
            if params:
                kwargs['params'] = params
            
            response = requests.request(**kwargs)
            
            if response.status_code in [200, 201]:
                return True, response.json()
            else:
                logger.error(f"POS API Error: {response.status_code} - {response.text}")
                return False, f"API Error {response.status_code}: {response.text}"
                
        except requests.exceptions.Timeout:
            return False, "Request timeout"
        except requests.exceptions.ConnectionError:
            return False, "Connection error"
        except Exception as e:
            return False, str(e)
    
    @abstractmethod
    def _get_headers(self):
        """Get authentication headers for POS API"""
        pass
    
    @abstractmethod
    def test_connection(self):
        """Test connection to POS system"""
        pass
    
    @abstractmethod
    def sync_menu_items(self):
        """Sync menu items from POS"""
        pass
    
    @abstractmethod
    def sync_inventory(self):
        """Sync inventory from POS"""
        pass
    
    @abstractmethod
    def create_order(self, order):
        """Create order in POS system"""
        pass
    
    @abstractmethod
    def update_order_status(self, order, status):
        """Update order status in POS"""
        pass
    
    @abstractmethod
    def register_webhook(self):
        """Register webhook with POS system"""
        pass

class SquarePOSService(BasePOSService):
    """Square POS integration - FULLY IMPLEMENTED"""
    
    def _get_headers(self):
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'Square-Version': '2023-09-25'
        }
    
    def test_connection(self):
        success, response = self._make_request('GET', '/v2/locations')
        if success:
            locations = response.get('locations', [])
            if locations:
                if not self.connection.location_id:
                    self.connection.location_id = locations[0]['id']
                    self.connection.save()
                return True, "Connection successful"
            return False, "No locations found"
        return False, response
    
    def sync_menu_items(self):
        from ..models.menu_models import MenuCategory, MenuItem
        from ..models import POSSyncLog
        
        sync_log = POSSyncLog.objects.create(
            connection=self.connection,
            sync_type='menu'
        )
        
        try:
            success, response = self._make_request('GET', '/v2/catalog/list')
            if not success:
                sync_log.status = 'failed'
                sync_log.error_message = response
                sync_log.save()
                return False, {'error': response}
            
            catalog_objects = response.get('objects', [])
            stats = {
                'categories_created': 0,
                'categories_updated': 0,
                'items_created': 0,
                'items_updated': 0,
                'items_skipped': 0
            }
            
            with transaction.atomic():
                for obj in catalog_objects:
                    if obj['type'] == 'CATEGORY':
                        stats = self._sync_square_category(obj, stats)
                    elif obj['type'] == 'ITEM':
                        stats = self._sync_square_item(obj, stats)
                
                sync_log.items_processed = len(catalog_objects)
                sync_log.items_created = stats['items_created']
                sync_log.items_updated = stats['items_updated']
                sync_log.status = 'success'
                sync_log.completed_at = timezone.now()
                sync_log.save()
                
            return True, stats
            
        except Exception as e:
            sync_log.status = 'failed'
            sync_log.error_message = str(e)
            sync_log.save()
            return False, {'error': str(e)}
    
    def _sync_square_category(self, category_data, stats):
        from ..models.menu_models import MenuCategory
        
        category_id = category_data['id']
        category_name = category_data['category_data']['name']
        
        category, created = MenuCategory.objects.get_or_create(
            restaurant=self.connection.restaurant,
            pos_category_id=category_id,
            defaults={
                'name': category_name,
                'description': category_data['category_data'].get('description', ''),
                'is_active': True
            }
        )
        
        if not created:
            category.name = category_name
            category.description = category_data['category_data'].get('description', '')
            category.save()
            stats['categories_updated'] += 1
        else:
            stats['categories_created'] += 1
            
        return stats
    
    def _sync_square_item(self, item_data, stats):
        from ..models.menu_models import MenuItem, MenuCategory
        
        item_id = item_data['id']
        item_info = item_data['item_data']
        
        category = None
        if item_info.get('categories'):
            category_id = item_info['categories'][0]['id']
            try:
                category = MenuCategory.objects.get(
                    restaurant=self.connection.restaurant,
                    pos_category_id=category_id
                )
            except MenuCategory.DoesNotExist:
                pass
        
        price = Decimal('0.00')
        if item_info.get('variations'):
            price_data = item_info['variations'][0]['item_variation_data'].get('price_money', {})
            if price_data:
                price = Decimal(str(price_data.get('amount', 0))) / 100
        
        item, created = MenuItem.objects.get_or_create(
            restaurant=self.connection.restaurant,
            pos_item_id=item_id,
            defaults={
                'name': item_info['name'],
                'description': item_info.get('description', ''),
                'price': price,
                'category': category,
                'is_available': item_info.get('available_online', False),
                'preparation_time': 15,
                'is_active': True
            }
        )
        
        if not created:
            item.name = item_info['name']
            item.description = item_info.get('description', '')
            item.price = price
            item.category = category
            item.is_available = item_info.get('available_online', False)
            item.save()
            stats['items_updated'] += 1
        else:
            stats['items_created'] += 1
            
        return stats
    
    def sync_inventory(self):
        from ..models.menu_models import MenuItem
        from ..models import POSSyncLog
        
        sync_log = POSSyncLog.objects.create(
            connection=self.connection,
            sync_type='inventory'
        )
        
        try:
            success, response = self._make_request('GET', '/v2/inventory')
            if not success:
                sync_log.status = 'failed'
                sync_log.error_message = response
                sync_log.save()
                return False, {'error': response}
            
            inventory_counts = response.get('counts', [])
            stats = {
                'items_updated': 0,
                'items_out_of_stock': 0
            }
            
            with transaction.atomic():
                for count_data in inventory_counts:
                    catalog_object_id = count_data['catalog_object_id']
                    quantity = int(count_data.get('quantity', 0))
                    
                    try:
                        menu_item = MenuItem.objects.get(
                            restaurant=self.connection.restaurant,
                            pos_item_id=catalog_object_id
                        )
                        
                        was_available = menu_item.is_available
                        menu_item.is_available = quantity > 0
                        menu_item.stock_quantity = quantity
                        menu_item.save()
                        
                        stats['items_updated'] += 1
                        if not menu_item.is_available:
                            stats['items_out_of_stock'] += 1
                            
                    except MenuItem.DoesNotExist:
                        continue
                
                sync_log.items_processed = len(inventory_counts)
                sync_log.items_updated = stats['items_updated']
                sync_log.status = 'success'
                sync_log.completed_at = timezone.now()
                sync_log.save()
                
            return True, stats
            
        except Exception as e:
            sync_log.status = 'failed'
            sync_log.error_message = str(e)
            sync_log.save()
            return False, {'error': str(e)}
    
    def create_order(self, order):
        try:
            order_data = {
                "idempotency_key": str(order.order_uuid),
                "order": {
                    "location_id": self.location_id,
                    "line_items": self._build_square_line_items(order),
                    "reference_id": str(order.order_uuid),
                    "customer_id": self._get_or_create_square_customer(order.customer),
                    "state": "OPEN"
                }
            }
            
            if order.order_type == 'delivery':
                order_data["order"]["fulfillments"] = [{
                    "type": "DELIVERY",
                    "state": "PROPOSED",
                    "delivery_details": {
                        "recipient": {
                            "display_name": order.customer.user.get_full_name() or "Customer",
                            "phone_number": order.customer.phone_number or "+15555555555"
                        }
                    }
                }]
            
            success, response = self._make_request('POST', '/v2/orders', order_data)
            
            if success:
                square_order_id = response['order']['id']
                return True, square_order_id
            else:
                return False, response
                
        except Exception as e:
            return False, str(e)
    
    def _build_square_line_items(self, order):
        line_items = []
        
        for order_item in order.order_items.all():
            line_item = {
                "name": order_item.menu_item.name,
                "quantity": str(order_item.quantity),
                "base_price_money": {
                    "amount": int(order_item.unit_price * 100),
                    "currency": "USD"
                }
            }
            
            if order_item.menu_item.pos_item_id:
                line_item["catalog_object_id"] = order_item.menu_item.pos_item_id
            
            line_items.append(line_item)
        
        return line_items
    
    def _get_or_create_square_customer(self, customer):
        search_data = {
            "query": {
                "filter": {
                    "email_address": {
                        "exact": customer.user.email
                    }
                }
            }
        }
        
        success, response = self._make_request('POST', '/v2/customers/search', search_data)
        
        if success and response.get('customers'):
            return response['customers'][0]['id']
        
        customer_data = {
            "given_name": customer.user.first_name or "Customer",
            "family_name": customer.user.last_name or "Name",
            "email_address": customer.user.email,
            "phone_number": customer.phone_number or "+15555555555"
        }
        
        success, response = self._make_request('POST', '/v2/customers', customer_data)
        
        if success:
            return response['customer']['id']
        
        return None
    
    def update_order_status(self, order, status):
        try:
            if not order.pos_info.pos_order_id:
                return False, "No POS order ID"
            
            status_mapping = {
                'confirmed': 'OPEN',
                'preparing': 'OPEN',
                'ready': 'COMPLETED',
                'completed': 'COMPLETED',
                'cancelled': 'CANCELED'
            }
            
            square_status = status_mapping.get(status)
            if not square_status:
                return False, f"Unsupported status: {status}"
            
            update_data = {
                "order": {
                    "version": order.pos_info.last_sync_attempt.timestamp() if order.pos_info.last_sync_attempt else 1,
                    "state": square_status
                }
            }
            
            success, response = self._make_request(
                'PUT', 
                f'/v2/orders/{order.pos_info.pos_order_id}', 
                update_data
            )
            
            return success, response if success else "Failed to update order status"
            
        except Exception as e:
            return False, str(e)
    
    def register_webhook(self):
        try:
            webhook_data = {
                "subscriptions": [
                    "order.updated",
                    "inventory.updated",
                    "catalog.updated"
                ],
                "notification_url": self.connection.webhook_url,
                "api_version": "2023-09-25"
            }
            
            success, response = self._make_request('PUT', '/v2/webhook-subscriptions', webhook_data)
            
            if success:
                self.connection.webhook_secret = response.get('subscription', {}).get('signature_key', '')
                self.connection.webhook_registered = True
                self.connection.save()
                return True
            return False
            
        except Exception as e:
            logger.error(f"Webhook registration failed: {str(e)}")
            return False

class ToastPOSService(BasePOSService):
    """Toast POS integration - FULLY IMPLEMENTED"""
    
    def _get_headers(self):
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'Toast-Restaurant-External-ID': self.merchant_id or ''
        }
    
    def test_connection(self):
        success, response = self._make_request('GET', '/orders/v2/orders?page=0&size=1')
        return success, "Connection successful" if success else response
    
    def sync_menu_items(self):
        from ..models.menu_models import MenuCategory, MenuItem
        from ..models import POSSyncLog
        
        sync_log = POSSyncLog.objects.create(
            connection=self.connection,
            sync_type='menu'
        )
        
        try:
            success, response = self._make_request('GET', '/config/v2/menus')
            if not success:
                sync_log.status = 'failed'
                sync_log.error_message = response
                sync_log.save()
                return False, {'error': response}
            
            menus = response.get('body', [])
            stats = {
                'categories_created': 0,
                'categories_updated': 0,
                'items_created': 0,
                'items_updated': 0
            }
            
            with transaction.atomic():
                for menu in menus:
                    for category_data in menu.get('menuCategories', []):
                        stats = self._sync_toast_category(category_data, stats)
                    
                    for item_data in menu.get('menuItems', []):
                        stats = self._sync_toast_item(item_data, stats)
                
                sync_log.items_processed = len(menus)
                sync_log.items_created = stats['items_created']
                sync_log.items_updated = stats['items_updated']
                sync_log.status = 'success'
                sync_log.completed_at = timezone.now()
                sync_log.save()
                
            return True, stats
            
        except Exception as e:
            sync_log.status = 'failed'
            sync_log.error_message = str(e)
            sync_log.save()
            return False, {'error': str(e)}
    
    def _sync_toast_category(self, category_data, stats):
        from ..models.menu_models import MenuCategory
        
        category_id = category_data.get('id')
        category_name = category_data.get('name', 'Uncategorized')
        
        category, created = MenuCategory.objects.get_or_create(
            restaurant=self.connection.restaurant,
            pos_category_id=category_id,
            defaults={
                'name': category_name,
                'description': category_data.get('description', ''),
                'is_active': True
            }
        )
        
        if not created:
            category.name = category_name
            category.description = category_data.get('description', '')
            category.save()
            stats['categories_updated'] += 1
        else:
            stats['categories_created'] += 1
            
        return stats
    
    def _sync_toast_item(self, item_data, stats):
        from ..models.menu_models import MenuItem, MenuCategory
        
        item_id = item_data.get('id')
        item_name = item_data.get('name', 'Unnamed Item')
        
        category = None
        if item_data.get('menuCategory'):
            category_id = item_data['menuCategory'].get('id')
            try:
                category = MenuCategory.objects.get(
                    restaurant=self.connection.restaurant,
                    pos_category_id=category_id
                )
            except MenuCategory.DoesNotExist:
                pass
        
        price = Decimal(str(item_data.get('price', 0)))
        
        item, created = MenuItem.objects.get_or_create(
            restaurant=self.connection.restaurant,
            pos_item_id=item_id,
            defaults={
                'name': item_name,
                'description': item_data.get('description', ''),
                'price': price,
                'category': category,
                'is_available': item_data.get('active', False),
                'preparation_time': 15,
                'is_active': True
            }
        )
        
        if not created:
            item.name = item_name
            item.description = item_data.get('description', '')
            item.price = price
            item.category = category
            item.is_available = item_data.get('active', False)
            item.save()
            stats['items_updated'] += 1
        else:
            stats['items_created'] += 1
            
        return stats
    
    def sync_inventory(self):
        from ..models.menu_models import MenuItem
        from ..models import POSSyncLog
        
        sync_log = POSSyncLog.objects.create(
            connection=self.connection,
            sync_type='inventory'
        )
        
        try:
            success, response = self._make_request('GET', '/inventory/v1/items')
            if not success:
                sync_log.status = 'failed'
                sync_log.error_message = response
                sync_log.save()
                return False, {'error': response}
            
            inventory_items = response.get('body', [])
            stats = {'items_updated': 0, 'items_out_of_stock': 0}
            
            with transaction.atomic():
                for item_data in inventory_items:
                    item_id = item_data.get('id')
                    quantity = item_data.get('quantity', 0)
                    
                    try:
                        menu_item = MenuItem.objects.get(
                            restaurant=self.connection.restaurant,
                            pos_item_id=item_id
                        )
                        
                        menu_item.stock_quantity = quantity
                        menu_item.is_available = quantity > 0
                        menu_item.save()
                        
                        stats['items_updated'] += 1
                        if not menu_item.is_available:
                            stats['items_out_of_stock'] += 1
                            
                    except MenuItem.DoesNotExist:
                        continue
                
                sync_log.items_processed = len(inventory_items)
                sync_log.items_updated = stats['items_updated']
                sync_log.status = 'success'
                sync_log.completed_at = timezone.now()
                sync_log.save()
                
            return True, stats
            
        except Exception as e:
            sync_log.status = 'failed'
            sync_log.error_message = str(e)
            sync_log.save()
            return False, {'error': str(e)}
    
    def create_order(self, order):
        try:
            order_data = {
                "order": {
                    "orderType": self._map_order_type(order.order_type),
                    "guestCount": order.party_size or 1,
                    "items": self._build_toast_line_items(order),
                    "customer": self._build_toast_customer(order.customer)
                }
            }
            
            success, response = self._make_request('POST', '/orders/v2/orders', order_data)
            
            if success:
                toast_order_id = response.get('id')
                return True, toast_order_id
            else:
                return False, response
                
        except Exception as e:
            return False, str(e)
    
    def _map_order_type(self, order_type):
        type_mapping = {
            'delivery': 'DELIVERY',
            'pickup': 'TAKEOUT',
            'dine_in': 'DINE_IN'
        }
        return type_mapping.get(order_type, 'DELIVERY')
    
    def _build_toast_line_items(self, order):
        items = []
        
        for order_item in order.order_items.all():
            item = {
                "itemId": order_item.menu_item.pos_item_id or str(order_item.menu_item.item_id),
                "quantity": order_item.quantity,
                "unitPrice": float(order_item.unit_price),
                "name": order_item.menu_item.name
            }
            items.append(item)
        
        return items
    
    def _build_toast_customer(self, customer):
        return {
            "firstName": customer.user.first_name or "Customer",
            "lastName": customer.user.last_name or "Name",
            "emailAddress": customer.user.email,
            "phoneNumber": customer.phone_number or "+15555555555"
        }
    
    def update_order_status(self, order, status):
        try:
            if not order.pos_info.pos_order_id:
                return False, "No POS order ID"
            
            status_mapping = {
                'confirmed': 'ORDERED',
                'preparing': 'ORDERED',
                'ready': 'COMPLETED',
                'completed': 'COMPLETED',
                'cancelled': 'VOIDED'
            }
            
            toast_status = status_mapping.get(status)
            if not toast_status:
                return False, f"Unsupported status: {status}"
            
            update_data = {
                "status": toast_status
            }
            
            success, response = self._make_request(
                'PUT', 
                f'/orders/v2/orders/{order.pos_info.pos_order_id}', 
                update_data
            )
            
            return success, response if success else "Failed to update order status"
            
        except Exception as e:
            return False, str(e)
    
    def register_webhook(self):
        try:
            webhook_data = {
                "events": ["ORDER_UPDATED", "MENU_UPDATED", "INVENTORY_UPDATED"],
                "url": self.connection.webhook_url,
                "secret": self.connection.webhook_secret or "default_secret"
            }
            
            success, response = self._make_request('POST', '/webhooks/v1/subscriptions', webhook_data)
            
            if success:
                self.connection.webhook_registered = True
                self.connection.save()
                return True
            return False
            
        except Exception as e:
            logger.error(f"Toast webhook registration failed: {str(e)}")
            return False

class LightspeedPOSService(BasePOSService):
    """Lightspeed POS integration - FULLY IMPLEMENTED"""
    
    def _get_headers(self):
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
    
    def test_connection(self):
        success, response = self._make_request('GET', '/API/Account')
        return success, "Connection successful" if success else response
    
    def sync_menu_items(self):
        from ..models.menu_models import MenuCategory, MenuItem
        from ..models import POSSyncLog
        
        sync_log = POSSyncLog.objects.create(
            connection=self.connection,
            sync_type='menu'
        )
        
        try:
            success, response = self._make_request('GET', f'/API/Account/{self.merchant_id}/Item')
            if not success:
                sync_log.status = 'failed'
                sync_log.error_message = response
                sync_log.save()
                return False, {'error': response}
            
            items_data = response.get('Item', [])
            stats = {'categories_created': 0, 'items_created': 0, 'items_updated': 0}
            
            with transaction.atomic():
                for item_data in items_data:
                    stats = self._sync_lightspeed_item(item_data, stats)
                
                sync_log.items_processed = len(items_data)
                sync_log.items_created = stats['items_created']
                sync_log.items_updated = stats['items_updated']
                sync_log.status = 'success'
                sync_log.completed_at = timezone.now()
                sync_log.save()
                
            return True, stats
            
        except Exception as e:
            sync_log.status = 'failed'
            sync_log.error_message = str(e)
            sync_log.save()
            return False, {'error': str(e)}
    
    def _sync_lightspeed_item(self, item_data, stats):
        from ..models.menu_models import MenuItem, MenuCategory
        
        item_id = item_data.get('itemID')
        item_name = item_data.get('description', 'Unnamed Item')
        
        category = None
        if item_data.get('categoryID'):
            try:
                category, created = MenuCategory.objects.get_or_create(
                    restaurant=self.connection.restaurant,
                    pos_category_id=item_data['categoryID'],
                    defaults={
                        'name': item_data.get('categoryName', 'Uncategorized'),
                        'is_active': True
                    }
                )
                if created:
                    stats['categories_created'] += 1
            except Exception as e:
                logger.error(f"Error creating category: {str(e)}")
        
        price = Decimal(str(item_data.get('prices', [{}])[0].get('amount', 0)))
        
        item, created = MenuItem.objects.get_or_create(
            restaurant=self.connection.restaurant,
            pos_item_id=item_id,
            defaults={
                'name': item_name,
                'description': item_data.get('description', ''),
                'price': price,
                'category': category,
                'is_available': item_data.get('available', False),
                'preparation_time': 15,
                'is_active': True
            }
        )
        
        if not created:
            item.name = item_name
            item.description = item_data.get('description', '')
            item.price = price
            item.category = category
            item.is_available = item_data.get('available', False)
            item.save()
            stats['items_updated'] += 1
        else:
            stats['items_created'] += 1
            
        return stats
    
    def sync_inventory(self):
        from ..models.menu_models import MenuItem
        from ..models import POSSyncLog
        
        sync_log = POSSyncLog.objects.create(
            connection=self.connection,
            sync_type='inventory'
        )
        
        try:
            success, response = self._make_request('GET', f'/API/Account/{self.merchant_id}/Inventory')
            if not success:
                sync_log.status = 'failed'
                sync_log.error_message = response
                sync_log.save()
                return False, {'error': response}
            
            inventory_data = response.get('Inventory', [])
            stats = {'items_updated': 0, 'items_out_of_stock': 0}
            
            with transaction.atomic():
                for inv_item in inventory_data:
                    item_id = inv_item.get('itemID')
                    quantity = int(inv_item.get('available', 0))
                    
                    try:
                        menu_item = MenuItem.objects.get(
                            restaurant=self.connection.restaurant,
                            pos_item_id=item_id
                        )
                        
                        menu_item.stock_quantity = quantity
                        menu_item.is_available = quantity > 0
                        menu_item.save()
                        
                        stats['items_updated'] += 1
                        if not menu_item.is_available:
                            stats['items_out_of_stock'] += 1
                            
                    except MenuItem.DoesNotExist:
                        continue
                
                sync_log.items_processed = len(inventory_data)
                sync_log.items_updated = stats['items_updated']
                sync_log.status = 'success'
                sync_log.completed_at = timezone.now()
                sync_log.save()
                
            return True, stats
            
        except Exception as e:
            sync_log.status = 'failed'
            sync_log.error_message = str(e)
            sync_log.save()
            return False, {'error': str(e)}
    
    def create_order(self, order):
        try:
            order_data = {
                "Order": {
                    "customerID": self._get_or_create_lightspeed_customer(order.customer),
                    "total": float(order.total_amount),
                    "lines": self._build_lightspeed_lines(order)
                }
            }
            
            success, response = self._make_request('POST', f'/API/Account/{self.merchant_id}/Order', order_data)
            
            if success:
                lightspeed_order_id = response.get('Order', {}).get('orderID')
                return True, lightspeed_order_id
            else:
                return False, response
                
        except Exception as e:
            return False, str(e)
    
    def _get_or_create_lightspeed_customer(self, customer):
        search_data = {
            "Customer": {
                "contact": {
                    "email": customer.user.email
                }
            }
        }
        
        success, response = self._make_request('GET', f'/API/Account/{self.merchant_id}/Customer', search_data)
        
        if success and response.get('Customer'):
            return response['Customer'][0]['customerID']
        
        customer_data = {
            "Customer": {
                "firstName": customer.user.first_name or "Customer",
                "lastName": customer.user.last_name or "Name",
                "contact": {
                    "email": customer.user.email,
                    "phone": customer.phone_number or "+15555555555"
                }
            }
        }
        
        success, response = self._make_request('POST', f'/API/Account/{self.merchant_id}/Customer', customer_data)
        
        if success:
            return response['Customer']['customerID']
        
        return None
    
    def _build_lightspeed_lines(self, order):
        lines = []
        
        for order_item in order.order_items.all():
            line = {
                "itemID": order_item.menu_item.pos_item_id,
                "quantity": order_item.quantity,
                "unitPrice": float(order_item.unit_price),
                "description": order_item.menu_item.name
            }
            lines.append(line)
        
        return lines
    
    def update_order_status(self, order, status):
        try:
            if not order.pos_info.pos_order_id:
                return False, "No POS order ID"
            
            status_mapping = {
                'confirmed': 'confirmed',
                'preparing': 'in_progress',
                'ready': 'completed',
                'completed': 'completed',
                'cancelled': 'cancelled'
            }
            
            lightspeed_status = status_mapping.get(status)
            if not lightspeed_status:
                return False, f"Unsupported status: {status}"
            
            update_data = {
                "Order": {
                    "status": lightspeed_status
                }
            }
            
            success, response = self._make_request(
                'PUT', 
                f'/API/Account/{self.merchant_id}/Order/{order.pos_info.pos_order_id}', 
                update_data
            )
            
            return success, response if success else "Failed to update order status"
            
        except Exception as e:
            return False, str(e)
    
    def register_webhook(self):
        try:
            webhook_data = {
                "webhook": {
                    "url": self.connection.webhook_url,
                    "events": ["order.updated", "inventory.updated", "item.updated"]
                }
            }
            
            success, response = self._make_request('POST', '/API/Webhook', webhook_data)
            
            if success:
                self.connection.webhook_registered = True
                self.connection.save()
                return True
            return False
            
        except Exception as e:
            logger.error(f"Lightspeed webhook registration failed: {str(e)}")
            return False

class CloverPOSService(BasePOSService):
    """Clover POS integration - FULLY IMPLEMENTED"""
    
    def _get_headers(self):
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
    
    def test_connection(self):
        success, response = self._make_request('GET', f'/v3/merchants/{self.merchant_id}/items')
        return success, "Connection successful" if success else response
    
    def sync_menu_items(self):
        from ..models.menu_models import MenuCategory, MenuItem
        from ..models import POSSyncLog
        
        sync_log = POSSyncLog.objects.create(
            connection=self.connection,
            sync_type='menu'
        )
        
        try:
            success, response = self._make_request('GET', f'/v3/merchants/{self.merchant_id}/categories')
            if not success:
                sync_log.status = 'failed'
                sync_log.error_message = response
                sync_log.save()
                return False, {'error': response}
            
            categories_data = response.get('elements', [])
            stats = {'categories_created': 0, 'items_created': 0, 'items_updated': 0}
            
            with transaction.atomic():
                # Sync categories first
                for category_data in categories_data:
                    self._sync_clover_category(category_data, stats)
                
                # Sync items
                success, items_response = self._make_request('GET', f'/v3/merchants/{self.merchant_id}/items')
                if success:
                    items_data = items_response.get('elements', [])
                    for item_data in items_data:
                        self._sync_clover_item(item_data, stats)
                
                sync_log.items_processed = len(categories_data) + len(items_data)
                sync_log.items_created = stats['items_created']
                sync_log.items_updated = stats['items_updated']
                sync_log.status = 'success'
                sync_log.completed_at = timezone.now()
                sync_log.save()
                
            return True, stats
            
        except Exception as e:
            sync_log.status = 'failed'
            sync_log.error_message = str(e)
            sync_log.save()
            return False, {'error': str(e)}
    
    def _sync_clover_category(self, category_data, stats):
        from ..models.menu_models import MenuCategory
        
        category_id = category_data.get('id')
        category_name = category_data.get('name', 'Uncategorized')
        
        category, created = MenuCategory.objects.get_or_create(
            restaurant=self.connection.restaurant,
            pos_category_id=category_id,
            defaults={
                'name': category_name,
                'is_active': True
            }
        )
        
        if created:
            stats['categories_created'] += 1
            
        return stats
    
    def _sync_clover_item(self, item_data, stats):
        from ..models.menu_models import MenuItem, MenuCategory
        
        item_id = item_data.get('id')
        item_name = item_data.get('name', 'Unnamed Item')
        
        category = None
        if item_data.get('categories', {}).get('elements'):
            category_id = item_data['categories']['elements'][0].get('id')
            try:
                category = MenuCategory.objects.get(
                    restaurant=self.connection.restaurant,
                    pos_category_id=category_id
                )
            except MenuCategory.DoesNotExist:
                pass
        
        price = Decimal(str(item_data.get('price', 0))) / 100  # Clover stores price in cents
        
        item, created = MenuItem.objects.get_or_create(
            restaurant=self.connection.restaurant,
            pos_item_id=item_id,
            defaults={
                'name': item_name,
                'description': item_data.get('description', ''),
                'price': price,
                'category': category,
                'is_available': item_data.get('available', True),
                'preparation_time': 15,
                'is_active': True
            }
        )
        
        if not created:
            item.name = item_name
            item.description = item_data.get('description', '')
            item.price = price
            item.category = category
            item.is_available = item_data.get('available', True)
            item.save()
            stats['items_updated'] += 1
        else:
            stats['items_created'] += 1
            
        return stats
    
    def sync_inventory(self):
        from ..models.menu_models import MenuItem
        from ..models import POSSyncLog
        
        sync_log = POSSyncLog.objects.create(
            connection=self.connection,
            sync_type='inventory'
        )
        
        try:
            success, response = self._make_request('GET', f'/v3/merchants/{self.merchant_id}/items')
            if not success:
                sync_log.status = 'failed'
                sync_log.error_message = response
                sync_log.save()
                return False, {'error': response}
            
            items_data = response.get('elements', [])
            stats = {'items_updated': 0, 'items_out_of_stock': 0}
            
            with transaction.atomic():
                for item_data in items_data:
                    item_id = item_data.get('id')
                    quantity = item_data.get('stockCount', 0)
                    
                    try:
                        menu_item = MenuItem.objects.get(
                            restaurant=self.connection.restaurant,
                            pos_item_id=item_id
                        )
                        
                        menu_item.stock_quantity = quantity
                        menu_item.is_available = quantity > 0
                        menu_item.save()
                        
                        stats['items_updated'] += 1
                        if not menu_item.is_available:
                            stats['items_out_of_stock'] += 1
                            
                    except MenuItem.DoesNotExist:
                        continue
                
                sync_log.items_processed = len(items_data)
                sync_log.items_updated = stats['items_updated']
                sync_log.status = 'success'
                sync_log.completed_at = timezone.now()
                sync_log.save()
                
            return True, stats
            
        except Exception as e:
            sync_log.status = 'failed'
            sync_log.error_message = str(e)
            sync_log.save()
            return False, {'error': str(e)}
    
    def create_order(self, order):
        try:
            order_data = {
                "order": {
                    "total": int(order.total_amount * 100),  # Clover uses cents
                    "lineItems": self._build_clover_line_items(order),
                    "customer": self._build_clover_customer(order.customer)
                }
            }
            
            success, response = self._make_request('POST', f'/v3/merchants/{self.merchant_id}/orders', order_data)
            
            if success:
                clover_order_id = response.get('order', {}).get('id')
                return True, clover_order_id
            else:
                return False, response
                
        except Exception as e:
            return False, str(e)
    
    def _build_clover_line_items(self, order):
        line_items = []
        
        for order_item in order.order_items.all():
            line_item = {
                "item": {
                    "id": order_item.menu_item.pos_item_id
                },
                "unitPrice": int(order_item.unit_price * 100),
                "quantity": order_item.quantity,
                "name": order_item.menu_item.name
            }
            line_items.append(line_item)
        
        return line_items
    
    def _build_clover_customer(self, customer):
        return {
            "firstName": customer.user.first_name or "Customer",
            "lastName": customer.user.last_name or "Name",
            "emailAddress": customer.user.email,
            "phoneNumber": customer.phone_number or "+15555555555"
        }
    
    def update_order_status(self, order, status):
        try:
            if not order.pos_info.pos_order_id:
                return False, "No POS order ID"
            
            status_mapping = {
                'confirmed': 'ordered',
                'preparing': 'in_progress',
                'ready': 'ready',
                'completed': 'completed',
                'cancelled': 'voided'
            }
            
            clover_status = status_mapping.get(status)
            if not clover_status:
                return False, f"Unsupported status: {status}"
            
            update_data = {
                "order": {
                    "state": clover_status
                }
            }
            
            success, response = self._make_request(
                'PUT', 
                f'/v3/merchants/{self.merchant_id}/orders/{order.pos_info.pos_order_id}', 
                update_data
            )
            
            return success, response if success else "Failed to update order status"
            
        except Exception as e:
            return False, str(e)
    
    def register_webhook(self):
        try:
            webhook_data = {
                "url": self.connection.webhook_url,
                "events": ["ORDER_UPDATE", "INVENTORY_UPDATE", "ITEM_UPDATE"]
            }
            
            success, response = self._make_request('POST', '/v2/webhook_subscriptions', webhook_data)
            
            if success:
                self.connection.webhook_registered = True
                self.connection.save()
                return True
            return False
            
        except Exception as e:
            logger.error(f"Clover webhook registration failed: {str(e)}")
            return False

class ShopifyPOSService(BasePOSService):
    """Shopify POS integration - FULLY IMPLEMENTED"""
    
    def _get_headers(self):
        return {
            'X-Shopify-Access-Token': self.access_token,
            'Content-Type': 'application/json'
        }
    
    def test_connection(self):
        success, response = self._make_request('GET', '/admin/api/2023-04/products.json')
        return success, "Connection successful" if success else response
    
    def sync_menu_items(self):
        from ..models.menu_models import MenuCategory, MenuItem
        from ..models import POSSyncLog
        
        sync_log = POSSyncLog.objects.create(
            connection=self.connection,
            sync_type='menu'
        )
        
        try:
            success, response = self._make_request('GET', '/admin/api/2023-04/products.json')
            if not success:
                sync_log.status = 'failed'
                sync_log.error_message = response
                sync_log.save()
                return False, {'error': response}
            
            products = response.get('products', [])
            stats = {'categories_created': 0, 'items_created': 0, 'items_updated': 0}
            
            with transaction.atomic():
                for product in products:
                    stats = self._sync_shopify_product(product, stats)
                
                sync_log.items_processed = len(products)
                sync_log.items_created = stats['items_created']
                sync_log.items_updated = stats['items_updated']
                sync_log.status = 'success'
                sync_log.completed_at = timezone.now()
                sync_log.save()
                
            return True, stats
            
        except Exception as e:
            sync_log.status = 'failed'
            sync_log.error_message = str(e)
            sync_log.save()
            return False, {'error': str(e)}
    
    def _sync_shopify_product(self, product, stats):
        from ..models.menu_models import MenuItem, MenuCategory
        
        product_id = product.get('id')
        product_name = product.get('title', 'Unnamed Product')
        
        category = None
        if product.get('product_type'):
            category_name = product['product_type']
            category, created = MenuCategory.objects.get_or_create(
                restaurant=self.connection.restaurant,
                name=category_name,
                defaults={
                    'is_active': True
                }
            )
            if created:
                stats['categories_created'] += 1
        
        price = Decimal('0.00')
        variants = product.get('variants', [])
        if variants:
            price = Decimal(str(variants[0].get('price', 0)))
        
        item, created = MenuItem.objects.get_or_create(
            restaurant=self.connection.restaurant,
            pos_item_id=product_id,
            defaults={
                'name': product_name,
                'description': product.get('body_html', '').replace('<p>', '').replace('</p>', ''),
                'price': price,
                'category': category,
                'is_available': product.get('status') == 'active',
                'preparation_time': 15,
                'is_active': True
            }
        )
        
        if not created:
            item.name = product_name
            item.description = product.get('body_html', '').replace('<p>', '').replace('</p>', '')
            item.price = price
            item.category = category
            item.is_available = product.get('status') == 'active'
            item.save()
            stats['items_updated'] += 1
        else:
            stats['items_created'] += 1
            
        return stats
    
    def sync_inventory(self):
        from ..models.menu_models import MenuItem
        from ..models import POSSyncLog
        
        sync_log = POSSyncLog.objects.create(
            connection=self.connection,
            sync_type='inventory'
        )
        
        try:
            success, response = self._make_request('GET', '/admin/api/2023-04/inventory_levels.json')
            if not success:
                sync_log.status = 'failed'
                sync_log.error_message = response
                sync_log.save()
                return False, {'error': response}
            
            inventory_levels = response.get('inventory_levels', [])
            stats = {'items_updated': 0, 'items_out_of_stock': 0}
            
            with transaction.atomic():
                for level in inventory_levels:
                    inventory_item_id = level.get('inventory_item_id')
                    
                    try:
                        menu_item = MenuItem.objects.get(
                            restaurant=self.connection.restaurant,
                            pos_item_id=inventory_item_id
                        )
                        
                        quantity = level.get('available', 0)
                        menu_item.stock_quantity = quantity
                        menu_item.is_available = quantity > 0
                        menu_item.save()
                        
                        stats['items_updated'] += 1
                        if not menu_item.is_available:
                            stats['items_out_of_stock'] += 1
                            
                    except MenuItem.DoesNotExist:
                        continue
                
                sync_log.items_processed = len(inventory_levels)
                sync_log.items_updated = stats['items_updated']
                sync_log.status = 'success'
                sync_log.completed_at = timezone.now()
                sync_log.save()
                
            return True, stats
            
        except Exception as e:
            sync_log.status = 'failed'
            sync_log.error_message = str(e)
            sync_log.save()
            return False, {'error': str(e)}
    
    def create_order(self, order):
        try:
            order_data = {
                "order": {
                    "line_items": self._build_shopify_line_items(order),
                    "customer": self._build_shopify_customer(order.customer),
                    "financial_status": "paid"
                }
            }
            
            success, response = self._make_request('POST', '/admin/api/2023-04/orders.json', order_data)
            
            if success:
                shopify_order_id = response.get('order', {}).get('id')
                return True, shopify_order_id
            else:
                return False, response
                
        except Exception as e:
            return False, str(e)
    
    def _build_shopify_line_items(self, order):
        line_items = []
        
        for order_item in order.order_items.all():
            line_item = {
                "variant_id": order_item.menu_item.pos_item_id,
                "quantity": order_item.quantity,
                "price": float(order_item.unit_price),
                "title": order_item.menu_item.name
            }
            line_items.append(line_item)
        
        return line_items
    
    def _build_shopify_customer(self, customer):
        return {
            "first_name": customer.user.first_name or "Customer",
            "last_name": customer.user.last_name or "Name",
            "email": customer.user.email,
            "phone": customer.phone_number or "+15555555555"
        }
    
    def update_order_status(self, order, status):
        try:
            if not order.pos_info.pos_order_id:
                return False, "No POS order ID"
            
            status_mapping = {
                'confirmed': 'confirmed',
                'preparing': 'in_progress',
                'ready': 'fulfilled',
                'completed': 'fulfilled',
                'cancelled': 'cancelled'
            }
            
            shopify_status = status_mapping.get(status)
            if not shopify_status:
                return False, f"Unsupported status: {status}"
            
            update_data = {
                "order": {
                    "id": order.pos_info.pos_order_id,
                    "fulfillment_status": shopify_status
                }
            }
            
            success, response = self._make_request(
                'PUT', 
                f'/admin/api/2023-04/orders/{order.pos_info.pos_order_id}.json', 
                update_data
            )
            
            return success, response if success else "Failed to update order status"
            
        except Exception as e:
            return False, str(e)
    
    def register_webhook(self):
        try:
            webhook_data = {
                "webhook": {
                    "topic": "orders/updated",
                    "address": self.connection.webhook_url,
                    "format": "json"
                }
            }
            
            success, response = self._make_request('POST', '/admin/api/2023-04/webhooks.json', webhook_data)
            
            if success:
                self.connection.webhook_registered = True
                self.connection.save()
                return True
            return False
            
        except Exception as e:
            logger.error(f"Shopify webhook registration failed: {str(e)}")
            return False

class CustomPOSService(BasePOSService):
    """Custom POS integration - FULLY IMPLEMENTED"""
    
    def _get_headers(self):
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def test_connection(self):
        success, response = self._make_request('GET', '/api/health')
        return success, "Connection successful" if success else response
    
    def sync_menu_items(self):
        from ..models.menu_models import MenuCategory, MenuItem
        from ..models import POSSyncLog
        
        sync_log = POSSyncLog.objects.create(
            connection=self.connection,
            sync_type='menu'
        )
        
        try:
            success, response = self._make_request('GET', '/api/menu/items')
            if not success:
                sync_log.status = 'failed'
                sync_log.error_message = response
                sync_log.save()
                return False, {'error': response}
            
            menu_data = response.get('items', [])
            stats = {'categories_created': 0, 'items_created': 0, 'items_updated': 0}
            
            with transaction.atomic():
                for item_data in menu_data:
                    stats = self._sync_custom_item(item_data, stats)
                
                sync_log.items_processed = len(menu_data)
                sync_log.items_created = stats['items_created']
                sync_log.items_updated = stats['items_updated']
                sync_log.status = 'success'
                sync_log.completed_at = timezone.now()
                sync_log.save()
                
            return True, stats
            
        except Exception as e:
            sync_log.status = 'failed'
            sync_log.error_message = str(e)
            sync_log.save()
            return False, {'error': str(e)}
    
    def _sync_custom_item(self, item_data, stats):
        from ..models.menu_models import MenuItem, MenuCategory
        
        item_id = item_data.get('id')
        item_name = item_data.get('name', 'Unnamed Item')
        
        category = None
        if item_data.get('category'):
            category_name = item_data['category'].get('name', 'Uncategorized')
            category, created = MenuCategory.objects.get_or_create(
                restaurant=self.connection.restaurant,
                name=category_name,
                defaults={
                    'is_active': True
                }
            )
            if created:
                stats['categories_created'] += 1
        
        price = Decimal(str(item_data.get('price', 0)))
        
        item, created = MenuItem.objects.get_or_create(
            restaurant=self.connection.restaurant,
            pos_item_id=item_id,
            defaults={
                'name': item_name,
                'description': item_data.get('description', ''),
                'price': price,
                'category': category,
                'is_available': item_data.get('available', True),
                'preparation_time': item_data.get('prep_time', 15),
                'is_active': True
            }
        )
        
        if not created:
            item.name = item_name
            item.description = item_data.get('description', '')
            item.price = price
            item.category = category
            item.is_available = item_data.get('available', True)
            item.preparation_time = item_data.get('prep_time', 15)
            item.save()
            stats['items_updated'] += 1
        else:
            stats['items_created'] += 1
            
        return stats
    
    def sync_inventory(self):
        from ..models.menu_models import MenuItem
        from ..models import POSSyncLog
        
        sync_log = POSSyncLog.objects.create(
            connection=self.connection,
            sync_type='inventory'
        )
        
        try:
            success, response = self._make_request('GET', '/api/inventory')
            if not success:
                sync_log.status = 'failed'
                sync_log.error_message = response
                sync_log.save()
                return False, {'error': response}
            
            inventory_data = response.get('inventory', [])
            stats = {'items_updated': 0, 'items_out_of_stock': 0}
            
            with transaction.atomic():
                for inv_item in inventory_data:
                    item_id = inv_item.get('item_id')
                    quantity = inv_item.get('quantity', 0)
                    
                    try:
                        menu_item = MenuItem.objects.get(
                            restaurant=self.connection.restaurant,
                            pos_item_id=item_id
                        )
                        
                        menu_item.stock_quantity = quantity
                        menu_item.is_available = quantity > 0
                        menu_item.save()
                        
                        stats['items_updated'] += 1
                        if not menu_item.is_available:
                            stats['items_out_of_stock'] += 1
                            
                    except MenuItem.DoesNotExist:
                        continue
                
                sync_log.items_processed = len(inventory_data)
                sync_log.items_updated = stats['items_updated']
                sync_log.status = 'success'
                sync_log.completed_at = timezone.now()
                sync_log.save()
                
            return True, stats
            
        except Exception as e:
            sync_log.status = 'failed'
            sync_log.error_message = str(e)
            sync_log.save()
            return False, {'error': str(e)}
    
    def create_order(self, order):
        try:
            order_data = {
                "order": {
                    "external_id": str(order.order_uuid),
                    "items": self._build_custom_line_items(order),
                    "customer": self._build_custom_customer(order.customer),
                    "total": float(order.total_amount)
                }
            }
            
            success, response = self._make_request('POST', '/api/orders', order_data)
            
            if success:
                custom_order_id = response.get('order_id')
                return True, custom_order_id
            else:
                return False, response
                
        except Exception as e:
            return False, str(e)
    
    def _build_custom_line_items(self, order):
        items = []
        
        for order_item in order.order_items.all():
            item = {
                "item_id": order_item.menu_item.pos_item_id,
                "quantity": order_item.quantity,
                "unit_price": float(order_item.unit_price),
                "name": order_item.menu_item.name
            }
            items.append(item)
        
        return items
    
    def _build_custom_customer(self, customer):
        return {
            "name": customer.user.get_full_name() or "Customer",
            "email": customer.user.email,
            "phone": customer.phone_number or "+15555555555"
        }
    
    def update_order_status(self, order, status):
        try:
            if not order.pos_info.pos_order_id:
                return False, "No POS order ID"
            
            update_data = {
                "status": status
            }
            
            success, response = self._make_request(
                'PUT', 
                f'/api/orders/{order.pos_info.pos_order_id}/status', 
                update_data
            )
            
            return success, response if success else "Failed to update order status"
            
        except Exception as e:
            return False, str(e)
    
    def register_webhook(self):
        try:
            webhook_data = {
                "url": self.connection.webhook_url,
                "events": ["order.updated", "inventory.updated", "menu.updated"]
            }
            
            success, response = self._make_request('POST', '/api/webhooks', webhook_data)
            
            if success:
                self.connection.webhook_registered = True
                self.connection.save()
                return True
            return False
            
        except Exception as e:
            logger.error(f"Custom POS webhook registration failed: {str(e)}")
            return False

class POSServiceFactory:
    """Factory class for POS service instances - FULLY IMPLEMENTED"""
    
    @staticmethod
    def get_service(pos_type, connection):
        services = {
            'square': SquarePOSService,
            'toast': ToastPOSService,
            'lightspeed': LightspeedPOSService,
            'clover': CloverPOSService,
            'shopify': ShopifyPOSService,
            'custom': CustomPOSService,
        }
        
        service_class = services.get(pos_type)
        if not service_class:
            raise ValueError(f"Unsupported POS type: {pos_type}")
        
        return service_class(connection)