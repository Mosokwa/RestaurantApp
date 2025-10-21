from django.db import transaction, DatabaseError, models
from django.utils import timezone
# from django.core.exceptions import ValidationError
from decimal import Decimal, ROUND_HALF_UP
import logging
from ..models import Referral, MultiRestaurantLoyaltyProgram, CustomerLoyalty, RestaurantLoyaltySettings, Reward
from .email_services import EmailService

logger = logging.getLogger(__name__)

class MultiRestaurantLoyaltyService:
    """
    Production-ready service for handling loyalty across multiple restaurants
    """
    
    @staticmethod
    def get_available_programs_for_restaurant(restaurant):
        """Get all available loyalty programs for a specific restaurant"""
        return MultiRestaurantLoyaltyProgram.objects.filter(
            is_active=True
        ).filter(
            models.Q(program_type='global') |
            models.Q(participating_restaurants=restaurant)
        ).distinct()
    
    @staticmethod
    def get_default_program_for_restaurant(restaurant):
        """Get the default loyalty program for a restaurant"""
        programs = MultiRestaurantLoyaltyService.get_available_programs_for_restaurant(restaurant)
        return programs.first()  # Or implement more sophisticated logic
    
    @staticmethod
    @transaction.atomic
    def award_order_points(order):
        """COMPLETE implementation - no missing parts"""
        try:
            if not order.can_award_loyalty_points():
                return False, "Order is not eligible for loyalty points"
            
            program = MultiRestaurantLoyaltyService.get_default_program_for_restaurant(order.restaurant)
            if not program:
                return False, "No loyalty program available for this restaurant"
            
            try:
                loyalty_profile = order.customer.loyalty_profile.get(program=program)
            except CustomerLoyalty.DoesNotExist:
                return False, "Customer is not enrolled in this restaurant's loyalty program"
            
            try:
                loyalty_settings = order.restaurant.loyalty_settings.get(program=program)
                if not loyalty_settings.is_loyalty_active():
                    return False, "Loyalty program is disabled for this restaurant"
                
                if (loyalty_settings.minimum_order_amount_for_points > 0 and 
                    order.subtotal < loyalty_settings.minimum_order_amount_for_points):
                    return False, f"Order amount below minimum for points (${loyalty_settings.minimum_order_amount_for_points})"
                
                points_rate = loyalty_settings.effective_points_rate
                
            except RestaurantLoyaltySettings.DoesNotExist:
                return False, "This restaurant is not configured for the loyalty program"
            
            points_to_add = (order.subtotal * points_rate).quantize(Decimal('1.'), rounding=ROUND_HALF_UP)
            points_to_add = int(points_to_add)
            
            if points_to_add <= 0:
                return False, "No points to award for this order"
            
            success, message = loyalty_profile.add_points(
                points_to_add,
                reason=f"Order at {order.restaurant.name} - #{order.order_uuid}",
                order=order,
                restaurant=order.restaurant
            )
            
            if success:
                order.loyalty_points_earned = points_to_add
                order.loyalty_points_awarded = True
                order.loyalty_points_awarded_at = timezone.now()
                order.loyalty_program_used = program
                order.save()
                
                try:
                    from ..models import PointsTransaction
                    latest_transaction = PointsTransaction.objects.filter(
                        customer_loyalty=loyalty_profile,
                        order=order
                    ).first()
                    if latest_transaction:
                        EmailService.send_points_earned_email(latest_transaction)
                except Exception as e:
                    logger.error(f"Failed to send points earned email: {e}")
                
                logger.info(f"Awarded {points_to_add} points to customer {order.customer.id} for order {order.order_id} at {order.restaurant.name}")
                return True, f"Successfully awarded {points_to_add} loyalty points"
            else:
                logger.error(f"Failed to award points for order {order.order_id}: {message}")
                return False, message
                
        except Exception as e:
            logger.error(f"Unexpected error awarding points for order {order.order_id}: {e}")
            return False, "An unexpected error occurred while processing loyalty points"


    @staticmethod
    @transaction.atomic
    def enroll_customer_in_program(customer, restaurant):
        """COMPLETE implementation"""
        try:
            program = MultiRestaurantLoyaltyService.get_default_program_for_restaurant(restaurant)
            if not program:
                return False, "No loyalty program available for this restaurant"
            
            if customer.loyalty_profile.filter(program=program).exists():
                return False, "Customer is already enrolled in this program"
            
            loyalty_profile = CustomerLoyalty.objects.create(
                customer=customer,
                program=program
            )
            
            try:
                loyalty_settings = restaurant.loyalty_settings.get(program=program)
                signup_bonus = loyalty_settings.effective_signup_bonus
            except RestaurantLoyaltySettings.DoesNotExist:
                signup_bonus = program.global_signup_bonus_points
            
            if signup_bonus > 0:
                success, message = loyalty_profile.add_points(
                    signup_bonus,
                    reason=f"Welcome bonus at {restaurant.name}",
                    restaurant=restaurant
                )
                
                if success:
                    logger.info(f"Enrolled customer {customer.id} in program {program.program_id} with {signup_bonus} bonus points")
                else:
                    logger.warning(f"Failed to award signup bonus to customer {customer.id}: {message}")
            
            return True, loyalty_profile
            
        except Exception as e:
            logger.error(f"Error enrolling customer {customer.id} in program: {e}")
            return False, f"Error enrolling in loyalty program: {str(e)}"

    @staticmethod
    def get_customer_loyalty_status(customer, restaurant):
        """
        Get customer's loyalty status for a specific restaurant
        """
        try:
            program = MultiRestaurantLoyaltyService.get_default_program_for_restaurant(restaurant)
            if not program:
                return None
            
            try:
                loyalty_profile = customer.loyalty_profile.get(program=program)
                restaurant_stats = loyalty_profile.get_restaurant_stats(restaurant)
                tier_benefits = loyalty_profile.get_tier_benefits(restaurant)
                
                return {
                    'is_enrolled': True,
                    'loyalty_profile': loyalty_profile,
                    'restaurant_stats': restaurant_stats,
                    'tier_benefits': tier_benefits,
                    'program': program,
                }
            except CustomerLoyalty.DoesNotExist:
                return {
                    'is_enrolled': False,
                    'program': program,
                }
                
        except Exception as e:
            logger.error(f"Error getting loyalty status for customer {customer.id} at {restaurant.name}: {e}")
            return None

    @staticmethod
    def get_available_rewards_for_restaurant(customer, restaurant):
        """
        Get rewards available to a customer at a specific restaurant
        """
        try:
            program = MultiRestaurantLoyaltyService.get_default_program_for_restaurant(restaurant)
            if not program:
                return []
            
            try:
                loyalty_profile = customer.loyalty_profile.get(program=program)
                
                # Get rewards available for this restaurant
                available_rewards = Reward.objects.filter(
                    program=program,
                    is_active=True,
                    min_tier_required__in=MultiRestaurantLoyaltyService._get_eligible_tiers(loyalty_profile.tier),
                    points_required__lte=loyalty_profile.current_points
                ).filter(
                    models.Q(restaurant=restaurant) |
                    models.Q(restaurant__isnull=True) |
                    models.Q(applicable_restaurants=restaurant)
                ).filter(
                    valid_from__lte=timezone.now()
                ).filter(
                    models.Q(valid_until__isnull=True) | models.Q(valid_until__gte=timezone.now())
                ).distinct()
                
                # Filter by restaurant-specific availability
                available_rewards = [
                    reward for reward in available_rewards 
                    if reward.is_available(restaurant) and reward.can_redeem_at_restaurant(restaurant)
                ]
                
                return available_rewards
                
            except CustomerLoyalty.DoesNotExist:
                return []
                
        except Exception as e:
            logger.error(f"Error getting available rewards for customer {customer.id} at {restaurant.name}: {e}")
            return []

    @staticmethod
    def _get_eligible_tiers(current_tier):
        """Get tiers that are eligible based on current tier"""
        tier_order = ['bronze', 'silver', 'gold', 'platinum']
        current_index = tier_order.index(current_tier)
        return tier_order[:current_index + 1]

    @staticmethod
    def _check_referral_completion(customer, order):
        """
        Check if this order completes any pending referrals
        """
        try:
            # Check if this customer was referred and this is their first completed order
            if customer.orders.filter(status='delivered').count() == 1:  # First completed order
                pending_referrals = Referral.objects.filter(
                    referred_email=customer.user.email,
                    status='pending'
                )
                
                for referral in pending_referrals:
                    if not referral.is_expired():
                        success, message = referral.complete_referral(customer)
                        if success:
                            logger.info(f"Completed referral {referral.referral_id} for customer {customer.id}")
                        else:
                            logger.warning(f"Failed to complete referral {referral.referral_id}: {message}")
        except Exception as e:
            logger.error(f"Error checking referral completion for customer {customer.id}: {e}")

    @staticmethod
    @transaction.atomic
    def process_referral(inviter_loyalty, referred_email):
        """
        Process a new referral invitation
        """
        try:
            # Check if email is already registered
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            if User.objects.filter(email=referred_email).exists():
                return False, "This email is already registered"
            
            # Check for existing pending referral to this email
            existing_referral = Referral.objects.filter(
                referrer=inviter_loyalty.customer,
                referred_email=referred_email,
                status='pending'
            ).first()
            
            if existing_referral:
                if existing_referral.is_expired():
                    existing_referral.status = 'expired'
                    existing_referral.save()
                else:
                    return False, "You have already sent a referral to this email"
            
            # Create new referral
            referral = Referral.objects.create(
                referrer=inviter_loyalty.customer,
                referred_email=referred_email,
                referral_code=inviter_loyalty.referral_code
            )
            
            # Generate referral URL
            from django.urls import reverse
            from django.conf import settings
            referral_url = f"{settings.FRONTEND_URL}{reverse('signup')}?ref={referral.referral_token}"
            
            # Send referral email
            email_sent = EmailService.send_referral_email(referral, referral_url)
            
            if email_sent:
                logger.info(f"Referral created and email sent: {referral.referral_id}")
                return True, referral
            else:
                referral.delete()
                return False, "Failed to send referral email"
                
        except Exception as e:
            logger.error(f"Error processing referral: {e}")
            return False, "Error processing referral"

    @staticmethod
    @transaction.atomic
    def process_referral_bonus(referrer_loyalty, referred_customer):
        """
        Process referral bonus for both referrer and referred customer
        """
        try:
            program = referrer_loyalty.program
            
            # Award bonus to referrer
            if program.referral_bonus_points > 0:
                success, message = referrer_loyalty.add_points(
                    program.referral_bonus_points,
                    reason=f"Referral bonus for {referred_customer.user.email}",
                    restaurant=None
                )
                if not success:
                    logger.error(f"Failed to award referral bonus to referrer {referrer_loyalty.customer.id}: {message}")
                    return False, message
            
            # Award bonus to referred customer (if they have loyalty profile)
            try:
                referred_loyalty = referred_customer.loyalty_profile
                if program.signup_bonus_points > 0:
                    success, message = referred_loyalty.add_points(
                        program.signup_bonus_points,
                        reason="Referral signup bonus",
                        restaurant=None
                    )
                    if not success:
                        logger.error(f"Failed to award referral bonus to referred customer {referred_customer.id}: {message}")
            except Exception as e:
                logger.warning(f"Referred customer {referred_customer.id} has no loyalty profile: {e}")
            
            logger.info(f"Processed referral bonus for referrer {referrer_loyalty.customer.id} and referred customer {referred_customer.id}")
            return True, "Referral bonus processed successfully"
            
        except Exception as e:
            logger.error(f"Error processing referral bonus: {e}")
            return False, "Error processing referral bonus"

    @staticmethod
    @transaction.atomic
    def redeem_points_for_reward(customer_loyalty, reward, restaurant=None):
        """
        Redeem points for a reward with comprehensive validation
        """
        try:
            # Validate reward availability
            if not reward.is_available(restaurant):
                return False, "Reward is not available for redemption"
            
            # Validate customer has enough points
            if customer_loyalty.current_points < reward.points_required:
                return False, "Insufficient points for this reward"
            
            # Validate tier requirements
            tier_order = ['bronze', 'silver', 'gold', 'platinum']
            current_tier_index = tier_order.index(customer_loyalty.tier)
            required_tier_index = tier_order.index(reward.min_tier_required)
            
            if current_tier_index < required_tier_index:
                return False, f"This reward requires {reward.min_tier_required} tier or higher"
            
            # Validate restaurant-specific restrictions
            if restaurant and not reward.can_redeem_at_restaurant(restaurant):
                return False, "This reward cannot be redeemed at the selected restaurant"
            
            # Check restaurant loyalty settings
            if restaurant:
                try:
                    loyalty_settings = restaurant.loyalty_settings
                    if not loyalty_settings.allow_reward_redemption:
                        return False, "Reward redemption is disabled for this restaurant"
                except Exception:
                    pass  # No settings, allow by default
            
            # Create redemption record
            from ..models import RewardRedemption
            redemption = RewardRedemption.objects.create(
                customer_loyalty=customer_loyalty,
                reward=reward,
                points_used=reward.points_required,
                restaurant=restaurant if restaurant else reward.restaurant,
                expires_at=timezone.now() + timezone.timedelta(days=30)
            )
            
            # Deduct points
            success, message = customer_loyalty.redeem_points(
                reward.points_required, 
                reward, 
                restaurant
            )
            
            if not success:
                # Delete the redemption record if points deduction failed
                redemption.delete()
                return False, message
            
            # Handle reward type specific logic
            if reward.reward_type == 'discount':
                MultiRestaurantLoyaltyService._create_discount_voucher(redemption, reward, restaurant)
            
            # Update reward redemption count
            reward.redeemed_count += 1
            reward.save()
            
            logger.info(f"Customer {customer_loyalty.customer.id} redeemed reward {reward.reward_id} for {reward.points_required} points")
            return True, redemption
            
        except DatabaseError as e:
            logger.error(f"Database error redeeming reward {reward.reward_id} for customer {customer_loyalty.customer.id}: {e}")
            return False, "Database error occurred while processing reward redemption"
        except Exception as e:
            logger.error(f"Unexpected error redeeming reward {reward.reward_id} for customer {customer_loyalty.customer.id}: {e}")
            return False, "An unexpected error occurred while processing reward redemption"

    @staticmethod
    def _create_discount_voucher(redemption, reward, restaurant):
        """Create discount voucher for discount-type rewards"""
        from ..models import DiscountVoucher
        
        voucher_code = f"DISC-{redemption.redemption_code}"
        
        discount_value = reward.discount_amount
        if reward.discount_percentage:
            discount_value = reward.discount_percentage
        
        voucher = DiscountVoucher.objects.create(
            code=voucher_code,
            restaurant=restaurant if restaurant else reward.restaurant,
            discount_type='percentage' if reward.discount_percentage else 'fixed',
            discount_value=discount_value,
            max_discount_amount=reward.discount_amount if reward.discount_percentage else None,
            valid_until=redemption.expires_at
        )
        
        redemption.discount_voucher = voucher
        redemption.save()

    @staticmethod
    def expire_points():
        """
        Expire points that have reached their expiration date
        """
        try:
            from ..models import PointsTransaction
            expired_transactions = PointsTransaction.objects.filter(
                expires_at__lte=timezone.now(),
                is_active=True,
                points__gt=0  # Only expire earned points, not redemptions
            )
            
            expired_count = 0
            for transaction in expired_transactions:
                with transaction.atomic():
                    # Create expiration transaction
                    PointsTransaction.objects.create(
                        customer_loyalty=transaction.customer_loyalty,
                        points=-transaction.points,
                        transaction_type='expired',
                        reason="Points expired",
                        restaurant=transaction.restaurant,
                        is_active=False
                    )
                    
                    # Update customer loyalty points
                    loyalty_profile = transaction.customer_loyalty
                    loyalty_profile.current_points = max(0, loyalty_profile.current_points - transaction.points)
                    loyalty_profile.save()
                    
                    # Mark original transaction as inactive
                    transaction.is_active = False
                    transaction.save()
                    
                    expired_count += 1
            
            logger.info(f"Expired points for {expired_count} transactions")
            return expired_count
            
        except Exception as e:
            logger.error(f"Error expiring points: {e}")
            return 0

