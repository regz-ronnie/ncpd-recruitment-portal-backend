try:
    import numpy as np
except Exception:
    np = None
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q, Count, Avg
from apps.recruitment.models import Application, JobPost
from apps.users.models import User
from apps.ai_engine.models import BiasDetectionResult, AIModel
from types import SimpleNamespace
try:
    import openai
except Exception:
    openai = None
from django.conf import settings


class AutomatedScreeningService:
    """Automated screening and ranking service with bias detection"""
    
    def __init__(self):
        # Lazy import matching engine to avoid import-time crashes when optional deps are missing
        self.matching_engine = None
        try:
            from .matching_engine import AIMatchingEngine as _AIMatchingEngine
            try:
                self.matching_engine = _AIMatchingEngine()
            except Exception:
                self.matching_engine = None
        except Exception:
            self.matching_engine = None

        if openai is not None and getattr(settings, 'OPENAI_API_KEY', None):
            try:
                openai.api_key = settings.OPENAI_API_KEY
            except Exception:
                pass
        
        # Bias detection patterns
        self.gendered_words = {
            'masculine': ['aggressive', 'ambitious', 'analytical', 'competitive', 'dominant', 
                         'leader', 'outspoken', 'self-confident', 'strong'],
            'feminine': ['collaborative', 'committed', 'cooperative', 'dependable', 'emotional',
                        'enthusiastic', 'interpersonal', 'kind', 'loyal', 'sensitive']
        }
        
        self.demographic_indicators = ['gender', 'age', 'marital', 'race', 'ethnic', 'religion']
    
    def screen_applications(self, job_id: int, enable_anonymous_screening: bool = True) -> Dict[str, any]:
        """Comprehensive screening of all applications for a job"""
        
        job = JobPost.objects.get(id=job_id)
        applications = Application.objects.filter(job=job)
        
        screening_results = {
            'job': job,
            'total_applications': applications.count(),
            'screened_applications': 0,
            'ranked_candidates': [],
            'bias_analysis': {},
            'screening_flags': [],
            'recommendations': []
        }
        
        # Process each application
        for application in applications:
            try:
                # Calculate AI match score
                if self.matching_engine is not None:
                    match_result = self.matching_engine.calculate_match_score(application)
                else:
                    # Fallback dummy result when matching engine unavailable
                    match_result = SimpleNamespace(
                        overall_score=50.0,
                        missing_skills=[],
                        experience_match_score=50.0,
                        education_match_score=50.0,
                        __dict__={}
                    )
                
                # Perform bias detection
                bias_result = self.detect_bias(application)
                
                # Apply anonymous screening if enabled
                if enable_anonymous_screening:
                    application.is_anonymous = True
                    application.save()
                
                # Generate screening flags
                flags = self.generate_screening_flags(application, match_result)
                
                # Determine recommendation
                recommendation = self.get_screening_recommendation(match_result, bias_result, flags)
                
                # Update application with screening results
                application.ai_score = match_result.overall_score
                application.ai_analysis = {
                    'match_result': match_result.__dict__,
                    'bias_result': bias_result.__dict__ if bias_result else {},
                    'flags': flags,
                    'recommendation': recommendation
                }
                application.screening_flags = flags
                application.save()
                
                screening_results['ranked_candidates'].append({
                    'application': application,
                    'match_score': match_result.overall_score,
                    'recommendation': recommendation,
                    'flags': flags,
                    'bias_score': bias_result.bias_score if bias_result else 0
                })
                
                screening_results['screened_applications'] += 1
                
            except Exception as e:
                print(f"Error screening application {application.id}: {e}")
                screening_results['screening_flags'].append({
                    'application_id': application.id,
                    'error': str(e)
                })
        
        # Sort candidates by score
        screening_results['ranked_candidates'].sort(
            key=lambda x: x['match_score'], 
            reverse=True
        )
        
        # Generate aggregate bias analysis
        screening_results['bias_analysis'] = self.analyze_aggregate_bias(job)
        
        # Generate recommendations
        screening_results['recommendations'] = self.generate_screening_recommendations(screening_results)
        
        return screening_results
    
    def detect_bias(self, application: Application) -> Optional[BiasDetectionResult]:
        """Detect bias in application evaluation"""
        
        # Get text content for analysis
        text_content = self._get_application_text(application)
        
        if not text_content:
            return None
        
        # Check for demographic indicators
        demographic_bias = self._check_demographic_bias(text_content)
        
        # Check for gendered language
        gender_bias = self._check_gendered_language(text_content)
        
        # Check for cultural bias
        cultural_bias = self._check_cultural_bias(text_content)
        
        # Calculate overall bias score
        bias_score = self._calculate_bias_score(demographic_bias, gender_bias, cultural_bias)
        
        # Generate suggestions
        suggestions = self._generate_bias_suggestions(demographic_bias, gender_bias, cultural_bias)
        
        # Create bias detection result
        bias_result = BiasDetectionResult.objects.create(
            content_type='evaluation',
            content_id=str(application.id),
            original_text=text_content,
            bias_flags=demographic_bias + gender_bias + cultural_bias,
            bias_score=bias_score,
            bias_categories=['demographic', 'gender', 'cultural'],
            suggestions=suggestions
        )
        
        return bias_result
    
    def _get_application_text(self, application: Application) -> str:
        """Extract text content from application"""
        
        text_parts = []
        
        # Add cover letter
        if application.cover_letter:
            text_parts.append(application.cover_letter)
        
        # Add resume text if available
        if hasattr(application.applicant, 'profile') and application.applicant.profile.resume_text:
            text_parts.append(application.applicant.profile.resume_text)
        
        # Add work experience descriptions
        experiences = application.applicant.work_experiences.all()
        for exp in experiences:
            text_parts.append(f"{exp.position} at {exp.company}: {exp.description}")
        
        return ' '.join(text_parts)
    
    def _check_demographic_bias(self, text: str) -> List[str]:
        """Check for demographic indicators that could lead to bias"""
        
        flags = []
        text_lower = text.lower()
        
        # Check for age indicators
        age_patterns = [
            r'(\d+)\s*years?\s*old',
            r'over\s*(\d+)\s*years?',
            r'under\s*(\d+)\s*years?',
            r'(\d{2})\s*-\s*(\d{2})\s*years?'
        ]
        
        for pattern in age_patterns:
            import re
            if re.search(pattern, text_lower):
                flags.append('age_indicator_detected')
                break
        
        # Check for marital status
        marital_keywords = ['married', 'single', 'divorced', 'widowed', 'engaged']
        if any(keyword in text_lower for keyword in marital_keywords):
            flags.append('marital_status_detected')
        
        # Check for gender-specific pronouns
        gender_pronouns = ['he', 'she', 'him', 'her', 'his', 'hers']
        pronoun_count = sum(text_lower.count(pronoun) for pronoun in gender_pronouns)
        if pronoun_count > 5:  # Threshold for potential bias
            flags.append('gender_pronouns_excessive')
        
        # Check for religious indicators
        religious_keywords = ['christian', 'muslim', 'hindu', 'buddhist', 'church', 'mosque', 'temple']
        if any(keyword in text_lower for keyword in religious_keywords):
            flags.append('religious_affiliation_detected')
        
        return flags
    
    def _check_gendered_language(self, text: str) -> List[str]:
        """Check for gendered language in job descriptions or evaluations"""
        
        flags = []
        text_lower = text.lower()
        
        # Count masculine and feminine words
        masculine_count = sum(text_lower.count(word) for word in self.gendered_words['masculine'])
        feminine_count = sum(text_lower.count(word) for word in self.gendered_words['feminine'])
        
        # Check for imbalance
        total_gendered_words = masculine_count + feminine_count
        if total_gendered_words > 0:
            masculine_ratio = masculine_count / total_gendered_words
            feminine_ratio = feminine_count / total_gendered_words
            
            if masculine_ratio > 0.7:
                flags.append('masculine_language_dominant')
            elif feminine_ratio > 0.7:
                flags.append('feminine_language_dominant')
        
        # Check for specific biased phrases
        biased_phrases = [
            'fit in with our culture',
            'work hard play hard',
            'family atmosphere',
            'recent graduate',
            'young and dynamic'
        ]
        
        for phrase in biased_phrases:
            if phrase in text_lower:
                flags.append(f'biased_phrase: {phrase}')
        
        return flags
    
    def _check_cultural_bias(self, text: str) -> List[str]:
        """Check for cultural bias indicators"""
        
        flags = []
        text_lower = text.lower()
        
        # Check for nationality indicators
        nationality_keywords = ['kenyan', 'american', 'british', 'indian', 'chinese']
        if any(keyword in text_lower for keyword in nationality_keywords):
            flags.append('nationality_mentioned')
        
        # Check for language requirements that might be exclusionary
        if 'native speaker' in text_lower:
            flags.append('native_speaker_requirement')
        
        # Check for cultural references
        cultural_references = ['local', 'expatriate', 'expat', 'foreign']
        if any(ref in text_lower for ref in cultural_references):
            flags.append('cultural_reference_detected')
        
        return flags
    
    def _calculate_bias_score(self, demographic_flags: List, gender_flags: List, cultural_flags: List) -> float:
        """Calculate overall bias score (0 = no bias, 1 = high bias)"""
        
        total_flags = len(demographic_flags) + len(gender_flags) + len(cultural_flags)
        
        # Weight different types of bias differently
        weights = {
            'demographic': 0.4,
            'gender': 0.3,
            'cultural': 0.3
        }
        
        weighted_score = (
            len(demographic_flags) * weights['demographic'] +
            len(gender_flags) * weights['gender'] +
            len(cultural_flags) * weights['cultural']
        )
        
        # Normalize to 0-1 scale
        max_possible_score = 10  # Assumed maximum number of flags
        return min(weighted_score / max_possible_score, 1.0)
    
    def _generate_bias_suggestions(self, demographic_flags: List, gender_flags: List, cultural_flags: List) -> List[str]:
        """Generate suggestions to reduce bias"""
        
        suggestions = []
        
        if demographic_flags:
            suggestions.append("Consider implementing anonymous screening to reduce demographic bias")
            suggestions.append("Focus evaluation on skills and qualifications only")
        
        if gender_flags:
            suggestions.append("Review language for gender neutrality")
            suggestions.append("Use gender-inclusive terminology in evaluations")
        
        if cultural_flags:
            suggestions.append("Ensure cultural requirements are job-related and necessary")
            suggestions.append("Avoid language that might favor certain cultural backgrounds")
        
        return suggestions
    
    def generate_screening_flags(self, application: Application, match_result) -> List[str]:
        """Generate screening flags for applications"""
        
        flags = []
        
        # Low score warning
        if match_result.overall_score < 30:
            flags.append('very_low_match_score')
        elif match_result.overall_score < 50:
            flags.append('low_match_score')
        
        # Missing critical skills
        missing_critical = len(match_result.missing_skills)
        if missing_critical > 3:
            flags.append('missing_critical_skills')
        elif missing_critical > 0:
            flags.append('missing_some_skills')
        
        # Experience gap
        if match_result.experience_match_score < 40:
            flags.append('insufficient_experience')
        
        # Education gap
        if match_result.education_match_score < 40:
            flags.append('insufficient_education')
        
        # Incomplete application
        if not application.cover_letter:
            flags.append('missing_cover_letter')
        
        if not hasattr(application.applicant, 'profile') or not application.applicant.profile.resume_file:
            flags.append('missing_resume')
        
        # Overqualified warning
        if match_result.experience_match_score > 90 and match_result.overall_score > 85:
            flags.append('potentially_overqualified')
        
        return flags
    
    def get_screening_recommendation(self, match_result, bias_result, flags: List[str]) -> str:
        """Generate screening recommendation based on all factors"""
        
        # Base recommendation on match score
        if match_result.overall_score >= 85:
            base_recommendation = 'high_priority'
        elif match_result.overall_score >= 75:
            base_recommendation = 'interview'
        elif match_result.overall_score >= 60:
            base_recommendation = 'strong_consider'
        elif match_result.overall_score >= 40:
            base_recommendation = 'consider'
        else:
            base_recommendation = 'reject'
        
        # Adjust for critical flags
        critical_flags = ['missing_critical_skills', 'insufficient_experience', 'insufficient_education']
        if any(flag in flags for flag in critical_flags):
            if base_recommendation in ['high_priority', 'interview']:
                base_recommendation = 'strong_consider'
            elif base_recommendation == 'strong_consider':
                base_recommendation = 'consider'
        
        # Adjust for bias concerns
        if bias_result and bias_result.bias_score > 0.7:
            flags.append('high_bias_concern')
        
        return base_recommendation
    
    def analyze_aggregate_bias(self, job: JobPost) -> Dict[str, any]:
        """Analyze bias across all applications for a job"""
        
        applications = Application.objects.filter(job=job)
        
        # Get bias detection results
        bias_results = BiasDetectionResult.objects.filter(
            content_type='evaluation',
            content_id__in=[str(app.id) for app in applications]
        )
        
        analysis = {
            'total_applications': applications.count(),
            'applications_with_bias_analysis': bias_results.count(),
            'average_bias_score': 0,
            'common_bias_flags': {},
            'bias_distribution': {
                'low': 0,    # 0-0.3
                'medium': 0, # 0.3-0.7
                'high': 0    # 0.7-1.0
            },
            'recommendations': []
        }
        
        if bias_results.exists():
            bias_scores = [result.bias_score for result in bias_results]
            if np is not None:
                try:
                    analysis['average_bias_score'] = float(np.mean(bias_scores))
                except Exception:
                    analysis['average_bias_score'] = 0
            else:
                import statistics
                try:
                    analysis['average_bias_score'] = float(statistics.mean(bias_scores)) if bias_scores else 0
                except Exception:
                    analysis['average_bias_score'] = 0
            
            # Categorize bias scores
            for score in bias_scores:
                if score <= 0.3:
                    analysis['bias_distribution']['low'] += 1
                elif score <= 0.7:
                    analysis['bias_distribution']['medium'] += 1
                else:
                    analysis['bias_distribution']['high'] += 1
            
            # Find common bias flags
            all_flags = []
            for result in bias_results:
                all_flags.extend(result.bias_flags)
            
            from collections import Counter
            flag_counts = Counter(all_flags)
            analysis['common_bias_flags'] = dict(flag_counts.most_common(10))
        
        # Generate recommendations
        if analysis['average_bias_score'] > 0.5:
            analysis['recommendations'].append("Consider implementing stricter anonymous screening")
        
        if analysis['bias_distribution']['high'] > analysis['total_applications'] * 0.2:
            analysis['recommendations'].append("Review job description for biased language")
        
        return analysis
    
    def generate_screening_recommendations(self, screening_results: Dict) -> List[str]:
        """Generate overall screening recommendations"""
        
        recommendations = []
        total_apps = screening_results['total_applications']
        ranked_candidates = screening_results['ranked_candidates']
        
        if not ranked_candidates:
            return ["No candidates met minimum requirements"]
        
        # Count by recommendation
        high_priority = len([c for c in ranked_candidates if c['recommendation'] == 'high_priority'])
        interview = len([c for c in ranked_candidates if c['recommendation'] == 'interview'])
        strong_consider = len([c for c in ranked_candidates if c['recommendation'] == 'strong_consider'])
        
        # Generate recommendations based on distribution
        if high_priority >= 5:
            recommendations.append(f"Strong candidate pool with {high_priority} high-priority applicants")
            recommendations.append("Consider fast-tracking top 3 candidates")
        elif high_priority >= 2:
            recommendations.append(f"Good candidate pool with {high_priority} high-priority applicants")
        elif interview >= 10:
            recommendations.append(f"Large interview pool with {interview} qualified candidates")
            recommendations.append("Consider phone screening to narrow down")
        else:
            recommendations.append("Limited qualified candidates - consider widening search")
        
        # Bias-related recommendations
        bias_analysis = screening_results.get('bias_analysis', {})
        if bias_analysis.get('average_bias_score', 0) > 0.5:
            recommendations.append("High bias detected - implement anonymous screening")
        
        # Quality recommendations
        avg_score = np.mean([c['match_score'] for c in ranked_candidates]) if ranked_candidates else 0
        if avg_score < 50:
            recommendations.append("Low average match score - review job requirements")
        elif avg_score > 80:
            recommendations.append("High-quality applicant pool - expedite process")
        
        return recommendations
    
    def update_screening_weights(self, job_id: int, weights: Dict[str, float]) -> bool:
        """Update screening weights for specific job"""
        
        try:
            job = JobPost.objects.get(id=job_id)
            
            # Validate weights sum to 1
            total_weight = sum(weights.values())
            if abs(total_weight - 1.0) > 0.01:
                return False
            
            # Store custom weights in job metadata
            if not job.metadata:
                job.metadata = {}
            job.metadata['screening_weights'] = weights
            job.save()
            
            return True
        except:
            return False
    
    def get_screening_report(self, job_id: int) -> Dict[str, any]:
        """Generate comprehensive screening report"""
        
        job = JobPost.objects.get(id=job_id)
        applications = Application.objects.filter(job=job)
        
        report = {
            'job_info': {
                'title': job.title,
                'department': job.department,
                'total_applications': applications.count()
            },
            'screening_summary': {
                'processed_applications': applications.filter(ai_score__isnull=False).count(),
                'average_score': applications.aggregate(Avg('ai_score'))['ai_score__avg'] or 0,
                'screening_completion_rate': 0
            },
            'candidate_distribution': {
                'high_priority': 0,
                'interview': 0,
                'strong_consider': 0,
                'consider': 0,
                'reject': 0
            },
            'bias_analysis': {},
            'recommendations': [],
            'top_candidates': []
        }
        
        # Calculate screening completion rate
        if applications.exists():
            report['screening_summary']['screening_completion_rate'] = (
                report['screening_summary']['processed_applications'] / applications.count() * 100
            )
        
        # Get candidate distribution
        for app in applications:
            if app.ai_analysis and 'recommendation' in app.ai_analysis:
                rec = app.ai_analysis['recommendation']
                if rec in report['candidate_distribution']:
                    report['candidate_distribution'][rec] += 1
        
        # Get top candidates
        top_apps = applications.filter(ai_score__isnull=False).order_by('-ai_score')[:10]
        report['top_candidates'] = [
            {
                'candidate_name': app.applicant.get_full_name(),
                'score': app.ai_score,
                'recommendation': app.ai_analysis.get('recommendation', 'unknown')
            }
            for app in top_apps
        ]
        
        return report
