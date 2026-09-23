import json

import json

from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html
from apps.recruitment.models import JobPost, Application, Interview
from apps.users.models import User
from .models import (
    WorkflowTemplate, WorkflowInstance, WorkflowStage, 
    EmailTemplate, EmailLog, Notification, AuditLog, Task, Report
)


@admin.register(WorkflowTemplate)
class WorkflowTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'usage_count', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['-usage_count', '-created_at']
    
    fieldsets = (
        ('Template Info', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Configuration', {
            'fields': ('stages', 'conditions', 'auto_actions')
        }),
        ('Metadata', {
            'fields': ('usage_count', 'created_by', 'created_at', 'updated_at')
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'usage_count']


@admin.register(WorkflowInstance)
class WorkflowInstanceAdmin(admin.ModelAdmin):
    list_display = ['id', 'template', 'current_stage', 'status', 'started_at']
    list_filter = ['status', 'template', 'started_at']
    search_fields = ['template__name', 'job__title', 'application__applicant__first_name']
    ordering = ['-started_at']
    date_hierarchy = 'started_at'
    
    fieldsets = (
        ('Instance Info', {
            'fields': ('template', 'status', 'current_stage')
        }),
        ('Context', {
            'fields': ('job', 'application')
        }),
        ('Stage Data', {
            'fields': ('stage_data',)
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at')
        }),
        ('Participants', {
            'fields': ('assignees',)
        }),
    )
    
    readonly_fields = ['started_at', 'completed_at']


@admin.register(WorkflowStage)
class WorkflowStageAdmin(admin.ModelAdmin):
    list_display = ['id', 'instance', 'name', 'stage_type', 'status', 'due_date']
    list_filter = ['stage_type', 'status', 'due_date']
    search_fields = ['name', 'instance__template__name']
    ordering = ['-started_at']
    date_hierarchy = 'started_at'
    
    fieldsets = (
        ('Stage Info', {
            'fields': ('instance', 'name', 'stage_type', 'status')
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at', 'due_date')
        }),
        ('Requirements', {
            'fields': ('assignees', 'required_actions', 'completion_criteria')
        }),
        ('Results', {
            'fields': ('outcome', 'notes')
        }),
    )
    
    readonly_fields = ['started_at', 'completed_at']


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'template_type', 'is_active', 'auto_send', 'created_at']
    list_filter = ['template_type', 'is_active', 'auto_send', 'created_at']
    search_fields = ['name', 'subject']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Template Info', {
            'fields': ('name', 'template_type', 'is_active')
        }),
        ('Email Content', {
            'fields': ('subject', 'html_content', 'text_content')
        }),
        ('Variables', {
            'fields': ('variables',)
        }),
        ('Automation', {
            'fields': ('auto_send', 'send_delay_hours')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'to_email', 'subject', 'status', 'sent_at']
    list_filter = ['status', 'sent_at', 'created_at']
    search_fields = ['to_email', 'subject', 'template__name']
    ordering = ['-created_at']
    date_hierarchy = 'sent_at'
    
    fieldsets = (
        ('Email Info', {
            'fields': ('template', 'to_email', 'subject', 'status')
        }),
        ('Recipients', {
            'fields': ('cc_emails', 'bcc_emails')
        }),
        ('Content', {
            'fields': ('content',)
        }),
        ('Context', {
            'fields': ('application', 'user')
        }),
        ('Tracking', {
            'fields': ('sent_at', 'delivered_at', 'opened_at', 'external_id')
        }),
        ('Error Handling', {
            'fields': ('error_message', 'retry_count')
        }),
    )
    
    readonly_fields = ['created_at', 'sent_at', 'delivered_at', 'opened_at']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'notification_type', 'title', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['user__username', 'title', 'message']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Notification Info', {
            'fields': ('user', 'notification_type', 'title', 'message', 'is_read')
        }),
        ('Context', {
            'fields': ('application', 'job')
        }),
        ('Actions', {
            'fields': ('action_url', 'action_text')
        }),
        ('Delivery', {
            'fields': ('email_sent', 'sms_sent', 'push_sent')
        }),
        ('Timing', {
            'fields': ('read_at', 'created_at')
        }),
    )
    
    readonly_fields = ['created_at', 'read_at']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'action', 'object_type', 'created_at']
    list_filter = ['action', 'object_type', 'created_at']
    search_fields = ['user__username', 'object_type', 'object_repr']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Action Info', {
            'fields': ('user', 'action', 'object_type', 'object_id', 'object_repr')
        }),
        ('Context', {
            'fields': ('ip_address', 'user_agent', 'reason')
        }),
        ('Changes', {
            'fields': ('old_values', 'new_values')
        }),
        ('Metadata', {
            'fields': ('metadata', 'created_at')
        }),
    )
    
    readonly_fields = ['created_at']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'status', 'priority', 'due_date', 'assignee']
    list_filter = ['status', 'priority', 'due_date']
    search_fields = ['title', 'description']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Task Info', {
            'fields': ('title', 'description', 'status', 'priority')
        }),
        ('Assignment', {
            'fields': ('assignee', 'created_by', 'workflow_stage', 'application')
        }),
        ('Timing', {
            'fields': ('due_date', 'completed_at')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'completed_at']


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    change_form_template = 'admin/workflow/report/change_form.html'
    list_display = ['id', 'name', 'report_type', 'generated_at', 'pdf_file_link', 'excel_file_link']
    list_filter = ['report_type', 'generated_at']
    search_fields = ['name']
    ordering = ['-generated_at']
    date_hierarchy = 'generated_at'

    def pdf_file_link(self, obj):
        if obj.pdf_file:
            return format_html('<a href="{}" target="_blank">PDF</a>', obj.pdf_file.url)
        return '-'
    pdf_file_link.short_description = 'PDF'

    def excel_file_link(self, obj):
        if obj.excel_file:
            return format_html('<a href="{}" target="_blank">Excel</a>', obj.excel_file.url)
        return '-'
    excel_file_link.short_description = 'Excel'

    def _get_fallback_chart_data(self):
        return {
            'job_status_counts': list(JobPost.objects.values('status').annotate(count=Count('id'))),
            'application_status_counts': list(Application.objects.values('status').annotate(count=Count('id'))),
            'interview_status_counts': list(Interview.objects.values('status').annotate(count=Count('id'))),
            'user_type_counts': list(User.objects.values('user_type').annotate(count=Count('id'))),
        }

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        extra_context = extra_context or {}
        report = None
        if object_id:
            report = self.get_object(request, object_id)

        chart_data = report.data if report and report.data else self._get_fallback_chart_data()
        extra_context['report_chart_data'] = json.dumps(chart_data)
        extra_context['report_summary'] = getattr(report, 'summary', '') if report else ''
        return super().changeform_view(request, object_id, form_url, extra_context)

    fieldsets = (
        ('Report Info', {
            'fields': ('name', 'report_type')
        }),
        ('Configuration', {
            'fields': ('parameters', 'filters')
        }),
        ('Generated Output', {
            'fields': ('data', 'summary', 'pdf_file', 'excel_file')
        }),
        ('Metadata', {
            'fields': ('generated_by', 'generated_at', 'expires_at', 'is_scheduled', 'schedule_frequency', 'next_run')
        }),
    )

    readonly_fields = ['generated_at']