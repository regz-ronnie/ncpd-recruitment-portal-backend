import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from django.utils import timezone
from django.db import transaction
from django.db.models import Avg, Count, Q
from django.core.mail import send_mail
from django.conf import settings
from celery import shared_task
from apps.recruitment.models import Application, Interview, JobPost
from apps.users.models import User
from apps.workflow.models import (
    WorkflowTemplate, WorkflowInstance, WorkflowStage, 
    EmailTemplate, EmailLog, Notification, Task, AuditLog
)
from apps.ai_engine.services.screening_service import AutomatedScreeningService


class WorkflowEngine:
    """End-to-end recruitment workflow automation engine"""
    
    def __init__(self):
        self.screening_service = AutomatedScreeningService()
        
    def create_recruitment_workflow(self, job: JobPost, template_name: str = "standard_recruitment") -> WorkflowInstance:
        """Create and start a recruitment workflow for a job"""
        
        # Get or create workflow template
        template = self._get_workflow_template(template_name)
        
        # Create workflow instance
        workflow = WorkflowInstance.objects.create(
            template=template,
            job=job,
            current_stage=template.stages[0]['name'] if template.stages else 'initial',
            status='active'
        )
        
        # Create workflow stages
        for i, stage_config in enumerate(template.stages):
            stage = WorkflowStage.objects.create(
                instance=workflow,
                name=stage_config['name'],
                stage_type=stage_config['type'],
                status='pending' if i > 0 else 'in_progress',
                due_date=self._calculate_stage_due_date(stage_config)
            )
            
            # Assign stage to appropriate users
            self._assign_stage_to_users(stage, stage_config, job)
        
        # Log workflow creation
        AuditLog.objects.create(
            action='create',
            object_type='workflow',
            object_id=str(workflow.id),
            object_repr=f"Recruitment workflow for {job.title}",
            metadata={'job_id': job.id, 'template': template_name}
        )
        
        # Trigger initial stage actions
        self._trigger_stage_actions(workflow.stages.first())
        
        return workflow
    
    def advance_workflow_stage(self, workflow: WorkflowInstance, stage: WorkflowStage, outcome: Dict[str, Any]) -> bool:
        """Advance workflow to the next stage"""
        
        try:
            with transaction.atomic():
                # Complete current stage
                stage.status = 'completed'
                stage.completed_at = timezone.now()
                stage.outcome = outcome
                stage.save()
                
                # Find next stage
                current_stages = list(workflow.stages.all().order_by('id'))
                current_index = current_stages.index(stage)
                
                if current_index < len(current_stages) - 1:
                    # Move to next stage
                    next_stage = current_stages[current_index + 1]
                    next_stage.status = 'in_progress'
                    next_stage.started_at = timezone.now()
                    next_stage.save()
                    
                    # Update workflow current stage
                    workflow.current_stage = next_stage.name
                    workflow.save()
                    
                    # Trigger next stage actions
                    self._trigger_stage_actions(next_stage)
                    
                    # Log stage completion
                    AuditLog.objects.create(
                        user=workflow.assignees.first() if workflow.assignees.exists() else None,
                        action='update',
                        object_type='workflow_stage',
                        object_id=str(stage.id),
                        object_repr=f"Completed {stage.name}",
                        new_values={'status': 'completed', 'outcome': outcome}
                    )
                    
                    return True
                else:
                    # Workflow completed
                    workflow.status = 'completed'
                    workflow.completed_at = timezone.now()
                    workflow.save()
                    
                    # Send completion notifications
                    self._send_workflow_completion_notifications(workflow)
                    
                    return True
                    
        except Exception as e:
            print(f"Error advancing workflow stage: {e}")
            return False
    
    def trigger_automated_actions(self, workflow: WorkflowInstance, stage: WorkflowStage):
        """Trigger automated actions based on stage completion"""
        
        stage_config = self._get_stage_config(stage)
        
        # Send automated emails
        if 'emails' in stage_config:
            for email_config in stage_config['emails']:
                self._send_automated_email(workflow, stage, email_config)
        
        # Create tasks
        if 'tasks' in stage_config:
            for task_config in stage_config['tasks']:
                self._create_automated_task(workflow, stage, task_config)
        
        # Schedule interviews
        if 'interview_scheduling' in stage_config:
            self._schedule_interviews(workflow, stage, stage_config['interview_scheduling'])
        
        # Update application status
        if 'application_status' in stage_config:
            self._update_application_status(workflow, stage, stage_config['application_status'])
    
    def _get_workflow_template(self, template_name: str) -> WorkflowTemplate:
        """Get or create workflow template"""
        
        template, created = WorkflowTemplate.objects.get_or_create(
            name=template_name,
            defaults={
                'description': 'Standard recruitment workflow',
                'stages': self._get_default_stages(),
                'conditions': {},
                'auto_actions': []
            }
        )
        
        return template
    
    def _get_default_stages(self) -> List[Dict]:
        """Get default workflow stages"""
        
        return [
            {
                'name': 'Application Intake',
                'type': 'application_review',
                'duration_days': 1,
                'assignees': ['hr'],
                'actions': ['send_confirmation', 'initial_screening'],
                'completion_criteria': {'min_applications': 1}
            },
            {
                'name': 'AI Screening',
                'type': 'screening',
                'duration_days': 2,
                'assignees': ['system'],
                'actions': ['ai_matching', 'bias_detection'],
                'completion_criteria': {'screening_complete': True}
            },
            {
                'name': 'Application Review',
                'type': 'application_review',
                'duration_days': 3,
                'assignees': ['hr', 'hiring_manager'],
                'actions': ['review_applications', 'shortlist_candidates'],
                'completion_criteria': {'min_shortlisted': 3}
            },
            {
                'name': 'Initial Interview',
                'type': 'interview',
                'duration_days': 5,
                'assignees': ['hr', 'panel_member'],
                'actions': ['schedule_interviews', 'send_interview_invites'],
                'completion_criteria': {'interviews_completed': True}
            },
            {
                'name': 'Technical Assessment',
                'type': 'technical',
                'duration_days': 3,
                'assignees': ['technical_lead'],
                'actions': ['assign_tests', 'review_submissions'],
                'completion_criteria': {'assessments_complete': True}
            },
            {
                'name': 'Final Interview',
                'type': 'interview',
                'duration_days': 5,
                'assignees': ['hiring_manager', 'department_head'],
                'actions': ['schedule_final_interviews', 'collect_feedback'],
                'completion_criteria': {'final_interviews_complete': True}
            },
            {
                'name': 'Background Check',
                'type': 'background_check',
                'duration_days': 7,
                'assignees': ['hr'],
                'actions': ['initiate_checks', 'verify_credentials'],
                'completion_criteria': {'checks_passed': True}
            },
            {
                'name': 'Offer Preparation',
                'type': 'offer_preparation',
                'duration_days': 2,
                'assignees': ['hr', 'hiring_manager'],
                'actions': ['prepare_offer', 'get_approvals'],
                'completion_criteria': {'offer_approved': True}
            },
            {
                'name': 'Offer Extension',
                'type': 'offer',
                'duration_days': 3,
                'assignees': ['hr'],
                'actions': ['send_offer', 'track_response'],
                'completion_criteria': {'offer_accepted': True}
            },
            {
                'name': 'Onboarding',
                'type': 'onboarding',
                'duration_days': 1,
                'assignees': ['hr', 'hiring_manager'],
                'actions': ['schedule_onboarding', 'prepare_welcome'],
                'completion_criteria': {'onboarding_scheduled': True}
            }
        ]
    
    def _calculate_stage_due_date(self, stage_config: Dict) -> Optional[datetime]:
        """Calculate due date for workflow stage"""
        
        duration_days = stage_config.get('duration_days', 3)
        return timezone.now() + timedelta(days=duration_days)
    
    def _assign_stage_to_users(self, stage: WorkflowStage, stage_config: Dict, job: JobPost):
        """Assign stage to appropriate users"""
        
        assignee_roles = stage_config.get('assignees', [])
        
        for role in assignee_roles:
            if role == 'hr':
                hr_users = User.objects.filter(user_type='hr')
                stage.assignees.add(*hr_users)
            elif role == 'hiring_manager':
                # Assign to department manager or job poster
                if job.posted_by:
                    stage.assignees.add(job.posted_by)
            elif role == 'system':
                # System-assigned stage (no human assignee)
                pass
            elif role == 'panel_member':
                panel_users = User.objects.filter(user_type='panel_member')
                stage.assignees.add(*panel_users)
    
    def _trigger_stage_actions(self, stage: WorkflowStage):
        """Trigger actions when stage starts"""
        
        stage_config = self._get_stage_config(stage)
        
        # Handle AI screening
        if stage.stage_type == 'screening':
            self._trigger_ai_screening(stage)
        
        # Send notifications
        self._send_stage_notifications(stage)
        
        # Create tasks for assignees
        self._create_stage_tasks(stage, stage_config)
    
    def _trigger_ai_screening(self, stage: WorkflowStage):
        """Trigger AI screening for all applications"""
        
        job = stage.instance.job
        applications = Application.objects.filter(job=job)
        
        for application in applications:
            try:
                # Run AI screening
                screening_result = self.screening_service.screen_applications(job.id)
                
                # Update application with results
                application.status = 'screening'
                application.save()
                
            except Exception as e:
                print(f"AI screening failed for application {application.id}: {e}")
    
    def _send_stage_notifications(self, stage: WorkflowStage):
        """Send notifications to stage assignees"""
        
        for assignee in stage.assignees.all():
            Notification.objects.create(
                user=assignee,
                notification_type='workflow_update',
                title=f'New Stage: {stage.name}',
                message=f'You have been assigned to {stage.name} for {stage.instance.job.title}',
                workflow_stage=stage,
                job=stage.instance.job,
                action_url=f'/hr-dashboard?workflow={stage.instance.id}'
            )
    
    def _create_stage_tasks(self, stage: WorkflowStage, stage_config: Dict):
        """Create tasks for stage assignees"""
        
        task_templates = stage_config.get('tasks', [])
        
        for task_template in task_templates:
            for assignee in stage.assignees.all():
                Task.objects.create(
                    title=task_template['title'],
                    description=task_template.get('description', ''),
                    assignee=assignee,
                    workflow_stage=stage,
                    due_date=stage.due_date,
                    is_auto_generated=True,
                    auto_task_type=task_template.get('type', 'general')
                )
    
    def _send_automated_email(self, workflow: WorkflowInstance, stage: WorkflowStage, email_config: Dict):
        """Send automated email"""
        
        template = EmailTemplate.objects.filter(
            template_type=email_config['template_type']
        ).first()
        
        if not template:
            return
        
        # Get recipient
        recipient = self._get_email_recipient(workflow, stage, email_config)
        
        if not recipient:
            return
        
        # Prepare email content
        context = self._prepare_email_context(workflow, stage, email_config)
        subject = self._render_template(template.subject, context)
        content = self._render_template(template.html_content, context)
        
        # Send email
        try:
            send_mail(
                subject=subject,
                message='',
                html_message=content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                fail_silently=False
            )
            
            # Log email
            EmailLog.objects.create(
                template=template,
                to_email=recipient,
                subject=subject,
                content=content,
                application=self._get_related_application(workflow, stage),
                status='sent',
                sent_at=timezone.now()
            )
            
        except Exception as e:
            print(f"Failed to send automated email: {e}")
    
    def _get_email_recipient(self, workflow: WorkflowInstance, stage: WorkflowStage, email_config: Dict) -> Optional[str]:
        """Get email recipient based on configuration"""
        
        recipient_type = email_config.get('recipient', 'applicant')
        
        if recipient_type == 'applicant':
            # Get top candidate or all applicants
            application = self._get_related_application(workflow, stage)
            if application:
                return application.applicant.email
        
        elif recipient_type == 'hiring_manager':
            if workflow.job.posted_by:
                return workflow.job.posted_by.email
        
        elif recipient_type == 'hr':
            hr_users = User.objects.filter(user_type='hr')
            return hr_users.first().email if hr_users.exists() else None
        
        return None
    
    def _prepare_email_context(self, workflow: WorkflowInstance, stage: WorkflowStage, email_config: Dict) -> Dict:
        """Prepare context for email template rendering"""
        
        return {
            'job_title': workflow.job.title,
            'department': workflow.job.department,
            'stage_name': stage.name,
            'applicant_name': self._get_applicant_name(workflow, stage),
            'interview_date': self._get_interview_date(workflow, stage),
            'application_deadline': workflow.job.application_deadline,
        }
    
    def _render_template(self, template: str, context: Dict) -> str:
        """Render template with context"""
        
        try:
            from django.template import Template, Context
            template_obj = Template(template)
            return template_obj.render(Context(context))
        except:
            # Fallback to simple string replacement
            result = template
            for key, value in context.items():
                result = result.replace(f'{{{{{key}}}}}', str(value))
            return result
    
    def _get_related_application(self, workflow: WorkflowInstance, stage: WorkflowStage) -> Optional[Application]:
        """Get related application for workflow stage"""
        
        # For now, get the highest-scoring application
        applications = Application.objects.filter(job=workflow.job, ai_score__isnull=False).order_by('-ai_score')
        return applications.first()
    
    def _get_applicant_name(self, workflow: WorkflowInstance, stage: WorkflowStage) -> str:
        """Get applicant name for email context"""
        
        application = self._get_related_application(workflow, stage)
        if application:
            return application.applicant.get_full_name()
        return 'Candidate'
    
    def _get_interview_date(self, workflow: WorkflowInstance, stage: WorkflowStage) -> str:
        """Get interview date for email context"""
        
        interviews = Interview.objects.filter(application__job=workflow.job)
        if interviews.exists():
            return interviews.first().scheduled_date.strftime('%B %d, %Y at %I:%M %p')
        return 'To be scheduled'
    
    def _schedule_interviews(self, workflow: WorkflowInstance, stage: WorkflowStage, config: Dict):
        """Schedule interviews automatically"""
        
        # Get shortlisted candidates
        shortlisted_apps = Application.objects.filter(
            job=workflow.job,
            status='shortlisted'
        ).order_by('-ai_score')
        
        for application in shortlisted_apps[:config.get('max_candidates', 5)]:
            # Create interview
            interview = Interview.objects.create(
                application=application,
                interview_type=config.get('interview_type', 'video'),
                scheduled_date=timezone.now() + timedelta(days=3),
                duration_minutes=config.get('duration', 60),
                location=config.get('location', 'Video Call'),
                meeting_link=config.get('meeting_link', ''),
                status='scheduled'
            )
            
            # Assign interviewers
            interviewers = User.objects.filter(user_type__in=['hr', 'panel_member'])
            interview.interviewers.add(*interviewers[:2])
    
    def _update_application_status(self, workflow: WorkflowInstance, stage: WorkflowStage, status_config: Dict):
        """Update application status based on workflow stage"""
        
        target_status = status_config.get('status')
        criteria = status_config.get('criteria', {})
        
        applications = Application.objects.filter(job=workflow.job)
        
        for application in applications:
            if self._meets_criteria(application, criteria):
                application.status = target_status
                application.save()
    
    def _meets_criteria(self, application: Application, criteria: Dict) -> bool:
        """Check if application meets criteria"""
        
        if 'min_score' in criteria:
            if (application.ai_score or 0) < criteria['min_score']:
                return False
        
        if 'status' in criteria:
            if application.status != criteria['status']:
                return False
        
        return True
    
    def _send_workflow_completion_notifications(self, workflow: WorkflowInstance):
        """Send notifications when workflow completes"""
        
        # Notify all assignees
        for assignee in workflow.assignees.all():
            Notification.objects.create(
                user=assignee,
                notification_type='workflow_update',
                title='Workflow Completed',
                message=f'Recruitment workflow for {workflow.job.title} has been completed',
                job=workflow.job,
                action_url=f'/hr-dashboard?job={workflow.job.id}'
            )
        
        # Send completion email to hiring manager
        if workflow.job.posted_by:
            try:
                send_mail(
                    subject=f'Recruitment Completed: {workflow.job.title}',
                    message=f'The recruitment workflow for {workflow.job.title} has been completed successfully.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[workflow.job.posted_by.email],
                    fail_silently=True
                )
            except:
                pass
    
    def _get_stage_config(self, stage: WorkflowStage) -> Dict:
        """Get configuration for workflow stage"""
        
        template = stage.instance.template
        for stage_config in template.stages:
            if stage_config['name'] == stage.name:
                return stage_config
        return {}

    def generate_report(self, report_type: str, parameters: Dict[str, Any] = None, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate analytics report payload for the given report type."""

        parameters = parameters or {}
        filters = filters or {}

        job_filter = Q()
        application_filter = Q()
        interview_filter = Q()
        user_filter = Q()

        if filters.get('job_id'):
            job_filter &= Q(id=filters['job_id'])
            application_filter &= Q(job_id=filters['job_id'])
            interview_filter &= Q(application__job_id=filters['job_id'])

        if filters.get('generated_after'):
            job_filter &= Q(created_at__gte=filters['generated_after'])
            application_filter &= Q(created_at__gte=filters['generated_after'])
            interview_filter &= Q(created_at__gte=filters['generated_after'])
            user_filter &= Q(date_joined__gte=filters['generated_after'])

        if filters.get('generated_before'):
            job_filter &= Q(created_at__lte=filters['generated_before'])
            application_filter &= Q(created_at__lte=filters['generated_before'])
            interview_filter &= Q(created_at__lte=filters['generated_before'])
            user_filter &= Q(date_joined__lte=filters['generated_before'])

        jobs_qs = JobPost.objects.filter(job_filter)
        applications_qs = Application.objects.filter(application_filter)
        interviews_qs = Interview.objects.filter(interview_filter)
        users_qs = User.objects.filter(user_filter)

        data = {
            'job_status_counts': list(jobs_qs.values('status').annotate(count=Count('id')).order_by('-count')),
            'application_status_counts': list(applications_qs.values('status').annotate(count=Count('id')).order_by('-count')),
            'interview_status_counts': list(interviews_qs.values('status').annotate(count=Count('id')).order_by('-count')),
            'user_type_counts': list(users_qs.values('user_type').annotate(count=Count('id')).order_by('-count')),
            'average_ai_score_by_job': list(applications_qs.values('job__title').annotate(avg_ai_score=Avg('ai_score')).order_by('-avg_ai_score')[:10]),
            'applications_by_job': list(jobs_qs.annotate(application_count=Count('applications')).values('title', 'application_count').order_by('-application_count')[:10]),
            'gender_counts': list(users_qs.values('gender').annotate(count=Count('id')).order_by('-count')),
            'ethnicity_counts': list(users_qs.values('ethnicity').annotate(count=Count('id')).order_by('-count')),
        }

        summary_parts = []

        total_jobs = jobs_qs.count()
        total_applications = applications_qs.count()
        total_interviews = interviews_qs.count()

        if report_type == 'hiring_metrics':
            summary_parts.append(
                f"Total jobs: {total_jobs}, total applications: {total_applications}, total interviews: {total_interviews}."
            )
        elif report_type == 'time_to_hire':
            accepted_apps = applications_qs.filter(status='offer_accepted', review_date__isnull=False)
            if accepted_apps.exists():
                total_days = sum(
                    (app.review_date - app.created_at).days for app in accepted_apps if app.review_date
                )
                avg_days = total_days / accepted_apps.count()
                summary_parts.append(f"Average time to hire for accepted offers: {avg_days:.1f} days.")
            else:
                summary_parts.append('No accepted applications with review dates available for time to hire analysis.')
        elif report_type == 'candidate_pipeline':
            pipeline_counts = applications_qs.values('status').annotate(count=Count('id')).order_by('-count')
            summary_parts.append(
                f"Candidate pipeline includes {total_applications} applications across {pipeline_counts.count()} statuses."
            )
        elif report_type == 'diversity_report':
            gender_summary = ', '.join(
                f"{item.get('gender') or 'Unknown'}={item['count']}" for item in data['gender_counts']
            )
            summary_parts.append(f"Gender breakdown: {gender_summary}.")
        elif report_type == 'workflow_efficiency':
            summary_parts.append('Workflow efficiency metrics include average AI score by job and application throughput.')
        elif report_type == 'cost_analysis':
            summary_parts.append('Cost analysis data is based on job counts and application volume; attach financial metrics to parameters for deeper detail.')
        else:
            summary_parts.append('General hiring analytics report generated.')

        return {
            'data': data,
            'summary': ' '.join(summary_parts)
        }


# Celery tasks for async workflow processing
@shared_task
def process_workflow_stage_async(stage_id: int):
    """Process workflow stage asynchronously"""
    
    try:
        stage = WorkflowStage.objects.get(id=stage_id)
        engine = WorkflowEngine()
        engine.trigger_automated_actions(stage.instance, stage)
    except Exception as e:
        print(f"Error processing workflow stage {stage_id}: {e}")


@shared_task
def send_reminder_emails():
    """Send reminder emails for overdue tasks"""
    
    from datetime import timedelta
    
    # Get overdue tasks
    overdue_tasks = Task.objects.filter(
        due_date__lt=timezone.now(),
        status__in=['pending', 'in_progress']
    )
    
    for task in overdue_tasks:
        try:
            send_mail(
                subject=f'Task Overdue: {task.title}',
                message=f'The task "{task.title}" was due on {task.due_date.strftime("%B %d, %Y")}.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[task.assignee.email],
                fail_silently=True
            )
        except:
            pass


@shared_task
def update_workflow_metrics():
    """Update workflow metrics and analytics"""
    
    # This would update recruitment metrics in the database
    # Implementation depends on specific metrics requirements
    pass
