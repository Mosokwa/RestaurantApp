import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

class PaymentVerificationService:
    """
    NEW: Payment verification service for multiple gateways
    SUPPORTS: Stripe, M-Pesa, Azam Pay
    INTEGRATES WITH: Your existing Payment model
    """
    
    def verify_payment(self, transaction_id, gateway_type):
        """
        NEW: Verify payment status with the appropriate gateway
        """
        try:
            if gateway_type == 'stripe':
                return self._verify_stripe_payment(transaction_id)
            elif gateway_type == 'mpesa':
                return self._verify_mpesa_payment(transaction_id)
            elif gateway_type == 'azam_pay':
                return self._verify_azam_pay_payment(transaction_id)
            else:
                return {
                    'status': 'failed',
                    'error': f'Unsupported gateway: {gateway_type}',
                    'payment_status': 'unknown'
                }
                
        except Exception as e:
            logger.error(f"Payment verification failed: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e),
                'payment_status': 'unknown'
            }
    
    def _verify_stripe_payment(self, transaction_id):
        """
        NEW: Verify Stripe payment
        """
        try:
            import stripe
            stripe.api_key = settings.STRIPE_SECRET_KEY
            
            if transaction_id.startswith('ch_'):
                # Charge-based transaction
                charge = stripe.Charge.retrieve(transaction_id)
                payment_status = 'completed' if charge.status == 'succeeded' else 'failed'
            elif transaction_id.startswith('pi_'):
                # Payment Intent transaction
                payment_intent = stripe.PaymentIntent.retrieve(transaction_id)
                payment_status = 'completed' if payment_intent.status == 'succeeded' else 'failed'
            else:
                return {
                    'status': 'failed',
                    'error': 'Invalid Stripe transaction ID',
                    'payment_status': 'unknown'
                }
            
            return {
                'status': 'verified',
                'payment_status': payment_status,
                'gateway_data': {'stripe_status': payment_status}
            }
            
        except stripe.error.StripeError as e:
            return {
                'status': 'failed',
                'error': f'Stripe error: {str(e)}',
                'payment_status': 'unknown'
            }
    
    def _verify_mpesa_payment(self, transaction_id):
        """
        NEW: Verify M-Pesa payment
        INTEGRATION POINT: Replace with actual M-Pesa API calls
        """
        try:
            # Example M-Pesa verification - replace with actual API integration
            mpesa_api_url = getattr(settings, 'MPESA_VERIFICATION_URL', 'https://api.mpesa.com')
            api_key = getattr(settings, 'MPESA_API_KEY', '')
            
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            # This would be the actual API call in production
            # response = requests.get(f"{mpesa_api_url}/transactions/{transaction_id}", headers=headers)
            # response_data = response.json()
            
            # Mock response for demonstration
            mock_response = {
                'status': 'success',
                'transaction_status': 'completed'
            }
            
            if mock_response['status'] == 'success':
                return {
                    'status': 'verified',
                    'payment_status': 'completed',
                    'gateway_data': mock_response
                }
            else:
                return {
                    'status': 'failed',
                    'error': 'M-Pesa verification failed',
                    'payment_status': 'unknown'
                }
                
        except Exception as e:
            return {
                'status': 'failed',
                'error': f'M-Pesa verification error: {str(e)}',
                'payment_status': 'unknown'
            }
    
    def _verify_azam_pay_payment(self, transaction_id):
        """
        NEW: Verify Azam Pay payment
        INTEGRATION POINT: Replace with actual Azam Pay API calls
        """
        try:
            # Example Azam Pay verification - replace with actual API integration
            azam_api_url = getattr(settings, 'AZAM_PAY_VERIFICATION_URL', 'https://api.azampay.com')
            api_key = getattr(settings, 'AZAM_PAY_API_KEY', '')
            
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            # This would be the actual API call in production
            # response = requests.get(f"{azam_api_url}/payments/{transaction_id}", headers=headers)
            # response_data = response.json()
            
            # Mock response for demonstration
            mock_response = {
                'status': 'success',
                'payment_status': 'completed'
            }
            
            if mock_response['status'] == 'success':
                return {
                    'status': 'verified',
                    'payment_status': 'completed',
                    'gateway_data': mock_response
                }
            else:
                return {
                    'status': 'failed',
                    'error': 'Azam Pay verification failed',
                    'payment_status': 'unknown'
                }
                
        except Exception as e:
            return {
                'status': 'failed',
                'error': f'Azam Pay verification error: {str(e)}',
                'payment_status': 'unknown'
            }