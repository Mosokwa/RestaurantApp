from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
import logging
from .models import Order, Customer, LoyaltyProgram, CustomerLoyalty, RestaurantLoyaltySettings, Restaurant
from .services.loyalty_services import LoyaltyService

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Order)
def handle_order_status_change(sender, instance, created, **kwargs):
    """
    Handle order status changes and award loyalty points when order is delivered
    """
    if created:
        return  # Only process updates, not creations
    
    try:
        # Check if this is a status change to 'delivered'
        if instance.status == 'delivered' and instance.tracker.has_changed('status'):
            logger.info(f"Order {instance.order_id} delivered, processing loyalty points")
            
            # Use the production-ready service to award points
            success, message = LoyaltyService.award_order_points(instance)
            
            if success:
                logger.info(f"Successfully awarded loyalty points for order {instance.order_id}: {message}")
            else:
                logger.warning(f"Failed to award loyalty points for order {instance.order_id}: {message}")
    
    except Exception as e:
        logger.error(f"Error processing loyalty points for order {instance.order_id}: {e}")

@receiver(post_save, sender=Customer)
def create_loyalty_profile(sender, instance, created, **kwargs):
    """
    Create loyalty profile when new customer is created with comprehensive error handling
    """
    if created:
        try:
            # Get or create default loyalty program
            program, created_program = LoyaltyProgram.objects.get_or_create(
                is_active=True,
                defaults={
                    'name': 'Default Loyalty Program',
                    'points_per_dollar': 1.00,
                    'signup_bonus_points': 100,
                    'referral_bonus_points': 500,
                    'bronze_min_points': 0,
                    'silver_min_points': 1000,
                    'gold_min_points': 5000,
                    'platinum_min_points': 15000,
                }
            )
            
            # Create loyalty profile
            loyalty_profile = CustomerLoyalty.objects.create(
                customer=instance,
                program=program
            )
            
            # Add signup bonus points
            if program.signup_bonus_points > 0:
                success, message = loyalty_profile.add_points(
                    program.signup_bonus_points,
                    reason="Welcome bonus"
                )
                
                if success:
                    logger.info(f"Added signup bonus points to customer {instance.id}")
                else:
                    logger.warning(f"Failed to add signup bonus points to customer {instance.id}: {message}")
            
            logger.info(f"Created loyalty profile for customer {instance.id}")
        
        except Exception as e:
            logger.error(f"Error creating loyalty profile for customer {instance.id}: {e}")
            # Don't raise exception to avoid breaking customer creation

@receiver(post_save, sender=Restaurant)
def create_default_loyalty_settings(sender, instance, created, **kwargs):
    """
    Create default loyalty settings when new restaurant is created
    """
    if created:
        try:
            # Create default enabled settings for new restaurants
            RestaurantLoyaltySettings.objects.create(
                restaurant=instance,
                is_loyalty_enabled=True  # Enable by default for new restaurants
            )
            logger.info(f"Created default loyalty settings for restaurant {instance.restaurant_id}")
        
        except Exception as e:
            logger.error(f"Error creating loyalty settings for restaurant {instance.restaurant_id}: {e}")

@receiver(pre_save, sender=CustomerLoyalty)
def update_tier_on_points_change(sender, instance, **kwargs):
    """
    Update customer tier when points change
    """
    if instance.pk:  # Only for existing instances
        try:
            old_instance = CustomerLoyalty.objects.get(pk=instance.pk)
            if old_instance.current_points != instance.current_points:
                instance._update_tier()
        except CustomerLoyalty.DoesNotExist:
            pass

# Additional signal for handling referral completions
@receiver(post_save, sender=CustomerLoyalty)
def handle_referral_completion(sender, instance, created, **kwargs):
    """
    Handle referral completion when a referred customer creates their first order
    """
    if created and instance.referred_by:
        try:
            # Wait for the first order to be completed before awarding referral bonus
            # This will be handled by a separate process or when the first order is delivered
            logger.info(f"New customer {instance.customer.id} was referred by {instance.referred_by.id}")
        except Exception as e:
            logger.error(f"Error handling referral completion for customer {instance.customer.id}: {e}")