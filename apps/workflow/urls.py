from django.urls import path
from . import views

app_name = 'workflow'

urlpatterns = [
    path('templates/', views.WorkflowTemplateViewSet.as_view({'get': 'list', 'post': 'create'}), name='workflow-templates'),
    path('templates/<int:pk>/', views.WorkflowTemplateViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name='workflow-templates-detail'),
    path('instances/', views.WorkflowInstanceViewSet.as_view({'get': 'list', 'post': 'create'}), name='workflow-instances'),
    path('instances/<int:pk>/', views.WorkflowInstanceViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name='workflow-instances-detail'),
    path('stages/', views.WorkflowStageViewSet.as_view({'get': 'list', 'post': 'create'}), name='workflow-stages'),
    path('stages/<int:pk>/', views.WorkflowStageViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name='workflow-stages-detail'),
    path('tasks/', views.TaskViewSet.as_view({'get': 'list', 'post': 'create'}), name='workflow-tasks'),
    path('tasks/<int:pk>/', views.TaskViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name='workflow-tasks-detail'),
    path('notifications/', views.NotificationViewSet.as_view({'get': 'list', 'post': 'create'}), name='workflow-notifications'),
    path('notifications/<int:pk>/', views.NotificationViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name='workflow-notifications-detail'),
]
