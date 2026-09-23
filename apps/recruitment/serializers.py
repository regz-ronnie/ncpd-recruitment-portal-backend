from rest_framework import serializers
from .models import JobPost, Application, Interview, RecruitmentMetric, JobCategory, ApplicationComment, InterviewFeedback
from django.contrib.auth import get_user_model
from apps.users.serializers import UserSerializer

User = get_user_model()


class JobCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = JobCategory
        fields = '__all__'


class JobPostSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    posted_by_name = serializers.CharField(source='posted_by.get_full_name', read_only=True)
    is_active = serializers.ReadOnlyField()
    days_until_deadline = serializers.ReadOnlyField()
    
    class Meta:
        model = JobPost
        fields = '__all__'
        read_only_fields = ['posted_by', 'created_at', 'updated_at', 'published_at']


class ApplicationSerializer(serializers.ModelSerializer):
    applicant_name = serializers.CharField(source='applicant.get_full_name', read_only=True)
    job_title = serializers.CharField(source='job.title', read_only=True)
    job = JobPostSerializer(read_only=True)
    applicant = UserSerializer(read_only=True)
    total_score = serializers.ReadOnlyField()
    
    # Include applicant's qualification and experience data for longlisting
    academic_qualifications = serializers.JSONField(source='applicant.academic_qualifications', read_only=True)
    professional_qualifications = serializers.JSONField(source='applicant.professional_qualifications', read_only=True)
    work_experiences = serializers.JSONField(source='applicant.work_experiences_json', read_only=True)
    highest_education = serializers.CharField(source='applicant.get_highest_education_display', read_only=True)
    field_of_study = serializers.CharField(source='applicant.field_of_study', read_only=True)
    institution = serializers.CharField(source='applicant.institution', read_only=True)
    current_employer = serializers.CharField(source='applicant.current_employer', read_only=True)
    current_position = serializers.CharField(source='applicant.current_position', read_only=True)
    experience_years = serializers.IntegerField(source='applicant.years_of_experience', read_only=True)
    gender = serializers.CharField(source='applicant.gender', read_only=True)
    county = serializers.CharField(source='applicant.county', read_only=True)
    national_id = serializers.CharField(source='applicant.national_id', read_only=True)
    passport_no = serializers.CharField(source='applicant.passport_no', read_only=True)
    date_of_birth = serializers.DateField(source='applicant.date_of_birth', read_only=True)
    resume_file = serializers.FileField(read_only=True)
    portfolio_file = serializers.FileField(read_only=True)
    additional_documents = serializers.JSONField(read_only=True)
    all_documents = serializers.SerializerMethodField()
    
    # Include AI analysis data
    ai_analysis = serializers.SerializerMethodField()
    
    def get_all_documents(self, obj):
        """Get all documents specifically uploaded for this application"""
        documents = []
        request = self.context.get('request')
        
        def get_absolute_url(file_url):
            """Convert relative media URL to absolute backend URL"""
            if not file_url:
                return None
            # Handle if file_url is a dict (from FileField)
            if isinstance(file_url, dict):
                file_url = file_url.get('url', str(file_url))
            # Convert to string if it's a FileField object
            if hasattr(file_url, 'url'):
                file_url = file_url.url
            file_url = str(file_url)
            if file_url.startswith('http://') or file_url.startswith('https://'):
                return file_url
            if request:
                return request.build_absolute_uri(file_url)
            from django.conf import settings
            if hasattr(settings, 'ALLOWED_HOSTS') and settings.ALLOWED_HOSTS:
                host = settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS[0] != '*' else 'localhost:8000'
                return f"http://{host}{file_url}"
            return file_url
        
        # Add resume if exists (specific to this application)
        if obj.resume_file:
            file_url = obj.resume_file.url if hasattr(obj.resume_file, 'url') else str(obj.resume_file)
            documents.append({
                'name': 'Resume/CV',
                'file': get_absolute_url(file_url),
                'type': 'resume'
            })
        
        # Add portfolio if exists (specific to this application)
        if obj.portfolio_file:
            file_url = obj.portfolio_file.url if hasattr(obj.portfolio_file, 'url') else str(obj.portfolio_file)
            documents.append({
                'name': 'Portfolio',
                'file': get_absolute_url(file_url),
                'type': 'portfolio'
            })
        
        # Add additional documents from application (specific to this application)
        for doc in obj.additional_documents or []:
            if isinstance(doc, dict):
                file_url = doc.get('file_url', doc.get('url', doc.get('file')))
                if file_url:
                    documents.append({
                        'name': doc.get('name', doc.get('document_type', 'Document')),
                        'file': get_absolute_url(file_url),
                        'type': 'additional'
                    })
        
        return documents
    
    def get_ai_analysis(self, obj):
        """Get AI analysis data from MatchingResult"""
        try:
            from apps.ai_engine.models import MatchingResult
            matching_result = MatchingResult.objects.filter(application=obj).first()
            if matching_result:
                return {
                    'education_match': matching_result.education_match_score,
                    'experience_match': matching_result.experience_match_score,
                    'certifications_match': matching_result.skill_match_score,  # Using skill_match as proxy for now
                    'skills_match': matching_result.skill_match_score,
                    'overall_score': matching_result.overall_score,
                    'recommendation': matching_result.recommendation,
                    'matched_skills': matching_result.matched_skills,
                    'missing_skills': matching_result.missing_skills,
                    'additional_skills': matching_result.additional_skills,
                    'reasoning': matching_result.reasoning
                }
        except Exception:
            pass
        return None
    
    class Meta:
        model = Application
        fields = '__all__'
        read_only_fields = ['applicant', 'created_at', 'updated_at', 'ai_score', 'ai_analysis']


class ApplicationCommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)
    
    class Meta:
        model = ApplicationComment
        fields = '__all__'
        read_only_fields = ['application', 'author', 'created_at', 'updated_at']


class InterviewSerializer(serializers.ModelSerializer):
    application_job = serializers.CharField(source='application.job.title', read_only=True)
    applicant_name = serializers.CharField(source='application.applicant.get_full_name', read_only=True)
    primary_interviewer_name = serializers.CharField(source='primary_interviewer.get_full_name', read_only=True)
    
    class Meta:
        model = Interview
        fields = '__all__'
        read_only_fields = ['application', 'created_at', 'updated_at']


class InterviewFeedbackSerializer(serializers.ModelSerializer):
    interviewer_name = serializers.CharField(source='interviewer.get_full_name', read_only=True)
    
    class Meta:
        model = InterviewFeedback
        fields = '__all__'
        read_only_fields = ['interview', 'interviewer', 'created_at', 'updated_at']


class RecruitmentMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecruitmentMetric
        fields = '__all__'
        read_only_fields = ['created_at']
