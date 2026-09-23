import numpy as np
from typing import Dict, List, Tuple, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from django.conf import settings
from django.utils import timezone

try:
    from sentence_transformers import SentenceTransformer
    _HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    SentenceTransformer = None
    _HAS_SENTENCE_TRANSFORMERS = False

try:
    import openai
except ImportError:
    openai = None
from apps.recruitment.models import JobPost, Application
from apps.users.models import User, UserSkill, Skill
from .models import AIModel, MatchingResult, SkillEmbedding


class AIMatchingEngine:
    """AI-powered candidate-job matching engine"""
    
    def __init__(self):
        self.sentence_model = None
        if _HAS_SENTENCE_TRANSFORMERS and SentenceTransformer is not None:
            try:
                self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
            except Exception:
                self.sentence_model = None
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        if openai is not None and getattr(settings, 'OPENAI_API_KEY', None):
            openai.api_key = settings.OPENAI_API_KEY
        
    def calculate_match_score(self, application: Application) -> MatchingResult:
        """Calculate comprehensive match score for an application"""
        
        job = application.job
        candidate = application.applicant
        
        # Initialize scores
        skill_score = self._calculate_skill_match(job, candidate)
        experience_score = self._calculate_experience_match(job, candidate)
        education_score = self._calculate_education_match(job, candidate)
        certifications_score = self._calculate_certifications_match(job, candidate)
        semantic_score = self._calculate_semantic_similarity(job, candidate)
        
        # Calculate weighted overall score
        weights = {
            'skill': 0.35,
            'experience': 0.30,
            'education': 0.20,
            'certifications': 0.10,
            'semantic': 0.05
        }
        
        overall_score = (
            skill_score * weights['skill'] +
            experience_score * weights['experience'] +
            education_score * weights['education'] +
            certifications_score * weights['certifications'] +
            semantic_score * weights['semantic']
        )
        
        # Determine recommendation
        recommendation = self._get_recommendation(overall_score)
        
        # Create matching result
        matching_result = MatchingResult.objects.create(
            application=application,
            job=job,
            candidate=candidate,
            overall_score=overall_score,
            confidence_level=self._calculate_confidence(skill_score, experience_score, education_score),
            skill_match_score=skill_score,
            experience_match_score=experience_score,
            education_match_score=education_score,
            semantic_similarity_score=semantic_score,
            matched_skills=self._get_matched_skills(job, candidate),
            missing_skills=self._get_missing_skills(job, candidate),
            additional_skills=self._get_additional_skills(job, candidate),
            matching_algorithm='hybrid_v2',
            recommendation=recommendation,
            reasoning=self._generate_reasoning(job, candidate, overall_score)
        )
        
        return matching_result
    
    def _calculate_skill_match(self, job: JobPost, candidate: User) -> float:
        """Calculate skill match score"""
        required_skills = set(job.skills_required or [])
        candidate_skills = set()
        
        # Get candidate's skills from their profile
        user_skills = UserSkill.objects.filter(user=candidate).select_related('skill')
        for user_skill in user_skills:
            candidate_skills.add(user_skill.skill.name.lower())
        
        # Also check skills from User model skills field
        if candidate.skills:
            candidate_skills.update(skill.lower() for skill in candidate.skills.split(','))
        
        # Also check parsed CV skills
        if candidate.resume_text:
            cv_skills = self._extract_skills_from_text(candidate.resume_text)
            candidate_skills.update(cv_skills)
        
        if not required_skills:
            return 50.0  # Default score if no skills specified
        
        # Calculate match percentage
        matches = len(required_skills.intersection(candidate_skills))
        total_required = len(required_skills)
        
        if total_required == 0:
            return 50.0
        
        base_score = (matches / total_required) * 100
        
        # Bonus for additional relevant skills
        additional_relevant = len(candidate_skills - required_skills)
        bonus = min(additional_relevant * 2, 20)  # Max 20 bonus points
        
        return min(base_score + bonus, 100)
    
    def _calculate_experience_match(self, job: JobPost, candidate: User) -> float:
        """Calculate experience match score"""
        candidate_experience = self._get_total_experience(candidate)
        
        # Extract required experience from job description
        required_experience = self._extract_required_experience(job.description + ' ' + job.requirements)
        
        if required_experience == 0:
            return 80.0  # Good default if no experience requirement
        
        if candidate_experience >= required_experience:
            # Bonus for exceeding requirements
            excess = candidate_experience - required_experience
            bonus = min(excess * 2, 20)
            return min(80 + bonus, 100)
        else:
            # Penalty for insufficient experience
            ratio = candidate_experience / required_experience if required_experience > 0 else 0
            return ratio * 60  # Max 60 if underqualified
    
    def _calculate_education_match(self, job: JobPost, candidate: User) -> float:
        """Calculate education match score"""
        education_levels = {
            'high_school': 1,
            'diploma': 2,
            'bachelor': 3,
            'master': 4,
            'phd': 5,
            'professional_certification': 2,
            'other': 1
        }
        
        candidate_level = 1
        if candidate.highest_education:
            candidate_level = education_levels.get(candidate.highest_education, 1)
        
        # Also check academic_qualifications JSON field
        if candidate.academic_qualifications and len(candidate.academic_qualifications) > 0:
            # Use the highest qualification from the array
            for qual in candidate.academic_qualifications:
                qual_level = education_levels.get(qual.get('level', '').lower(), 1)
                candidate_level = max(candidate_level, qual_level)
        
        # Extract required education level from job
        required_level = self._extract_required_education(job.qualifications)
        
        if candidate_level >= required_level:
            bonus = min((candidate_level - required_level) * 5, 15)
            return 85 + bonus
        else:
            return max(30, candidate_level * 20)
    
    def _calculate_certifications_match(self, job: JobPost, candidate: User) -> float:
        """Calculate certifications match score"""
        required_certs = set()
        # Extract required certifications from job description
        job_text = f"{job.description} {job.requirements} {job.qualifications}".lower()
        
        # Common certification keywords
        cert_keywords = [
            'certified', 'certificate', 'certification', 'cisco', 'ccna', 'ccnp',
            'pmp', 'aws', 'azure', 'comptia', 'microsoft', 'google',
            'professional', 'license', 'accredited', 'qualified'
        ]
        
        for keyword in cert_keywords:
            if keyword in job_text:
                required_certs.add(keyword)
        
        candidate_certs = set()
        
        # Check professional_qualifications JSON field
        if candidate.professional_qualifications:
            for qual in candidate.professional_qualifications:
                cert_name = qual.get('name', '').lower()
                candidate_certs.add(cert_name)
                # Also extract keywords from the name
                for keyword in cert_keywords:
                    if keyword in cert_name:
                        candidate_certs.add(keyword)
        
        # Check professional_bodies JSON field
        if candidate.professional_bodies:
            for body in candidate.professional_bodies:
                body_name = body.get('name', '').lower()
                candidate_certs.add(body_name)
        
        if not required_certs:
            return 70.0  # Good default if no specific certifications required
        
        # Calculate match percentage
        matches = len(required_certs.intersection(candidate_certs))
        total_required = len(required_certs)
        
        if total_required == 0:
            return 70.0
        
        base_score = (matches / total_required) * 100
        
        # Bonus for having additional relevant certifications
        additional_relevant = len(candidate_certs - required_certs)
        bonus = min(additional_relevant * 5, 30)  # Max 30 bonus points
        
        return min(base_score + bonus, 100)
    
    def _calculate_semantic_similarity(self, job: JobPost, candidate: User) -> float:
        """Calculate semantic similarity between job description and candidate profile"""
        job_text = f"{job.title} {job.description} {job.requirements} {job.qualifications}"
        
        candidate_text = candidate.resume_text or ""
        
        # Add work experience descriptions from JSON field
        if candidate.work_experiences_json:
            for exp in candidate.work_experiences_json:
                candidate_text += f" {exp.get('description', '')} {exp.get('position', '')} {exp.get('company', '')}"
        
        # Add professional qualifications
        if candidate.professional_qualifications:
            for qual in candidate.professional_qualifications:
                candidate_text += f" {qual.get('name', '')} {qual.get('description', '')}"
        
        if not candidate_text:
            return 50.0  # Default score
        
        # Use sentence transformers for semantic similarity when available
        if self.sentence_model is not None:
            try:
                job_embedding = self.sentence_model.encode(job_text)
                candidate_embedding = self.sentence_model.encode(candidate_text)
                similarity = cosine_similarity([job_embedding], [candidate_embedding])[0][0]
                return float(similarity * 100)
            except Exception:
                pass

        # Fallback to TF-IDF similarity if transformer is unavailable or fails
        try:
            documents = [job_text, candidate_text]
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(documents)
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return float(similarity * 100)
        except Exception:
            return 50.0
    
    def _get_total_experience(self, candidate: User) -> float:
        """Calculate total years of experience"""
        total_months = 0
        
        # Use work_experiences_json from User model
        if candidate.work_experiences_json:
            for exp in candidate.work_experiences_json:
                try:
                    from datetime import datetime
                    start_date = datetime.strptime(exp.get('start_date', ''), '%Y-%m-%d').date()
                    end_date_str = exp.get('end_date', '')
                    
                    if exp.get('is_current_job', False) or not end_date_str:
                        end_date = timezone.now().date()
                    else:
                        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                    
                    months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
                    total_months += max(0, months)
                except Exception:
                    continue
        
        # Also use the work_experience field as fallback
        if total_months == 0 and candidate.work_experience:
            total_months = candidate.work_experience * 12
        
        return total_months / 12  # Convert to years
    
    def _extract_required_experience(self, text: str) -> int:
        """Extract required years of experience from text"""
        import re
        
        patterns = [
            r'(\d+)\+?\s*years?\s*(?:of\s*)?experience',
            r'experience\s*:?\s*(\d+)\+?\s*years?',
            r'minimum\s*(\d+)\s*years?',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return int(match.group(1))
        
        return 0
    
    def _extract_required_education(self, text: str) -> int:
        """Extract required education level from text"""
        education_keywords = {
            'phd': 5,
            'doctorate': 5,
            'master': 4,
            'm.sc': 4,
            'm.s': 4,
            'mba': 4,
            'bachelor': 3,
            'b.sc': 3,
            'b.s': 3,
            'degree': 3,
            'diploma': 2,
            'certificate': 1,
            'high school': 1
        }
        
        text_lower = text.lower()
        max_level = 1
        
        for keyword, level in education_keywords.items():
            if keyword in text_lower:
                max_level = max(max_level, level)
        
        return max_level
    
    def _extract_skills_from_text(self, text: str) -> set:
        """Extract skills from text using NLP"""
        # This would use a more sophisticated NLP model in production
        common_skills = {
            'python', 'java', 'javascript', 'react', 'node.js', 'sql', 'mongodb',
            'aws', 'azure', 'docker', 'kubernetes', 'git', 'linux', 'windows',
            'excel', 'powerpoint', 'word', 'communication', 'leadership',
            'project management', 'data analysis', 'machine learning', 'ai',
            'web development', 'mobile development', 'devops', 'testing'
        }
        
        text_lower = text.lower()
        found_skills = set()
        
        for skill in common_skills:
            if skill in text_lower:
                found_skills.add(skill)
        
        return found_skills
    
    def _get_matched_skills(self, job: JobPost, candidate: User) -> List[str]:
        """Get list of matched skills"""
        required_skills = set(job.skills_required or [])
        candidate_skills = set()
        
        user_skills = UserSkill.objects.filter(user=candidate).select_related('skill')
        for user_skill in user_skills:
            candidate_skills.add(user_skill.skill.name)
        
        return list(required_skills.intersection(candidate_skills))
    
    def _get_missing_skills(self, job: JobPost, candidate: User) -> List[str]:
        """Get list of missing required skills"""
        required_skills = set(job.skills_required or [])
        candidate_skills = set()
        
        user_skills = UserSkill.objects.filter(user=candidate).select_related('skill')
        for user_skill in user_skills:
            candidate_skills.add(user_skill.skill.name)
        
        return list(required_skills - candidate_skills)
    
    def _get_additional_skills(self, job: JobPost, candidate: User) -> List[str]:
        """Get list of additional skills candidate has"""
        required_skills = set(job.skills_required or [])
        candidate_skills = set()
        
        user_skills = UserSkill.objects.filter(user=candidate).select_related('skill')
        for user_skill in user_skills:
            candidate_skills.add(user_skill.skill.name)
        
        return list(candidate_skills - required_skills)
    
    def _get_recommendation(self, score: float) -> str:
        """Get recommendation based on score"""
        if score >= 85:
            return 'high_priority'
        elif score >= 75:
            return 'interview'
        elif score >= 60:
            return 'strong_consider'
        elif score >= 40:
            return 'consider'
        else:
            return 'reject'
    
    def _calculate_confidence(self, skill_score: float, experience_score: float, education_score: float) -> float:
        """Calculate confidence level in the matching"""
        scores = [skill_score, experience_score, education_score]
        variance = np.var(scores)
        
        # Lower variance = higher confidence
        confidence = max(0.5, 1.0 - (variance / 100))
        return float(confidence)
    
    def _generate_reasoning(self, job: JobPost, candidate: User, score: float) -> str:
        """Generate human-readable reasoning for the match score"""
        reasons = []
        
        skill_score = self._calculate_skill_match(job, candidate)
        if skill_score >= 80:
            reasons.append("Strong skill alignment with job requirements")
        elif skill_score >= 60:
            reasons.append("Good skill match with some gaps")
        else:
            reasons.append("Significant skill gaps identified")
        
        experience_score = self._calculate_experience_match(job, candidate)
        if experience_score >= 80:
            reasons.append("Experience exceeds requirements")
        elif experience_score >= 60:
            reasons.append("Experience meets requirements")
        else:
            reasons.append("Experience below requirements")
        
        education_score = self._calculate_education_match(job, candidate)
        if education_score >= 80:
            reasons.append("Education level exceeds requirements")
        elif education_score >= 60:
            reasons.append("Education meets requirements")
        
        return "; ".join(reasons)
    
    def batch_process_applications(self, job_id: int) -> List[MatchingResult]:
        """Process all applications for a job"""
        job = JobPost.objects.get(id=job_id)
        applications = Application.objects.filter(job=job)
        
        results = []
        for application in applications:
            try:
                result = self.calculate_match_score(application)
                results.append(result)
            except Exception as e:
                print(f"Error processing application {application.id}: {e}")
        
        return results
    
    def get_top_candidates(self, job_id: int, limit: int = 50) -> List[MatchingResult]:
        """Get top candidates for a job"""
        results = self.batch_process_applications(job_id)
        
        # Sort by overall score and confidence
        sorted_results = sorted(
            results,
            key=lambda x: (x.overall_score, x.confidence_level),
            reverse=True
        )
        
        return sorted_results[:limit]
