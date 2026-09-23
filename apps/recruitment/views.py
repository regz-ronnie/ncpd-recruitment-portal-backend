from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import JobPost, Application, Interview, RecruitmentMetric, JobCategory, ApplicationComment, InterviewFeedback
from .serializers import (
    JobPostSerializer, ApplicationSerializer, InterviewSerializer, 
    RecruitmentMetricSerializer, JobCategorySerializer, ApplicationCommentSerializer,
    InterviewFeedbackSerializer
)

# Import STATUS_CHOICES from Application model
STATUS_CHOICES = Application.STATUS_CHOICES


class JobCategoryViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = JobCategory.objects.all()
    serializer_class = JobCategorySerializer


class JobPostViewSet(viewsets.ModelViewSet):
    """
    ViewSet for job listings with filtering and search
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = JobPost.objects.all()
    serializer_class = JobPostSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'department', 'employment_type', 'status']
    search_fields = ['title', 'description', 'requirements', 'location']
    ordering_fields = ['created_at', 'application_deadline', 'title']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Only return published jobs for public view"""
        if self.request.user.is_authenticated:
            return JobPost.objects.all()
        return JobPost.objects.filter(status='published', application_deadline__gt=timezone.now())
    
    def perform_create(self, serializer):
        serializer.save(posted_by=self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def apply(self, request, pk=None):
        """
        Apply for a specific job
        """
        job = self.get_object()
        
        # Check if already applied
        if Application.objects.filter(job=job, applicant=request.user).exists():
            return Response({
                'error': 'You have already applied for this position'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create application with provided data
        application_data = {
            'job': job,
            'applicant': request.user,
            'status': 'submitted'
        }
        
        # Handle additional application data if provided
        if 'cover_letter' in request.data:
            application_data['cover_letter'] = request.data['cover_letter']
        
        # Handle file uploads (specific to this job application)
        if 'resume_file' in request.FILES:
            application_data['resume_file'] = request.FILES['resume_file']
        
        if 'portfolio_file' in request.FILES:
            application_data['portfolio_file'] = request.FILES['portfolio_file']
        
        # Handle additional documents (JSON field - specific to this job application)
        if 'additional_documents' in request.data:
            import json
            try:
                additional_docs = request.data['additional_documents']
                if isinstance(additional_docs, str):
                    application_data['additional_documents'] = json.loads(additional_docs)
                else:
                    application_data['additional_documents'] = additional_docs
            except (json.JSONDecodeError, TypeError):
                application_data['additional_documents'] = []
        
        # Copy documents from user profile if not provided in request
        # This ensures each application gets its own copy of documents at time of application
        if 'resume_file' not in request.FILES and request.user.resume_file:
            application_data['resume_file'] = request.user.resume_file
        
        if 'additional_documents' not in request.data and request.user.attachments:
            application_data['additional_documents'] = request.user.attachments
        
        application = Application.objects.create(**application_data)
        
        serializer = ApplicationSerializer(application)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured job postings"""
        featured_jobs = JobPost.objects.filter(is_featured=True, status='published')
        serializer = self.get_serializer(featured_jobs, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def urgent(self, request):
        """Get urgent job postings"""
        urgent_jobs = JobPost.objects.filter(is_urgent=True, status='published')
        serializer = self.get_serializer(urgent_jobs, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def ai_shortlist(self, request, pk=None):
        """Trigger AI shortlisting for a specific job"""
        job = self.get_object()
        
        # Check if user has HR permissions
        if request.user.user_type not in ['hr', 'manager', 'admin']:
            return Response(
                {'error': 'You do not have permission to run AI shortlisting'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            from apps.ai_engine.services.matching_engine import AIMatchingEngine
            from apps.ai_engine.models import MatchingResult
            
            # Initialize the matching engine
            engine = AIMatchingEngine()
            
            # Process all applications for this job
            applications = Application.objects.filter(job=job)
            results = []
            
            for application in applications:
                try:
                    # Delete existing matching result if exists
                    MatchingResult.objects.filter(application=application).delete()
                    
                    # Calculate new match score
                    result = engine.calculate_match_score(application)
                    results.append({
                        'application_id': application.id,
                        'applicant_name': application.applicant.get_full_name() or application.applicant.username,
                        'overall_score': result.overall_score,
                        'skill_match': result.skill_match_score,
                        'experience_match': result.experience_match_score,
                        'education_match': result.education_match_score,
                        'recommendation': result.recommendation
                    })
                except Exception as e:
                    print(f"Error processing application {application.id}: {e}")
            
            return Response({
                'success': True,
                'message': f'AI shortlisting completed for {len(results)} applications',
                'results': results
            })
        except Exception as e:
            return Response(
                {'error': f'AI shortlisting failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ApplicationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for job applications
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ApplicationSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'priority', 'job']
    search_fields = ['applicant__first_name', 'applicant__last_name', 'job__title']
    ordering_fields = ['created_at', 'ai_score', 'total_score']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Users can only see their own applications, HR staff can see all"""
        user = self.request.user
        print(f"Debug: User in get_queryset: {user}, ID: {user.id if user.is_authenticated else 'None'}, user_type: {getattr(user, 'user_type', None)}")
        print(f"Debug: All applications count: {Application.objects.count()}")
        print(f"Debug: User applications count: {Application.objects.filter(applicant=user).count()}")
        
        # Show all applications with their applicant IDs for debugging
        all_apps = Application.objects.all()
        print(f"Debug: All applications: {list(all_apps.values('id', 'job_id', 'applicant_id', 'status'))}")
        
        # Handle cases where user_type might not be set
        user_type = getattr(user, 'user_type', None)
        if user_type in ['hr', 'manager', 'admin']:
            return Application.objects.all()
        return Application.objects.filter(applicant=user)
    
    def perform_create(self, serializer):
        """Assign the authenticated user as the applicant"""
        # Check if user already applied for this job
        job = serializer.validated_data.get('job')
        if Application.objects.filter(job=job, applicant=self.request.user).exists():
            from rest_framework.exceptions import ValidationError
            raise ValidationError("You have already applied for this position.")
        
        serializer.save(applicant=self.request.user)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_applications(self, request):
        """Get all applications for current user"""
        applications = self.get_queryset()
        serializer = self.get_serializer(applications, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def add_comment(self, request, pk=None):
        """Add a comment to an application"""
        application = self.get_object()
        serializer = ApplicationCommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(application=application, author=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        """Get all comments for an application"""
        application = self.get_object()
        comments = application.comments.all()
        serializer = ApplicationCommentSerializer(comments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def shortlist(self, request, pk=None):
        """Move application to shortlisted status"""
        application = self.get_object()
        
        # Check if user has HR permissions
        if request.user.user_type not in ['hr', 'manager', 'admin']:
            return Response(
                {'error': 'You do not have permission to shortlist applications'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Update status to shortlisted
        application.status = 'shortlisted'
        application.reviewed_by = request.user
        application.review_date = timezone.now()
        application.review_notes = request.data.get('notes', '')
        application.save()
        
        serializer = ApplicationSerializer(application)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def move_to_interview(self, request, pk=None):
        """Move shortlisted application to interview stage"""
        application = self.get_object()
        
        # Check if user has HR permissions
        if request.user.user_type not in ['hr', 'manager', 'admin']:
            return Response(
                {'error': 'You do not have permission to schedule interviews'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if application is shortlisted
        if application.status != 'shortlisted':
            return Response(
                {'error': 'Only shortlisted applications can be moved to interview stage'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update status to interview_scheduled
        application.status = 'interview_scheduled'
        application.reviewed_by = request.user
        application.review_date = timezone.now()
        application.review_notes = request.data.get('notes', '')
        application.save()
        
        serializer = ApplicationSerializer(application)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def complete_interview(self, request, pk=None):
        """Mark interview as completed"""
        application = self.get_object()
        
        # Check if user has HR permissions
        if request.user.user_type not in ['hr', 'manager', 'admin']:
            return Response(
                {'error': 'You do not have permission to complete interviews'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if application is in interview stage
        if application.status != 'interview_scheduled':
            return Response(
                {'error': 'Only applications with scheduled interviews can be completed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update status to interview_completed
        application.status = 'interview_completed'
        application.reviewed_by = request.user
        application.review_date = timezone.now()
        application.review_notes = request.data.get('notes', '')
        application.save()
        
        serializer = ApplicationSerializer(application)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def extend_offer(self, request, pk=None):
        """Extend job offer to candidate"""
        application = self.get_object()
        
        # Check if user has HR permissions
        if request.user.user_type not in ['hr', 'manager', 'admin']:
            return Response(
                {'error': 'You do not have permission to extend offers'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if application has completed interview
        if application.status != 'interview_completed':
            return Response(
                {'error': 'Only applications with completed interviews can receive offers'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update status to offer_extended
        application.status = 'offer_extended'
        application.reviewed_by = request.user
        application.review_date = timezone.now()
        application.review_notes = request.data.get('notes', '')
        application.save()
        
        serializer = ApplicationSerializer(application)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def accept_offer(self, request, pk=None):
        """Mark offer as accepted by candidate"""
        application = self.get_object()
        
        # Check if user has HR permissions or is the applicant
        if request.user.user_type not in ['hr', 'manager', 'admin'] and application.applicant != request.user:
            return Response(
                {'error': 'You do not have permission to accept this offer'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if offer has been extended
        if application.status != 'offer_extended':
            return Response(
                {'error': 'Only extended offers can be accepted'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update status to offer_accepted
        application.status = 'offer_accepted'
        application.reviewed_by = request.user if request.user.user_type in ['hr', 'manager', 'admin'] else application.reviewed_by
        application.review_date = timezone.now()
        application.review_notes = request.data.get('notes', application.review_notes)
        application.save()
        
        serializer = ApplicationSerializer(application)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def decline_offer(self, request, pk=None):
        """Mark offer as declined by candidate"""
        application = self.get_object()
        
        # Check if user has HR permissions or is the applicant
        if request.user.user_type not in ['hr', 'manager', 'admin'] and application.applicant != request.user:
            return Response(
                {'error': 'You do not have permission to decline this offer'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if offer has been extended
        if application.status != 'offer_extended':
            return Response(
                {'error': 'Only extended offers can be declined'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update status to offer_declined
        application.status = 'offer_declined'
        application.review_notes = request.data.get('notes', application.review_notes)
        application.save()
        
        serializer = ApplicationSerializer(application)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def reject(self, request, pk=None):
        """Reject application at any stage"""
        application = self.get_object()
        
        # Check if user has HR permissions
        if request.user.user_type not in ['hr', 'manager', 'admin']:
            return Response(
                {'error': 'You do not have permission to reject applications'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Update status to rejected
        application.status = 'rejected'
        application.reviewed_by = request.user
        application.review_date = timezone.now()
        application.review_notes = request.data.get('notes', '')
        application.save()
        
        serializer = ApplicationSerializer(application)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def by_status(self, request):
        """Get applications grouped by status for pipeline view"""
        user = request.user
        
        if user.user_type not in ['hr', 'manager', 'admin']:
            return Response(
                {'error': 'You do not have permission to view pipeline'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        applications = Application.objects.all()
        
        # Group applications by status
        pipeline = {}
        
        for status_choice in STATUS_CHOICES:
            status_key = status_choice[0]
            status_label = status_choice[1]
            pipeline[status_key] = {
                'label': status_label,
                'count': applications.filter(status=status_key).count(),
                'applications': ApplicationSerializer(
                    applications.filter(status=status_key), 
                    many=True
                ).data
            }
        
        return Response(pipeline)


class InterviewViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Interview.objects.all()
    serializer_class = InterviewSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'interview_type']
    search_fields = ['application__applicant__first_name', 'application__applicant__last_name']
    ordering_fields = ['scheduled_date', 'created_at']
    ordering = ['scheduled_date']
    
    def get_queryset(self):
        """Users can only see their own interviews, HR staff can see all"""
        user = self.request.user
        if user.user_type in ['hr', 'manager', 'admin']:
            return Interview.objects.all()
        return Interview.objects.filter(application__applicant=user)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def add_feedback(self, request, pk=None):
        """Add feedback to an interview"""
        interview = self.get_object()
        serializer = InterviewFeedbackSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(interview=interview, interviewer=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def feedback(self, request, pk=None):
        """Get all feedback for an interview"""
        interview = self.get_object()
        feedback = interview.feedback_entries.all()
        serializer = InterviewFeedbackSerializer(feedback, many=True)
        return Response(serializer.data)


class RecruitmentMetricViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = RecruitmentMetric.objects.all()
    serializer_class = RecruitmentMetricSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['metric_type', 'job_category', 'department']
    ordering_fields = ['period_start', 'period_end', 'created_at']
    ordering = ['-period_start']
