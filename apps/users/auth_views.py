from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from dj_rest_auth.jwt_auth import JWTCookieAuthentication
from captcha.fields import CaptchaField
from captcha.models import CaptchaStore
import pyotp
import random
from .serializers import UserSerializer, UserRegistrationSerializer, UserProfileSerializer
from .models import User

User = get_user_model()


def generate_otp(user):
    """Generate a 6-digit OTP for the user"""
    # Generate a random 6-digit code
    otp = str(random.randint(100000, 999999))
    
    # Store the OTP and expiry time (5 minutes from now)
    from django.utils import timezone
    import json
    user.otp_secret = json.dumps({
        'code': otp,
        'expires_at': (timezone.now() + timezone.timedelta(minutes=5)).isoformat()
    })
    user.save()
    
    return otp


def verify_otp(user, otp_code):
    """Verify the OTP code for the user"""
    if not user.otp_secret:
        return False
    
    try:
        import json
        from django.utils import timezone
        from datetime import datetime
        
        otp_data = json.loads(user.otp_secret)
        stored_code = otp_data.get('code')
        expires_at = datetime.fromisoformat(otp_data.get('expires_at'))
        
        # Check if OTP has expired
        if timezone.now() > expires_at:
            print(f"OTP expired. Current time: {timezone.now()}, Expires at: {expires_at}")
            return False
        
        # Verify the code
        if str(otp_code) == str(stored_code):
            print(f"OTP verified successfully")
            return True
        else:
            print(f"OTP mismatch. Expected: {stored_code}, Got: {otp_code}")
            return False
            
    except Exception as e:
        print(f"OTP verification error: {e}")
        return False


def send_otp_via_email(user, otp):
    """Send OTP to user's email"""
    subject = 'Your NCPD Recruitment Portal Verification Code'
    message = f'''
    Your verification code is: {otp}
    
    This code will expire in 5 minutes.
    
    If you did not request this code, please ignore this email.
    '''
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        print(f"OTP sent to {user.email}: {otp}")
        return True
    except Exception as e:
        print(f"Failed to send OTP email: {e}")
        return False


