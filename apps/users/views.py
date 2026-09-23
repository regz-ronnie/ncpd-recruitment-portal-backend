from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils import timezone
import datetime
from .models import User, Profile, UserSkill, WorkExperience, Certification, Skill
from .serializers import (
    UserSerializer, ProfileSerializer, UserSkillSerializer, 
    WorkExperienceSerializer, CertificationSerializer, SkillSerializer,
    UserProfileSerializer, AdminUserSerializer
)

class UserProfileView(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()
    serializer_class = UserSerializer
    parser_classes = [MultiPartParser, FormParser]
    
    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id)
    
    @action(detail=False, methods=['get', 'put', 'patch'])
    def me(self, request):
        """Get or update current user profile"""
        if request.method == 'GET':
            serializer = UserProfileSerializer(request.user)
            return Response(serializer.data)
        else:
            try:
                # Handle multipart form data for file uploads
                if request.content_type.startswith('multipart/form-data'):
                    data = request.data.dict()
                    files = request.FILES
                    
                    # Process file uploads and save them
                    attachments = request.user.attachments or []
                    
                    # For simplicity, we'll process files and store metadata
                    # In production, you'd want separate file fields or a proper file storage system
                    file_index = 0
                    for key, file in files.items():
                        # Generate unique filename
                        timestamp = int((datetime.datetime.now() - datetime.datetime(1970,1,1)).total_seconds())
                        file_name = f"{request.user.username}_{timestamp}_{file.name}"
                        
                        # Temporarily save to resume_file (this will be overwritten by the last file)
                        # In production, you'd have separate file fields or use a proper file storage service
                        request.user.resume_file = file
                        request.user.save()
                        
                        file_url = request.user.resume_file.url if request.user.resume_file else ''
                        
                        # Determine document type from field name or request data
                        if key.startswith('file_'):
                            index = key.split('_')[1]
                            doc_type = request.data.get(f'document_type_{index}', 'Other')
                        else:
                            doc_type = 'Other'
                        
                        new_attachment = {
                            'name': file.name,
                            'document_type': doc_type,
                            'file_url': file_url,
                            'date_uploaded': timezone.now().isoformat()
                        }
                        
                        attachments.append(new_attachment)
                        file_index += 1
                    
                    data['attachments'] = attachments
                    serializer = UserProfileSerializer(request.user, data=data, partial=True)
                else:
                    serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
                
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                import traceback
                print(f"Error in profile update: {str(e)}")
                print(f"Traceback: {traceback.format_exc()}")
                return Response({'error': str(e), 'detail': traceback.format_exc()}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ProfileView(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    
    def get_queryset(self):
        return Profile.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get', 'put', 'patch'])
    def me(self, request):
        """Get or update current user's extended profile"""
        profile, created = Profile.objects.get_or_create(user=request.user)
        if request.method == 'GET':
            serializer = ProfileSerializer(profile)
            return Response(serializer.data)
        else:
            serializer = ProfileSerializer(profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserSkillListView(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = UserSkill.objects.all()
    serializer_class = UserSkillSerializer
    
    def get_queryset(self):
        return UserSkill.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class UserExperienceListView(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = WorkExperience.objects.all()
    serializer_class = WorkExperienceSerializer
    
    def get_queryset(self):
        return WorkExperience.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class CertificationListView(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Certification.objects.all()
    serializer_class = CertificationSerializer
    
    def get_queryset(self):
        return Certification.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class SkillListView(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer

class HRUserListView(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type in ['hr', 'manager', 'admin']:
            return User.objects.all()
        return User.objects.filter(id=user.id)


class AdminUserViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()
    serializer_class = AdminUserSerializer

    def _require_admin(self):
        user = self.request.user
        if not (user.user_type == 'admin' or user.is_superuser):
            raise PermissionDenied('Admin privileges are required.')

    def get_queryset(self):
        self._require_admin()
        return User.objects.all().order_by('-date_joined')

    def perform_create(self, serializer):
        self._require_admin()
        serializer.save()

    def update(self, request, *args, **kwargs):
        self._require_admin()
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        self._require_admin()
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        self._require_admin()
        return super().destroy(request, *args, **kwargs)
