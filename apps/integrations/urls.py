from django.urls import path
from . import views

app_name = 'integrations'

urlpatterns = [
    path('verification-requests/', views.VerificationRequestViewSet.as_view({'get': 'list', 'post': 'create'}), name='verification-requests'),
    path('verification-requests/<int:pk>/', views.VerificationRequestViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name='verification-requests-detail'),
    path('verification-results/', views.VerificationResultViewSet.as_view({'get': 'list', 'post': 'create'}), name='verification-results'),
    path('verification-results/<int:pk>/', views.VerificationResultViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name='verification-results-detail'),
]
