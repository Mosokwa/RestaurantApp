import uuid
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError

class Referral(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    )
    
    referral_id = models.AutoField(primary_key=True)
    referrer = models.ForeignKey(
        'api.Customer',
        on_delete=models.CASCADE,
        related_name='referrals_made'
    )
    referred_email = models.EmailField()
    referral_code = models.CharField(max_length=20)
    
    # Tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    referral_token = models.UUIDField(default=uuid.uuid4, unique=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        db_table = 'referrals'
        indexes = [
            models.Index(fields=['referral_token']),
            models.Index(fields=['referred_email', 'status']),
        ]

    def __str__(self):
        return f"{self.referrer.user.email} -> {self.referred_email}"

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(days=30)
        super().save(*args, **kwargs)
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def complete_referral(self, referred_customer):
        """Complete the referral when the referred customer signs up and completes first order"""
        from ..services.loyalty_services import LoyaltyService
        
        if self.status != 'pending':
            raise ValidationError("Referral is not in pending state")
        
        if self.is_expired():
            self.status = 'expired'
            self.save()
            raise ValidationError("Referral has expired")
        
        # Award referral bonuses
        try:
            referrer_loyalty = self.referrer.loyalty_profile
            success, message = LoyaltyService.process_referral_bonus(referrer_loyalty, referred_customer)
            
            if success:
                self.status = 'completed'
                self.completed_at = timezone.now()
                self.save()
                return True, "Referral completed successfully"
            else:
                return False, message
                
        except Exception as e:
            return False, f"Error completing referral: {str(e)}"