class LoyaltyValidationService:
    """
    Service for validating loyalty-related operations
    """
    
    @staticmethod
    def validate_order_for_points(order):
        """
        Comprehensive validation for order points eligibility
        """
        errors = []
        
        if not order:
            errors.append("Order is required")
            return False, errors
        
        # Check order status
        if order.status != 'delivered':
            errors.append("Order must be delivered to earn points")
        
        # Check if points already awarded
        if order.loyalty_points_awarded:
            errors.append("Loyalty points have already been awarded for this order")
        
        # Check customer
        try:
            loyalty_profile = order.customer.loyalty_profile
            if not loyalty_profile:
                errors.append("Customer does not have a loyalty profile")
        except Exception:
            errors.append("Customer does not have a loyalty profile")
        
        # Check restaurant loyalty settings
        try:
            loyalty_settings = order.restaurant.loyalty_settings
            if not loyalty_settings.is_loyalty_active():
                errors.append("Loyalty program is disabled for this restaurant")
            
            # Check minimum order amount
            if (loyalty_settings.minimum_order_amount_for_points > 0 and 
                order.subtotal < loyalty_settings.minimum_order_amount_for_points):
                errors.append(f"Order amount below minimum for points (${loyalty_settings.minimum_order_amount_for_points})")
                
        except Exception:
            # Check if global program exists
            try:
                from ..models import LoyaltyProgram
                program = LoyaltyProgram.objects.filter(is_active=True).first()
                if not program:
                    errors.append("No active loyalty program found")
            except Exception:
                errors.append("No active loyalty program found")
        
        return len(errors) == 0, errors

    @staticmethod
    def validate_reward_redemption(customer_loyalty, reward, restaurant=None):
        """
        Comprehensive validation for reward redemption
        """
        errors = []
        
        if not customer_loyalty:
            errors.append("Customer loyalty profile is required")
        
        if not reward:
            errors.append("Reward is required")
        
        if not errors:
            # Check reward availability
            if not reward.is_available(restaurant):
                errors.append("Reward is not available for redemption")
            
            # Check points balance
            if customer_loyalty.current_points < reward.points_required:
                errors.append("Insufficient points for this reward")
            
            # Check tier requirements
            tier_order = ['bronze', 'silver', 'gold', 'platinum']
            current_tier_index = tier_order.index(customer_loyalty.tier)
            required_tier_index = tier_order.index(reward.min_tier_required)
            
            if current_tier_index < required_tier_index:
                errors.append(f"This reward requires {reward.min_tier_required} tier or higher")
            
            # Check restaurant restrictions
            if restaurant and not reward.can_redeem_at_restaurant(restaurant):
                errors.append("This reward cannot be redeemed at the selected restaurant")
            
            # Check restaurant loyalty settings
            if restaurant:
                try:
                    loyalty_settings = restaurant.loyalty_settings
                    if not loyalty_settings.allow_reward_redemption:
                        errors.append("Reward redemption is disabled for this restaurant")
                except Exception:
                    pass  # No settings, allow by default
        
        return len(errors) == 0, errors