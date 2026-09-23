from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import (
    MatchingResult, CVParsingResult, BiasDetectionResult, 
    ChatbotConversation, AIInsight, AIModel, SkillEmbedding
)
from .serializers import (
    MatchingResultSerializer, CVParsingResultSerializer, 
    BiasDetectionResultSerializer, ChatbotConversationSerializer, 
    AIInsightSerializer, AIModelSerializer, SkillEmbeddingSerializer
)


class AIModelViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = AIModel.objects.all()
    serializer_class = AIModelSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['model_type', 'is_active', 'provider']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'accuracy_score']
    ordering = ['-created_at']


class MatchingResultViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = MatchingResult.objects.all()
    serializer_class = MatchingResultSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['job', 'candidate', 'recommendation']
    search_fields = ['candidate__first_name', 'candidate__last_name', 'job__title']
    ordering_fields = ['overall_score', 'created_at']
    ordering = ['-overall_score']
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type in ['hr', 'manager', 'admin']:
            return MatchingResult.objects.all()
        return MatchingResult.objects.filter(candidate=user)


class CVParsingResultViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = CVParsingResult.objects.all()
    serializer_class = CVParsingResultSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['ai_model']
    ordering_fields = ['processed_at', 'confidence_score']
    ordering = ['-processed_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type in ['hr', 'manager', 'admin']:
            return CVParsingResult.objects.all()
        return CVParsingResult.objects.filter(user=user)


class BiasDetectionResultViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = BiasDetectionResult.objects.all()
    serializer_class = BiasDetectionResultSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['content_type']
    ordering_fields = ['processed_at', 'bias_score']
    ordering = ['-processed_at']


class ChatbotConversationViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = ChatbotConversation.objects.all()
    serializer_class = ChatbotConversationSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['conversation_type', 'resolution_status']
    search_fields = ['initial_query', 'session_id']
    ordering_fields = ['started_at', 'last_message_at']
    ordering = ['-last_message_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type in ['hr', 'manager', 'admin']:
            return ChatbotConversation.objects.all()
        return ChatbotConversation.objects.filter(user=user)
    
    @action(detail=False, methods=['post'])
    def start_conversation(self, request):
        """Start a new chatbot conversation"""
        from .services.chatbot_service import RecruitmentChatbot
        
        try:
            chatbot = RecruitmentChatbot()
            conversation_type = request.data.get('conversation_type', 'faq')
            initial_query = request.data.get('initial_query', 'Start conversation')
            
            conversation = chatbot.start_conversation(
                user=request.user,
                conversation_type=conversation_type,
                initial_query=initial_query
            )
            
            serializer = self.get_serializer(conversation)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'], url_path='session/(?P<session_id>[^/]+)/continue')
    def continue_conversation_by_session(self, request, session_id=None):
        """Continue an existing conversation by session ID"""
        from .services.chatbot_service import RecruitmentChatbot
        from .models import ChatbotConversation
        
        try:
            chatbot = RecruitmentChatbot()
            
            user_message = request.data.get('message', '')
            attachment = request.data.get('attachment')
            
            # If there's an attachment, add it to the message
            if attachment:
                user_message += f" [Attachment: {attachment.get('name', 'file')}]"
            
            response_data = chatbot.continue_conversation(
                session_id=session_id,
                user_message=user_message,
                attachment=attachment
            )
            
            if 'error' in response_data:
                return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
            
            # Get conversation data
            try:
                conversation = ChatbotConversation.objects.get(session_id=session_id)
                serializer = self.get_serializer(conversation)
                conversation_data = serializer.data
            except ChatbotConversation.DoesNotExist:
                conversation_data = None
            
            return Response({
                'response': response_data.get('response'),
                'conversation': conversation_data,
                'extracted_info': response_data.get('extracted_info'),
                'next_actions': response_data.get('next_actions'),
                'status': response_data.get('status')
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AIInsightViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = AIInsight.objects.all()
    serializer_class = AIInsightSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['insight_type']
    search_fields = ['title', 'description']
    ordering_fields = ['generated_at', 'confidence_level']
    ordering = ['-generated_at']


class SkillEmbeddingViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = SkillEmbedding.objects.all()
    serializer_class = SkillEmbeddingSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['content_type', 'embedding_model']
    search_fields = ['text_content']
