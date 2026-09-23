from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class VerificationRequest(models.Model):
    """Government verification requests"""
    
    VERIFICATION_TYPES = [
        ('national_id', 'National ID Verification'),
        ('academic', 'Academic Credential Verification'),
        ('integrity', 'Chapter Six Integrity Check'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verification_requests')
    verification_type = models.CharField(max_length=20, choices=VERIFICATION_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    request_data = models.JSONField(default=dict)
    response_data = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.get_verification_type_display()}"


class VerificationResult(models.Model):
    """Results of government verifications"""
    
    VERIFICATION_TYPES = [
        ('national_id', 'National ID Verification'),
        ('academic', 'Academic Credential Verification'),
        ('integrity', 'Chapter Six Integrity Check'),
    ]
    
    verification_request = models.OneToOneField(
        VerificationRequest, 
        on_delete=models.CASCADE, 
        related_name='verification_result'
    )
    verification_type = models.CharField(max_length=20, choices=VERIFICATION_TYPES)
    is_verified = models.BooleanField(default=False)
    verified_data = models.JSONField(default=dict)
    confidence_score = models.FloatField(default=0.0)
    verification_date = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.verification_request} - {'Verified' if self.is_verified else 'Not Verified'}"
