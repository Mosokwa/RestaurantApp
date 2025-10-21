# Create signals.py
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from api.models import Order, RestaurantReview, Reservation
from .models import UserBehavior

@receiver(post_save, sender=Order)
def track_order_behavior(sender, instance, created, **kwargs):
    """Track order behaviors automatically"""
    if created and instance.customer:
        UserBehavior.objects.create(
            user=instance.customer.user,
            behavior_type='order',
            restaurant=instance.restaurant,
            value=float(instance.total_amount),
            metadata={
                'order_id': instance.order_id,
                'status': instance.status,
                'items_count': instance.order_items.count()
            }
        )

@receiver(post_save, sender=RestaurantReview)
def track_review_behavior(sender, instance, created, **kwargs):
    """Track review behaviors automatically"""
    if created and instance.customer:
        UserBehavior.objects.create(
            user=instance.customer.user,
            behavior_type='rating',
            restaurant=instance.restaurant,
            value=float(instance.rating),
            metadata={
                'review_id': instance.review_id,
                'comment_length': len(instance.comment) if instance.comment else 0
            }
        )

# Reservation signals
@receiver(pre_save, sender=Reservation)
def validate_reservation(sender, instance, **kwargs):
    """Validate reservation before saving"""
    if instance.table and instance.status in ['confirmed', 'pending', 'seated']:
        if instance.check_time_conflicts():
            raise ValueError("Time conflict with existing reservation")

@receiver(post_save, sender=Reservation)
def handle_reservation_notifications(sender, instance, created, **kwargs):
    """Handle reservation notifications"""
    if created:
        send_reservation_confirmation(instance)
    elif instance.status == 'cancelled':
        send_reservation_cancellation(instance)

def send_reservation_confirmation(reservation):
    """Send reservation confirmation email"""
    subject = f"Reservation Confirmation - {reservation.restaurant.name}"
    message = f"""
    Dear {reservation.customer.user.get_full_name() or reservation.customer.user.username},
    
    Your reservation has been confirmed!
    
    Reservation Details:
    - Restaurant: {reservation.restaurant.name}
    - Date: {reservation.reservation_date}
    - Time: {reservation.reservation_time}
    - Party Size: {reservation.party_size}
    - Reservation Code: {reservation.reservation_code}
    
    Thank you for choosing us!
    """
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [reservation.customer.user.email],
        fail_silently=False,
    )

def send_reservation_cancellation(reservation):
    """Send reservation cancellation email"""
    subject = f"Reservation Cancelled - {reservation.restaurant.name}"
    message = f"""
    Dear {reservation.customer.user.get_full_name() or reservation.customer.user.username},
    
    Your reservation has been cancelled.
    
    Reservation Details:
    - Restaurant: {reservation.restaurant.name}
    - Date: {reservation.reservation_date}
    - Time: {reservation.reservation_time}
    - Reservation Code: {reservation.reservation_code}
    
    We hope to see you another time!
    """
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [reservation.customer.user.email],
        fail_silently=False,
    )