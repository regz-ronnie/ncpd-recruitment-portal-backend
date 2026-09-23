import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from django.conf import settings
from django.utils import timezone
from apps.users.models import User, Certification
from apps.recruitment.models import Application
from .models import VerificationRequest, VerificationResult


class GovernmentIntegrationService:
    """Service for integrating with Kenyan government APIs"""
    
    def __init__(self):
        self.id_api_url = settings.GOVERNMENT_ID_API_URL
        self.knqa_api_url = settings.KNQA_API_URL
        self.api_key = settings.GOVERNMENT_API_KEY
        
        # Request timeout settings
        self.timeout = 30
        
    def verify_national_id(self, national_id: str, user: User) -> Dict[str, Any]:
        """Verify national ID with government system"""
        
        try:
            # Create verification request
            verification_request = VerificationRequest.objects.create(
                user=user,
                verification_type='national_id',
                request_data={'national_id': national_id},
                status='pending'
            )
            
            # Prepare API request
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'national_id': national_id,
                'request_reason': 'employment_verification',
                'requester': 'NCPD Recruitment Portal'
            }
            
            # Make API call
            response = requests.post(
                f"{self.id_api_url}/verify",
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result_data = response.json()
                
                # Process verification result
                verification_result = self._process_id_verification_result(result_data, user)
                
                # Update verification request
                verification_request.status = 'completed'
                verification_request.response_data = result_data
                verification_request.verification_result = verification_result
                verification_request.completed_at = timezone.now()
                verification_request.save()
                
                return {
                    'success': True,
                    'verified': verification_result.is_verified,
                    'data': verification_result.verified_data,
                    'verification_id': verification_request.id
                }
            else:
                # Handle API error
                verification_request.status = 'failed'
                verification_request.error_message = f"API Error: {response.status_code}"
                verification_request.save()
                
                return {
                    'success': False,
                    'error': f"Government API error: {response.status_code}",
                    'verification_id': verification_request.id
                }
                
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'Verification request timed out. Please try again later.'
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'Network error: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Verification failed: {str(e)}'
            }
    
    def verify_academic_credentials(self, certification: Certification) -> Dict[str, Any]:
        """Verify academic credentials with KNQA"""
        
        try:
            # Create verification request
            verification_request = VerificationRequest.objects.create(
                user=certification.user,
                verification_type='academic',
                request_data={
                    'institution': certification.issuing_organization,
                    'credential_name': certification.name,
                    'credential_id': certification.credential_id,
                    'issue_date': certification.issue_date.isoformat()
                },
                status='pending'
            )
            
            # Prepare API request
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'institution': certification.issuing_organization,
                'qualification': certification.name,
                'certificate_number': certification.credential_id,
                'issue_date': certification.issue_date.isoformat(),
                'verification_type': 'academic'
            }
            
            # Make API call
            response = requests.post(
                f"{self.knqa_api_url}/verify",
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result_data = response.json()
                
                # Process verification result
                verification_result = self._process_academic_verification_result(result_data, certification)
                
                # Update verification request
                verification_request.status = 'completed'
                verification_request.response_data = result_data
                verification_request.verification_result = verification_result
                verification_request.completed_at = timezone.now()
                verification_request.save()
                
                # Update certification
                certification.is_verified = verification_result.is_verified
                certification.verification_date = timezone.now()
                certification.save()
                
                return {
                    'success': True,
                    'verified': verification_result.is_verified,
                    'data': verification_result.verified_data,
                    'verification_id': verification_request.id
                }
            else:
                # Handle API error
                verification_request.status = 'failed'
                verification_request.error_message = f"KNQA API Error: {response.status_code}"
                verification_request.save()
                
                return {
                    'success': False,
                    'error': f"KNQA API error: {response.status_code}",
                    'verification_id': verification_request.id
                }
                
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'Academic verification request timed out. Please try again later.'
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'Network error: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Academic verification failed: {str(e)}'
            }
    
    def check_chapter_six_compliance(self, user: User) -> Dict[str, Any]:
        """Check Chapter Six integrity compliance"""
        
        try:
            # Create verification request
            verification_request = VerificationRequest.objects.create(
                user=user,
                verification_type='integrity',
                request_data={'national_id': user.national_id},
                status='pending'
            )
            
            # Prepare API request
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'national_id': user.national_id,
                'full_name': user.get_full_name(),
                'check_types': [
                    'dci_clearance',  # Directorate of Criminal Investigations
                    'eacc_clearance',  # Ethics and Anti-Corruption Commission
                    'crb_clearance'     # Credit Reference Bureau
                ]
            }
            
            # Make API call
            response = requests.post(
                f"{self.id_api_url}/chapter-six-check",
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result_data = response.json()
                
                # Process verification result
                verification_result = self._process_integrity_verification_result(result_data, user)
                
                # Update verification request
                verification_request.status = 'completed'
                verification_request.response_data = result_data
                verification_request.verification_result = verification_result
                verification_request.completed_at = timezone.now()
                verification_request.save()
                
                return {
                    'success': True,
                    'compliant': verification_result.is_verified,
                    'data': verification_result.verified_data,
                    'verification_id': verification_request.id
                }
            else:
                # Handle API error
                verification_request.status = 'failed'
                verification_request.error_message = f"Chapter Six API Error: {response.status_code}"
                verification_request.save()
                
                return {
                    'success': False,
                    'error': f"Chapter Six API error: {response.status_code}",
                    'verification_id': verification_request.id
                }
                
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'Integrity check request timed out. Please try again later.'
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'Network error: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Integrity check failed: {str(e)}'
            }
    
    def _process_id_verification_result(self, result_data: Dict, user: User) -> VerificationResult:
        """Process national ID verification result"""
        
        is_verified = result_data.get('status') == 'verified'
        verified_data = {}
        
        if is_verified:
            verified_data = {
                'full_name': result_data.get('full_name'),
                'date_of_birth': result_data.get('date_of_birth'),
                'gender': result_data.get('gender'),
                'county': result_data.get('county'),
                'constituency': result_data.get('constituency'),
                'issue_date': result_data.get('issue_date'),
                'expiry_date': result_data.get('expiry_date')
            }
            
            # Update user profile with verified information
            if hasattr(user, 'profile'):
                profile = user.profile
                profile.county = result_data.get('county', profile.county)
                profile.save()
        
        return VerificationResult.objects.create(
            verification_type='national_id',
            is_verified=is_verified,
            verified_data=verified_data,
            confidence_score=result_data.get('confidence_score', 0.95),
            verification_date=timezone.now()
        )
    
    def _process_academic_verification_result(self, result_data: Dict, certification: Certification) -> VerificationResult:
        """Process academic verification result"""
        
        is_verified = result_data.get('status') == 'verified'
        verified_data = {}
        
        if is_verified:
            verified_data = {
                'institution_name': result_data.get('institution_name'),
                'qualification_name': result_data.get('qualification_name'),
                'qualification_level': result_data.get('qualification_level'),
                'graduation_date': result_data.get('graduation_date'),
                'certificate_number': result_data.get('certificate_number'),
                'verification_code': result_data.get('verification_code')
            }
        
        return VerificationResult.objects.create(
            verification_type='academic',
            is_verified=is_verified,
            verified_data=verified_data,
            confidence_score=result_data.get('confidence_score', 0.90),
            verification_date=timezone.now()
        )
    
    def _process_integrity_verification_result(self, result_data: Dict, user: User) -> VerificationResult:
        """Process Chapter Six integrity verification result"""
        
        # Check if all clearances are valid
        dci_status = result_data.get('dci_clearance', {}).get('status', 'unknown')
        eacc_status = result_data.get('eacc_clearance', {}).get('status', 'unknown')
        crb_status = result_data.get('crb_clearance', {}).get('status', 'unknown')
        
        is_compliant = (
            dci_status == 'clear' and
            eacc_status == 'clear' and
            crb_status == 'clear'
        )
        
        verified_data = {
            'dci_clearance': {
                'status': dci_status,
                'reference_number': result_data.get('dci_clearance', {}).get('reference_number'),
                'issue_date': result_data.get('dci_clearance', {}).get('issue_date'),
                'expiry_date': result_data.get('dci_clearance', {}).get('expiry_date')
            },
            'eacc_clearance': {
                'status': eacc_status,
                'reference_number': result_data.get('eacc_clearance', {}).get('reference_number'),
                'issue_date': result_data.get('eacc_clearance', {}).get('issue_date'),
                'expiry_date': result_data.get('eacc_clearance', {}).get('expiry_date')
            },
            'crb_clearance': {
                'status': crb_status,
                'reference_number': result_data.get('crb_clearance', {}).get('reference_number'),
                'issue_date': result_data.get('crb_clearance', {}).get('issue_date'),
                'credit_score': result_data.get('crb_clearance', {}).get('credit_score')
            }
        }
        
        return VerificationResult.objects.create(
            verification_type='integrity',
            is_verified=is_compliant,
            verified_data=verified_data,
            confidence_score=result_data.get('confidence_score', 0.95),
            verification_date=timezone.now()
        )
    
    def get_verification_status(self, verification_id: int) -> Dict[str, Any]:
        """Get status of a verification request"""
        
        try:
            verification_request = VerificationRequest.objects.get(id=verification_id)
            
            return {
                'verification_id': verification_id,
                'status': verification_request.status,
                'verification_type': verification_request.verification_type,
                'created_at': verification_request.created_at,
                'completed_at': verification_request.completed_at,
                'is_verified': verification_request.verification_result.is_verified if verification_request.verification_result else None,
                'error_message': verification_request.error_message
            }
            
        except VerificationRequest.DoesNotExist:
            return {
                'error': 'Verification request not found'
            }
    
    def batch_verify_applications(self, application_ids: List[int]) -> Dict[str, Any]:
        """Batch verify multiple applications"""
        
        results = {
            'total': len(application_ids),
            'successful': 0,
            'failed': 0,
            'details': []
        }
        
        for app_id in application_ids:
            try:
                application = Application.objects.get(id=app_id)
                user = application.applicant
                
                # Verify national ID
                id_result = self.verify_national_id(user.national_id, user)
                
                # Verify academic credentials
                academic_results = []
                for certification in user.certifications.all():
                    academic_result = self.verify_academic_credentials(certification)
                    academic_results.append(academic_result)
                
                # Check Chapter Six compliance
                integrity_result = self.check_chapter_six_compliance(user)
                
                results['details'].append({
                    'application_id': app_id,
                    'id_verification': id_result,
                    'academic_verifications': academic_results,
                    'integrity_check': integrity_result
                })
                
                if (id_result.get('success', False) and 
                    all(ar.get('success', False) for ar in academic_results) and
                    integrity_result.get('success', False)):
                    results['successful'] += 1
                else:
                    results['failed'] += 1
                    
            except Exception as e:
                results['failed'] += 1
                results['details'].append({
                    'application_id': app_id,
                    'error': str(e)
                })
        
        return results
    
    def generate_verification_report(self, user: User) -> Dict[str, Any]:
        """Generate comprehensive verification report for a user"""
        
        # Get all verification requests for the user
        verification_requests = VerificationRequest.objects.filter(user=user)
        
        report = {
            'user': {
                'id': user.id,
                'name': user.get_full_name(),
                'national_id': user.national_id
            },
            'verifications': {
                'national_id': None,
                'academic': [],
                'integrity': None
            },
            'overall_status': 'pending',
            'generated_at': timezone.now().isoformat()
        }
        
        completed_count = 0
        total_required = 3  # ID, at least one academic, integrity
        
        for request in verification_requests:
            if request.status == 'completed' and request.verification_result:
                completed_count += 1
                
                if request.verification_type == 'national_id':
                    report['verifications']['national_id'] = {
                        'status': 'verified' if request.verification_result.is_verified else 'failed',
                        'verified_at': request.completed_at.isoformat(),
                        'data': request.verification_result.verified_data
                    }
                elif request.verification_type == 'academic':
                    report['verifications']['academic'].append({
                        'status': 'verified' if request.verification_result.is_verified else 'failed',
                        'verified_at': request.completed_at.isoformat(),
                        'data': request.verification_result.verified_data
                    })
                elif request.verification_type == 'integrity':
                    report['verifications']['integrity'] = {
                        'status': 'compliant' if request.verification_result.is_verified else 'non_compliant',
                        'verified_at': request.completed_at.isoformat(),
                        'data': request.verification_result.verified_data
                    }
        
        # Determine overall status
        if completed_count == total_required:
            all_verified = (
                report['verifications']['national_id'] and 
                report['verifications']['national_id']['status'] == 'verified' and
                len(report['verifications']['academic']) > 0 and
                all(acad['status'] == 'verified' for acad in report['verifications']['academic']) and
                report['verifications']['integrity'] and
                report['verifications']['integrity']['status'] == 'compliant'
            )
            report['overall_status'] = 'verified' if all_verified else 'issues_found'
        elif completed_count > 0:
            report['overall_status'] = 'partial'
        
        return report
    
    def schedule_recurring_verifications(self):
        """Schedule recurring verifications for critical positions"""
        
        # Get applications for positions requiring verification
        from apps.recruitment.models import JobPost
        critical_positions = JobPost.objects.filter(
            auto_screening=True,
            status='published'
        )
        
        for job in critical_positions:
            applications = Application.objects.filter(
                job=job,
                status__in=['shortlisted', 'interview_scheduled']
            )
            
            for application in applications:
                user = application.applicant
                
                # Check if verifications are recent (within 30 days)
                recent_verifications = VerificationRequest.objects.filter(
                    user=user,
                    completed_at__gte=timezone.now() - timedelta(days=30)
                )
                
                if not recent_verifications.exists():
                    # Trigger new verification
                    self.verify_national_id(user.national_id, user)
                    self.check_chapter_six_compliance(user)
