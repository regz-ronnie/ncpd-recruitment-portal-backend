from django.contrib import admin
from .models import JobPost, JobCategory, Application, Interview, RecruitmentMetric, ApplicationComment, InterviewFeedback


class SuperuserAccessMixin:
    def has_view_permission(self, request, obj=None):
        return request.user.is_active and (request.user.is_superuser or request.user.is_staff)

    def has_add_permission(self, request):
        return request.user.is_active and (request.user.is_superuser or request.user.is_staff)

    def has_change_permission(self, request, obj=None):
        return request.user.is_active and (request.user.is_superuser or request.user.is_staff)

    def has_delete_permission(self, request, obj=None):
        return request.user.is_active and (request.user.is_superuser or request.user.is_staff)


@admin.register(JobCategory)
class JobCategoryAdmin(SuperuserAccessMixin, admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']


@admin.register(JobPost)
class JobPostAdmin(SuperuserAccessMixin, admin.ModelAdmin):
    list_display = ['title', 'department', 'location', 'status', 'employment_type', 'application_deadline', 'created_at']
    list_filter = ['status', 'employment_type', 'category', 'department', 'is_featured', 'is_urgent']
    search_fields = ['title', 'description', 'requirements', 'location', 'department']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'category', 'department', 'location', 'county')
        }),
        ('Job Details', {
            'fields': ('employment_type', 'salary_min', 'salary_max', 'is_salary_negotiable', 'application_deadline')
        }),
        ('Requirements', {
            'fields': ('requirements', 'responsibilities', 'qualifications', 'skills_required')
        }),
        ('Status & Flags', {
            'fields': ('status', 'is_featured', 'is_urgent', 'auto_screening', 'require_cover_letter')
        }),
        ('Additional Info', {
            'fields': ('max_applications', 'job_grade', 'job_reference')
        }),
        ('Metadata', {
            'fields': ('posted_by', 'created_at', 'updated_at')
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Application)
class ApplicationAdmin(SuperuserAccessMixin, admin.ModelAdmin):
    list_display = ['id', 'applicant', 'job', 'status', 'ai_score', 'total_score', 'created_at']
    list_filter = ['status', 'priority', 'job__department', 'job__location']
    search_fields = ['applicant__first_name', 'applicant__last_name', 'applicant__email', 'job__title']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Application Info', {
            'fields': ('job', 'applicant', 'status', 'priority')
        }),
        ('Scoring', {
            'fields': ('ai_score', 'skill_match_score', 'experience_match_score', 'qualification_match_score')
        }),
        ('Application Content', {
            'fields': ('cover_letter', 'portfolio_file', 'additional_documents')
        }),
        ('Screening Results', {
            'fields': ('screening_notes', 'screening_flags', 'reviewed_by', 'review_date', 'review_notes')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Interview)
class InterviewAdmin(SuperuserAccessMixin, admin.ModelAdmin):
    list_display = ['application', 'interview_type', 'scheduled_date', 'status', 'location']
    list_filter = ['status', 'interview_type', 'location']
    search_fields = ['application__applicant__first_name', 'application__applicant__last_name', 'application__job__title']
    ordering = ['scheduled_date']
    date_hierarchy = 'scheduled_date'
    
    fieldsets = (
        ('Interview Details', {
            'fields': ('application', 'interview_type', 'scheduled_date', 'duration_minutes', 'location', 'meeting_link')
        }),
        ('Interviewers', {
            'fields': ('interviewers', 'primary_interviewer')
        }),
        ('Status & Notes', {
            'fields': ('status', 'feedback', 'rating', 'recommendation', 'interview_notes')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(RecruitmentMetric)
class RecruitmentMetricAdmin(SuperuserAccessMixin, admin.ModelAdmin):
    list_display = ['metric_type', 'value', 'period_start', 'period_end', 'department']
    list_filter = ['metric_type', 'department', 'period_start', 'period_end']
    search_fields = ['metric_type', 'department']
    ordering = ['-period_end']


@admin.register(ApplicationComment)
class ApplicationCommentAdmin(SuperuserAccessMixin, admin.ModelAdmin):
    list_display = ['application', 'author', 'created_at']
    list_filter = ['created_at']
    search_fields = ['content', 'author__username', 'application__applicant__first_name']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Comment', {
            'fields': ('application', 'author', 'content')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(InterviewFeedback)
class InterviewFeedbackAdmin(SuperuserAccessMixin, admin.ModelAdmin):
    list_display = ['interview', 'interviewer', 'recommendation', 'created_at']
    list_filter = ['recommendation', 'created_at']
    search_fields = ['comments', 'interviewer__username', 'interview__application__applicant__first_name']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Feedback', {
            'fields': ('interview', 'interviewer', 'recommendation', 'comments')
        }),
        ('Assessment', {
            'fields': ('strengths', 'weaknesses', 'overall_assessment')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']