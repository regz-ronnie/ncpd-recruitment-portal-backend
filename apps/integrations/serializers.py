from rest_framework import serializers
from .models import VerificationRequest, VerificationResult
from django.contrib.auth import get_user_model

User = get_user_model()


class VerificationRequestSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = VerificationRequest
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'completed_at']


class VerificationResultSerializer(serializers.ModelSerializer):
    request_user = serializers.CharField(source='verification_request.user.get_full_name', read_only=True)
    
    class Meta:
        model = VerificationResult
        fields = '__all__'
        read_only_fields = ['verification_request', 'verification_date']
