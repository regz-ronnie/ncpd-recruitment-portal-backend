from rest_framework import serializers
from .models import (
    WorkflowTemplate, WorkflowInstance, WorkflowStage, Task, 
    Notification, AuditLog, EmailLog, Report, EmailTemplate
)
from django.contrib.auth import get_user_model

User = get_user_model()


class WorkflowTemplateSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = WorkflowTemplate
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at', 'updated_at', 'usage_count']


class WorkflowInstanceSerializer(serializers.ModelSerializer):
    template_name = serializers.CharField(source='template.name', read_only=True)
    job_title = serializers.CharField(source='job.title', read_only=True)
    
    class Meta:
        model = WorkflowInstance
        fields = '__all__'
        read_only_fields = ['started_at', 'completed_at']


class WorkflowStageSerializer(serializers.ModelSerializer):
    instance_name = serializers.CharField(source='instance.template.name', read_only=True)
    
    class Meta:
        model = WorkflowStage
        fields = '__all__'
        read_only_fields = ['started_at', 'completed_at']


class EmailTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailTemplate
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class EmailLogSerializer(serializers.ModelSerializer):
    template_name = serializers.CharField(source='template.name', read_only=True)
    
    class Meta:
        model = EmailLog
        fields = '__all__'
        read_only_fields = ['created_at', 'sent_at', 'delivered_at', 'opened_at']


class TaskSerializer(serializers.ModelSerializer):
    assignee_name = serializers.CharField(source='assignee.get_full_name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    is_overdue = serializers.ReadOnlyField()
    
    class Meta:
        model = Task
        fields = '__all__'
        read_only_fields = ['assignee', 'created_by', 'created_at', 'updated_at', 'completed_at']


class NotificationSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'read_at']


class AuditLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = '__all__'
        read_only_fields = ['user', 'created_at']


class ReportSerializer(serializers.ModelSerializer):
    generated_by_name = serializers.CharField(source='generated_by.get_full_name', read_only=True)
    
    class Meta:
        model = Report
        fields = '__all__'
        read_only_fields = ['generated_by', 'generated_at', 'expires_at']
