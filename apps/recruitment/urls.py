from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    JobPostViewSet, ApplicationViewSet, InterviewViewSet, 
    RecruitmentMetricViewSet, JobCategoryViewSet
)

router = DefaultRouter()
router.register(r'jobs', JobPostViewSet, basename='job')
router.register(r'job-categories', JobCategoryViewSet, basename='jobcategory')
router.register(r'applications', ApplicationViewSet, basename='application')
router.register(r'interviews', InterviewViewSet, basename='interview')
router.register(r'metrics', RecruitmentMetricViewSet, basename='metric')

app_name = 'recruitment'

urlpatterns = [
    path('', include(router.urls)),
]
