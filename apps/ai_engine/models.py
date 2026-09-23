from django.db import models
from django.contrib.auth import get_user_model
from apps.recruitment.models import JobPost, Application
import json

User = get_user_model()


class AIModel(models.Model):
    """AI models used for various recruitment tasks"""
    
    MODEL_TYPES = [
        ('cv_parser', 'CV Parser'),
        ('skill_matcher', 'Skill Matcher'),
        ('semantic_search', 'Semantic Search'),
        ('sentiment_analysis', 'Sentiment Analysis'),
        ('bias_detector', 'Bias Detector'),
        ('chatbot', 'Recruitment Chatbot'),
    ]
    
    name = models.CharField(max_length=100)
    model_type = models.CharField(max_length=30, choices=MODEL_TYPES)
    version = models.CharField(max_length=20)
    description = models.TextField(blank=True)
    
    # Model configuration
    config = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    accuracy_score = models.DecimalField(max_digits=5, decimal_places=4, blank=True, null=True)
    
    # External model info
    provider = models.CharField(max_length=50, blank=True, help_text="e.g., OpenAI, HuggingFace")
    model_id = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.model_type})"


class CVParsingResult(models.Model):
    """Results from AI CV parsing"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cv_parsing_results')
    original_file = models.FileField(upload_to='original_cvs/')
    
    # Parsed content
    parsed_text = models.TextField()
    structured_data = models.JSONField(default=dict)
    
    # Extracted information
    contact_info = models.JSONField(default=dict)
    education = models.JSONField(default=list)
    experience = models.JSONField(default=list)
    skills = models.JSONField(default=list)
    certifications = models.JSONField(default=list)
    
    # Quality metrics
    confidence_score = models.DecimalField(max_digits=5, decimal_places=4)
    processing_time = models.DurationField(blank=True, null=True)
    
    # Processing info
    ai_model = models.ForeignKey(AIModel, on_delete=models.SET_NULL, null=True)
    processed_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"CV Parsing for {self.user.username}"


class SkillEmbedding(models.Model):
    """Vector embeddings for skills and job descriptions"""
    
    CONTENT_TYPES = [
        ('skill', 'Skill'),
        ('job_description', 'Job Description'),
        ('resume_text', 'Resume Text'),
        ('qualification', 'Qualification'),
    ]
    
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES)
    content_id = models.CharField(max_length=100)
    text_content = models.TextField()
    
    # Vector embedding
    embedding = models.JSONField()
    embedding_model = models.CharField(max_length=50)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['content_type', 'content_id']
    
    def __str__(self):
        return f"{self.content_type}: {self.content_id}"


class MatchingResult(models.Model):
    """AI matching results between jobs and candidates"""
    
    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name='matching_result')
    job = models.ForeignKey(JobPost, on_delete=models.CASCADE)
    candidate = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Overall scores
    overall_score = models.DecimalField(max_digits=5, decimal_places=2)
    confidence_level = models.DecimalField(max_digits=5, decimal_places=4)
    
    # Detailed scoring
    skill_match_score = models.DecimalField(max_digits=5, decimal_places=2)
    experience_match_score = models.DecimalField(max_digits=5, decimal_places=2)
    education_match_score = models.DecimalField(max_digits=5, decimal_places=2)
    semantic_similarity_score = models.DecimalField(max_digits=5, decimal_places=2)
    
    # Matched items
    matched_skills = models.JSONField(default=list)
    missing_skills = models.JSONField(default=list)
    additional_skills = models.JSONField(default=list)
    
    # Analysis details
    matching_algorithm = models.CharField(max_length=50)
    ai_model = models.ForeignKey(AIModel, on_delete=models.SET_NULL, null=True)
    processing_time = models.DurationField()
    
    # Recommendations
    recommendation = models.CharField(
        max_length=20,
        choices=[
            ('reject', 'Reject'),
            ('consider', 'Consider'),
            ('strong_consider', 'Strongly Consider'),
            ('interview', 'Interview'),
            ('high_priority', 'High Priority'),
        ]
    )
    reasoning = models.TextField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Matching: {self.candidate.username} -> {self.job.title} ({self.overall_score}%)"


class BiasDetectionResult(models.Model):
    """Results from bias analysis on job descriptions and evaluations"""
    
    CONTENT_TYPES = [
        ('job_description', 'Job Description'),
        ('evaluation', 'Candidate Evaluation'),
        ('interview_notes', 'Interview Notes'),
    ]
    
    content_type = models.CharField(max_length=30, choices=CONTENT_TYPES)
    content_id = models.CharField(max_length=100)
    original_text = models.TextField()
    
    # Bias detection results
    bias_flags = models.JSONField(default=list)
    bias_score = models.DecimalField(max_digits=5, decimal_places=4)
    bias_categories = models.JSONField(default=list)
    
    # Suggestions
    suggestions = models.JSONField(default=list)
    corrected_text = models.TextField(blank=True)
    
    # Processing info
    ai_model = models.ForeignKey(AIModel, on_delete=models.SET_NULL, null=True)
    processed_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Bias Analysis: {self.content_type} - {self.content_id}"


class ChatbotConversation(models.Model):
    """Recruitment chatbot conversations"""
    
    CONVERSATION_TYPES = [
        ('pre_screening', 'Pre-screening'),
        ('application_help', 'Application Help'),
        ('faq', 'FAQ'),
        ('interview_prep', 'Interview Preparation'),
    ]
    
    session_id = models.CharField(max_length=100, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    conversation_type = models.CharField(max_length=30, choices=CONVERSATION_TYPES)
    
    # Context
    job_application = models.ForeignKey(Application, on_delete=models.CASCADE, blank=True, null=True)
    initial_query = models.TextField()
    
    # Conversation data
    messages = models.JSONField(default=list)
    extracted_info = models.JSONField(default=dict)
    next_actions = models.JSONField(default=list)
    
    # Metrics
    satisfaction_score = models.IntegerField(blank=True, null=True)
    resolution_status = models.CharField(
        max_length=20,
        choices=[
            ('resolved', 'Resolved'),
            ('escalated', 'Escalated'),
            ('abandoned', 'Abandoned'),
            ('ongoing', 'Ongoing'),
        ],
        default='ongoing'
    )
    
    # Timing
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(blank=True, null=True)
    last_message_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Chat: {self.session_id} ({self.conversation_type})"


class AIInsight(models.Model):
    """AI-generated insights and recommendations"""
    
    INSIGHT_TYPES = [
        ('hiring_trend', 'Hiring Trend'),
        ('skill_gap', 'Skill Gap Analysis'),
        ('candidate_pool', 'Candidate Pool Analysis'),
        ('process_efficiency', 'Process Efficiency'),
        ('diversity_analysis', 'Diversity Analysis'),
    ]
    
    insight_type = models.CharField(max_length=30, choices=INSIGHT_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    # Data and analysis
    data_points = models.JSONField(default=list)
    analysis_results = models.JSONField(default=dict)
    confidence_level = models.DecimalField(max_digits=5, decimal_places=4)
    
    # Recommendations
    recommendations = models.JSONField(default=list)
    action_items = models.JSONField(default=list)
    
    # Context
    relevant_jobs = models.ManyToManyField(JobPost, blank=True)
    time_period = models.JSONField(default=dict)
    
    # Metadata
    ai_model = models.ForeignKey(AIModel, on_delete=models.SET_NULL, null=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.insight_type}: {self.title}"


class ModelTrainingData(models.Model):
    """Training data for AI models"""
    
    DATA_TYPES = [
        ('cv_samples', 'CV Samples'),
        ('job_descriptions', 'Job Descriptions'),
        ('skill_mappings', 'Skill Mappings'),
        ('interview_outcomes', 'Interview Outcomes'),
    ]
    
    data_type = models.CharField(max_length=30, choices=DATA_TYPES)
    raw_data = models.JSONField()
    processed_data = models.JSONField(blank=True, null=True)
    
    # Labels and annotations
    labels = models.JSONField(default=dict)
    annotations = models.JSONField(default=list)
    quality_score = models.DecimalField(max_digits=5, decimal_places=4, blank=True, null=True)
    
    # Usage tracking
    used_in_training = models.BooleanField(default=False)
    model_versions = models.JSONField(default=list)
    
    # Metadata
    source = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.data_type} - {self.id}"
