from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class EmailService:
    
    @staticmethod
    def send_referral_email(referral, referral_url):
        """Send referral invitation email"""
        try:
            subject = f"Join {settings.SITE_NAME} and get bonus rewards!"
            from_email = settings.DEFAULT_FROM_EMAIL
            to_email = referral.referred_email
            
            context = {
                'referrer_name': referral.referrer.user.get_full_name() or referral.referrer.user.email,
                'site_name': settings.SITE_NAME,
                'referral_url': referral_url,
                'referral_code': referral.referral_code,
                'bonus_points': referral.referrer.loyalty_profile.program.global_signup_bonus_points,
                'current_year': timezone.now().year,
            }
            
            html_content = render_to_string('emails/referral_invitation.html', context)
            text_content = strip_tags(html_content)
            
            email = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
            email.attach_alternative(html_content, "text/html")
            email.send()
            
            logger.info(f"Referral email sent to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send referral email: {str(e)}")
            return False

    @staticmethod
    def send_points_earned_email(transaction):
        """Send points earned notification"""
        try:
            customer = transaction.customer_loyalty.customer.user
            subject = f"You earned {transaction.points} points at {settings.SITE_NAME}!"
            from_email = settings.DEFAULT_FROM_EMAIL
            to_email = customer.email
            
            context = {
                'customer_name': customer.get_full_name() or customer.email,
                'points_earned': transaction.points,
                'reason': transaction.reason,
                'current_points': transaction.customer_loyalty.current_points,
                'restaurant_name': transaction.restaurant.name if transaction.restaurant else settings.SITE_NAME,
                'site_name': settings.SITE_NAME,
                'current_year': timezone.now().year,
            }
            
            html_content = render_to_string('emails/points_earned.html', context)
            text_content = strip_tags(html_content)
            
            email = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
            email.attach_alternative(html_content, "text/html")
            email.send()
            
            logger.info(f"Points earned email sent to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send points earned email: {str(e)}")
            return False

    @staticmethod
    def send_reward_redemption_email(redemption):
        """Send reward redemption confirmation"""
        try:
            customer = redemption.customer_loyalty.customer.user
            subject = f"Your {settings.SITE_NAME} reward is ready!"
            from_email = settings.DEFAULT_FROM_EMAIL
            to_email = customer.email
            
            context = {
                'customer_name': customer.get_full_name() or customer.email,
                'reward_name': redemption.reward.name,
                'points_used': redemption.points_used,
                'redemption_code': redemption.redemption_code,
                'restaurant_name': redemption.restaurant.name,
                'expires_at': redemption.expires_at,
                'site_name': settings.SITE_NAME,
                'current_year': timezone.now().year,
            }
            
            html_content = render_to_string('emails/reward_redemption.html', context)
            text_content = strip_tags(html_content)
            
            email = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
            email.attach_alternative(html_content, "text/html")
            email.send()
            
            logger.info(f"Reward redemption email sent to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send reward redemption email: {str(e)}")
            return False

    @staticmethod
    def send_welcome_email(loyalty_profile, restaurant):
        """Send welcome email with bonus points"""
        try:
            customer = loyalty_profile.customer.user
            subject = f"Welcome to {settings.SITE_NAME} Loyalty Program!"
            from_email = settings.DEFAULT_FROM_EMAIL
            to_email = customer.email
            
            # Calculate next tier
            program = loyalty_profile.program
            next_tier = "Silver" if loyalty_profile.tier == "bronze" else "Gold" if loyalty_profile.tier == "silver" else "Platinum"
            next_tier_points = program.silver_min_points if loyalty_profile.tier == "bronze" else program.gold_min_points if loyalty_profile.tier == "silver" else program.platinum_min_points
            
            context = {
                'customer_name': customer.get_full_name() or customer.email,
                'program_name': program.name,
                'bonus_points': loyalty_profile.program.global_signup_bonus_points,
                'current_points': loyalty_profile.current_points,
                'current_tier': loyalty_profile.tier.title(),
                'next_tier': next_tier,
                'next_tier_points': next_tier_points,
                'site_name': settings.SITE_NAME,
                'current_year': timezone.now().year,
            }
            
            html_content = render_to_string('emails/welcome_bonus.html', context)
            text_content = strip_tags(html_content)
            
            email = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
            email.attach_alternative(html_content, "text/html")
            email.send()
            
            logger.info(f"Welcome email sent to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send welcome email: {str(e)}")
            return False

    @staticmethod
    def send_tier_upgrade_email(loyalty_profile, old_tier, new_tier, new_benefits):
        """Send tier upgrade notification"""
        try:
            customer = loyalty_profile.customer.user
            subject = f"Congratulations! You've reached {new_tier} tier at {settings.SITE_NAME}!"
            from_email = settings.DEFAULT_FROM_EMAIL
            to_email = customer.email
            
            # Calculate next tier info
            program = loyalty_profile.program
            tier_order = ['bronze', 'silver', 'gold', 'platinum']
            current_index = tier_order.index(new_tier)
            next_tier = tier_order[current_index + 1] if current_index + 1 < len(tier_order) else None
            points_to_next = program.gold_min_points - loyalty_profile.current_points if next_tier == "gold" else program.platinum_min_points - loyalty_profile.current_points if next_tier == "platinum" else 0
            
            context = {
                'customer_name': customer.get_full_name() or customer.email,
                'new_tier': new_tier,
                'current_points': loyalty_profile.current_points,
                'restaurant_count': len(loyalty_profile.restaurant_stats),
                'new_benefits': new_benefits,
                'next_tier': next_tier.title() if next_tier else "Maximum",
                'points_to_next_tier': points_to_next if next_tier else 0,
                'site_name': settings.SITE_NAME,
                'current_year': timezone.now().year,
            }
            
            html_content = render_to_string('emails/tier_upgrade.html', context)
            text_content = strip_tags(html_content)
            
            email = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
            email.attach_alternative(html_content, "text/html")
            email.send()
            
            logger.info(f"Tier upgrade email sent to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send tier upgrade email: {str(e)}")
            return False