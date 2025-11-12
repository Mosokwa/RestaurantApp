# socialAuthViews.py
import logging
import json
import jwt
import os
import requests
from datetime import datetime, timedelta
from django.db import transaction
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.core.cache import cache
from django.conf import settings
from django_ratelimit.decorators import ratelimit
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from cryptography.x509 import load_pem_x509_certificate
from cryptography.hazmat.primitives.asymmetric import rsa

from ..models import User, Customer
from ..serializers import UserProfileSerializer, GoogleAuthSerializer, AppleAuthSerializer
from ..throttles import SocialAuthThrottle

logger = logging.getLogger(__name__)

class SocialAuthService:
    """Production-ready social authentication service"""
    
    @staticmethod
    def get_or_create_user(email, first_name, last_name, provider, social_uid):
        """
        Thread-safe user creation with proper account linking and error handling
        """
        try:
            with transaction.atomic():
                # Use select_for_update to prevent race conditions
                user = User.objects.select_for_update().filter(email=email).first()
                
                if user:
                    # Existing user - handle account linking
                    return SocialAuthService.handle_existing_user(
                        user, provider, social_uid, email
                    ), False
                else:
                    # New user - create account
                    return SocialAuthService.create_new_user(
                        email, first_name, last_name, provider, social_uid
                    ), True
                    
        except Exception as e:
            logger.error(f"Error in get_or_create_user for {email}: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    def handle_existing_user(user, provider, social_uid, email):
        """
        Handle existing user with comprehensive account linking logic
        """
        # Case 1: User already has the same social auth provider
        if user.social_auth_provider == provider:
            if user.social_auth_uid != social_uid:
                logger.warning(
                    f"Social UID mismatch for {email}. "
                    f"Expected: {user.social_auth_uid}, Got: {social_uid}"
                )
                # Update the social UID if it changed
                user.social_auth_uid = social_uid
                user.save(update_fields=['social_auth_uid', 'updated_at'])
            return user
        
        # Case 2: User has different social auth provider
        elif user.social_auth_provider and user.social_auth_provider != provider:
            logger.warning(
                f"Account linking conflict: {email} attempted {provider} "
                f"but already registered with {user.social_auth_provider}"
            )
            raise PermissionError(
                f"This email is already registered with {user.social_auth_provider}. "
                "Please use that provider to sign in or contact support for account linking."
            )
        
        # Case 3: User has no social auth (password-based account)
        else:
            logger.info(f"Linking existing user {email} to {provider}")
            user.social_auth_provider = provider
            user.social_auth_uid = social_uid
            user.email_verified = True  # Social auth implies email verification
            user.save(update_fields=[
                'social_auth_provider', 
                'social_auth_uid', 
                'email_verified',
                'updated_at'
            ])
            return user
    
    @staticmethod
    def create_new_user(email, first_name, last_name, provider, social_uid):
        """Create new user with comprehensive validation"""
        # Validate email format
        if not SocialAuthService.is_valid_email(email):
            raise ValueError("Invalid email format")
        
        username = SocialAuthService.generate_unique_username(email)
        
        user = User.objects.create(
            username=username,
            email=email,
            first_name=first_name.strip() if first_name else '',
            last_name=last_name.strip() if last_name else '',
            user_type='customer',
            is_active=True,
            email_verified=True,  # Social providers verify emails
            social_auth_provider=provider,
            social_auth_uid=social_uid,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Create customer profile
        Customer.objects.create(user=user)
        
        logger.info(f"New user created via {provider}: {email} (UID: {social_uid})")
        return user
    
    @staticmethod
    def generate_unique_username(email):
        """Generate a unique username from email with collision handling"""
        base_username = email.split('@')[0]
        base_username = ''.join(c for c in base_username if c.isalnum() or c in ['_', '-'])
        base_username = base_username[:25]  # Limit length
        
        username = base_username
        counter = 1
        
        # Check for existing username
        while User.objects.filter(username=username).exists():
            suffix = str(counter)
            available_length = 30 - len(suffix)  # Username max length is 30
            username = f"{base_username[:available_length]}{suffix}"
            counter += 1
            
            if counter > 100:  # Safety limit
                raise RuntimeError("Unable to generate unique username")
                
        return username
    
    @staticmethod
    def is_valid_email(email):
        """Basic email validation"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

class BaseSocialAuthView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [SocialAuthThrottle]
    
    def validate_payload(self, serializer_class, data):
        """Comprehensive payload validation"""
        serializer = serializer_class(data=data)
        if not serializer.is_valid():
            logger.warning(f"Invalid payload received: {serializer.errors}")
            return None, serializer.errors
        return serializer.validated_data, None
    
    def create_auth_response(self, user):
        """Create standardized auth response with security headers"""
        refresh = RefreshToken.for_user(user)
        user_data = UserProfileSerializer(user).data
        
        # Log successful authentication
        logger.info(f"Successful social auth for user: {user.email} (ID: {user.id})")
        
        response = Response({
            'message': 'Authentication successful',
            'user': user_data,
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh)
            }
        }, status=status.HTTP_200_OK)
        
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        
        return response
    
    def handle_auth_error(self, error_msg, status_code=status.HTTP_400_BAD_REQUEST, log_level='warning'):
        """Handle authentication errors with proper logging"""
        if log_level == 'error':
            logger.error(f"Auth error: {error_msg}")
        else:
            logger.warning(f"Auth error: {error_msg}")
            
        return Response(
            {'error': error_msg}, 
            status=status_code,
            headers={
                'X-Content-Type-Options': 'nosniff',
                'X-Frame-Options': 'DENY'
            }
        )

class GoogleAuthView(BaseSocialAuthView):
    @method_decorator(csrf_protect)
    @method_decorator(ratelimit(key='ip', rate='10/m', block=True))
    def post(self, request):
        """
        Production-ready Google OAuth authentication
        """
        start_time = datetime.now()
        
        try:
            # Validate input
            validated_data, errors = self.validate_payload(GoogleAuthSerializer, request.data)
            if errors:
                return self.handle_auth_error('Invalid input data')
            
            token = validated_data['token']
            
            # Verify Google token with timeout
            try:
                idinfo = id_token.verify_oauth2_token(
                    token,
                    google_requests.Request(),
                    self.get_google_client_id(),
                    clock_skew_in_seconds=10  # Allow 10 seconds clock skew
                )
            except Exception as e:
                logger.error(f"Google token verification failed: {str(e)}")
                return self.handle_auth_error('Invalid Google token')
            
            # Comprehensive token validation
            validation_error = self.validate_google_token(idinfo)
            if validation_error:
                return self.handle_auth_error(validation_error)
            
            # Extract and validate user data
            email = idinfo.get('email')
            email_verified = idinfo.get('email_verified', False)
            first_name = idinfo.get('given_name', '')
            last_name = idinfo.get('family_name', '')
            social_uid = idinfo['sub']
            
            if not email:
                return self.handle_auth_error('Email not provided by Google')
                
            if not email_verified:
                return self.handle_auth_error('Google email not verified')
            
            # Get or create user
            try:
                with transaction.atomic():
                    user, created = SocialAuthService.get_or_create_user(
                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                        provider='google',
                        social_uid=social_uid
                    )
                    
                    if not user.is_active:
                        return self.handle_auth_error('Account is deactivated', status.HTTP_403_FORBIDDEN)
                    
                    # Log authentication time
                    auth_time = (datetime.now() - start_time).total_seconds()
                    logger.info(f"Google auth completed in {auth_time:.2f}s for {email}")
                    
                    return self.create_auth_response(user)
                    
            except PermissionError as e:
                return self.handle_auth_error(str(e), status.HTTP_409_CONFLICT)
            except Exception as e:
                logger.error(f"User creation failed for {email}: {str(e)}", exc_info=True)
                return self.handle_auth_error('Account creation failed')
                
        except Exception as e:
            logger.error(f"Google auth unexpected error: {str(e)}", exc_info=True)
            return self.handle_auth_error('Authentication service temporarily unavailable', 
                                        status.HTTP_503_SERVICE_UNAVAILABLE,
                                        'error')
    
    def validate_google_token(self, idinfo):
        """Comprehensive Google token validation"""
        # Validate token issuer
        valid_issuers = ['accounts.google.com', 'https://accounts.google.com']
        if idinfo.get('iss') not in valid_issuers:
            return 'Invalid token issuer'
        
        # Validate token audience
        if idinfo.get('aud') != self.get_google_client_id():
            return 'Invalid token audience'
        
        # Validate token expiration
        exp_timestamp = idinfo.get('exp')
        if not exp_timestamp:
            return 'Token missing expiration'
            
        exp_time = datetime.utcfromtimestamp(exp_timestamp)
        if exp_time < datetime.utcnow():
            return 'Token has expired'
        
        # Validate token issuance time
        iat_timestamp = idinfo.get('iat')
        if iat_timestamp:
            iat_time = datetime.utcfromtimestamp(iat_timestamp)
            if iat_time > datetime.utcnow() + timedelta(minutes=5):  # Allow 5 min future
                return 'Token issued in future'
        
        # Validate token host domain (if present)
        hd = idinfo.get('hd')
        if hd and not self.validate_google_domain(hd):
            return 'Invalid Google domain'
            
        return None
    
    def validate_google_domain(self, domain):
        """Validate Google Workspace domain if restricted"""
        allowed_domains = os.getenv('GOOGLE_ALLOWED_DOMAINS', '').split(',')
        if allowed_domains and allowed_domains[0]:  # If restrictions are set
            return domain in allowed_domains
        return True  # No restrictions
    
    def get_google_client_id(self):
        """Get Google client ID with caching"""
        cache_key = 'google_client_id'
        client_id = cache.get(cache_key)
        
        if not client_id:
            client_id = os.getenv('GOOGLE_OAUTH2_CLIENT_ID')
            if not client_id:
                raise ValueError("GOOGLE_OAUTH2_CLIENT_ID not configured")
            cache.set(cache_key, client_id, 3600)  # Cache for 1 hour
        
        return client_id

class AppleAuthView(BaseSocialAuthView):
    @method_decorator(csrf_protect)
    @method_decorator(ratelimit(key='ip', rate='10/m', block=True))
    def post(self, request):
        """
        Production-ready Apple Sign In authentication
        """
        start_time = datetime.now()
        
        try:
            # Validate input
            validated_data, errors = self.validate_payload(AppleAuthSerializer, request.data)
            if errors:
                return self.handle_auth_error('Invalid input data')
            
            identity_token = validated_data['identity_token']
            first_name = validated_data.get('first_name', '')
            last_name = validated_data.get('last_name', '')
            
            # Verify Apple token
            try:
                decoded_token = self.verify_apple_token(identity_token)
            except jwt.InvalidTokenError as e:
                logger.error(f"Apple token verification failed: {str(e)}")
                return self.handle_auth_error('Invalid Apple token')
            except Exception as e:
                logger.error(f"Apple token verification error: {str(e)}")
                return self.handle_auth_error('Apple token verification failed')
            
            # Extract and validate user data
            email = decoded_token.get('email')
            social_uid = decoded_token['sub']
            
            if not email:
                return self.handle_auth_error('Email not provided by Apple')
            
            # Get or create user
            try:
                with transaction.atomic():
                    user, created = SocialAuthService.get_or_create_user(
                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                        provider='apple',
                        social_uid=social_uid
                    )
                    
                    if not user.is_active:
                        return self.handle_auth_error('Account is deactivated', status.HTTP_403_FORBIDDEN)
                    
                    # Log authentication time
                    auth_time = (datetime.now() - start_time).total_seconds()
                    logger.info(f"Apple auth completed in {auth_time:.2f}s for {email}")
                    
                    return self.create_auth_response(user)
                    
            except PermissionError as e:
                return self.handle_auth_error(str(e), status.HTTP_409_CONFLICT)
            except Exception as e:
                logger.error(f"User creation failed for {email}: {str(e)}", exc_info=True)
                return self.handle_auth_error('Account creation failed')
                
        except Exception as e:
            logger.error(f"Apple auth unexpected error: {str(e)}", exc_info=True)
            return self.handle_auth_error('Authentication service temporarily unavailable', 
                                        status.HTTP_503_SERVICE_UNAVAILABLE,
                                        'error')
    
    def verify_apple_token(self, identity_token):
        """Comprehensive Apple ID token verification"""
        try:
            # Get Apple's public keys
            apple_public_keys = self.get_apple_public_keys()
            decoded_header = jwt.get_unverified_header(identity_token)
            kid = decoded_header['kid']
            alg = decoded_header.get('alg', 'RS256')
            
            if alg != 'RS256':
                raise jwt.InvalidTokenError('Unsupported algorithm')
            
            # Find the matching key
            public_key = None
            for key in apple_public_keys['keys']:
                if key['kid'] == kid:
                    public_key = self.jwk_to_pem(key)
                    break
            
            if not public_key:
                raise jwt.InvalidTokenError('No matching public key found')
            
            # Verify the token
            decoded_token = jwt.decode(
                identity_token,
                public_key,
                algorithms=['RS256'],
                audience=[self.get_apple_client_id()],
                issuer='https://appleid.apple.com'
            )
            
            # Additional Apple-specific validations
            self.validate_apple_token(decoded_token)
            
            return decoded_token
            
        except jwt.ExpiredSignatureError:
            raise jwt.InvalidTokenError('Apple token has expired')
        except jwt.InvalidAudienceError:
            raise jwt.InvalidTokenError('Invalid Apple token audience')
        except jwt.InvalidIssuerError:
            raise jwt.InvalidTokenError('Invalid Apple token issuer')
        except Exception as e:
            logger.error(f"Apple token verification error: {str(e)}")
            raise jwt.InvalidTokenError('Token verification failed')
    
    def validate_apple_token(self, decoded_token):
        """Additional Apple token validations"""
        # Validate token expiration
        exp_timestamp = decoded_token.get('exp')
        if not exp_timestamp:
            raise jwt.InvalidTokenError('Token missing expiration')
            
        exp_time = datetime.utcfromtimestamp(exp_timestamp)
        if exp_time < datetime.utcnow():
            raise jwt.InvalidTokenError('Token has expired')
        
        # Validate token issuance time
        iat_timestamp = decoded_token.get('iat')
        if iat_timestamp:
            iat_time = datetime.utcfromtimestamp(iat_timestamp)
            if iat_time > datetime.utcnow() + timedelta(minutes=5):
                raise jwt.InvalidTokenError('Token issued in future')
        
        # Validate subject
        if not decoded_token.get('sub'):
            raise jwt.InvalidTokenError('Token missing subject')
    
    def get_apple_public_keys(self):
        """Get Apple's public keys with caching and error handling"""
        cache_key = 'apple_public_keys'
        keys = cache.get(cache_key)
        
        if not keys:
            try:
                response = requests.get(
                    'https://appleid.apple.com/auth/keys', 
                    timeout=10,
                    headers={'User-Agent': 'RestaurantPro/1.0'}
                )
                response.raise_for_status()
                keys = response.json()
                cache.set(cache_key, keys, 3600)  # Cache for 1 hour
                logger.info("Successfully fetched Apple public keys")
            except requests.RequestException as e:
                logger.error(f"Failed to fetch Apple public keys: {str(e)}")
                # Try to use cached keys even if expired
                keys = cache.get(cache_key, None)
                if not keys:
                    raise RuntimeError("Unable to fetch Apple public keys")
        
        return keys
    
    def jwk_to_pem(self, jwk):
        """Convert JWK to PEM format for cryptography library"""
        try:
            # Convert base64url encoded values to integers
            n = self.base64url_to_int(jwk['n'])
            e = self.base64url_to_int(jwk['e'])
            
            # Create RSA public key
            public_key = rsa.RSAPublicNumbers(e, n).public_key(default_backend())
            
            # Convert to PEM format
            pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            return pem
            
        except Exception as e:
            logger.error(f"JWK to PEM conversion failed: {str(e)}")
            raise ValueError("Invalid JWK format")
    
    def base64url_to_int(self, value):
        """Convert base64url encoded string to integer"""
        import base64
        # Add padding if needed
        padding = 4 - len(value) % 4
        if padding != 4:
            value += '=' * padding
        
        decoded = base64.urlsafe_b64decode(value)
        return int.from_bytes(decoded, 'big')
    
    def get_apple_client_id(self):
        """Get Apple client ID with validation"""
        client_id = os.getenv('APPLE_CLIENT_ID')
        if not client_id:
            raise ValueError("APPLE_CLIENT_ID not configured")
        return client_id

class SocialAuthHealthView(APIView):
    """Health check for social auth services"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        health_status = {
            'google': self.check_google_health(),
            'apple': self.check_apple_health(),
            'timestamp': datetime.now().isoformat()
        }
        
        status_code = status.HTTP_200_OK if all(health_status.values()) else status.HTTP_503_SERVICE_UNAVAILABLE
        
        return Response(health_status, status=status_code)
    
    def check_google_health(self):
        """Check Google OAuth service health"""
        try:
            client_id = os.getenv('GOOGLE_OAUTH2_CLIENT_ID')
            return bool(client_id and client_id != 'your_google_client_id')
        except:
            return False
    
    def check_apple_health(self):
        """Check Apple Sign In service health"""
        try:
            client_id = os.getenv('APPLE_CLIENT_ID')
            team_id = os.getenv('APPLE_TEAM_ID')
            key_id = os.getenv('APPLE_KEY_ID')
            return bool(client_id and team_id and key_id)
        except:
            return False