from rest_framework import serializers

class SocialAuthSerializer(serializers.Serializer):
    provider = serializers.CharField(max_length=20)
    access_token = serializers.CharField()

class GoogleAuthSerializer(serializers.Serializer):
    token = serializers.CharField()

class FacebookAuthSerializer(serializers.Serializer):
    token = serializers.CharField()