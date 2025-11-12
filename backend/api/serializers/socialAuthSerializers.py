# socialAuthSerializers.py
import re
import jwt
from rest_framework import serializers

class BaseTokenSerializer(serializers.Serializer):
    """Base serializer with common token validation"""
    
    def validate_token_structure(self, value):
        """Validate JWT token structure"""
        if not value or not isinstance(value, str):
            raise serializers.ValidationError('Token must be a string')
        
        # Check token length (reasonable bounds for JWT)
        if len(value) < 100 or len(value) > 2000:
            raise serializers.ValidationError('Invalid token length')
        
        # Basic JWT structure validation (3 parts separated by dots)
        parts = value.split('.')
        if len(parts) != 3:
            raise serializers.ValidationError('Invalid token format')
        
        # Check if parts are base64url encoded
        try:
            for part in parts:
                self.base64url_decode(part)
        except Exception:
            raise serializers.ValidationError('Invalid token encoding')
        
        return value
    
    def base64url_decode(self, input):
        """Base64url decode with padding"""
        import base64
        input += '=' * (4 - len(input) % 4)  # Add padding
        return base64.urlsafe_b64decode(input)

class GoogleAuthSerializer(BaseTokenSerializer):
    token = serializers.CharField(
        max_length=2000, 
        min_length=100,
        validators=[]  # We'll handle validation in method
    )
    
    def validate_token(self, value):
        """Comprehensive Google token validation"""
        value = self.validate_token_structure(value)
        
        # Additional Google-specific validations can be added here
        # For example, check if token contains expected claims
        
        return value

class AppleAuthSerializer(BaseTokenSerializer):
    identity_token = serializers.CharField(
        max_length=2000,
        min_length=100,
        validators=[]  # We'll handle validation in method
    )
    first_name = serializers.CharField(
        max_length=30, 
        required=False, 
        allow_blank=True,
        allow_null=True,
        trim_whitespace=True
    )
    last_name = serializers.CharField(
        max_length=30, 
        required=False, 
        allow_blank=True,
        allow_null=True,
        trim_whitespace=True
    )
    
    def validate_identity_token(self, value):
        """Comprehensive Apple token validation"""
        value = self.validate_token_structure(value)
        return value
    
    def validate_first_name(self, value):
        """Sanitize first name"""
        if value:
            # Remove potentially dangerous characters
            value = re.sub(r'[<>"\']', '', value).strip()
        return value
    
    def validate_last_name(self, value):
        """Sanitize last name"""
        if value:
            # Remove potentially dangerous characters
            value = re.sub(r'[<>"\']', '', value).strip()
        return value