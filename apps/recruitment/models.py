from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django_countries.fields import CountryField
import os

User = get_user_model()


def application_upload_path(instance, filename):
    """Generate upload path for application files: applications/{applicant_username}/{filename}"""
    # Create a folder per applicant (all their application files go here)
    applicant_username = instance.applicant.username
    safe_filename = filename.replace(' ', '_')
    return os.path.join('applications', applicant_username, safe_filename)


class JobCategory(models.Model):
    """Job categories for classification"""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name='children')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name


class JobPost(models.Model):
    """Job postings/vacancies"""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('closed', 'Closed'),
        ('archived', 'Archived'),
    ]
    
    EMPLOYMENT_TYPE = [
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
        ('temporary', 'Temporary'),
        ('internship', 'Internship'),
        ('volunteer', 'Volunteer'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    requirements = models.TextField(help_text="Job requirements and qualifications")
    responsibilities = models.TextField(help_text="Key responsibilities")
    qualifications = models.TextField(help_text="Required qualifications")
    skills_required = models.JSONField(default=list, blank=True, help_text="List of required skills")
    
    category = models.ForeignKey(JobCategory, on_delete=models.SET_NULL, null=True, related_name='jobs')
    department = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=200)
    county = models.CharField(max_length=100, blank=True)
    country = CountryField(default='KE')
    job_grade = models.CharField(max_length=50, blank=True, help_text="Job grade level (e.g., NCPD 05)")
    job_reference = models.CharField(max_length=50, blank=True, help_text="Job reference number (e.g., VN00993)")
    positions = models.IntegerField(default=1, help_text="Number of positions available")
    
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPE, default='full_time')
    salary_min = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    salary_max = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    is_salary_negotiable = models.BooleanField(default=True)
    
    application_deadline = models.DateTimeField()
    start_date = models.DateField(blank=True, null=True)
    duration = models.IntegerField(blank=True, null=True, help_text="Duration in months for temporary positions")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_featured = models.BooleanField(default=False)
    is_urgent = models.BooleanField(default=False)
    
    # Application settings
    max_applications = models.IntegerField(blank=True, null=True, help_text="Maximum number of applications to accept")
    auto_screening = models.BooleanField(default=True, help_text="Enable AI-powered screening")
    require_cover_letter = models.BooleanField(default=True)
    require_portfolio = models.BooleanField(default=False)
    
    # Metadata
    posted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='posted_jobs')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.department}"
    
    @property
    def is_active(self):
        return self.status == 'published' and self.application_deadline > timezone.now()
    
    @property
    def days_until_deadline(self):
        if self.application_deadline:
            return (self.application_deadline - timezone.now()).days
        return 0


class Application(models.Model):
    """Job applications"""
    
    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('screening', 'AI Screening'),
        ('shortlisted', 'Shortlisted'),
        ('interview_scheduled', 'Interview Scheduled'),
        ('interview_completed', 'Interview Completed'),
        ('offer_extended', 'Offer Extended'),
        ('offer_accepted', 'Offer Accepted'),
        ('offer_declined', 'Offer Declined'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    job = models.ForeignKey(JobPost, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    
    # Application details
    cover_letter = models.TextField(blank=True)
    resume_file = models.FileField(upload_to=application_upload_path, blank=True, null=True)
    portfolio_file = models.FileField(upload_to=application_upload_path, blank=True, null=True)
    additional_documents = models.JSONField(default=list, blank=True)
    
    # AI Processing
    ai_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="AI matching score (0-100)")
    ai_analysis = models.JSONField(default=dict, blank=True, help_text="AI analysis results")
    skill_match_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    experience_match_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    qualification_match_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    
    # Screening results
    screening_notes = models.TextField(blank=True)
    screening_flags = models.JSONField(default=list, blank=True, help_text="Issues flagged during screening")
    
    # Status and priority
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='submitted')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    
    # Review information
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_applications')
    review_date = models.DateTimeField(blank=True, null=True)
    review_notes = models.TextField(blank=True)
    
    # Anonymous screening (to reduce bias)
    is_anonymous = models.BooleanField(default=False, help_text="Hide applicant identity during initial screening")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['job', 'applicant']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.applicant.get_full_name()} - {self.job.title}"
    
    @property
    def total_score(self):
        """Calculate total matching score"""
        scores = [
            self.skill_match_score or 0,
            self.experience_match_score or 0,
            self.qualification_match_score or 0,
        ]
        return sum(scores) / len(scores) if scores else 0


