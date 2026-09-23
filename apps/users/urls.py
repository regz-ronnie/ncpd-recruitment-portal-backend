from django.urls import path
from . import views, auth_views
from rest_framework_simplejwt.views import TokenRefreshView

app_name = 'users'

urlpatterns = [
    # Authentication endpoints
    path('captcha/', auth_views.get_captcha, name='get_captcha'),
    path('register/', auth_views.register, name='register'),
    path('login/', auth_views.login, name='login'),
    path('logout/', auth_views.logout, name='logout'),
    path('profile/', auth_views.profile, name='profile'),
    path('profile/update/', auth_views.update_profile, name='update_profile'),
    path('upload-document/', auth_views.upload_document, name='upload-document'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('admin-access/', auth_views.admin_access, name='admin-access'),
    
    # Password reset endpoints
    path('forgot-password/', auth_views.forgot_password, name='forgot_password'),
    path('reset-password/', auth_views.reset_password, name='reset_password'),
    
    # 2FA endpoints
    path('verify-otp-login/', auth_views.verify_otp_and_login, name='verify-otp-login'),
    path('2fa/enable/', auth_views.enable_2fa, name='enable-2fa'),
    path('2fa/disable/', auth_views.disable_2fa, name='disable-2fa'),
    path('2fa/verify-setup/', auth_views.verify_2fa_setup, name='verify-2fa-setup'),
    
    # User profile endpoints
    path('user/profile/', views.UserProfileView.as_view({'get': 'retrieve', 'put': 'update'}), name='user-profile'),
    path('user/skills/', views.UserSkillListView.as_view({'get': 'list', 'post': 'create'}), name='user-skills'),
    path('user/skills/<int:pk>/', views.UserSkillListView.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name='user-skills-detail'),
    path('user/experience/', views.UserExperienceListView.as_view({'get': 'list', 'post': 'create'}), name='user-experience'),
    path('user/experience/<int:pk>/', views.UserExperienceListView.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name='user-experience-detail'),
    path('user/certifications/', views.CertificationListView.as_view({'get': 'list', 'post': 'create'}), name='user-certifications'),
    path('user/certifications/<int:pk>/', views.CertificationListView.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name='user-certifications-detail'),
    path('admin/users/', views.AdminUserViewSet.as_view({'get': 'list', 'post': 'create'}), name='admin-users-list'),
    path('admin/users/<int:pk>/', views.AdminUserViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='admin-users-detail'),
]
