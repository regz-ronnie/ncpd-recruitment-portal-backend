from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.recruitment.models import JobPost, Application, Interview
import json

User = get_user_model()


class WorkflowTemplate(models.Model):
    """Templates for automated recruitment workflows"""
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    
    # Workflow configuration
    stages = models.JSONField(default=list, help_text="Ordered list of workflow stages")
    conditions = models.JSONField(default=dict, help_text="Conditions for stage transitions")
    auto_actions = models.JSONField(default=list, help_text="Automated actions to perform")
    
    # Usage tracking
    is_active = models.BooleanField(default=True)
    usage_count = models.IntegerField(default=0)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name


class WorkflowInstance(models.Model):
    """Active workflow instances for specific recruitment processes"""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled'),
        ('failed', 'Failed'),
    ]
    
    template = models.ForeignKey(WorkflowTemplate, on_delete=models.CASCADE, related_name='instances')
    
    # Context
    job = models.ForeignKey(JobPost, on_delete=models.CASCADE, blank=True, null=True)
    application = models.ForeignKey(Application, on_delete=models.CASCADE, blank=True, null=True)
    
    # Current state
    current_stage = models.CharField(max_length=100)
    stage_data = models.JSONField(default=dict)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Timing
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    # Participants
    assignees = models.ManyToManyField(User, related_name='assigned_workflows', blank=True)
    
    def __str__(self):
        return f"{self.template.name} - {self.get_status_display()}"


class WorkflowStage(models.Model):
    """Individual stages within a workflow"""
    
    instance = models.ForeignKey(WorkflowInstance, on_delete=models.CASCADE, related_name='stages')
    
    # Stage details
    name = models.CharField(max_length=100)
    stage_type = models.CharField(
        max_length=50,
        choices=[
            ('application_review', 'Application Review'),
            ('screening', 'Screening'),
            ('interview', 'Interview'),
            ('background_check', 'Background Check'),
            ('offer_preparation', 'Offer Preparation'),
            ('onboarding', 'Onboarding'),
        ]
    )
    
    # Status and timing
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('in_progress', 'In Progress'),
            ('completed', 'Completed'),
            ('skipped', 'Skipped'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )
    
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    due_date = models.DateTimeField(blank=True, null=True)
    
    # Assignees and requirements
    assignees = models.ManyToManyField(User, related_name='workflow_stages', blank=True)
    required_actions = models.JSONField(default=list)
    completion_criteria = models.JSONField(default=dict)
    
    # Results
    outcome = models.JSONField(default=dict)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.instance.template.name} - {self.name}"


class EmailTemplate(models.Model):
    """Email templates for automated communications"""
    
    TEMPLATE_TYPES = [
        ('application_received', 'Application Received'),
        ('application_under_review', 'Application Under Review'),
        ('shortlisted', 'Shortlisted'),
        ('interview_invitation', 'Interview Invitation'),
        ('interview_reminder', 'Interview Reminder'),
        ('rejection', 'Rejection'),
        ('offer_extended', 'Offer Extended'),
        ('welcome', 'Welcome/Onboarding'),
    ]
    
    name = models.CharField(max_length=100)
    template_type = models.CharField(max_length=50, choices=TEMPLATE_TYPES)
    
    # Email content
    subject = models.CharField(max_length=200)
    html_content = models.TextField()
    text_content = models.TextField(blank=True)
    
    # Template variables
    variables = models.JSONField(default=list, help_text="List of template variables")
    
    # Settings
    is_active = models.BooleanField(default=True)
    auto_send = models.BooleanField(default=False)
    send_delay_hours = models.IntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.template_type})"


