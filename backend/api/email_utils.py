import logging
import random
import string
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger('api.auth')

def send_verification_email(user):
    """Send a verification email with a 6-digit code (compatible with frontend)"""
    try:
        # Generate a 6-digit verification code
        verification_code = ''.join(random.choices(string.digits, k=6))
        
        # Store the code in the user's profile
        user.verification_code = verification_code
        user.verification_code_expires = timezone.now() + timezone.timedelta(hours=24)
        user.save()
        
        # HTML email content
        html_message = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #2563eb; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9fafb; }}
                .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #6b7280; }}
                .code {{ font-size: 24px; font-weight: bold; color: #2563eb; padding: 10px; 
                        background: #f3f4f6; display: inline-block; margin: 10px 0; }}
                .warning {{ color: #ef4444; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Email Verification</h1>
                </div>
                <div class="content">
                    <p>Hello {user.username},</p>
                    <p>Thank you for signing up for our Restaurant App. Please verify your email address using the code below:</p>
                    
                    <div class="code">{verification_code}</div>
                    
                    <p>Enter this code on the verification page to complete your registration.</p>
                    
                    <p class="warning">This code will expire in 24 hours for security reasons.</p>
                    <p>If you didn't create this account, please ignore this email.</p>
                </div>
                <div class="footer">
                    <p>This is an automated message. Please do not reply to this email.</p>
                    <p>&copy; {timezone.now().year} Restaurant App. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text version
        message = f"""
        Verify Your Email Address
        
        Hello {user.username},
        
        Thank you for signing up for our Restaurant App. 
        
        Your verification code is: {verification_code}
        
        Enter this code on the verification page to complete your registration.
        
        This code will expire in 24 hours for security reasons.
        
        If you didn't create this account, please ignore this email.
        
        --
        This is an automated message. Please do not reply to this email.
        © {timezone.now().year} Restaurant App. All rights reserved.
        """
        
        # Send the email
        send_mail(
            'Verify Your Email Address - Restaurant App',
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Verification email sent to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send verification email to {user.email}: {str(e)}")
        return False