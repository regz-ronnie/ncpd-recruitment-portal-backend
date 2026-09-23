from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import UserSkill, WorkExperience, Certification, Skill, Profile

User = get_user_model()


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = '__all__'


class UserSkillSerializer(serializers.ModelSerializer):
    skill = SkillSerializer(read_only=True)
    
    class Meta:
        model = UserSkill
        fields = '__all__'


class WorkExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkExperience
        fields = '__all__'


class CertificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certification
        fields = '__all__'


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    user_type = serializers.CharField(required=False, default='applicant')
    phone_number = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone_number', 'password', 'password_confirm', 'user_type']
        extra_kwargs = {
            'password': {'write_only': True},
            'password_confirm': {'write_only': True}
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        
        # Validate user_type if provided
        if 'user_type' in attrs:
            valid_types = [choice[0] for choice in User.USER_TYPES]
            if attrs['user_type'] not in valid_types:
                raise serializers.ValidationError(f"Invalid user_type. Must be one of: {valid_types}")
        
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        # Use email as username for the custom user model
        validated_data['username'] = validated_data['email']
        user = User.objects.create_user(**validated_data)
        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    email = serializers.EmailField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if not email or not password:
            raise serializers.ValidationError('Email and password are required')
        
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    """Enhanced user profile serializer - now uses User model directly with field mapping"""
    user_skills = UserSkillSerializer(many=True, read_only=True)
    profile_completion = serializers.IntegerField(read_only=True)
    highest_education_display = serializers.CharField(source='get_highest_education_display', read_only=True)
    
    # Add file URL fields from attachments
    def to_representation(self, instance):
        data = super().to_representation(instance)
        
        # Add file URLs from attachments if they exist
        attachments = instance.attachments or []
        attachment_urls = {}
        
        for attachment in attachments:
            if isinstance(attachment, dict):
                doc_type = attachment.get('document_type', '').lower()
                file_url = attachment.get('file_url') or attachment.get('file')
                if file_url:
                    attachment_urls[doc_type] = file_url
        
        data['attachment_urls'] = attachment_urls
        return data

    class Meta:
        model = User
        fields = '__all__'  # Use all fields to ensure comprehensive data is returned
        read_only_fields = ['created_at', 'updated_at', 'profile_completion']
        extra_kwargs = {
            # Allow unknown fields to be ignored instead of causing validation errors
        }

    def to_internal_value(self, data):
        """Map frontend field names to backend field names"""
        # Create reverse mapping from camelCase to snake_case
        reverse_mapping = {
            'firstName': 'first_name',
            'surname': 'last_name',
            'phoneNumber': 'phone_number',
            'phone': 'phone_number',  # Frontend uses 'phone' for phone_number
            'alternativePhone': 'alternative_phone',
            'idNumber': 'national_id',
            'dateOfBirth': 'date_of_birth',
            'otherNames': 'other_names',
            'subCounty': 'sub_county',
            'postalAddress': 'postal_address',
            'postalCode': 'postal_code',
            'postCode': 'postal_code',  # Frontend may use 'postCode'
            'disabilityDetails': 'disability_details',
            'disabilityCertificateNo': 'disability_certificate_no',
            'highestQualificationDescription': 'highest_qualification_description',
            'maritalStatus': 'marital_status',
            'religion': 'religion',
            'passportNo': 'passport_no',
            'ethnicity': 'ethnicity',
            'nhifNumber': 'nhif_number',
            'nssfNumber': 'nssf_number',
            'kraPin': 'kra_pin',
            'managementExperience': 'management_experience',
            'workExperience': 'work_experience',
            'highestQualification': 'highest_qualification',
            'countyOfResidence': 'county_of_residence',
            'professionalTitle': 'professional_title',
            'yearsOfExperience': 'years_of_experience',
            'currentEmployer': 'current_employer',
            'currentPosition': 'current_position',
            'highestEducation': 'highest_education',
            'fieldOfStudy': 'field_of_study',
            'graduationYear': 'graduation_year',
            'institution': 'institution',
            'academicQualifications': 'academic_qualifications',
            'professionalQualifications': 'professional_qualifications',
            'professionalBodies': 'professional_bodies',
            'workExperiences': 'work_experiences_json',
            'work_experiences': 'work_experiences_json',  # Also accept snake_case
            'experiences': 'work_experiences_json',  # Frontend may use 'experiences'
            'referees': 'referees',
            'preferredJobTypes': 'preferred_job_types',
            'expectedSalary': 'expected_salary',
            'availableImmediately': 'available_immediately',
            'noticePeriod': 'notice_period',
            'linkedinUrl': 'linkedin_url',
            'githubUrl': 'github_url',
            'portfolioUrl': 'portfolio_url',
            'resumeFile': 'resume_file',
            'resumeText': 'resume_text',
            'declarationDate': 'declaration_date',
            'placeOfDeclaration': 'place_of_declaration',
            'attachments': 'attachments',
            'declaration1': 'declaration1',
            'declaration2': 'declaration2',
            'declaration3': 'declaration3',
            'gender': 'gender',
            'title': 'title',
            'nationality': 'nationality',
            'email': 'email',
            'county': 'county',
            'constituency': 'constituency',
            'ward': 'ward',
            'town': 'town',
            'disability': 'disability',
            'skills': 'skills',
        }

        # Convert camelCase keys to snake_case
        mapped_data = {}
        for key, value in data.items():
            if key in reverse_mapping:
                mapped_data[reverse_mapping[key]] = value
            else:
                mapped_data[key] = value

        # Filter out fields that don't exist in the model to avoid validation errors
        model_fields = {field.name for field in User._meta.get_fields()}
        filtered_data = {k: v for k, v in mapped_data.items() if k in model_fields}

        # Convert empty strings to False for boolean fields
        boolean_fields = ['disability', 'is_verified', 'is_active', 'is_staff', 'is_superuser',
                         'declaration1', 'declaration2', 'declaration3', 'available_immediately']
        for field in boolean_fields:
            if field in filtered_data and filtered_data[field] == '':
                filtered_data[field] = False

        # Convert gender display names to codes
        gender_display_map = {'Male': 'M', 'Female': 'F', 'Other': 'O'}
        if 'gender' in filtered_data and filtered_data['gender'] in gender_display_map:
            filtered_data['gender'] = gender_display_map[filtered_data['gender']]

        # Convert disability display names to boolean
        disability_display_map = {'Yes': True, 'No': False}
        if 'disability' in filtered_data and filtered_data['disability'] in disability_display_map:
            filtered_data['disability'] = disability_display_map[filtered_data['disability']]

        print(f"UserProfileSerializer to_internal_value: {filtered_data}")
        return super().to_internal_value(filtered_data)

    def to_representation(self, instance):
        """Map backend field names to frontend field names"""
        data = super().to_representation(instance)

        # Convert gender codes to display names for frontend
        gender_code_map = {'M': 'Male', 'F': 'Female', 'O': 'Other'}
        if 'gender' in data and data['gender']:
            data['gender'] = gender_code_map.get(data['gender'], data['gender'])

        # Add field name mapping for frontend compatibility
        field_mapping = {
            'first_name': 'firstName',
            'last_name': 'surname',
            'phone_number': 'phoneNumber',
            'phone_number': 'phone',  # Frontend uses 'phone' for phone_number
            'alternative_phone': 'alternativePhone',
            'national_id': 'idNumber',
            'date_of_birth': 'dateOfBirth',
            'other_names': 'otherNames',
            'sub_county': 'subCounty',
            'postal_address': 'postalAddress',
            'postal_code': 'postalCode',
            'postal_code': 'postCode',  # Frontend may use 'postCode'
            'disability_details': 'disabilityDetails',
            'disability_certificate_no': 'disabilityCertificateNo',
            'highest_qualification_description': 'highestQualificationDescription',
            'marital_status': 'maritalStatus',
            'religion': 'religion',
            'passport_no': 'passportNo',
            'ethnicity': 'ethnicity',
            'nhif_number': 'nhifNumber',
            'nssf_number': 'nssfNumber',
            'kra_pin': 'kraPin',
            'management_experience': 'managementExperience',
            'work_experience': 'workExperience',
            'highest_qualification': 'highestQualification',
            'county_of_residence': 'countyOfResidence',
            'professional_title': 'professionalTitle',
            'years_of_experience': 'yearsOfExperience',
            'current_employer': 'currentEmployer',
            'current_position': 'currentPosition',
            'highest_education': 'highestEducation',
            'field_of_study': 'fieldOfStudy',
            'graduation_year': 'graduationYear',
            'institution': 'institution',
            'academic_qualifications': 'academicQualifications',
            'professional_qualifications': 'professionalQualifications',
            'professional_bodies': 'professionalBodies',
            'work_experiences_json': 'workExperiences',
            'work_experiences_json': 'experiences',  # Frontend may use 'experiences'
            'referees': 'referees',
            'preferred_job_types': 'preferredJobTypes',
            'expected_salary': 'expectedSalary',
            'available_immediately': 'availableImmediately',
            'notice_period': 'noticePeriod',
            'linkedin_url': 'linkedinUrl',
            'github_url': 'githubUrl',
            'portfolio_url': 'portfolioUrl',
            'resume_file': 'resumeFile',
            'resume_text': 'resumeText',
            'declaration_date': 'declarationDate',
            'place_of_declaration': 'placeOfDeclaration',
            'profile_completion': 'profileCompletion',
            'attachments': 'attachments',
            'gender': 'gender',
            'title': 'title',
            'nationality': 'nationality',
            'email': 'email',
            'county': 'county',
            'constituency': 'constituency',
            'ward': 'ward',
            'town': 'town',
            'disability': 'disability',
            'skills': 'skills',
            'declaration1': 'declaration1',
            'declaration2': 'declaration2',
            'declaration3': 'declaration3',
        }

        # Create a new dict with both snake_case and camelCase keys
        mapped_data = {}
        for key, value in data.items():
            mapped_data[key] = value
            if key in field_mapping:
                mapped_data[field_mapping[key]] = value
        
        # Ensure work_experiences is available in snake_case for frontend compatibility
        if 'work_experiences_json' in mapped_data:
            mapped_data['work_experiences'] = mapped_data['work_experiences_json']
        
        # Add phone alias for frontend compatibility
        if 'phone_number' in mapped_data:
            mapped_data['phone'] = mapped_data['phone_number']

        print(f"UserProfileSerializer to_representation: JSON fields present", {
            'academic_qualifications': bool(data.get('academic_qualifications')),
            'professional_qualifications': bool(data.get('professional_qualifications')),
            'professional_bodies': bool(data.get('professional_bodies')),
            'work_experiences_json': bool(data.get('work_experiences_json')),
            'referees': bool(data.get('referees')),
            'attachments': bool(data.get('attachments')),
        })

        return mapped_data


class AdminUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    password_confirm = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'phone_number',
            'user_type', 'is_active', 'is_staff', 'is_superuser',
            'password', 'password_confirm'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'password_confirm': {'write_only': True}
        }

    def validate(self, attrs):
        if self.instance is None and not attrs.get('password'):
            raise serializers.ValidationError({'password': 'Password is required when creating a user.'})

        if attrs.get('password') and attrs.get('password') != attrs.get('password_confirm'):
            raise serializers.ValidationError({'password_confirm': "Passwords don't match"})

        if 'user_type' in attrs:
            valid_types = [choice[0] for choice in User.USER_TYPES]
            if attrs['user_type'] not in valid_types:
                raise serializers.ValidationError({'user_type': f"Invalid user_type. Must be one of: {valid_types}"})

        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm', None)
        password = validated_data.pop('password', None)
        validated_data['username'] = validated_data.get('email')
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user

    def update(self, instance, validated_data):
        validated_data.pop('password_confirm', None)
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class UserSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source='user_type', read_only=True)
    is_hr = serializers.SerializerMethodField()
    is_staff = serializers.SerializerMethodField()
    highest_education_display = serializers.CharField(source='get_highest_education_display', read_only=True)

    class Meta:
        model = User
        fields = '__all__'
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def get_is_hr(self, obj):
        return obj.user_type == 'hr'

    def get_is_staff(self, obj):
        return obj.user_type in ['hr', 'manager', 'admin']
    
    def to_representation(self, instance):
        """Map backend field names to frontend field names"""
        data = super().to_representation(instance)

        # Convert gender codes to display names for frontend
        gender_code_map = {'M': 'Male', 'F': 'Female', 'O': 'Other'}
        if 'gender' in data and data['gender']:
            data['gender'] = gender_code_map.get(data['gender'], data['gender'])

        # Add field name mapping for frontend compatibility
        field_mapping = {
            'first_name': 'firstName',
            'last_name': 'lastName',
            'phone_number': 'phoneNumber',
            'national_id': 'idNumber',
            'date_of_birth': 'dateOfBirth',
            'user_type': 'userType',
            'alternative_phone': 'alternativePhone',
            'sub_county': 'subCounty',
            'constituency': 'constituency',
            'ward': 'ward',
            'postal_address': 'postalAddress',
            'postal_code': 'postalCode',
            'postal_code': 'postCode',  # Frontend may use 'postCode'
            'town': 'town',
            'disability': 'disability',
            'disability_details': 'disabilityDetails',
            'disability_certificate_no': 'disabilityCertificateNo',
            'marital_status': 'maritalStatus',
            'religion': 'religion',
            'passport_no': 'passportNo',
            'ethnicity': 'ethnicity',
            'nhif_number': 'nhifNumber',
            'nssf_number': 'nssfNumber',
            'kra_pin': 'kraPin',
            'management_experience': 'managementExperience',
            'work_experience': 'workExperience',
            'highest_qualification': 'highestQualification',
            'county_of_residence': 'countyOfResidence',
            'professional_title': 'professionalTitle',
            'years_of_experience': 'yearsOfExperience',
            'current_employer': 'currentEmployer',
            'current_position': 'currentPosition',
            'highest_education': 'highestEducation',
            'field_of_study': 'fieldOfStudy',
            'graduation_year': 'graduationYear',
            'institution': 'institution',
            'academic_qualifications': 'academicQualifications',
            'professional_qualifications': 'professionalQualifications',
            'professional_bodies': 'professionalBodies',
            'work_experiences_json': 'workExperiences',
            'work_experiences_json': 'experiences',  # Frontend may use 'experiences'
            'referees': 'referees',
            'preferred_job_types': 'preferredJobTypes',
            'expected_salary': 'expectedSalary',
            'available_immediately': 'availableImmediately',
            'notice_period': 'noticePeriod',
            'linkedin_url': 'linkedinUrl',
            'github_url': 'githubUrl',
            'portfolio_url': 'portfolioUrl',
            'resume_file': 'resumeFile',
            'resume_text': 'resumeText',
            'declaration_date': 'declarationDate',
            'place_of_declaration': 'placeOfDeclaration',
            'gender': 'gender',
            'title': 'title',
            'nationality': 'nationality',
            'email': 'email',
            'county': 'county',
            'skills': 'skills',
            'declaration1': 'declaration1',
            'declaration2': 'declaration2',
            'declaration3': 'declaration3',
            'attachments': 'attachments',
        }

        # Create a new dict with both snake_case and camelCase keys
        mapped_data = {}
        for key, value in data.items():
            mapped_data[key] = value
            if key in field_mapping:
                mapped_data[field_mapping[key]] = value
        
        # Ensure work_experiences is available in snake_case for frontend compatibility
        if 'work_experiences_json' in mapped_data:
            mapped_data['work_experiences'] = mapped_data['work_experiences_json']
        
        # Add phone alias for frontend compatibility
        if 'phone_number' in mapped_data:
            mapped_data['phone'] = mapped_data['phone_number']

        return mapped_data


class ProfileSerializer(serializers.ModelSerializer):
    """Minimal profile serializer - Profile now only has bio and profile_picture"""

    class Meta:
        model = Profile
        fields = ['id', 'bio', 'profile_picture', 'created_at', 'updated_at']
        extra_kwargs = {
            'user': {'read_only': True}
        }
