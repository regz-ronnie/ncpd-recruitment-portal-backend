from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import (
    WorkflowTemplate, WorkflowInstance, WorkflowStage, Task, 
    Notification, AuditLog, EmailLog, Report, EmailTemplate
)
from .serializers import (
    WorkflowTemplateSerializer, WorkflowInstanceSerializer, 
    WorkflowStageSerializer, TaskSerializer, NotificationSerializer, 
    AuditLogSerializer, EmailLogSerializer, ReportSerializer, EmailTemplateSerializer
)
from .services.workflow_engine import WorkflowEngine


class WorkflowTemplateViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = WorkflowTemplate.objects.all()
    serializer_class = WorkflowTemplateSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'usage_count']
    ordering = ['-created_at']
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class WorkflowInstanceViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = WorkflowInstance.objects.all()
    serializer_class = WorkflowInstanceSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['template', 'status', 'job']
    search_fields = ['template__name', 'current_stage']
    ordering_fields = ['started_at', 'completed_at']
    ordering = ['-started_at']
    
    @action(detail=True, methods=['post'])
    def advance_stage(self, request, pk=None):
        """Advance workflow to next stage"""
        instance = self.get_object()
        # Logic to advance stage would go here
        return Response({'message': 'Stage advanced successfully'})


class WorkflowStageViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = WorkflowStage.objects.all()
    serializer_class = WorkflowStageSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['instance', 'stage_type', 'status']
    search_fields = ['name']
    ordering_fields = ['started_at', 'completed_at', 'due_date']
    ordering = ['-started_at']


class EmailTemplateViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = EmailTemplate.objects.all()
    serializer_class = EmailTemplateSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['template_type', 'is_active', 'auto_send']
    search_fields = ['name', 'subject']
    ordering_fields = ['created_at']
    ordering = ['-created_at']


class EmailLogViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = EmailLog.objects.all()
    serializer_class = EmailLogSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['template', 'status']
    search_fields = ['to_email', 'subject']
    ordering_fields = ['created_at', 'sent_at']
    ordering = ['-created_at']


class TaskViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'priority', 'assignee']
    search_fields = ['title', 'description']
    ordering_fields = ['due_date', 'created_at', 'priority']
    ordering = ['-due_date']
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type in ['hr', 'manager', 'admin']:
            return Task.objects.all()
        return Task.objects.filter(assignee=user)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark task as completed"""
        task = self.get_object()
        task.status = 'completed'
        task.completed_at = timezone.now()
        task.completion_notes = request.data.get('completion_notes', '')
        task.save()
        serializer = self.get_serializer(task)
        return Response(serializer.data)


class NotificationViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['notification_type', 'is_read']
    search_fields = ['title', 'message']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        from django.utils import timezone
        updated = Notification.objects.filter(
            user=request.user, 
            is_read=False
        ).update(is_read=True, read_at=timezone.now())
        return Response({'updated_count': updated})
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark notification as read"""
        from django.utils import timezone
        notification = self.get_object()
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()
        serializer = self.get_serializer(notification)
        return Response(serializer.data)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['action', 'object_type']
    search_fields = ['object_repr', 'user__username']
    ordering_fields = ['created_at']
    ordering = ['-created_at']


class ReportViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['report_type', 'is_scheduled']
    search_fields = ['name']
    ordering_fields = ['generated_at']
    ordering = ['-generated_at']
    
    def perform_create(self, serializer):
        report_type = serializer.validated_data.get('report_type')
        parameters = serializer.validated_data.get('parameters', {})
        filters = serializer.validated_data.get('filters', {})
        generator = WorkflowEngine()
        result = generator.generate_report(report_type, parameters=parameters, filters=filters)
        serializer.save(
            generated_by=self.request.user,
            data=result.get('data', {}),
            summary=result.get('summary', '')
        )