@api_view(['POST'])
@authentication_classes([])
@permission_classes([permissions.AllowAny])
def register(request):
    """
    Register a new user
    """
    try:
        # Handle 'role' field from frontend, map to 'user_type'
        request_data = request.data.copy()
        if 'role' in request_data and 'user_type' not in request_data:
            request_data['user_type'] = request_data.pop('role')
        
        serializer = UserRegistrationSerializer(data=request_data)
        
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            
            # Use UserProfileSerializer to return complete profile data
            from .serializers import UserProfileSerializer
            
            return Response({
                'user': UserProfileSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'error': 'Validation failed',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        return Response({
            'error': 'Registration failed',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([])
@permission_classes([permissions.AllowAny])
def get_captcha(request):
    """
    Generate a new CAPTCHA image and return the key
    """
    try:
        from captcha.helpers import captcha_image_url
        from captcha.conf import settings as captcha_settings
        
        # Generate a new captcha
        captcha_key = CaptchaStore.generate_key()
        captcha_image = captcha_image_url(captcha_key)
        
        return Response({
            'captcha_key': captcha_key,
            'captcha_image': captcha_image
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'error': 'Failed to generate CAPTCHA'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([permissions.AllowAny])
def login(request):
    """
    Custom login view that returns JWT tokens with CAPTCHA and 2FA support
    """
    try:
        email = request.data.get('email')
        password = request.data.get('password')
        captcha_key = request.data.get('captcha_key')
        captcha_value = request.data.get('captcha_value')

        if not all([email, password]):
            return Response({
                'error': 'Please provide email and password'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Verify CAPTCHA (required for all users)
        if not captcha_key or not captcha_value:
            return Response({
                'error': 'CAPTCHA is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            captcha_store = CaptchaStore.objects.get(hashkey=captcha_key)
            if captcha_store.response != captcha_value.lower():
                return Response({
                    'error': 'Invalid CAPTCHA'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Delete the captcha after successful verification
            captcha_store.delete()
        except CaptchaStore.DoesNotExist:
            return Response({
                'error': 'Invalid CAPTCHA'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Authenticate user
        from django.contrib.auth import authenticate
        user = authenticate(request, username=email, password=password)

        if not user:
            return Response({
                'error': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_active:
            return Response({
                'error': 'Account is disabled'
            }, status=status.HTTP_401_UNAUTHORIZED)

        # Check if 2FA is enabled
        if user.otp_enabled:
            # Generate and send OTP
            otp = generate_otp(user)
            send_otp_via_email(user, otp)

            return Response({
                'message': '2FA required. OTP sent to your email.',
                'requires_2fa': True,
                'user_id': user.id,
                'email': user.email
            }, status=status.HTTP_200_OK)

        # Generate tokens
        refresh = RefreshToken.for_user(user)

        # Use simple UserSerializer instead of UserProfileSerializer to avoid complexity
        try:
            user_data = UserSerializer(user).data
        except Exception as e:
            print(f"Error serializing user: {e}")
            # Fallback to basic user data
            user_data = {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'user_type': user.user_type,
                'is_verified': user.is_verified,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
            }

        print(f"Login - User data keys: {list(user_data.keys()) if isinstance(user_data, dict) else 'Not a dict'}")

        return Response({
            'user': user_data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_200_OK)

    except Exception as e:
        print(f"Login error: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout(request):
    """
    Logout user by blacklisting their refresh token
    """
    try:
        refresh_token = request.data.get('refresh')
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except Exception as e:
                # Token might be invalid or already blacklisted, but logout should still succeed
                pass
        
        return Response({
            'message': 'Successfully logged out'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def profile(request):
    """
    Get current user profile - returns comprehensive user data
    """
    try:
        from .serializers import UserProfileSerializer

        print(f"Profile request for user: {request.user.id}")
        print(f"User academic_qualifications from DB: {request.user.academic_qualifications}")
        print(f"User work_experiences_json from DB: {request.user.work_experiences_json}")
        print(f"User referees from DB: {request.user.referees}")
        print(f"User attachments from DB: {request.user.attachments}")
        
        # Return comprehensive user data using UserProfileSerializer
        profile_data = UserProfileSerializer(request.user).data

        print(f"Profile data keys: {list(profile_data.keys())}")
        print(f"Total fields: {len(profile_data.keys())}")
        print(f"Key JSON fields in response: academic_qualifications={bool(profile_data.get('academic_qualifications'))}, work_experiences={bool(profile_data.get('work_experiences'))}, referees={bool(profile_data.get('referees'))}, attachments={bool(profile_data.get('attachments'))}")

        return Response(profile_data, status=status.HTTP_200_OK)
    except Exception as e:
        print(f"Error in profile endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def upload_document(request):
    """
    Upload a single document and return its URL
    """
    try:
        if 'file' not in request.FILES:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

        uploaded_file = request.FILES['file']
        document_type = request.data.get('document_type', 'Document')

        # File validation
        # Check file size (max 5MB)
        max_size = 5 * 1024 * 1024  # 5MB
        if uploaded_file.size > max_size:
            return Response({'error': 'File size exceeds 5MB limit'}, status=status.HTTP_400_BAD_REQUEST)

        # Check file type
        allowed_types = [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'image/jpeg',
            'image/png',
            'image/jpg'
        ]
        
        if uploaded_file.content_type not in allowed_types:
            return Response({
                'error': f'File type {uploaded_file.content_type} not allowed. Allowed types: PDF, DOC, DOCX, JPEG, PNG'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Sanitize filename
        import os
        safe_filename = os.path.basename(uploaded_file.name)
        # Remove any path components and potentially dangerous characters
        safe_filename = "".join(c for c in safe_filename if c.isalnum() or c in '._-')
        
        # Add timestamp to prevent overwrites
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_filename = f"{timestamp}_{safe_filename}"

        # Save file using the user's upload path
        from django.core.files.storage import default_storage
        file_path = f"applications/{request.user.username}/{safe_filename}"
        saved_path = default_storage.save(file_path, uploaded_file)
        file_url = default_storage.url(saved_path)

        return Response({
            'url': file_url,
            'file_name': uploaded_file.name,
            'safe_filename': safe_filename,
            'document_type': document_type,
            'file_size': uploaded_file.size,
            'content_type': uploaded_file.content_type
        }, status=status.HTTP_200_OK)
    except Exception as e:
        print(f"Upload document exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def update_profile(request):
    """
    Update current user profile - updates User model directly
    """
    try:
        from .serializers import UserProfileSerializer

        print(f"Update profile request data keys: {list(request.data.keys())}")
        print(f"Update profile request content type: {request.content_type}")

        # Handle file uploads
        if request.content_type and 'multipart/form-data' in request.content_type:
            # Process file uploads and update attachments
            attachments = request.user.attachments or []
            updated_attachments = []

            # Find all file uploads
            file_index = 0
            while f'file_{file_index}' in request.data:
                uploaded_file = request.data.get(f'file_{file_index}')
                document_type = request.data.get(f'document_type_{file_index}', 'Document')

                if uploaded_file:
                    # Save file and get URL
                    file_path = request.user.resume_file.field.upload_to(request.user, uploaded_file.name)
                    from django.core.files.storage import default_storage
                    saved_path = default_storage.save(file_path, uploaded_file)
                    file_url = default_storage.url(saved_path)

                    # Find corresponding attachment and update its file field
                    attachment_found = False
                    for attachment in attachments:
                        if attachment.get('documentType') == document_type:
                            attachment['file'] = {'url': file_url, 'name': uploaded_file.name}
                            updated_attachments.append(attachment)
                            attachment_found = True
                            break

                    # If no matching attachment found, create new one
                    if not attachment_found:
                        new_attachment = {
                            'id': str(int(hash(uploaded_file.name) * 1000)),
                            'documentType': document_type,
                            'fileName': uploaded_file.name,
                            'dateUploaded': None,
                            'file': {'url': file_url, 'name': uploaded_file.name}
                        }
                        updated_attachments.append(new_attachment)

                    print(f"Uploaded file: {uploaded_file.name} -> {file_url}")

                file_index += 1

            # Update request data with processed attachments
            request_data = request.data.copy()
            request_data['attachments'] = updated_attachments

            # Remove file fields from data before serialization
            for key in list(request_data.keys()):
                if key.startswith('file_') or key.startswith('document_type_'):
                    del request_data[key]

            print(f"Processed attachments: {updated_attachments}")
        else:
            request_data = request.data

        # Update user fields directly using serializer
        user_serializer = UserProfileSerializer(request.user, data=request_data, partial=True)
        if user_serializer.is_valid():
            user_serializer.save()
        else:
            print(f"Serializer validation errors: {user_serializer.errors}")
            return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Return updated user data
        profile_data = UserProfileSerializer(request.user).data

        return Response(profile_data, status=status.HTTP_200_OK)
    except Exception as e:
        print(f"Update profile exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def admin_access(request):
    """
    Check if user has admin access and provide admin URL
    """
    try:
        user = request.user
        
        if not (user.is_staff or user.is_superuser):
            return Response({
                'error': 'User does not have admin access'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Ensure Django session is active
        from django.contrib.auth import login as django_login
        django_login(request, user)
        
        return Response({
            'has_admin_access': True,
            'admin_url': '/admin/',
            'username': user.username,
            'is_superuser': user.is_superuser,
            'is_staff': user.is_staff
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([permissions.AllowAny])
def forgot_password(request):
    """
    Send password reset email with token
    """
    try:
        email = request.data.get('email')
        
        if not email:
            return Response({
                'error': 'Please provide your email address'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Don't reveal if email exists or not for security
            return Response({
                'message': 'If the email exists, a password reset link has been sent.'
            }, status=status.HTTP_200_OK)
        
        # Generate password reset token
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes
        
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        # Send email with reset link
        reset_link = f"http://localhost:5173/reset-password/{uid}/{token}/"
        
        subject = 'Password Reset Request - NCPD Recruitment Portal'
        message = f'''
        You requested a password reset for your NCPD Recruitment Portal account.
        
        Click the link below to reset your password:
        {reset_link}
        
        This link will expire in 24 hours.
        
        If you did not request this password reset, please ignore this email.
        '''
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=True
        )
        
        return Response({
            'message': 'If the email exists, a password reset link has been sent.'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': 'Failed to send password reset email'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([permissions.AllowAny])
def reset_password(request):
    """
    Reset password using token
    """
    try:
        uid = request.data.get('uid')
        token = request.data.get('token')
        new_password = request.data.get('new_password')
        
        if not all([uid, token, new_password]):
            return Response({
                'error': 'Please provide uid, token, and new password'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        from django.utils.http import urlsafe_base64_decode
        from django.contrib.auth.tokens import default_token_generator
        
        try:
            user_id = urlsafe_base64_decode(uid).decode()
            user = User.objects.get(pk=user_id)
        except (User.DoesNotExist, ValueError, TypeError):
            return Response({
                'error': 'Invalid reset link'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify token
        if not default_token_generator.check_token(user, token):
            return Response({
                'error': 'Invalid or expired reset link'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate password strength
        if len(new_password) < 8:
            return Response({
                'error': 'Password must be at least 8 characters long'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Set new password
        user.set_password(new_password)
        user.save()
        
        return Response({
            'message': 'Password reset successfully. You can now login with your new password.'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': 'Failed to reset password'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([permissions.AllowAny])
def verify_otp_and_login(request):
    """
    Verify OTP and complete login with JWT tokens
    """
    try:
        print(f"OTP verification request data: {request.data}")
        user_id = request.data.get('user_id')
        otp_code = request.data.get('otp_code')
        email = request.data.get('email')
        password = request.data.get('password')

        print(f"Extracted values - user_id: {user_id}, otp_code: {otp_code}, email: {email}, password: {'*' * len(password) if password else 'None'}")

        if not all([user_id, otp_code, email, password]):
            return Response({
                'error': 'Please provide user_id, otp_code, email, and password'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get user
        try:
            user = User.objects.get(id=user_id, email=email)
            print(f"User found: {user.email}, 2FA enabled: {user.otp_enabled}, OTP secret: {user.otp_secret}")
        except User.DoesNotExist:
            print(f"User not found with id={user_id}, email={email}")
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Verify credentials again for security
        from django.contrib.auth import authenticate
        authenticated_user = authenticate(request, username=email, password=password)
        
        print(f"Authentication result: {authenticated_user is not None}")
        
        if not authenticated_user or authenticated_user.id != user.id:
            print(f"Authentication failed or ID mismatch")
            return Response({
                'error': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)

        # Verify OTP
        otp_valid = verify_otp(user, otp_code)
        print(f"OTP verification result: {otp_valid}")
        
        if not otp_valid:
            return Response({
                'error': 'Invalid or expired OTP'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Mark OTP as verified
        user.otp_verified = True
        user.save()

        # Generate tokens
        refresh = RefreshToken.for_user(user)

        try:
            user_data = UserSerializer(user).data
        except Exception as e:
            print(f"Error serializing user: {e}")
            user_data = {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'user_type': user.user_type,
                'is_verified': user.is_verified,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
            }

        return Response({
            'user': user_data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_200_OK)

    except Exception as e:
        print(f"OTP verification error: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def enable_2fa(request):
    """
    Enable two-factor authentication for the user
    """
    try:
        user = request.user
        
        # Generate OTP secret
        user.otp_secret = pyotp.random_base32()
        user.otp_enabled = True
        user.otp_verified = False
        user.save()

        # Generate and send initial OTP
        otp = generate_otp(user)
        send_otp_via_email(user, otp)

        return Response({
            'message': '2FA enabled. OTP sent to your email.',
            'otp_enabled': True
        }, status=status.HTTP_200_OK)

    except Exception as e:
        print(f"Enable 2FA error: {str(e)}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def disable_2fa(request):
    """
    Disable two-factor authentication for the user
    """
    try:
        user = request.user
        
        user.otp_enabled = False
        user.otp_secret = None
        user.otp_verified = False
        user.save()

        return Response({
            'message': '2FA disabled successfully',
            'otp_enabled': False
        }, status=status.HTTP_200_OK)

    except Exception as e:
        print(f"Disable 2FA error: {str(e)}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def verify_2fa_setup(request):
    """
    Verify OTP during 2FA setup
    """
    try:
        user = request.user
        otp_code = request.data.get('otp_code')

        if not otp_code:
            return Response({
                'error': 'Please provide OTP code'
            }, status=status.HTTP_400_BAD_REQUEST)

        if verify_otp(user, otp_code):
            user.otp_verified = True
            user.save()
            return Response({
                'message': '2FA setup verified successfully',
                'otp_verified': True
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'Invalid OTP code'
            }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        print(f"Verify 2FA setup error: {str(e)}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
