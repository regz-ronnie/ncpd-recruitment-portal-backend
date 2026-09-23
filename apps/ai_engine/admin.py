from django.contrib import admin
from .models import CVParsingResult, MatchingResult, AIInsight, BiasDetectionResult, ChatbotConversation


@admin.register(CVParsingResult)
class CVParsingResultAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'confidence_score', 'processed_at']
    list_filter = ['processed_at']
    search_fields = ['user__username', 'user__email']
    ordering = ['-processed_at']
    date_hierarchy = 'processed_at'
    
    fieldsets = (
        ('Parsing Info', {
            'fields': ('user', 'original_file', 'ai_model')
        }),
        ('Parsed Content', {
            'fields': ('parsed_text', 'structured_data')
        }),
        ('Extracted Information', {
            'fields': ('contact_info', 'education', 'experience', 'skills', 'certifications')
        }),
        ('Quality Metrics', {
            'fields': ('confidence_score', 'processing_time')
        }),
        ('Metadata', {
            'fields': ('processed_at',)
        }),
    )
    
    readonly_fields = ['processed_at']


@admin.register(MatchingResult)
class MatchingResultAdmin(admin.ModelAdmin):
    list_display = ['id', 'candidate', 'job', 'overall_score', 'recommendation', 'created_at']
    list_filter = ['recommendation', 'created_at']
    search_fields = ['candidate__username', 'job__title']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Matching Info', {
            'fields': ('application', 'job', 'candidate', 'overall_score', 'confidence_level')
        }),
        ('Detailed Scoring', {
            'fields': ('skill_match_score', 'experience_match_score', 'education_match_score', 'semantic_similarity_score')
        }),
        ('Match Analysis', {
            'fields': ('matched_skills', 'missing_skills', 'additional_skills')
        }),
        ('Processing Details', {
            'fields': ('matching_algorithm', 'ai_model', 'processing_time')
        }),
        ('Recommendations', {
            'fields': ('recommendation', 'reasoning')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(AIInsight)
class AIInsightAdmin(admin.ModelAdmin):
    list_display = ['id', 'insight_type', 'title', 'generated_at']
    list_filter = ['insight_type', 'generated_at']
    search_fields = ['title', 'description', 'insight_type']
    ordering = ['-generated_at']
    date_hierarchy = 'generated_at'
    
    fieldsets = (
        ('Insight Info', {
            'fields': ('insight_type', 'title', 'description')
        }),
        ('Analysis', {
            'fields': ('data_points', 'analysis_results', 'confidence_level')
        }),
        ('Recommendations', {
            'fields': ('recommendations', 'action_items')
        }),
        ('Context', {
            'fields': ('relevant_jobs', 'time_period')
        }),
        ('Metadata', {
            'fields': ('ai_model', 'generated_at', 'expires_at')
        }),
    )
    
    readonly_fields = ['generated_at']


@admin.register(BiasDetectionResult)
class BiasDetectionResultAdmin(admin.ModelAdmin):
    list_display = ['id', 'content_type', 'content_id', 'bias_score', 'processed_at']
    list_filter = ['content_type', 'processed_at']
    search_fields = ['content_id', 'content_type']
    ordering = ['-processed_at']
    date_hierarchy = 'processed_at'
    
    fieldsets = (
        ('Detection Info', {
            'fields': ('content_type', 'content_id', 'original_text')
        }),
        ('Bias Results', {
            'fields': ('bias_flags', 'bias_score', 'bias_categories')
        }),
        ('Suggestions', {
            'fields': ('suggestions', 'corrected_text')
        }),
        ('Processing Info', {
            'fields': ('ai_model', 'processed_at')
        }),
    )
    
    readonly_fields = ['processed_at']


@admin.register(ChatbotConversation)
class ChatbotConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'session_id', 'conversation_type', 'resolution_status', 'started_at']
    list_filter = ['conversation_type', 'resolution_status', 'started_at']
    search_fields = ['session_id', 'initial_query']
    ordering = ['-started_at']
    date_hierarchy = 'started_at'
    
    fieldsets = (
        ('Conversation Info', {
            'fields': ('session_id', 'user', 'conversation_type', 'job_application')
        }),
        ('Content', {
            'fields': ('initial_query', 'messages', 'extracted_info', 'next_actions')
        }),
        ('Metrics', {
            'fields': ('satisfaction_score', 'resolution_status')
        }),
        ('Timing', {
            'fields': ('started_at', 'ended_at', 'last_message_at')
        }),
    )
    
    readonly_fields = ['started_at', 'ended_at', 'last_message_at']