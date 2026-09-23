from django.http import JsonResponse
from django.urls import reverse
from django.views import View


class APIRootView(View):
    """API Root endpoint showing available endpoints"""
    
    def get(self, request):
        endpoints = {
            'message': 'NCPD Recruitment Portal API',
            'version': '1.0.0',
            'authentication': 'JWT Bearer Token required for most endpoints',
            'endpoints': {
                'auth': {
                    'register': '/api/auth/register/',
                    'login': '/api/auth/login/',
                    'logout': '/api/auth/logout/',
                    'profile': '/api/auth/profile/',
                    'update_profile': '/api/auth/profile/update/',
                },
                'users': {
                    'profile': '/api/users/user/profile/',
                    'skills': '/api/users/user/skills/',
                    'experience': '/api/users/user/experience/',
                    'certifications': '/api/users/user/certifications/',
                },
                'recruitment': {
                    'jobs': '/api/recruitment/jobs/',
                    'job_categories': '/api/recruitment/job-categories/',
                    'applications': '/api/recruitment/applications/',
                    'interviews': '/api/recruitment/interviews/',
                    'metrics': '/api/recruitment/metrics/',
                },
                'ai_engine': {
                    'ai_models': '/api/ai-engine/aimodels/',
                    'matching_results': '/api/ai-engine/matchingresults/',
                    'cv_parsing': '/api/ai-engine/cvparsingresults/',
                    'bias_detection': '/api/ai-engine/biasdetectionresults/',
                    'conversations': '/api/ai-engine/chatbotconversations/',
                    'insights': '/api/ai-engine/aiinsights/',
                    'skill_embeddings': '/api/ai-engine/skillembeddings/',
                },
                'workflow': {
                    'templates': '/api/workflow/workflowtemplates/',
                    'instances': '/api/workflow/workflowinstances/',
                    'stages': '/api/workflow/workflowstages/',
                    'email_templates': '/api/workflow/emailtemplates/',
                    'email_logs': '/api/workflow/emaillogs/',
                    'tasks': '/api/workflow/tasks/',
                    'notifications': '/api/workflow/notifications/',
                    'audit_logs': '/api/workflow/auditlogs/',
                    'reports': '/api/workflow/reports/',
                },
                'integrations': {
                    'verification_requests': '/api/integrations/verificationrequests/',
                    'verification_results': '/api/integrations/verificationresults/',
                },
                'documentation': {
                    'schema': '/api/schema/',
                    'swagger_docs': '/api/docs/',
                },
                'admin': '/admin/'
            }
        }
        
        return JsonResponse(endpoints)
