from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from django.utils.html import format_html
from .models import Profile

User = get_user_model()

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'

# Register our custom User admin
class UserAdmin(BaseUserAdmin):
    inlines = [ProfileInline]
    """Custom admin interface for User model with full CRUD operations"""
    
    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.is_staff
    
    def has_add_permission(self, request):
        return request.user.is_superuser or request.user.is_staff
    
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.is_staff
    
    PROTECTED_USER_EMAILS = ['admin@ncpd.go.ke']

    def _is_protected_user(self, obj):
        return obj is not None and (
            obj.email in self.PROTECTED_USER_EMAILS or obj.is_superuser or obj.user_type == 'admin'
        )

    def has_delete_permission(self, request, obj=None):
        if obj is not None and self._is_protected_user(obj):
            return False
        return request.user.is_superuser or request.user.is_staff
    
    def delete_model(self, request, obj):
        if self._is_protected_user(obj):
            self.message_user(request, 'This system administrator account cannot be deleted.', messages.ERROR)
        else:
            super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        protected = queryset.filter(
            email__in=self.PROTECTED_USER_EMAILS
        ) | queryset.filter(is_superuser=True) | queryset.filter(user_type='admin')
        if protected.exists():
            self.message_user(request, 'Protected system administrator accounts cannot be deleted.', messages.ERROR)
            queryset = queryset.exclude(pk__in=protected.values_list('pk', flat=True))
        super().delete_queryset(request, queryset)

    def has_module_permission(self, request):
        return request.user.is_superuser or request.user.is_staff
    
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} user(s) successfully activated.', messages.SUCCESS)
    activate_users.short_description = 'Activate selected users'
    
    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} user(s) successfully deactivated.', messages.SUCCESS)
    deactivate_users.short_description = 'Deactivate selected users'
    
    def make_staff(self, request, queryset):
        updated = queryset.update(is_staff=True)
        self.message_user(request, f'{updated} user(s) successfully made staff.', messages.SUCCESS)
    make_staff.short_description = 'Make selected users staff'
    
    def remove_staff(self, request, queryset):
        updated = queryset.update(is_staff=False)
        self.message_user(request, f'{updated} user(s) successfully removed from staff.', messages.SUCCESS)
    remove_staff.short_description = 'Remove staff status from selected users'
    
    def make_superuser(self, request, queryset):
        updated = queryset.update(is_superuser=True, is_staff=True)
        self.message_user(request, f'{updated} user(s) successfully made superuser.', messages.SUCCESS)
    make_superuser.short_description = 'Make selected users superuser'
    
    def remove_superuser(self, request, queryset):
        updated = queryset.update(is_superuser=False)
        self.message_user(request, f'{updated} user(s) successfully removed from superuser.', messages.SUCCESS)
    remove_superuser.short_description = 'Remove superuser status from selected users'
    
    def set_user_type_applicant(self, request, queryset):
        updated = queryset.update(user_type='applicant')
        self.message_user(request, f'{updated} user(s) successfully set as applicant.', messages.SUCCESS)
    set_user_type_applicant.short_description = 'Set selected users as applicant'
    
    def set_user_type_hr(self, request, queryset):
        updated = queryset.update(user_type='hr')
        self.message_user(request, f'{updated} user(s) successfully set as HR.', messages.SUCCESS)
    set_user_type_hr.short_description = 'Set selected users as HR'
    
    def set_user_type_admin(self, request, queryset):
        updated = queryset.update(user_type='admin')
        self.message_user(request, f'{updated} user(s) successfully set as admin.', messages.SUCCESS)
    set_user_type_admin.short_description = 'Set selected users as admin'
    
    actions = [
        'activate_users',
        'deactivate_users', 
        'make_staff',
        'remove_staff',
        'make_superuser',
        'remove_superuser',
        'set_user_type_applicant',
        'set_user_type_hr',
        'set_user_type_admin',
    ]
    
    def resume_file_link(self, obj):
        if obj.resume_file:
            return format_html('<a href="{}" target="_blank">{}</a>', obj.resume_file.url, 'Download')
        return '-'
    resume_file_link.short_description = 'Resume File'

    def attachments_summary(self, obj):
        if obj.attachments:
            return f"{len(obj.attachments)} item(s)"
        return 'None'
    attachments_summary.short_description = 'Attachments'

    list_display = ['username', 'email', 'first_name', 'last_name', 'user_type', 'resume_file_link', 'attachments_summary', 'is_active', 'is_staff', 'is_superuser', 'date_joined']
    list_display_links = ['username', 'email']
    list_filter = ['user_type', 'is_active', 'is_staff', 'is_superuser', 'is_verified', 'gender', 'disability', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'national_id', 'phone_number']
    ordering = ['-date_joined']
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {
            'fields': ('first_name', 'last_name', 'email', 'title', 'phone_number', 'alternative_phone', 
                      'national_id', 'date_of_birth', 'gender', 'disability', 'disability_details')
        }),
        ('Location', {
            'fields': ('county', 'sub_county', 'constituency', 'ward', 'postal_address', 'postal_code', 
                      'town', 'city', 'country', 'address')
        }),
        ('Professional Info', {
            'fields': ('user_type', 'professional_title', 'years_of_experience', 'current_employer', 
                      'current_position', 'highest_education', 'field_of_study', 'institution', 'graduation_year')
        }),
        ('Education & Qualifications', {
            'fields': ('academic_qualifications', 'professional_qualifications', 'professional_bodies', 
                      'highest_qualification', 'highest_qualification_description')
        }),
        ('Work Experience', {
            'fields': ('work_experiences_json', 'work_experience', 'management_experience')
        }),
        ('Additional Info', {
            'fields': ('other_names', 'nationality', 'marital_status', 'religion', 'passport_no', 
                      'ethnicity', 'nhif_number', 'nssf_number', 'kra_pin', 'skills', 
                      'county_of_residence')
        }),
        ('Preferences', {
            'fields': ('preferred_job_types', 'expected_salary', 'available_immediately', 'notice_period')
        }),
        ('Social Links', {
            'fields': ('linkedin_url', 'github_url', 'portfolio_url')
        }),
        ('Files', {
            'fields': ('resume_file', 'resume_text')
        }),
        ('Referees & Attachments', {
            'fields': ('referees', 'attachments')
        }),
        ('Declaration', {
            'fields': ('declaration1', 'declaration2', 'declaration3', 'declaration_date', 'place_of_declaration')
        }),
        ('Profile', {
            'fields': ('profile_completion', 'is_verified')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined')
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'user_type', 'first_name', 'last_name', 'is_staff'),
        }),
    )
    
    readonly_fields = ['date_joined', 'last_login', 'profile_completion']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related()

# First, unregister any existing User registrations to avoid duplicates
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

# Set app_label to 'auth' so it appears under Authentication and Authorization
User._meta.app_label = 'auth'

# Register our custom User admin with proper CRUD permissions
admin.site.register(User, UserAdmin)