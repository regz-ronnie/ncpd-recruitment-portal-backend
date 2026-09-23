import re
import spacy
from typing import Dict, List, Any
from django.core.files.uploadedfile import UploadedFile
from PyPDF2 import PdfReader
import docx
from django.conf import settings
import openai
from .models import CVParsingResult, AIModel


class CVParser:
    """AI-powered CV parsing service"""
    
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        openai.api_key = settings.OPENAI_API_KEY
        
        # Common patterns for extraction
        self.email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        self.phone_pattern = r'(\+254|\+254-|0|07)\d{9}'
        self.date_pattern = r'\b(0[1-9]|[12][0-9]|3[01])[-/](0[1-9]|1[0-2])[-/](19|20)\d{2}\b'
        
    def parse_cv(self, file: UploadedFile, user_id: int) -> CVParsingResult:
        """Parse CV file and extract structured information"""
        
        # Extract text from file
        text_content = self._extract_text_from_file(file)
        
        # Use AI for structured extraction
        structured_data = self._extract_structured_data(text_content)
        
        # Extract specific sections
        contact_info = self._extract_contact_info(text_content)
        education = self._extract_education(text_content)
        experience = self._extract_experience(text_content)
        skills = self._extract_skills(text_content)
        certifications = self._extract_certifications(text_content)
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(structured_data)
        
        # Create parsing result
        parsing_result = CVParsingResult.objects.create(
            user_id=user_id,
            original_file=file,
            parsed_text=text_content,
            structured_data=structured_data,
            contact_info=contact_info,
            education=education,
            experience=experience,
            skills=skills,
            certifications=certifications,
            confidence_score=confidence_score
        )
        
        return parsing_result
    
    def _extract_text_from_file(self, file: UploadedFile) -> str:
        """Extract text from uploaded file"""
        
        if file.name.endswith('.pdf'):
            return self._extract_from_pdf(file)
        elif file.name.endswith('.docx'):
            return self._extract_from_docx(file)
        elif file.name.endswith('.txt'):
            return file.read().decode('utf-8')
        else:
            raise ValueError("Unsupported file format")
    
    def _extract_from_pdf(self, file: UploadedFile) -> str:
        """Extract text from PDF file"""
        reader = PdfReader(file)
        text = ""
        
        for page in reader.pages:
            text += page.extract_text() + "\n"
        
        return text
    
    def _extract_from_docx(self, file: UploadedFile) -> str:
        """Extract text from DOCX file"""
        doc = docx.Document(file)
        text = ""
        
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        
        return text
    
    def _extract_structured_data(self, text: str) -> Dict[str, Any]:
        """Use AI to extract structured data from CV text"""
        
        prompt = f"""
        Extract the following information from this CV text and return as JSON:
        
        CV Text:
        {text[:4000]}  # Limit to first 4000 chars to avoid token limits
        
        Extract:
        1. Personal Information (name, email, phone, location)
        2. Professional Summary (title, years experience, current position)
        3. Education (degree, institution, graduation year)
        4. Work Experience (company, position, dates, description)
        5. Skills (technical and soft skills)
        6. Certifications (name, issuing organization, date)
        
        Return only valid JSON format.
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a CV parsing assistant. Extract structured information and return as valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            content = response.choices[0].message.content.strip()
            
            # Clean up the response to get pure JSON
            if content.startswith('```json'):
                content = content[7:]
            if content.endswith('```'):
                content = content[:-3]
            
            import json
            return json.loads(content)
            
        except Exception as e:
            print(f"AI parsing failed: {e}")
            return self._fallback_extraction(text)
    
    def _fallback_extraction(self, text: str) -> Dict[str, Any]:
        """Fallback rule-based extraction"""
        
        return {
            "personal_info": self._extract_contact_info(text),
            "professional_summary": self._extract_professional_summary(text),
            "education": self._extract_education(text),
            "work_experience": self._extract_experience(text),
            "skills": self._extract_skills(text),
            "certifications": self._extract_certifications(text)
        }
    
    def _extract_contact_info(self, text: str) -> Dict[str, str]:
        """Extract contact information"""
        
        # Extract email
        emails = re.findall(self.email_pattern, text)
        email = emails[0] if emails else ""
        
        # Extract phone
        phones = re.findall(self.phone_pattern, text)
        phone = phones[0] if phones else ""
        
        # Extract name (simplified - usually first line)
        lines = text.split('\n')
        name = lines[0].strip() if lines else ""
        
        # Extract location (Kenyan counties and cities)
        kenyan_locations = ['Nairobi', 'Mombasa', 'Kisumu', 'Nakuru', 'Eldoret', 'Thika', 
                           'Kitale', 'Garissa', 'Kakamega', 'Kisii', 'Machakos', 'Meru']
        
        location = ""
        for loc in kenyan_locations:
            if loc.lower() in text.lower():
                location = loc
                break
        
        return {
            "name": name,
            "email": email,
            "phone": phone,
            "location": location
        }
    
    def _extract_professional_summary(self, text: str) -> Dict[str, str]:
        """Extract professional summary"""
        
        # Look for patterns like "Software Engineer with 5+ years experience"
        experience_pattern = r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp)'
        experience_match = re.search(experience_pattern, text, re.IGNORECASE)
        years_experience = experience_match.group(1) if experience_match else "0"
        
        # Extract current position (simplified)
        current_position = ""
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if 'present' in line.lower() or 'current' in line.lower():
                if i > 0:
                    current_position = lines[i-1].strip()
                break
        
        return {
            "years_experience": years_experience,
            "current_position": current_position
        }
    
    def _extract_education(self, text: str) -> List[Dict[str, str]]:
        """Extract education information"""
        
        education_entries = []
        
        # Look for education keywords
        education_keywords = ['university', 'college', 'institute', 'school', 'degree', 
                            'bachelor', 'master', 'phd', 'diploma', 'certificate']
        
        lines = text.split('\n')
        current_education = {}
        
        for line in lines:
            line_lower = line.lower().strip()
            
            # Check if this line contains education info
            if any(keyword in line_lower for keyword in education_keywords):
                if current_education:
                    education_entries.append(current_education)
                
                current_education = {
                    "institution": line.strip(),
                    "degree": "",
                    "graduation_year": ""
                }
            
            # Extract graduation year
            year_match = re.search(r'\b(19|20)\d{2}\b', line)
            if year_match and current_education:
                current_education["graduation_year"] = year_match.group(0)
        
        # Add the last education entry
        if current_education:
            education_entries.append(current_education)
        
        return education_entries
    
    def _extract_experience(self, text: str) -> List[Dict[str, str]]:
        """Extract work experience"""
        
        experience_entries = []
        
        # Look for experience patterns
        lines = text.split('\n')
        current_experience = {}
        
        for line in lines:
            # Look for date patterns (experience entries usually have dates)
            date_match = re.search(self.date_pattern, line)
            if date_match:
                if current_experience:
                    experience_entries.append(current_experience)
                
                current_experience = {
                    "company": "",
                    "position": "",
                    "dates": line.strip(),
                    "description": ""
                }
            elif current_experience and "description" not in current_experience:
                # This might be the position or company
                if not current_experience["position"]:
                    current_experience["position"] = line.strip()
                elif not current_experience["company"]:
                    current_experience["company"] = line.strip()
        
        # Add the last experience entry
        if current_experience:
            experience_entries.append(current_experience)
        
        return experience_entries
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extract skills from text"""
        
        # Technical skills list
        technical_skills = [
            'python', 'java', 'javascript', 'react', 'angular', 'vue', 'node.js',
            'django', 'flask', 'spring', 'dotnet', 'php', 'ruby', 'swift', 'kotlin',
            'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'git',
            'linux', 'windows', 'macos', 'ubuntu', 'centos', 'debian',
            'html', 'css', 'sass', 'bootstrap', 'tailwind', 'material-ui',
            'tensorflow', 'pytorch', 'keras', 'scikit-learn', 'pandas', 'numpy',
            'excel', 'powerpoint', 'word', 'outlook', 'teams', 'slack'
        ]
        
        # Soft skills
        soft_skills = [
            'leadership', 'communication', 'teamwork', 'problem solving', 'critical thinking',
            'project management', 'time management', 'adaptability', 'creativity', 'collaboration',
            'analytical skills', 'attention to detail', 'multitasking', 'decision making'
        ]
        
        all_skills = technical_skills + soft_skills
        text_lower = text.lower()
        
        found_skills = []
        for skill in all_skills:
            if skill in text_lower:
                found_skills.append(skill.title())
        
        return found_skills
    
    def _extract_certifications(self, text: str) -> List[Dict[str, str]]:
        """Extract certifications"""
        
        certifications = []
        
        # Common certification patterns
        cert_patterns = [
            r'(AWS|Azure|GCP)\s+(Certified|Professional|Associate|Specialist)',
            r'(PMP|PRINCE2|ITIL|CISSP|CISA|CISM)\s+Certified?',
            r'Certified\s+(ScrumMaster|Product Owner|Developer)',
            r'(Google|Facebook|Microsoft)\s+Certified',
        ]
        
        for pattern in cert_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    cert_name = ' '.join(match)
                else:
                    cert_name = match
                
                certifications.append({
                    "name": cert_name,
                    "issuing_organization": "",
                    "date": ""
                })
        
        return certifications
    
    def _calculate_confidence_score(self, structured_data: Dict[str, Any]) -> float:
        """Calculate confidence score for the parsing result"""
        
        score = 0.0
        max_score = 100.0
        
        # Check for required fields
        if structured_data.get("personal_info", {}).get("email"):
            score += 20
        if structured_data.get("personal_info", {}).get("phone"):
            score += 15
        if structured_data.get("personal_info", {}).get("name"):
            score += 15
        
        if structured_data.get("education"):
            score += 15
        if structured_data.get("work_experience"):
            score += 20
        if structured_data.get("skills"):
            score += 10
        if structured_data.get("certifications"):
            score += 5
        
        return min(score, max_score)
    
    def validate_parsed_data(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean parsed data"""
        
        validation_results = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "cleaned_data": parsed_data.copy()
        }
        
        # Validate email
        email = parsed_data.get("personal_info", {}).get("email", "")
        if email and not re.match(self.email_pattern, email):
            validation_results["errors"].append("Invalid email format")
            validation_results["is_valid"] = False
        
        # Validate phone
        phone = parsed_data.get("personal_info", {}).get("phone", "")
        if phone and not re.match(self.phone_pattern, phone):
            validation_results["warnings"].append("Phone number format may be incorrect")
        
        # Check for missing critical information
        if not parsed_data.get("personal_info", {}).get("name"):
            validation_results["errors"].append("Name not found")
            validation_results["is_valid"] = False
        
        if not parsed_data.get("work_experience"):
            validation_results["warnings"].append("No work experience found")
        
        return validation_results
