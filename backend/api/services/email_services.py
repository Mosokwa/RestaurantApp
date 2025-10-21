from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class EmailService:
    """
    Complete email service for sending all types of emails
    """
    
    @staticmethod
    def send_referral_email(referral, referral_url):
        """
        Send referral invitation email
        """
        try:
            subject = f"Join {settings.SITE_NAME} and get bonus rewards!"
            from_email = settings.DEFAULT_FROM_EMAIL
            to_email = referral.referred_email
            
            # Prepare email context
            context = {
                'referrer_name': referral.referrer.user.get_full_name() or referral.referrer.user.email,
                'site_name': settings.SITE_NAME,
                'referral_url': referral_url,
                'bonus_points': referral.referrer.loyalty_profile.program.signup_bonus_points,
            }
            
            # Render HTML and text content
            html_content = render_to_string('emails/referral_invitation.html', context)
            text_content = strip_tags(html_content)
            
            # Create and send email
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email,
                to=[to_email],
                reply_to=[settings.REPLY_TO_EMAIL]
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
            
            logger.info(f"Referral email sent to {to_email} from {referral.referrer.user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send referral email to {referral.referred_email}: {str(e)}")
            return False
    
    @staticmethod
    def send_reward_redemption_email(redemption):
        """
        Send reward redemption confirmation email
        """
        try:
            customer = redemption.customer_loyalty.customer.user
            subject = f"Your {settings.SITE_NAME} reward is ready!"
            from_email = settings.DEFAULT_FROM_EMAIL
            to_email = customer.email
            
            context = {
                'customer_name': customer.get_full_name() or customer.email,
                'reward_name': redemption.reward.name,
                'redemption_code': redemption.redemption_code,
                'points_used': redemption.points_used,
                'expires_at': redemption.expires_at,
            }
            
            html_content = render_to_string('emails/reward_redemption.html', context)
            text_content = strip_tags(html_content)
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email,
                to=[to_email]
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
            
            logger.info(f"Reward redemption email sent to {to_email} for reward {redemption.reward.reward_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send reward redemption email to {customer.email}: {str(e)}")
            return False
    
    @staticmethod
    def send_points_earned_email(transaction):
        """
        Send points earned notification email
        """
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
            }
            
            html_content = render_to_string('emails/points_earned.html', context)
            text_content = strip_tags(html_content)
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email,
                to=[to_email]
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
            
            logger.info(f"Points earned email sent to {to_email} for {transaction.points} points")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send points earned email to {customer.email}: {str(e)}")
            return False