import logging
import random
import string
from django.utils import timezone 
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework import status
from ..throttles import AuthThrottle, PasswordResetThrottle
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login, logout, authenticate
from django.middleware.csrf import get_token
from ..models import  User
from ..serializers import (
    UserSerializer, LoginSerializer, UserProfileSerializer,
    PasswordResetSerializer, PasswordResetConfirmSerializer,
    ChangePasswordSerializer
)

class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AuthThrottle]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']

        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_active:
                from django_otp import devices_for_user
                devices = list(devices_for_user(user))
                
                if devices and devices[0].confirmed:
                    # 2FA is enabled, require token
                    token = request.data.get('totp_token')
                    if not token:
                        return Response({
                            'requires_2fa': True,
                            'message': '2FA token required'
                        }, status=status.HTTP_200_OK)
                    
                    if not devices[0].verify_token(token):
                        return Response({'error': 'Invalid 2FA token'}, 
                                      status=status.HTTP_401_UNAUTHORIZED)
                    
                # Generate JWT tokens
                refresh = RefreshToken.for_user(user)
                
                # Also create session for browser compatibility
                login(request, user)
                
                user_data = UserProfileSerializer(user).data
                return Response({
                    'message': 'Login successful',
                    'user': user_data,
                    'tokens': {
                        'access': str(refresh.access_token),
                        'refresh': str(refresh)
                    }
                })
            else:
                return Response({'error': 'Account not activated. Please verify your email.'}, 
                               status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response({'error': 'Invalid credentials'}, 
                           status=status.HTTP_401_UNAUTHORIZED)


class SignupView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AuthThrottle]
    
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            with transaction.atomic():
                user = serializer.save()
                
                # Set user as inactive until email verification
                user.is_active = False
                user.save()
                
                # Generate verification code but DON'T send email here
                # The frontend will call the resend-verification endpoint
                verification_code = ''.join(random.choices(string.digits, k=6))
                user.verification_code = verification_code
                user.verification_code_expires = timezone.now() + timezone.timedelta(hours=24)
                user.save()
                
                # Send verification email by calling EmailVerificationView's logic
                email_sent = self._send_verification_email(user)
                
                # Log the signup attempt
                import logging
                logger = logging.getLogger('api.auth')
                if email_sent:
                    logger.info(f"New user signup: {user.username} ({user.email}) - Verification email sent")
                else:
                    logger.error(f"New user signup: {user.username} ({user.email}) - Failed to send verification email")
            
            return Response({
                'message': 'User created successfully. Please check your email for verification.',
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'requires_verification': True,
                'email_sent': email_sent
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _send_verification_email(self, user):
        """Helper method that replicates EmailVerificationView's email sending logic"""
        try:
            # Generate new verification code (already done in signup, but just in case)
            if not user.verification_code:
                verification_code = ''.join(random.choices(string.digits, k=6))
                user.verification_code = verification_code
                user.verification_code_expires = timezone.now() + timezone.timedelta(hours=24)
                user.save()
            
            # Send verification email using the same utility
            from ..email_utils import send_verification_email
            return send_verification_email(user)
            
        except Exception as e:
            logger = logging.getLogger('api.auth')
            logger.error(f"Failed to send verification email to {user.email}: {str(e)}")
            return False
        
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Getting the refresh token from the request
            refresh_token = request.data.get('refresh')

            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()

                # Django session logout
                logout(request)

                # clear any session data
                request.session.flush()

                return Response({
                    'message': 'Successfully logged out'
                },
                status=status.HTTP_200_OK
                )
        except TokenError:
            return Response(
                {'error': 'Invalid token'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class CSRFTokenView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = []  # Remove throttling for this endpoint
    
    def get(self, request):
        """
        Get CSRF token without creating new sessions unnecessarily
        """
        # Use existing CSRF token if available
        if hasattr(request, 'csrf_token'):
            csrf_token = request.META.get('CSRF_COOKIE') or get_token(request)
        else:
            # Only create session if absolutely necessary
            if not request.session.session_key:
                request.session.create()
            csrf_token = get_token(request)
        
        response_data = {
            'csrfToken': csrf_token,
            'sessionExists': bool(request.session.session_key),
        }
        
        return Response(response_data)
    
class JWTObtainPairView(TokenObtainPairView):
    permission_classes = [AllowAny]

class PasswordResetView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [PasswordResetThrottle]
    
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Password reset email sent'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AuthThrottle]
    
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Password reset successful'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


import random
import string

class EmailVerificationView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        RESEND verification email. For when users need a new verification code.
        """
        email = request.data.get('email')
        
        if not email:
            return Response(
                {'error': 'Email is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(email=email)
            
            if user.is_active:
                return Response(
                    {'error': 'Email is already verified'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Generate NEW verification code (different from signup)
            verification_code = ''.join(random.choices(string.digits, k=6))
            user.verification_code = verification_code
            user.verification_code_expires = timezone.now() + timezone.timedelta(hours=24)
            user.save()
            
            # Send verification email
            from ..email_utils import send_verification_email
            email_sent = send_verification_email(user)
            
            if email_sent:
                return Response({
                    'message': 'New verification email sent',
                    'email': user.email,
                    'resend': True  # Indicate this is a resend
                })
            else:
                return Response(
                    {'error': 'Failed to send verification email. Please try again.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found with this email address'},
                status=status.HTTP_404_NOT_FOUND
            )

# views.py - Add this view
class VerifyCodeView(APIView):
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
            user = User.objects.get(email=email)
            
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
                
                return Response({
                    'message': 'Email verified successfully',
                    'user_id': user.id,
                    'verified': True
                })
            else:
                return Response(
                    {'error': 'Invalid or expired verification code'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    
    def put(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Password changed successfully'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RefreshTokenView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'error': 'Refresh token required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            token = RefreshToken(refresh_token)
            access_token = str(token.access_token)
            return Response({'access': access_token})
        except Exception as e:
            return Response({'error': 'Invalid refresh token'}, status=status.HTTP_400_BAD_REQUEST)