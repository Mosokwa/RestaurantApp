from time import time
from django.utils import timezone
import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import transaction
from rest_framework.throttling import AnonRateThrottle
from django.conf import settings
from django.contrib.auth import authenticate
from django_otp import devices_for_user
from ..models import User, Restaurant, RestaurantOwnership
from ..serializers import (
    OwnerLoginSerializer, OwnerRegisterSerializer, 
    OwnerProfileSerializer, StaffInviteSerializer
)
from ..email_utils import send_verification_email

logger = logging.getLogger('api.auth')

class OwnerLoginThrottle(AnonRateThrottle):
    """Custom throttle for owner login with reasonable limits"""
    scope = 'owner_login'
    rate = '10/minute'  # 10 attempts per minute
    
    def allow_request(self, request, view):
        # Allow login requests without throttling for development if needed
        if settings.DEBUG:
            return True
        return super().allow_request(request, view)
    
class OwnerLoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [OwnerLoginThrottle]
    
    def post(self, request):
      
        try:
            serializer = OwnerLoginSerializer(data=request.data)
            if not serializer.is_valid():
                logger.warning(f"Invalid login data: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']

            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                if not user.is_active:
                    logger.warning(f"Login attempt for inactive owner account: {username}")
                    return Response({
                        'error': 'Account not activated. Please verify your email.',
                        'requires_verification': True,
                        'email_verified': user.email_verified,
                        'email': user.email,
                        'can_resend': True  # Add this flag
                    }, status=status.HTTP_401_UNAUTHORIZED)
                
                if user.is_active and user.user_type == 'owner':

                    # PRODUCTION-READY 2FA ENFORCEMENT
                    try:
                        devices = list(devices_for_user(user))
                        
                        if devices and any(device.confirmed for device in devices):
                            # 2FA is enabled, require token
                            token = request.data.get('totp_token')
                            if not token:
                                logger.info(f"2FA required for owner login: {username}")
                                return Response({
                                    'requires_2fa': True,
                                    'message': '2FA token required',
                                    'email_verified': user.email_verified
                                }, status=status.HTTP_200_OK)
                            
                            # Verify 2FA token with all confirmed devices
                            token_valid = any(
                                device.verify_token(token) 
                                for device in devices 
                                if device.confirmed
                            )
                            
                            if not token_valid:
                                logger.warning(f"Invalid 2FA token for owner: {username}")
                                return Response({
                                    'error': 'Invalid 2FA token',
                                    'email_verified': user.email_verified
                                }, status=status.HTTP_401_UNAUTHORIZED)
                                
                            logger.info(f"2FA verification successful for owner: {username}")
                            
                    except Exception as e:
                        logger.error(f"2FA verification error for {username}: {str(e)}")
                        return Response({
                            'error': '2FA verification failed. Please try again.',
                            'email_verified': user.email_verified
                        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                    
                    # Generate JWT tokens
                    refresh = RefreshToken.for_user(user)
                    
                    # Get owner profile data
                    owner_data = OwnerProfileSerializer(user).data

                    logger.info(f"Owner login successful: {username}")

                    return Response({
                        'message': 'Owner login successful',
                        'user': owner_data,
                        'tokens': {
                            'access': str(refresh.access_token),
                            'refresh': str(refresh)
                        },
                        'email_verified': user.email_verified
                    })
                else:
                    logger.warning(f"Login attempt for inactive or non-owner account: {username}")
                    return Response(
                        {'error': 'Account not active or not an owner account',
                         'email_verified': user.email_verified}, 
                        status=status.HTTP_401_UNAUTHORIZED
                    )
            else:
                logger.warning(f"Invalid credentials for owner login: {username}")
                return Response(
                    {'error': 'Invalid credentials'}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )
        except Exception as e:
            logger.error(f"Login error for {request.data.get('username', 'unknown')}: {str(e)}")
            return Response(
                {'error': 'Login service temporarily unavailable'}, 
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )


class OwnerRegisterView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = []
    
    @transaction.atomic
    def post(self, request):
        logger.info(f"Registration attempt for: {request.data.get('email', 'unknown')}")
        serializer = OwnerRegisterSerializer(data=request.data)
        if serializer.is_valid():
            try:
                # Create user but mark as inactive until email verification
                user = serializer.save()
                
                # Set user as inactive until email verification (CRITICAL FIX)
                user.is_active = False
                user.email_verified = False
                user.save()
                
                # Use your existing email_utils to send verification email
                email_sent = send_verification_email(user)
                
                # Log the registration
                if email_sent:
                    logger.info(f"New owner registered: {user.username} ({user.email}) - Verification email sent")
                else:
                    logger.error(f"New owner registered: {user.username} ({user.email}) - Failed to send verification email")
                
                return Response({
                    'message': 'Owner account created successfully. Please check your email for verification.',
                    'user_id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'email_verified': user.email_verified,
                    'is_active': user.is_active,
                    'requires_verification': True,
                    'email_sent': email_sent
                }, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                logger.error(f"Owner registration failed: {str(e)}")
                return Response(
                    {'error': 'Registration failed. Please try again.'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OwnerProfileView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if request.user.user_type != 'owner':
            return Response(
                {'error': 'Access restricted to restaurant owners'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = OwnerProfileSerializer(request.user)
        return Response(serializer.data)


class StaffInviteView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        if request.user.user_type != 'owner':
            return Response(
                {'error': 'Only restaurant owners can invite staff'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = StaffInviteSerializer(
            data=request.data, 
            context={'request': request}
        )
        
        if serializer.is_valid():
            staff = serializer.save()
            
            return Response({
                'message': 'Staff invitation sent successfully',
                'staff_id': staff.staff_id,
                'email': staff.user.email,
                'role': staff.role
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OwnerRestaurantsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if request.user.user_type != 'owner':
            return Response(
                {'error': 'Access restricted to restaurant owners'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get restaurants owned by this user
        restaurants = Restaurant.objects.filter(owner=request.user)
        
        from ..serializers import RestaurantSerializer
        serializer = RestaurantSerializer(
            restaurants, 
            many=True,
            context={'request': request}
        )
        
        return Response({
            'count': restaurants.count(),
            'restaurants': serializer.data
        })
    
# ADD THESE NEW VIEWS FOR OWNER EMAIL VERIFICATION
class OwnerEmailVerificationView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        RESEND verification email for owners
        """
        email = request.data.get('email')
        
        if not email:
            return Response(
                {'error': 'Email is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(email=email, user_type='owner')
            
            if user.is_active:
                return Response(
                    {'error': 'Email is already verified'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Use your existing email_utils to send verification email
            email_sent = send_verification_email(user)
            
            if email_sent:
                return Response({
                    'message': 'New verification email sent',
                    'email': user.email,
                    'email_verified': user.email_verified,  # ADD THIS
                    'is_active': user.is_active,  # ADD THIS
                    'resend': True
                })
            else:
                return Response(
                    {'error': 'Failed to send verification email. Please try again.',
                     'email_verified': user.email_verified},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except User.DoesNotExist:
            return Response(
                {'error': 'Owner account not found with this email address'},
                status=status.HTTP_404_NOT_FOUND
            )


class OwnerVerifyCodeView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        code = request.data.get('code')
        
        if not email or not code:
            return Response(
                {'error': 'Email and verification code are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(email=email, user_type='owner')
            
            # Check if code matches and is not expired
            if (user.verification_code and 
                user.verification_code == code and 
                user.verification_code_expires and
                user.verification_code_expires > timezone.now()):
                
                # Activate user
                user.is_active = True
                user.email_verified = True
                user.verification_code = None
                user.verification_code_expires = None
                user.save()
                
                logger.info(f"Owner email verified successfully: {user.email}")
                
                return Response({
                    'message': 'Email verified successfully. You can now login to your owner account.',
                    'user_id': user.id,
                    'verified': True,
                    'email_verified': user.email_verified,  # ADD THIS
                    'is_active': user.is_active,  # ADD THIS
                    'user': {  # ADD THIS - return basic user info
                        'email': user.email,
                        'username': user.username,
                        'first_name': user.first_name,
                        'last_name': user.last_name
                        }
                })
            else:
                logger.warning(f"Invalid verification code attempt for owner: {email}")
                return Response(
                    {'error': 'Invalid or expired verification code',
                     'email_verified': user.email_verified},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except User.DoesNotExist:
            return Response(
                {'error': 'Owner account not found'},
                status=status.HTTP_404_NOT_FOUND
            )