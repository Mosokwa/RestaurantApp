# two_factor_views.py
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_otp import devices_for_user
import qrcode
import base64
from io import BytesIO

class TwoFactorSetupView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Check if 2FA is already enabled
        user = request.user
        existing_devices = devices_for_user(user)
        
        if existing_devices:
            return Response({'message': '2FA is already enabled'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create new TOTP device
        device = TOTPDevice.objects.create(user=user, confirmed=False)
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(device.config_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return Response({
            'secret': device.key,
            'qr_code': f"data:image/png;base64,{img_str}",
            'config_url': device.config_url
        })

class TwoFactorVerifyView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        token = request.data.get('token')
        if not token:
            return Response({'error': 'Token required'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = request.user
        device = TOTPDevice.objects.filter(user=user, confirmed=False).first()
        
        if not device:
            return Response({'error': 'No pending 2FA setup'}, status=status.HTTP_400_BAD_REQUEST)
        
        if device.verify_token(token):
            device.confirmed = True
            device.save()
            return Response({'message': '2FA enabled successfully'})
        
        return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)

class TwoFactorDisableView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        TOTPDevice.objects.filter(user=user).delete()
        return Response({'message': '2FA disabled successfully'})