from django.db import models
from django.contrib.auth.models import AbstractUser
from django_countries.fields import CountryField
from phonenumber_field.modelfields import PhoneNumberField
import os

# Constants
SKILL_LEVELS = [
    ('beginner', 'Beginner'),
    ('intermediate', 'Intermediate'),
    ('advanced', 'Advanced'),
    ('expert', 'Expert'),
]


def user_upload_path(instance, filename):
    """Generate upload path for user files: applications/{username}/{filename}"""
    return os.path.join('applications', instance.username, filename)


class User(AbstractUser):
    """Custom user model for NCPD recruitment portal"""

    USER_TYPES = [
        ('applicant', 'Applicant'),
        ('hr', 'HR Staff'),
        ('manager', 'Department Manager'),
        ('admin', 'System Administrator'),
        ('panel_member', 'Interview Panel Member'),
    ]

    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='applicant')
    is_verified = models.BooleanField(default=False)

    # Two-Factor Authentication fields
    otp_enabled = models.BooleanField(default=True)
    otp_secret = models.CharField(max_length=255, blank=True, null=True)
    otp_verified = models.BooleanField(default=False)
    otp_backup_codes = models.JSONField(default=list, blank=True)

    # Personal Details (moved from Profile for direct access)
    title = models.CharField(max_length=20, blank=True, null=True)
    phone_number = PhoneNumberField(blank=True, null=True)
    alternative_phone = PhoneNumberField(blank=True, null=True)
    national_id = models.CharField(max_length=20, blank=True, null=True)
    county = models.CharField(max_length=100, blank=True, null=True)
    sub_county = models.CharField(max_length=100, blank=True, null=True)
    constituency = models.CharField(max_length=100, blank=True, null=True)
    ward = models.CharField(max_length=100, blank=True, null=True)
    postal_address = models.TextField(blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    town = models.CharField(max_length=100, blank=True, null=True)
    disability = models.BooleanField(default=False)
    disability_details = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(
        max_length=10,
        choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')],
        blank=True,
        null=True
    )
    # Frontend expects phone as well
    phone = phone_number  # Alias for frontend compatibility

    # Additional Personal Details
    other_names = models.CharField(max_length=200, blank=True, null=True)
    nationality = models.CharField(max_length=100, blank=True, null=True)
    disability_certificate_no = models.CharField(max_length=100, blank=True, null=True)
    highest_qualification_description = models.TextField(blank=True, null=True)
    skills = models.TextField(blank=True, null=True, help_text="Skills and competencies")
    marital_status = models.CharField(max_length=20, blank=True, null=True)
    religion = models.CharField(max_length=50, blank=True, null=True)
    passport_no = models.CharField(max_length=50, blank=True, null=True)
    ethnicity = models.CharField(max_length=50, blank=True, null=True)
    nhif_number = models.CharField(max_length=50, blank=True, null=True)
    nssf_number = models.CharField(max_length=50, blank=True, null=True)
    kra_pin = models.CharField(max_length=20, blank=True, null=True)
    management_experience = models.IntegerField(default=0)
    work_experience = models.IntegerField(default=0)
    highest_qualification = models.CharField(max_length=50, blank=True, null=True)
    county_of_residence = models.CharField(max_length=100, blank=True, null=True)

    # Professional Information
    professional_title = models.CharField(max_length=200, blank=True)
    years_of_experience = models.IntegerField(default=0)
    current_employer = models.CharField(max_length=200, blank=True)
    current_position = models.CharField(max_length=200, blank=True)

    # Education (High-level recruitment - excluding basic education)
    highest_education = models.CharField(
        max_length=50,
        choices=[
            ('diploma', 'Diploma'),
            ('bachelor', 'Bachelor Degree'),
            ('master', 'Master Degree'),
            ('phd', 'PhD'),
            ('professional_certification', 'Professional Certification'),
            ('other', 'Other'),
        ],
        blank=True,
        null=True
    )
    field_of_study = models.CharField(max_length=200, blank=True)
    institution = models.CharField(max_length=200, blank=True)
    graduation_year = models.IntegerField(blank=True, null=True)

    # Academic Qualifications (JSON field for structured data)
    academic_qualifications = models.JSONField(default=list, blank=True)

    # Professional Qualifications (JSON field for structured data)
    professional_qualifications = models.JSONField(default=list, blank=True)

    # Professional Bodies (JSON field for structured data)
    professional_bodies = models.JSONField(default=list, blank=True)

    # Work Experiences (JSON field for structured data) - stored as JSON for frontend compatibility
    work_experiences_json = models.JSONField(default=list, blank=True, db_column='work_experiences')

    # Location
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = CountryField(default='KE')

    # Preferences
    preferred_job_types = models.JSONField(default=list, blank=True)
    expected_salary = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    available_immediately = models.BooleanField(default=True)
    notice_period = models.IntegerField(default=0, help_text="Notice period in days")

    # Social Links
    linkedin_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    portfolio_url = models.URLField(blank=True)

    # Resume/CV
    resume_file = models.FileField(upload_to=user_upload_path, blank=True, null=True)
    resume_text = models.TextField(blank=True, help_text="Parsed resume content")

    # Referees (JSON field for structured data)
    referees = models.JSONField(default=list, blank=True)

    # Attachments (JSON field for structured data)
    attachments = models.JSONField(default=list, blank=True)

    # Declaration (specific fields for frontend compatibility)
    declaration1 = models.BooleanField(default=False, help_text="Information is true and correct")
    declaration2 = models.BooleanField(default=False, help_text="Consent to background checks")
    declaration3 = models.BooleanField(default=False, help_text="Consent to data processing")
    declaration_date = models.DateField(blank=True, null=True, help_text="Date of declaration")
    place_of_declaration = models.CharField(max_length=200, blank=True, null=True, help_text="Place where declaration was made")

    # Profile completion percentage (calculated and stored)
    profile_completion = models.IntegerField(default=0, help_text="Profile completion percentage (0-100)")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_user_type_display()})"
    
    @property
    def phone(self):
        """Phone alias for frontend compatibility"""
        return self.phone_number

    def calculate_profile_completion(self):
        """Calculate profile completion percentage based on filled fields"""
        completed_steps = 0
        total_steps = 8

        # Step 1: Personal Details (9 required fields - at least 7 must be filled)
        personal_fields = ['title', 'first_name', 'last_name', 'email', 'phone_number',
                          'national_id', 'date_of_birth', 'gender', 'county']
        filled_personal_fields = sum(1 for field in personal_fields if getattr(self, field))
        if filled_personal_fields >= 7:
            completed_steps += 1

        # Step 2: Academic Qualifications (required - at least one)
        if self.academic_qualifications and len(self.academic_qualifications) > 0:
            completed_steps += 1

        # Step 3: Professional Qualifications (optional - only count if filled)
        if self.professional_qualifications and len(self.professional_qualifications) > 0:
            completed_steps += 1

        # Step 4: Professional Bodies (optional - only count if filled)
        if self.professional_bodies and len(self.professional_bodies) > 0:
            completed_steps += 1

        # Step 5: Work Experience (required - at least one)
        has_experience = (self.work_experiences_json and len(self.work_experiences_json) > 0) or \
                       (self.work_experience > 0)
        if has_experience:
            completed_steps += 1

        # Step 6: Referees (required - exactly 3)
        if self.referees and len(self.referees) >= 3:
            completed_steps += 1

        # Step 7: Attachments (required - CV, National ID, KRA PIN)
        if self.attachments and len(self.attachments) >= 3:
            completed_steps += 1

        # Step 8: Declaration (required - all checkboxes)
        if (self.declaration1 and self.declaration2 and self.declaration3 and
            self.declaration_date and self.place_of_declaration):
            completed_steps += 1

        return round((completed_steps / total_steps) * 100)

    def save(self, *args, **kwargs):
        """Override save to calculate and store profile completion only if not explicitly set"""
        # Only auto-calculate if profile_completion is not explicitly provided
        # This allows manual override during cleanup operations
        if 'update_fields' in kwargs and 'profile_completion' in kwargs['update_fields']:
            # Don't recalculate if we're explicitly updating profile_completion
            super().save(*args, **kwargs)
        else:
            self.profile_completion = self.calculate_profile_completion()
            super().save(*args, **kwargs)


