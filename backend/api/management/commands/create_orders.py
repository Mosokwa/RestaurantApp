# management/commands/create_orders.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
import random
from decimal import Decimal
from api.models.order_models import Order, OrderItem, Cart, CartItem, Payment, OrderTracking
from api.models.restaurant_models import Restaurant, Branch
from api.models.user_models import Customer
from api.models.menu_models import MenuItem
from api.models.ratingsandreviews_models import OfferUsage
from api.models.menu_models import SpecialOffer

class Command(BaseCommand):
    help = 'Create order history for customers'
    
    def handle(self, *args, **options):
        customers = Customer.objects.all()[:150]
        restaurants = Restaurant.objects.all()
        
        status_choices = ['delivered', 'delivered', 'delivered', 'delivered', 'cancelled', 'pending']
        order_types = ['delivery', 'pickup', 'dine_in']
        payment_methods = ['credit_card', 'debit_card', 'cash', 'mobile_wallet']
        
        orders_created = 0
        
        for i in range(1000):
            customer = random.choice(customers)
            restaurant = random.choice(restaurants)
            branch = restaurant.branches.first()
            
            days_ago = random.randint(0, 180)
            order_date = timezone.now() - timedelta(days=days_ago)
            
            status = random.choice(status_choices)
            order_type = random.choice(order_types)
            
            order = Order.objects.create(
                customer=customer,
                restaurant=restaurant,
                branch=branch,
                order_type=order_type,
                status=status,
                order_placed_at=order_date,
                subtotal=Decimal('0'),
                total_amount=Decimal('0')
            )
            
            num_items = random.randint(1, 6)
            menu_items = MenuItem.objects.filter(category__restaurant=restaurant, is_available=True)
            
            if menu_items.exists():
                selected_items = random.sample(list(menu_items), min(num_items, menu_items.count()))
                
                order_subtotal = Decimal('0')
                for menu_item in selected_items:
                    quantity = random.randint(1, 4)
                    unit_price = menu_item.price
                    total_price = unit_price * quantity
                    order_subtotal += total_price
                    
                    OrderItem.objects.create(
                        order=order,
                        menu_item=menu_item,
                        quantity=quantity,
                        unit_price=unit_price,
                        total_price=total_price
                    )
                
                discount_amount = Decimal('0')
                
                # Apply special offer 30% of the time
                if random.random() < 0.3:
                    offers = SpecialOffer.objects.filter(restaurant=restaurant, is_active=True)
                    if offers.exists():
                        offer = random.choice(list(offers))
                        if offer.offer_type == 'percentage':
                            discount_amount = (order_subtotal * offer.discount_value) / Decimal('100')
                        elif offer.offer_type == 'fixed':
                            discount_amount = min(offer.discount_value, order_subtotal)
                        
                        # Record offer usage
                        OfferUsage.objects.create(
                            offer=offer,
                            customer=customer,
                            order=order,
                            discount_applied=discount_amount,
                            original_order_amount=order_subtotal,
                            final_order_amount=order_subtotal - discount_amount,
                            is_successful=True,
                            redeemed_at=order_date
                        )
                
                tax_amount = order_subtotal * Decimal('0.18')
                delivery_fee = Decimal('3000') if order_type == 'delivery' else Decimal('0')
                total_amount = order_subtotal + tax_amount + delivery_fee - discount_amount
                
                order.subtotal = order_subtotal
                order.tax_amount = tax_amount
                order.delivery_fee = delivery_fee
                order.discount_amount = discount_amount
                order.total_amount = total_amount
                
                if status == 'delivered':
                    order.confirmed_at = order_date + timedelta(minutes=5)
                    order.preparation_started_at = order_date + timedelta(minutes=10)
                    order.ready_at = order_date + timedelta(minutes=30)
                    order.delivered_at = order_date + timedelta(minutes=60)
                elif status == 'cancelled':
                    order.cancelled_at = order_date + timedelta(minutes=10)
                
                order.save()
                
                # Create payment
                Payment.objects.create(
                    order=order,
                    payment_method=random.choice(payment_methods),
                    payment_status='completed' if status == 'delivered' else 'pending',
                    amount=total_amount,
                    transaction_id=f'TXN{random.randint(100000, 999999)}',
                    payment_completed_at=order.delivered_at if status == 'delivered' else None
                )
                
                # Create order tracking
                tracking_statuses = ['pending', 'confirmed', 'preparing', 'ready']
                if status == 'delivered':
                    tracking_statuses.extend(['out_for_delivery', 'delivered'])
                elif status == 'cancelled':
                    tracking_statuses.append('cancelled')
                
                for track_status in tracking_statuses:
                    track_time = order_date
                    if track_status == 'confirmed':
                        track_time += timedelta(minutes=5)
                    elif track_status == 'preparing':
                        track_time += timedelta(minutes=10)
                    elif track_status == 'ready':
                        track_time += timedelta(minutes=30)
                    elif track_status == 'out_for_delivery':
                        track_time += timedelta(minutes=45)
                    elif track_status == 'delivered':
                        track_time += timedelta(minutes=60)
                    
                    OrderTracking.objects.create(
                        order=order,
                        status=track_status,
                        description=f'Order marked as {track_status}',
                        created_at=track_time
                    )
                
                orders_created += 1
                
                # Update menu item popularity
                for menu_item in selected_items:
                    quantity = OrderItem.objects.filter(order=order, menu_item=menu_item).first().quantity
                    menu_item.order_count += quantity
                    menu_item.last_ordered = order_date
                    menu_item.popularity_score += random.randint(5, 15)
                    menu_item.save()
        
        self.stdout.write(self.style.SUCCESS(f'Created {orders_created} orders with payments and tracking'))