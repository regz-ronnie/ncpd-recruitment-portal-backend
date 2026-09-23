"""
URL configuration for ncpd_portal project.
"""
from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from django.contrib.auth import get_user_model

def api_info(request):
    return JsonResponse({
        'message': 'NCPD Recruitment Portal API',
        'version': '1.0.0',
        'endpoints': {
            'api_docs': '/api/docs/',
            'api_schema': '/api/schema/',
            'admin': '/admin/',
            'api': '/api/'
        }
    })

urlpatterns = [
    path('', api_info, name='api-info'),
    path('admin/', admin.site.urls),
    
    # CAPTCHA URLs
    path('captcha/', include('captcha.urls')),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    
    # API Endpoints
    path('api/', include('apps.api.urls')),
    path('api/auth/', include(('apps.users.urls', 'users'), namespace='auth')),
    path('api/users/', include('apps.users.urls')),
    path('api/v1/auth/', include(('apps.users.urls', 'users'), namespace='auth-v1')),
    path('api/v1/users/', include(('apps.users.urls', 'users'), namespace='users-v1')),
    path('api/v1/', include(('apps.recruitment.urls', 'recruitment'), namespace='recruitment-v1')),
    path('api/recruitment/', include(('apps.recruitment.urls', 'recruitment'), namespace='recruitment')),
    path('api/hr/', include(('apps.recruitment.hr_urls', 'hr'), namespace='hr')),
    path('api/v1/hr/', include(('apps.recruitment.hr_urls', 'hr'), namespace='hr-v1')),
    path('api/ai-engine/', include(('apps.ai_engine.urls', 'ai_engine'), namespace='ai_engine')),
    path('api/v1/ai-engine/', include(('apps.ai_engine.urls', 'ai_engine'), namespace='ai_engine-v1')),
    path('api/workflow/', include('apps.workflow.urls')),
    path('api/integrations/', include('apps.integrations.urls')),
    
    # Frontend routing (for SPA)
    # path('', include('frontend_urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)