class Profile(models.Model):
    """Extended user profile - kept for backward compatibility but minimal"""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True, help_text="Professional bio or summary")
    profile_picture = models.ImageField(upload_to=user_upload_path, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile of {self.user.get_full_name() or self.user.username}"


class Skill(models.Model):
    """Skills model for applicants"""
    
    SKILL_LEVELS = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ]
    
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name


class UserSkill(models.Model):
    """Many-to-many relationship between users and skills"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_skills')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    level = models.CharField(max_length=20, choices=SKILL_LEVELS, default='intermediate')
    years_of_experience = models.IntegerField(default=0)
    last_used = models.DateField(blank=True, null=True)
    is_primary = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'skill']
    
    def __str__(self):
        return f"{self.user.username} - {self.skill.name} ({self.level})"


class Certification(models.Model):
    """Certifications and qualifications"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='certifications')
    name = models.CharField(max_length=200)
    issuing_organization = models.CharField(max_length=200)
    issue_date = models.DateField()
    expiry_date = models.DateField(blank=True, null=True)
    credential_id = models.CharField(max_length=100, blank=True)
    credential_url = models.URLField(blank=True)
    is_verified = models.BooleanField(default=False)
    verification_date = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.name}"


class WorkExperience(models.Model):
    """Work experience entries"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='work_experiences')
    company = models.CharField(max_length=200)
    position = models.CharField(max_length=200)
    employment_type = models.CharField(
        max_length=20,
        choices=[
            ('full_time', 'Full Time'),
            ('part_time', 'Part Time'),
            ('contract', 'Contract'),
            ('internship', 'Internship'),
            ('volunteer', 'Volunteer'),
        ],
        default='full_time'
    )
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True, help_text="Leave blank if current")
    is_current_job = models.BooleanField(default=False)
    description = models.TextField(help_text="Job responsibilities and achievements")
    achievements = models.JSONField(default=list, blank=True, help_text="List of key achievements")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.position} at {self.company}"
