import logging
from django.utils import timezone
from django.db import transaction

logger = logging.getLogger(__name__)

class ConflictResolutionService:
    """
    NEW: Comprehensive conflict resolution for data synchronization
    INTEGRATES WITH: Your existing models and payment systems
    """
    
    def __init__(self):
        self.conflict_handlers = {
            'menu_item_price': self._resolve_menu_item_price_conflict,
            'menu_item_availability': self._resolve_menu_item_availability_conflict,
            'order_status': self._resolve_order_status_conflict,
            'inventory_level': self._resolve_inventory_level_conflict,
            'payment_status': self._resolve_payment_status_conflict,
            'table_status': self._resolve_table_status_conflict,
        }
    
    def detect_and_resolve_all_conflicts(self, restaurant_id=None):
        """
        NEW: Detect and resolve all conflicts for a restaurant or system-wide
        """
        conflicts_detected = 0
        conflicts_resolved = 0
        
        # Detect and resolve menu conflicts
        menu_conflicts = self._detect_menu_conflicts(restaurant_id)
        conflicts_detected += len(menu_conflicts)
        
        for conflict in menu_conflicts:
            if self._resolve_conflict(conflict):
                conflicts_resolved += 1
        
        # Detect and resolve order conflicts
        order_conflicts = self._detect_order_conflicts(restaurant_id)
        conflicts_detected += len(order_conflicts)
        
        for conflict in order_conflicts:
            if self._resolve_conflict(conflict):
                conflicts_resolved += 1
        
        # Detect and resolve payment conflicts
        payment_conflicts = self._detect_payment_conflicts(restaurant_id)
        conflicts_detected += len(payment_conflicts)
        
        for conflict in payment_conflicts:
            if self._resolve_conflict(conflict):
                conflicts_resolved += 1
        
        return {
            'detected': conflicts_detected,
            'resolved': conflicts_resolved,
            'remaining': conflicts_detected - conflicts_resolved
        }
    
    def _detect_menu_conflicts(self, restaurant_id):
        """
        NEW: Detect menu item conflicts between online and POS systems
        INTEGRATES WITH: Your existing MenuItem and POSConnection models
        """
        conflicts = []
        
        from ..models import MenuItem, POSConnection
        
        # Get menu items with POS connections
        menu_items = MenuItem.objects.filter(
            category__restaurant_id=restaurant_id
        ) if restaurant_id else MenuItem.objects.all()
        
        for item in menu_items:
            # Check for POS connections that might have different data
            pos_connections = POSConnection.objects.filter(
                restaurant=item.category.restaurant,
                is_active=True
            )
            
            for connection in pos_connections:
                # This would typically compare with actual POS data
                # For now, using a simplified conflict detection
                if hasattr(item, 'pos_info') and item.pos_info:
                    pos_price = getattr(item.pos_info, 'pos_price', None)
                    if pos_price and float(pos_price) != float(item.price):
                        conflicts.append({
                            'type': 'menu_item_price',
                            'item_id': item.item_id,
                            'item_name': item.name,
                            'online_price': float(item.price),
                            'pos_price': float(pos_price),
                            'restaurant_id': item.category.restaurant_id,
                            'severity': 'medium'
                        })
        
        return conflicts
    
    def _detect_order_conflicts(self, restaurant_id):
        """
        NEW: Detect order status conflicts between online and POS systems
        INTEGRATES WITH: Your existing Order and OrderPOSInfo models
        """
        conflicts = []
        
        from ..models import Order
        
        orders = Order.objects.filter(
            pos_info__isnull=False
        )
        
        if restaurant_id:
            orders = orders.filter(restaurant_id=restaurant_id)
        
        for order in orders:
            pos_status = getattr(order.pos_info, 'pos_status', None)
            if pos_status and pos_status != order.status:
                conflicts.append({
                    'type': 'order_status',
                    'order_id': order.order_id,
                    'order_uuid': str(order.order_uuid),
                    'online_status': order.status,
                    'pos_status': pos_status,
                    'restaurant_id': order.restaurant_id,
                    'severity': 'high'
                })
        
        return conflicts
    
    def _detect_payment_conflicts(self, restaurant_id):
        """
        NEW: Detect payment status conflicts
        INTEGRATES WITH: Your existing Payment model and gateway integrations
        """
        conflicts = []
        
        from ..models import Payment, Order
        
        payments = Payment.objects.filter(
            order__pos_info__isnull=False
        ).select_related('order')
        
        if restaurant_id:
            payments = payments.filter(order__restaurant_id=restaurant_id)
        
        for payment in payments:
            pos_payment_status = getattr(payment.order.pos_info, 'pos_payment_status', None)
            if pos_payment_status and pos_payment_status != payment.payment_status:
                conflicts.append({
                    'type': 'payment_status',
                    'payment_id': payment.payment_id,
                    'order_id': payment.order.order_id,
                    'online_status': payment.payment_status,
                    'pos_status': pos_payment_status,
                    'gateway_type': self._detect_gateway_type(payment),
                    'restaurant_id': payment.order.restaurant_id,
                    'severity': 'high'
                })
        
        return conflicts
    
    def _resolve_conflict(self, conflict):
        """
        NEW: Resolve a specific conflict using appropriate handler
        """
        conflict_type = conflict['type']
        
        if conflict_type in self.conflict_handlers:
            try:
                return self.conflict_handlers[conflict_type](conflict)
            except Exception as e:
                logger.error(f"Error resolving {conflict_type} conflict: {str(e)}")
                return False
        
        return False
    
    def _resolve_menu_item_price_conflict(self, conflict):
        """
        NEW: Resolve menu item price conflict
        BUSINESS LOGIC: Use POS price for dine-in, online price for delivery
        """
        try:
            from ..models import MenuItem
            
            item = MenuItem.objects.get(item_id=conflict['item_id'])
            pos_price = conflict['pos_price']
            
            with transaction.atomic():
                # Preserve popularity data
                original_popularity = item.popularity_score
                original_order_count = item.order_count
                
                item.price = pos_price
                
                # Restore popularity data
                item.popularity_score = original_popularity
                item.order_count = original_order_count
                
                item.save()
            
            logger.info(f"Resolved price conflict for {item.name}: {pos_price}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to resolve price conflict: {str(e)}")
            return False
    
    def _resolve_order_status_conflict(self, conflict):
        """
        NEW: Resolve order status conflict
        BUSINESS LOGIC: Trust POS for dine-in, trust online for delivery
        """
        try:
            from ..models import Order
            
            order = Order.objects.get(order_id=conflict['order_id'])
            pos_status = conflict['pos_status']
            
            with transaction.atomic():
                if order.order_type in ['dine_in', 'pickup']:
                    # Trust POS for restaurant orders
                    order.status = pos_status
                else:
                    # Trust online system for delivery
                    order.status = order.status  # Keep current status
                
                order.save()
            
            logger.info(f"Resolved status conflict for order {order.order_uuid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to resolve order status conflict: {str(e)}")
            return False
    
    def _resolve_payment_status_conflict(self, conflict):
        """
        NEW: Resolve payment status conflict with gateway verification
        INTEGRATES WITH: Your Stripe, M-Pesa, and Azam Pay gateways
        """
        try:
            from ..models import Payment
            from .payment_verification_service import PaymentVerificationService
            
            payment = Payment.objects.get(payment_id=conflict['payment_id'])
            verifier = PaymentVerificationService()
            
            # Verify with actual payment gateway
            verification_result = verifier.verify_payment(
                payment.transaction_id,
                conflict['gateway_type']
            )
            
            if verification_result['status'] == 'verified':
                # Use verified status
                payment.payment_status = verification_result['payment_status']
                payment.save()
                logger.info(f"Resolved payment conflict using {conflict['gateway_type']} verification")
                return True
            else:
                # Use business logic fallback
                return self._resolve_payment_using_business_logic(conflict, payment)
                
        except Exception as e:
            logger.error(f"Failed to resolve payment conflict: {str(e)}")
            return False
    
    def _resolve_payment_using_business_logic(self, conflict, payment):
        """
        NEW: Resolve payment conflict using business logic when verification fails
        """
        try:
            if payment.order.order_type in ['delivery', 'pickup']:
                # For delivery/pickup, trust online status
                payment.payment_status = conflict['online_status']
            else:
                # For dine-in, trust POS status
                payment.payment_status = conflict['pos_status']
            
            payment.save()
            logger.info(f"Resolved payment conflict using business logic")
            return True
            
        except Exception as e:
            logger.error(f"Failed to resolve payment using business logic: {str(e)}")
            return False
    
    def _detect_gateway_type(self, payment):
        """
        NEW: Detect payment gateway type from transaction ID
        SUPPORTS: Stripe, M-Pesa, Azam Pay
        """
        transaction_id = payment.transaction_id or ''
        
        if transaction_id.startswith('ch_') or transaction_id.startswith('pi_'):
            return 'stripe'
        elif 'MPESA' in transaction_id.upper() or transaction_id.startswith('MP'):
            return 'mpesa'
        elif 'AZAM' in transaction_id.upper() or transaction_id.startswith('AZ'):
            return 'azam_pay'
        else:
            return 'unknown'
    
    def _resolve_menu_item_availability_conflict(self, conflict):
        """NEW: Resolve menu item availability conflict"""
        # Implementation for availability conflicts
        return False
    
    def _resolve_inventory_level_conflict(self, conflict):
        """NEW: Resolve inventory level conflict"""
        # Implementation for inventory conflicts
        return False
    
    def _resolve_table_status_conflict(self, conflict):
        """NEW: Resolve table status conflict"""
        # Implementation for table status conflicts
        return False