class EmailLog(models.Model):
    """Log of all automated emails sent"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('opened', 'Opened'),
        ('clicked', 'Clicked'),
        ('bounced', 'Bounced'),
        ('failed', 'Failed'),
    ]
    
    template = models.ForeignKey(EmailTemplate, on_delete=models.SET_NULL, null=True)
    
    # Recipients
    to_email = models.EmailField()
    cc_emails = models.JSONField(default=list)
    bcc_emails = models.JSONField(default=list)
    
    # Email details
    subject = models.CharField(max_length=200)
    content = models.TextField()
    
    # Context
    application = models.ForeignKey(Application, on_delete=models.CASCADE, blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    
    # Tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    sent_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)
    opened_at = models.DateTimeField(blank=True, null=True)
    
    # External IDs
    external_id = models.CharField(max_length=100, blank=True, help_text="Email service provider ID")
    
    # Error handling
    error_message = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Email to {self.to_email} - {self.status}"


class Notification(models.Model):
    """System notifications for users"""
    
    NOTIFICATION_TYPES = [
        ('application_status', 'Application Status Change'),
        ('interview_scheduled', 'Interview Scheduled'),
        ('workflow_update', 'Workflow Update'),
        ('system_alert', 'System Alert'),
        ('deadline_reminder', 'Deadline Reminder'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    
    # Notification details
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    # Context
    application = models.ForeignKey(Application, on_delete=models.CASCADE, blank=True, null=True)
    job = models.ForeignKey(JobPost, on_delete=models.CASCADE, blank=True, null=True)
    
    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(blank=True, null=True)
    
    # Actions
    action_url = models.URLField(blank=True)
    action_text = models.CharField(max_length=50, blank=True)
    
    # Delivery channels
    email_sent = models.BooleanField(default=False)
    sms_sent = models.BooleanField(default=False)
    push_sent = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Notification for {self.user.username}: {self.title}"


class AuditLog(models.Model):
    """Comprehensive audit trail for all recruitment activities"""
    
    ACTION_TYPES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('view', 'View'),
        ('export', 'Export'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('send_email', 'Send Email'),
        ('schedule_interview', 'Schedule Interview'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20, choices=ACTION_TYPES)
    
    # Target object
    object_type = models.CharField(max_length=50)
    object_id = models.CharField(max_length=100)
    object_repr = models.CharField(max_length=200)
    
    # Changes
    old_values = models.JSONField(default=dict, blank=True)
    new_values = models.JSONField(default=dict, blank=True)
    
    # Context
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    
    # Additional info
    reason = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username if self.user else 'System'} {self.action} {self.object_type}"


class Task(models.Model):
    """Tasks assigned to users within workflows"""
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('overdue', 'Overdue'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Assignment
    assignee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_tasks')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_tasks')
    
    # Context
    workflow_stage = models.ForeignKey(WorkflowStage, on_delete=models.CASCADE, blank=True, null=True)
    application = models.ForeignKey(Application, on_delete=models.CASCADE, blank=True, null=True)
    
    # Status and priority
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    
    # Timing
    due_date = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    # Completion details
    completion_notes = models.TextField(blank=True)
    attachments = models.JSONField(default=list)
    
    # Automation
    is_auto_generated = models.BooleanField(default=False)
    auto_task_type = models.CharField(max_length=50, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Task: {self.title} ({self.assignee.username})"
    
    @property
    def is_overdue(self):
        if self.due_date and self.status not in ['completed', 'cancelled']:
            return timezone.now() > self.due_date
        return False


class Report(models.Model):
    """Automated reports and analytics"""
    
    REPORT_TYPES = [
        ('hiring_metrics', 'Hiring Metrics'),
        ('time_to_hire', 'Time to Hire Analysis'),
        ('candidate_pipeline', 'Candidate Pipeline'),
        ('diversity_report', 'Diversity Report'),
        ('workflow_efficiency', 'Workflow Efficiency'),
        ('cost_analysis', 'Cost Analysis'),
    ]
    
    name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=30, choices=REPORT_TYPES)
    
    # Report configuration
    parameters = models.JSONField(default=dict)
    filters = models.JSONField(default=dict)
    
    # Generated report
    data = models.JSONField(default=dict)
    summary = models.TextField(blank=True)
    
    # File output
    pdf_file = models.FileField(upload_to='reports/', blank=True, null=True)
    excel_file = models.FileField(upload_to='reports/', blank=True, null=True)
    
    # Generation info
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    
    # Scheduling
    is_scheduled = models.BooleanField(default=False)
    schedule_frequency = models.CharField(max_length=20, blank=True)
    next_run = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.name} ({self.report_type})"
