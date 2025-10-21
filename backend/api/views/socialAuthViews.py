from rest_framework import status
from ..throttles import AuthThrottle
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
import os
import requests
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from social_django.utils import load_strategy, load_backend
from social_core.exceptions import MissingBackend, AuthTokenError, AuthForbidden
from ..models import User, Customer
from ..serializers import (
    UserProfileSerializer, SocialAuthSerializer, GoogleAuthSerializer, FacebookAuthSerializer
)

class SocialLoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AuthThrottle]
    
    def post(self, request):
        serializer = SocialAuthSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        provider = serializer.validated_data['provider']
        access_token = serializer.validated_data['access_token']
        
        try:
            # Load the strategy and backend
            strategy = load_strategy(request)
            backend = load_backend(strategy, provider, redirect_uri=None)
            
            # Authenticate user using the social backend
            user = backend.do_auth(access_token)
            
            if user and user.is_active:
                # Generate JWT tokens
                refresh = RefreshToken.for_user(user)
                
                user_data = UserProfileSerializer(user).data
                return Response({
                    'message': f'Login with {provider} successful',
                    'user': user_data,
                    'tokens': {
                        'access': str(refresh.access_token),
                        'refresh': str(refresh)
                    }
                })
            else:
                return Response({'error': 'Authentication failed'}, 
                               status=status.HTTP_401_UNAUTHORIZED)
                
        except (MissingBackend, AuthTokenError, AuthForbidden) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class GoogleLoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AuthThrottle]
    
    def post(self, request):
        serializer = GoogleAuthSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Validate Google token and get user data
            idinfo = id_token.verify_oauth2_token(
                serializer.validated_data['token'], 
                google_requests.Request(), 
                os.getenv('GOOGLE_OAUTH2_CLIENT_ID', '')
            )
            
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Wrong issuer.')
            
            # Get or create user
            email = idinfo['email']
            first_name = idinfo.get('given_name', '')
            last_name = idinfo.get('family_name', '')
            
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                # Create new user
                username = email.split('@')[0]
                # Ensure username is unique
                counter = 1
                original_username = username
                while User.objects.filter(username=username).exists():
                    username = f"{original_username}{counter}"
                    counter += 1
                
                user = User.objects.create(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    user_type='customer',
                    is_active=True,
                    email_verified=True
                )
                # Create customer profile
                Customer.objects.create(user=user)
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            user_data = UserProfileSerializer(user).data
            return Response({
                'message': 'Google login successful',
                'user': user_data,
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh)
                }
            })
            
        except ValueError:
            return Response({'error': 'Invalid Google token'}, 
                           status=status.HTTP_400_BAD_REQUEST)

class FacebookLoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AuthThrottle]
    
    def post(self, request):
        serializer = FacebookAuthSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Verify Facebook token
            app_id = os.getenv('FACEBOOK_APP_ID')
            app_secret = os.getenv('FACEBOOK_APP_SECRET')
            url = f'https://graph.facebook.com/debug_token?input_token={serializer.validated_data["token"]}&access_token={app_id}|{app_secret}'
            
            response = requests.get(url)
            data = response.json()
            
            if 'data' not in data or not data['data']['is_valid']:
                return Response({'error': 'Invalid Facebook token'}, 
                               status=status.HTTP_400_BAD_REQUEST)
            
            # Get user info
            user_info_url = f'https://graph.facebook.com/me?fields=id,name,email&access_token={serializer.validated_data["token"]}'
            user_info_response = requests.get(user_info_url)
            user_info = user_info_response.json()
            
            email = user_info.get('email')
            if not email:
                return Response({'error': 'Email permission required'}, 
                               status=status.HTTP_400_BAD_REQUEST)
            
            name_parts = user_info.get('name', '').split(' ', 1)
            first_name = name_parts[0] if len(name_parts) > 0 else ''
            last_name = name_parts[1] if len(name_parts) > 1 else ''
            
            # Get or create user
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                # Create new user
                username = email.split('@')[0]
                # Ensure username is unique
                counter = 1
                original_username = username
                while User.objects.filter(username=username).exists():
                    username = f"{original_username}{counter}"
                    counter += 1
                
                user = User.objects.create(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    user_type='customer',
                    is_active=True,
                    email_verified=True
                )
                # Create customer profile
                Customer.objects.create(user=user)
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            user_data = UserProfileSerializer(user).data
            return Response({
                'message': 'Facebook login successful',
                'user': user_data,
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh)
                }
            })
            
        except Exception as e:
            return Response({'error': 'Facebook authentication failed'}, 
                           status=status.HTTP_400_BAD_REQUEST)