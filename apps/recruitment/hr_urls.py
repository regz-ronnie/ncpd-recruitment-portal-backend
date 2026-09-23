from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    JobPostViewSet, ApplicationViewSet, InterviewViewSet, 
    RecruitmentMetricViewSet, JobCategoryViewSet
)
from apps.users.views import HRUserListView

router = DefaultRouter()
router.register(r'applications', ApplicationViewSet, basename='hr-application')
router.register(r'vacancies', JobPostViewSet, basename='hr-vacancy')
router.register(r'interviews', InterviewViewSet, basename='hr-interview')
router.register(r'panels', InterviewViewSet, basename='hr-panel')
router.register(r'audit-logs', RecruitmentMetricViewSet, basename='hr-audit-log')
router.register(r'analytics', RecruitmentMetricViewSet, basename='hr-analytics')
router.register(r'talent-pool', ApplicationViewSet, basename='hr-talent-pool')
router.register(r'users', HRUserListView, basename='hr-user')

app_name = 'hr'

urlpatterns = [
    path('', include(router.urls)),
]
