from rest_framework import serializers
from .models import (
    MatchingResult, CVParsingResult, BiasDetectionResult, 
    ChatbotConversation, AIInsight, AIModel, SkillEmbedding
)
from django.contrib.auth import get_user_model

User = get_user_model()


class AIModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIModel
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class MatchingResultSerializer(serializers.ModelSerializer):
    candidate_name = serializers.CharField(source='candidate.get_full_name', read_only=True)
    job_title = serializers.CharField(source='job.title', read_only=True)
    
    class Meta:
        model = MatchingResult
        fields = '__all__'
        read_only_fields = ['application', 'job', 'candidate', 'created_at', 'updated_at']


class CVParsingResultSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = CVParsingResult
        fields = '__all__'
        read_only_fields = ['user', 'processed_at']


class BiasDetectionResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = BiasDetectionResult
        fields = '__all__'
        read_only_fields = ['processed_at']


class ChatbotConversationSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = ChatbotConversation
        fields = '__all__'
        read_only_fields = ['session_id', 'user', 'started_at', 'ended_at', 'last_message_at']


class AIInsightSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIInsight
        fields = '__all__'
        read_only_fields = ['generated_at', 'expires_at']


class SkillEmbeddingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SkillEmbedding
        fields = '__all__'
        read_only_fields = ['created_at']
