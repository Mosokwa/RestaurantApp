# management/commands/orders.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
import random
from datetime import timedelta

class Command(BaseCommand):
    help = 'Create orders, order items, and payments'
    
    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=500, help='Number of orders to create')
        parser.add_argument('--skip-existing', action='store_true')
    
    def handle(self, *args, **options):
        from api.models import (
            Customer, Restaurant, MenuItem, Order, OrderItem, OrderItemModifier,
            Payment, OrderTracking, CustomerLoyalty,
            PointsTransaction, MultiRestaurantLoyaltyProgram, ItemModifier,
            MenuItemModifier, RestaurantLoyaltySettings
        )
        
        order_count = options['count']
        customers = list(Customer.objects.all())
        loyalty_program = MultiRestaurantLoyaltyProgram.objects.first()
        
        if not customers:
            self.stdout.write(self.style.ERROR("  No customers found! Run customers first."))
            return
        
        orders_created = 0
        order_items_created = 0
        
        # Create orders spread over last 60 days
        for i in range(order_count):
            customer = random.choice(customers)
            
            # Get a restaurant this customer has favorited or random
            if customer.favorite_restaurants.exists() and random.random() > 0.3:
                restaurant = random.choice(list(customer.favorite_restaurants.all()))
            else:
                restaurant = random.choice(list(Restaurant.objects.filter(status='active')))
            
            # Get menu items from this restaurant
            menu_items = list(MenuItem.objects.filter(
                category__restaurant=restaurant, 
                is_available=True
            ))
            if not menu_items:
                continue
            
            # Random order date within last 60 days
            days_ago = random.randint(0, 60)
            hours_ago = random.randint(0, 23)
            minutes_ago = random.randint(0, 59)
            order_time = timezone.now() - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)
            
            # Random status based on age
            if days_ago <= 1:
                status = random.choice(['pending', 'confirmed', 'preparing', 'ready', 'out_for_delivery', 'delivered'])
            elif days_ago <= 7:
                status = random.choice(['delivered', 'delivered', 'delivered', 'cancelled', 'delivered'])
            else:
                status = random.choice(['delivered', 'delivered', 'delivered', 'cancelled', 'refunded'])
            
            order_type = random.choice(['delivery', 'pickup', 'dine_in'])
            
            # Calculate delivery fee
            delivery_fee = Decimal('5000') if order_type == 'delivery' else Decimal('0')
            
            # Create order
            order = Order.objects.create(
                customer=customer,
                restaurant=restaurant,
                order_type=order_type,
                status=status,
                special_instructions=random.choice(['', 'No onions please', 'Extra spicy', 'Call upon arrival', '']),
                delivery_fee=delivery_fee,
                loyalty_points_earned=0,
                loyalty_points_awarded=False,
                order_placed_at=order_time,
                confirmed_at=order_time + timedelta(minutes=random.randint(1, 10)) if status not in ['pending', 'cancelled'] else None,
                preparation_started_at=order_time + timedelta(minutes=random.randint(10, 20)) if status in ['preparing', 'ready', 'out_for_delivery', 'delivered'] else None,
                ready_at=order_time + timedelta(minutes=random.randint(25, 45)) if status in ['ready', 'out_for_delivery', 'delivered'] else None,
                delivered_at=order_time + timedelta(minutes=random.randint(45, 90)) if status == 'delivered' else None,
                cancelled_at=order_time + timedelta(minutes=random.randint(5, 30)) if status == 'cancelled' else None,
            )
            
            # Add order items (1-6 items)
            num_items = random.randint(1, 6)
            subtotal = Decimal('0')
            
            for _ in range(num_items):
                menu_item = random.choice(menu_items)
                quantity = random.randint(1, 3)
                unit_price = menu_item.price
                total_item_price = unit_price * quantity
                subtotal += total_item_price
                
                order_item = OrderItem.objects.create(
                    order=order,
                    menu_item=menu_item,
                    quantity=quantity,
                    unit_price=unit_price,
                    special_instructions=random.choice(['', 'Extra sauce', 'Well done', 'Light ice', '']),
                    total_price=total_item_price
                )
                order_items_created += 1
                
                # Add modifiers sometimes
                if random.random() > 0.7:
                    menu_item_modifiers = MenuItemModifier.objects.filter(
                        menu_item=menu_item
                    ).select_related('modifier_group')
                    
                    if menu_item_modifiers.exists():
                        menu_item_modifier = random.choice(menu_item_modifiers)
                        modifier_group = menu_item_modifier.modifier_group
                        
                        mods = list(ItemModifier.objects.filter(
                            modifier_group=modifier_group,
                            is_available=True
                        ))
                        
                        if mods:
                            modifier = random.choice(mods)
                            OrderItemModifier.objects.create(
                                order_item=order_item,
                                item_modifier=modifier,
                                quantity=1,
                                unit_price=modifier.price_modifier,
                                total_price=modifier.price_modifier
                            )
                            subtotal += modifier.price_modifier
            
            # Calculate totals
            tax_amount = subtotal * Decimal('0.18')
            total_amount = subtotal + tax_amount + delivery_fee
            
            order.subtotal = subtotal
            order.tax_amount = tax_amount
            order.total_amount = total_amount
            order.save()
            
            # Create payment
            if status != 'cancelled':
                payment_status = 'completed' if status == 'delivered' else random.choice(['pending', 'processing', 'completed'])
                payment_method = random.choice(['credit_card', 'mobile_wallet', 'cash', 'stripe'])
                
                Payment.objects.create(
                    order=order,
                    payment_method=payment_method,
                    payment_status=payment_status,
                    amount=total_amount,
                    transaction_id=f"TXN{random.randint(100000, 999999)}",
                    payment_completed_at=order_time + timedelta(minutes=random.randint(5, 20)) if payment_status == 'completed' else None
                )
            
            # Create tracking record
            OrderTracking.objects.create(
                order=order,
                status=status,
                description=f"Order {status}",
                created_at=order_time
            )
            
            # Award loyalty points for delivered orders
            if status == 'delivered' and not order.loyalty_points_awarded:
                try:
                    loyalty_settings = RestaurantLoyaltySettings.objects.filter(
                        restaurant=restaurant
                    ).first()
                    
                    if loyalty_settings and loyalty_settings.is_loyalty_active():
                        points_rate = loyalty_settings.effective_points_rate
                        points_earned = int(total_amount * points_rate)
                        
                        if points_earned > 0:
                            order.loyalty_points_earned = points_earned
                            order.loyalty_points_awarded = True
                            order.loyalty_points_awarded_at = order.delivered_at or timezone.now()
                            order.save()
                            
                            customer_loyalty, created = CustomerLoyalty.objects.get_or_create(
                                customer=customer,
                                program=loyalty_program
                            )
                            customer_loyalty.add_points(
                                points_earned,
                                reason=f"Order #{order.order_uuid}",
                                order=order,
                                restaurant=restaurant
                            )
                except Exception:
                    pass
            
            orders_created += 1
            
            if orders_created % 100 == 0:
                self.stdout.write(f"  Created {orders_created}/{order_count} orders")
        
        self.stdout.write(f"  ✅ Created {orders_created} orders with {order_items_created} order items")
        
        # Create carts (with duplicate handling)
        self._create_carts(customers)
    
    def _create_carts(self, customers):
        from api.models import Cart, CartItem, MenuItem, Restaurant
        from django.db import IntegrityError
        
        carts_created = 0
        cart_items_created = 0
        
        for customer in customers[:100]:
            # Check if cart already exists and has items
            from django.core.exceptions import ObjectDoesNotExist
            try:
                if hasattr(customer, 'cart') and customer.cart:
                    existing_cart = customer.cart
                    if existing_cart.cart_items.exists():
                        continue  # Skip if cart already has items
            except ObjectDoesNotExist:
                pass
            
            # Create cart
            cart = Cart(customer=customer)
            cart.save()
            
            # Add items
            restaurants_with_items = Restaurant.objects.filter(status='active')
            if restaurants_with_items:
                restaurant = random.choice(list(restaurants_with_items))
                menu_items = list(MenuItem.objects.filter(
                    category__restaurant=restaurant, 
                    is_available=True
                )[:15])
                
                if menu_items:
                    num_items = random.randint(0, 4)
                    selected_items = random.sample(menu_items, min(num_items, len(menu_items)))
                    
                    for menu_item in selected_items:
                        quantity = random.randint(1, 2)
                        
                        try:
                            cart_item, created = CartItem.objects.get_or_create(
                                cart=cart,
                                menu_item=menu_item,
                                defaults={
                                    'quantity': quantity,
                                    'unit_price': menu_item.price,
                                    'total_price': menu_item.price * quantity,
                                    'special_instructions': random.choice(['', 'Extra sauce', 'No onions', ''])
                                }
                            )
                            if created:
                                cart_items_created += 1
                        except IntegrityError:
                            continue
                    
                    cart.restaurant = restaurant
                    cart.save()
                    carts_created += 1
        
        self.stdout.write(f"  ✅ Created {carts_created} carts with {cart_items_created} items")