from django.urls import path
from . import views

app_name = 'ai_engine'

urlpatterns = [
    path('matching-results/', views.MatchingResultViewSet.as_view({'get': 'list', 'post': 'create'}), name='matching-results'),
    path('matching-results/<int:pk>/', views.MatchingResultViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name='matching-results-detail'),
    path('cv-parsing/', views.CVParsingResultViewSet.as_view({'get': 'list', 'post': 'create'}), name='cv-parsing'),
    path('cv-parsing/<int:pk>/', views.CVParsingResultViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name='cv-parsing-detail'),
    path('bias-detection/', views.BiasDetectionResultViewSet.as_view({'get': 'list', 'post': 'create'}), name='bias-detection'),
    path('bias-detection/<int:pk>/', views.BiasDetectionResultViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name='bias-detection-detail'),
    path('conversations/', views.ChatbotConversationViewSet.as_view({'get': 'list', 'post': 'create'}), name='conversations'),
    path('conversations/start_conversation/', views.ChatbotConversationViewSet.as_view({'post': 'start_conversation'}), name='start-conversation'),
    path('conversations/<int:pk>/', views.ChatbotConversationViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name='conversations-detail'),
    path('conversations/<int:pk>/continue_conversation/', views.ChatbotConversationViewSet.as_view({'post': 'continue_conversation'}), name='continue-conversation'),
    path('conversations/session/<str:session_id>/continue/', views.ChatbotConversationViewSet.as_view({'post': 'continue_conversation_by_session'}), name='continue-conversation-by-session'),
    path('insights/', views.AIInsightViewSet.as_view({'get': 'list', 'post': 'create'}), name='insights'),
    path('insights/<int:pk>/', views.AIInsightViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name='insights-detail'),
]
