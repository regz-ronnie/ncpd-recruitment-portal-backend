from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import permissions

# Import app routers
from apps.users.urls import urlpatterns as user_urls
from apps.recruitment.urls import urlpatterns as recruitment_urls

# Create API router
router = DefaultRouter()

# JWT token refresh endpoint
router.register(r'token/refresh/', TokenRefreshView.as_view(), basename='token-refresh')

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def api_root(request):
    """
    API root endpoint
    """
    return Response({
        'message': 'NCPD Recruitment Portal API',
        'version': 'v1',
        'endpoints': {
            'auth': '/api/auth/',
            'jobs': '/api/v1/jobs/',
            'applications': '/api/v1/applications/',
            'token_refresh': '/api/token/refresh/'
        }
    })

app_name = 'api'

urlpatterns = [
    # API root
    path('', api_root, name='api-root'),
    
    # Authentication endpoints
    path('auth/', include(user_urls)),
    
    # Recruitment endpoints
    path('v1/', include(recruitment_urls)),
    
    # JWT token refresh
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
]