class ApplicationComment(models.Model):
    """Comments and notes on applications"""
    
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField()
    is_internal = models.BooleanField(default=True, help_text="Internal notes vs applicant-facing comments")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Comment by {self.author.username} on {self.application}"


class Interview(models.Model):
    """Interview schedules and details"""
    
    TYPE_CHOICES = [
        ('phone', 'Phone Screen'),
        ('video', 'Video Interview'),
        ('technical', 'Technical Interview'),
        ('behavioral', 'Behavioral Interview'),
        ('panel', 'Panel Interview'),
        ('final', 'Final Interview'),
    ]
    
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('rescheduled', 'Rescheduled'),
        ('no_show', 'No Show'),
    ]
    
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='interviews')
    interview_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    
    # Schedule
    scheduled_date = models.DateTimeField()
    duration_minutes = models.IntegerField(default=60)
    location = models.CharField(max_length=200, blank=True, help_text="Physical location or meeting link")
    meeting_link = models.URLField(blank=True)
    
    # Interviewers
    interviewers = models.ManyToManyField(User, related_name='interviews_assigned', blank=True)
    primary_interviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='primary_interviews')
    
    # Status and feedback
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    feedback = models.TextField(blank=True)
    rating = models.IntegerField(blank=True, null=True, help_text="Interview rating 1-5")
    recommendation = models.CharField(
        max_length=20,
        choices=[
            ('reject', 'Reject'),
            ('maybe', 'Consider'),
            ('strong_maybe', 'Strongly Consider'),
            ('hire', 'Hire'),
        ],
        blank=True
    )
    
    # Additional details
    interview_notes = models.TextField(blank=True)
    follow_up_actions = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.interview_type} for {self.application}"


class InterviewFeedback(models.Model):
    """Individual feedback from interview panel members"""
    
    interview = models.ForeignKey(Interview, on_delete=models.CASCADE, related_name='feedback_entries')
    interviewer = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Scoring criteria
    technical_skills = models.IntegerField(help_text="Rating 1-5")
    communication_skills = models.IntegerField(help_text="Rating 1-5")
    problem_solving = models.IntegerField(help_text="Rating 1-5")
    cultural_fit = models.IntegerField(help_text="Rating 1-5")
    overall_rating = models.IntegerField(help_text="Rating 1-5")
    
    # Detailed feedback
    strengths = models.TextField(blank=True)
    weaknesses = models.TextField(blank=True)
    comments = models.TextField(blank=True)
    recommendation = models.CharField(
        max_length=20,
        choices=[
            ('reject', 'Reject'),
            ('maybe', 'Consider'),
            ('strong_maybe', 'Strongly Consider'),
            ('hire', 'Hire'),
        ]
    )
    
    # Anonymous option
    is_anonymous = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['interview', 'interviewer']
    
    def __str__(self):
        return f"Feedback from {self.interviewer.username} for {self.interview}"


class RecruitmentMetric(models.Model):
    """Recruitment analytics and metrics"""
    
    METRIC_TYPES = [
        ('time_to_hire', 'Time to Hire'),
        ('cost_per_hire', 'Cost per Hire'),
        ('application_rate', 'Application Rate'),
        ('conversion_rate', 'Conversion Rate'),
        ('diversity_metric', 'Diversity Metric'),
        ('quality_of_hire', 'Quality of Hire'),
    ]
    
    metric_type = models.CharField(max_length=30, choices=METRIC_TYPES)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    period_start = models.DateField()
    period_end = models.DateField()
    
    # Additional context
    job_category = models.ForeignKey(JobCategory, on_delete=models.SET_NULL, null=True, blank=True)
    department = models.CharField(max_length=100, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_metric_type_display()}: {self.value}"
