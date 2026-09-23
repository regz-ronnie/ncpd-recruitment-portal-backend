from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import VerificationRequest, VerificationResult
from .serializers import VerificationRequestSerializer, VerificationResultSerializer


class VerificationRequestViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = VerificationRequest.objects.all()
    serializer_class = VerificationRequestSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['verification_type', 'status']
    search_fields = ['user__first_name', 'user__last_name']
    ordering_fields = ['created_at', 'completed_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type in ['hr', 'manager', 'admin']:
            return VerificationRequest.objects.all()
        return VerificationRequest.objects.filter(user=user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def verify_national_id(self, request):
        """Trigger national ID verification"""
        serializer = self.get_serializer(data={
            **request.data,
            'verification_type': 'national_id'
        })
        if serializer.is_valid():
            verification = serializer.save(user=request.user)
            # Trigger actual verification logic here
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def verify_academic(self, request):
        """Trigger academic credential verification"""
        serializer = self.get_serializer(data={
            **request.data,
            'verification_type': 'academic'
        })
        if serializer.is_valid():
            verification = serializer.save(user=request.user)
            # Trigger actual verification logic here
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def verify_integrity(self, request):
        """Trigger Chapter Six integrity check"""
        serializer = self.get_serializer(data={
            **request.data,
            'verification_type': 'integrity'
        })
        if serializer.is_valid():
            verification = serializer.save(user=request.user)
            # Trigger actual verification logic here
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerificationResultViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = VerificationResult.objects.all()
    serializer_class = VerificationResultSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['verification_type', 'is_verified']
    search_fields = ['verification_request__user__first_name', 'verification_request__user__last_name']
    ordering_fields = ['verification_date']
    ordering = ['-verification_date']
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type in ['hr', 'manager', 'admin']:
            return VerificationResult.objects.all()
        return VerificationResult.objects.filter(verification_request__user=user)
