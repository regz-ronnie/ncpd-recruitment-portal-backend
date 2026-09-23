import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from django.utils import timezone
from django.db import transaction
from django.conf import settings
import requests
from apps.recruitment.models import JobPost, Application
from apps.users.models import User
from apps.ai_engine.models import ChatbotConversation, AIModel


class RecruitmentChatbot:
    """AI-powered recruitment chatbot for pre-screening and candidate engagement"""
    
    def __init__(self):
        self.session_timeout = 30  # minutes
        
        # AI Configuration - Support multiple providers (prioritize OpenAI)
        self.ai_providers = [
            {
                'name': 'openai',
                'api_key': getattr(settings, 'OPENAI_API_KEY', ''),
                'api_base': getattr(settings, 'OPENAI_API_BASE', 'https://api.openai.com/v1'),
                'model': getattr(settings, 'OPENAI_MODEL', 'gpt-4'),
                'enabled': bool(getattr(settings, 'OPENAI_API_KEY', '') and getattr(settings, 'OPENAI_API_KEY', '') != 'sk-proj-1234567890abcdef')
            },
            {
                'name': 'free_groq',
                'api_key': getattr(settings, 'FREE_AI_API_KEY', ''),
                'api_base': getattr(settings, 'FREE_AI_API_BASE', 'https://api.groq.com/openai/v1'),
                'model': getattr(settings, 'FREE_AI_MODEL', 'llama3-8b-8192'),
                'enabled': bool(getattr(settings, 'FREE_AI_API_KEY', '') and getattr(settings, 'FREE_AI_API_KEY', '') != 'gsk_demo_key')
            }
        ]
        
        # Find first available provider
        self.current_provider = None
        for provider in self.ai_providers:
            if provider['enabled']:
                self.current_provider = provider
                break
        
        if not self.current_provider:
            print("Warning: No AI API keys configured. Using rule-based responses only.")
        
        # Pre-screening questions templates
        self.screening_questions = {
            'technical': [
                "What programming languages are you proficient in?",
                "Describe your experience with {required_skill}",
                "Have you worked with {technology} in production environments?",
                "What's the most complex technical challenge you've solved?",
            ],
            'behavioral': [
                "Describe a situation where you had to work with a difficult team member.",
                "Tell me about a time you had to learn a new technology quickly.",
                "How do you handle tight deadlines and pressure?",
                "What motivates you in your work?",
            ],
            'experience': [
                "How many years of experience do you have with {skill}?",
                "What's your biggest professional achievement?",
                "Why are you interested in this position?",
                "What are your salary expectations?",
            ]
        }
        
        # Conversation flows
        self.conversation_flows = {
            'pre_screening': self._get_pre_screening_flow(),
            'application_help': self._get_application_help_flow(),
            'faq': self._get_faq_flow(),
            'interview_prep': self._get_interview_prep_flow()
        }
    
    def _call_ai_api(self, messages: List[Dict], system_prompt: str = None) -> str:
        """Call AI API with fallback to rule-based responses"""
        if not self.current_provider:
            return self._get_fallback_response(messages)
        
        try:
            # Prepare messages with system prompt
            api_messages = []
            if system_prompt:
                api_messages.append({"role": "system", "content": system_prompt})
            api_messages.extend(messages)
            
            # Make API call
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.current_provider['api_key']}"
            }
            
            payload = {
                "model": self.current_provider['model'],
                "messages": api_messages,
                "temperature": 0.7,
                "max_tokens": 500
            }
            
            response = requests.post(
                f"{self.current_provider['api_base']}/chat/completions",
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data['choices'][0]['message']['content']
            else:
                print(f"AI API error: {response.status_code} - {response.text}")
                return self._get_fallback_response(messages)
                
        except Exception as e:
            print(f"AI API call failed: {str(e)}")
            return self._get_fallback_response(messages)
    
    def _get_fallback_response(self, messages: List[Dict]) -> str:
        """Generate fallback response when AI is unavailable"""
        if not messages:
            return "Hello! I'm here to help you with your recruitment process at NCPD. How can I assist you today?"
        
        last_message = messages[-1].get('content', '').lower()
        
        # Enhanced keyword-based fallback with detailed responses
        if any(word in last_message for word in ['hello', 'hi', 'hey']):
            return "Hello! I'm here to help you with your recruitment process at NCPD (National Council for Population and Development). How can I assist you today?"
        elif any(word in last_message for word in ['help', 'assist', 'support']):
            return "I'm here to help! I can assist you with:\n• Job applications and requirements at NCPD\n• Interview preparation tips for NCPD positions\n• Common interview questions for population and development roles\n• Application status tracking\n• General recruitment process questions\n\nWhat would you like help with?"
        elif any(word in last_message for word in ['ncpd', 'national council', 'population', 'development']):
            return "NCPD (National Council for Population and Development) is the official body responsible for coordinating population and development programs in Kenya. We handle:\n\n• Population policy formulation and implementation\n• Development planning coordination\n• Research and data analysis on population trends\n• Capacity building for population programs\n• Monitoring and evaluation of development initiatives\n\nWe recruit for various positions including researchers, program officers, data analysts, administrators, and technical specialists. Would you like information about specific positions or the recruitment process?"
        elif any(word in last_message for word in ['apply', 'application', 'job']):
            return "To apply for a position at NCPD:\n1. Browse available jobs on our portal\n2. Click 'Apply' on a position that interests you\n3. Complete the application form with your details\n4. Upload your resume/CV and required documents\n5. Submit and track your application status\n\nMake sure your resume is in PDF or DOCX format and under 5MB. Would you like help with any specific step?"
        elif any(word in last_message for word in ['interview', 'prepare', 'question']):
            return "Here are common NCPD interview questions you should prepare for:\n\n**Personal Introduction:**\n• Tell me about yourself\n• Why do you want to work at NCPD?\n• What do you know about population and development issues?\n\n**Experience-Based:**\n• Describe a challenging situation you faced and how you handled it\n• Tell me about a time you demonstrated leadership\n• How do you handle pressure and tight deadlines?\n\n**Role-Specific:**\n• Why are you interested in this position?\n• What relevant experience do you have in population/development work?\n• Where do you see yourself in 5 years?\n\nWould you like tips on answering any of these questions?"
        elif any(word in last_message for word in ['sample', 'example']):
            return "Here are sample NCPD interview questions and answers:\n\n**Q: Why do you want to work at NCPD?**\nA: Focus on your passion for population and development issues, desire to contribute to national development goals, and alignment with NCPD's mission. Mention any relevant academic background or experience.\n\n**Q: How would you handle a challenging project with limited resources?**\nA: Emphasize prioritization skills, creative problem-solving, stakeholder engagement, and ability to deliver results despite constraints.\n\n**Q: What are your strengths relevant to population and development work?**\nA: Highlight qualities like analytical skills, research experience, project management, data analysis, communication skills, and understanding of development frameworks.\n\n**Q: How do you stay updated on population and development trends?**\nA: Mention reading research publications, attending conferences, following international organizations like UNFPA, and engaging with professional networks.\n\nWould you like more sample questions or tips on a specific topic?"
        elif any(word in last_message for word in ['resume', 'cv']):
            return "Resume tips for NCPD applications:\n• Use a clean, professional format\n• Include contact information at the top\n• Start with a strong summary/objective\n• List work experience in reverse chronological order\n• Include specific achievements and metrics\n• Highlight any population/development-related experience\n• Tailor your resume to each job application\n• Keep it to 1-2 pages\n• Proofread carefully for errors\n• Save as PDF for best compatibility\n\nNeed help with any specific section of your resume?"
        elif any(word in last_message for word in ['status', 'track']):
            return "To check your application status:\n1. Log into your account\n2. Go to your dashboard\n3. Click on 'My Applications'\n4. View the status of each application\n\nStatus updates include:\n• Submitted - Application received\n• Under Review - Being evaluated\n• Shortlisted - Selected for next round\n• Interview Scheduled - Interview details provided\n• Offer Extended - Job offer sent\n• Rejected - Not selected\n\nIs there a specific application you need help with?"
        elif any(word in last_message for word in ['requirement', 'qualification', 'skill']):
            return "NCPD job requirements vary by position but often include:\n\n**Education:**\n• Minimum KCSE grade C plain or equivalent\n• Relevant degree/diploma in population studies, development studies, statistics, social sciences, or related fields\n\n**Experience:**\n• Years of experience in relevant field\n• Specific technical skills (data analysis, research, project management)\n• Knowledge of development frameworks and policies\n\n**Skills:**\n• Analytical and research skills\n• Report writing and communication\n• Computer literacy (SPSS, Excel, data analysis tools)\n• Project management\n• Team collaboration\n\n**Character Requirements:**\n• Good conduct certificate\n• No criminal record\n• Kenyan citizenship\n• Age requirements (typically 21-35 years)\n\n**Documents:**\n• Updated resume/CV\n• Academic transcripts\n• ID card and birth certificate\n• Good conduct certificate\n• Professional references\n\nCheck specific job postings for detailed requirements. Would you like help with a particular position?"
        elif any(word in last_message for word in ['thank', 'thanks']):
            return "You're welcome! Is there anything else I can help you with regarding your NCPD application or the recruitment process?"
        else:
            return "Thank you for your message. I'm here to help with your NCPD recruitment process. I can assist with:\n• Job applications at NCPD\n• Interview preparation for population and development roles\n• Resume tips\n• Application status\n• Job requirements and qualifications\n\nCould you provide more details about what you need assistance with?"
    
    def start_conversation(self, user: Optional[User], conversation_type: str, initial_query: str, 
                          job_application: Optional[Application] = None) -> ChatbotConversation:
        """Start a new chatbot conversation"""
        
        session_id = str(uuid.uuid4())
        
        conversation = ChatbotConversation.objects.create(
            session_id=session_id,
            user=user,
            conversation_type=conversation_type,
            job_application=job_application,
            initial_query=initial_query,
            messages=[],
            started_at=timezone.now()
        )
        
        # Generate initial response
        response = self._generate_initial_response(conversation_type, initial_query, job_application)
        
        # Add messages to conversation
        conversation.messages = [
            {'role': 'user', 'content': initial_query, 'timestamp': timezone.now().isoformat()},
            {'role': 'assistant', 'content': response, 'timestamp': timezone.now().isoformat()}
        ]
        conversation.save()
        
        return conversation
    
    def continue_conversation(self, session_id: str, user_message: str, attachment: Optional[Dict] = None) -> Dict[str, Any]:
        """Continue an existing conversation"""
        
        try:
            conversation = ChatbotConversation.objects.get(session_id=session_id)
            
            # Check if conversation is still active
            if conversation.resolution_status != 'ongoing':
                return {
                    'error': 'Conversation has ended',
                    'status': conversation.resolution_status
                }
            
            # Add user message with attachment info if present
            message_data = {
                'role': 'user',
                'content': user_message,
                'timestamp': timezone.now().isoformat()
            }
            
            if attachment:
                message_data['attachment'] = attachment
            
            conversation.messages.append(message_data)
            
            # Generate response
            response_data = self._generate_conversational_response(conversation, user_message, attachment)
            
            # Add assistant response
            conversation.messages.append({
                'role': 'assistant',
                'content': response_data['response'],
                'timestamp': timezone.now().isoformat()
            })
            
            # Update extracted info and next actions
            if 'extracted_info' in response_data:
                conversation.extracted_info.update(response_data['extracted_info'])
            
            if 'next_actions' in response_data:
                conversation.next_actions = response_data['next_actions']
            
            conversation.last_message_at = timezone.now()
            conversation.save()
            
            # Check if conversation should be resolved
            self._check_conversation_resolution(conversation)
            
            return {
                'response': response_data['response'],
                'conversation_id': session_id,
                'extracted_info': conversation.extracted_info,
                'next_actions': conversation.next_actions,
                'status': conversation.resolution_status
            }
            
        except ChatbotConversation.DoesNotExist:
            return {'error': 'Conversation not found'}
        except Exception as e:
            return {'error': f'Error processing message: {str(e)}'}
    
    def _generate_initial_response(self, conversation_type: str, initial_query: str, 
                                 job_application: Optional[Application]) -> str:
        """Generate initial response for new conversation"""
        
        if conversation_type == 'pre_screening':
            return self._generate_pre_screening_initial(initial_query, job_application)
        elif conversation_type == 'application_help':
            return self._generate_help_response(initial_query)
        elif conversation_type == 'faq':
            return self._generate_faq_response(initial_query)
        elif conversation_type == 'interview_prep':
            return self._generate_interview_prep_response(initial_query, job_application)
        else:
            return "Hello! I'm here to help you with your recruitment process. How can I assist you today?"
    
    def _generate_pre_screening_initial(self, initial_query: str, job_application: Optional[Application]) -> str:
        """Generate initial response for pre-screening conversation"""
        
        if job_application:
            job = job_application.job
            response = f"Welcome! I'm here to help you with your application for the {job.title} position. "
            
            # Get job requirements
            if job.skills_required:
                response += f"This role requires skills in: {', '.join(job.skills_required[:3])}. "
            
            response += "I'd like to ask you a few questions to assess your fit for this position. "
            response += "First, could you tell me about your experience relevant to this role?"
            
            return response
        else:
            return "Hello! I can help you find the right position. What type of role are you looking for?"
    
    def _generate_conversational_response(self, conversation: ChatbotConversation, user_message: str, attachment: Optional[Dict] = None) -> Dict[str, Any]:
        """Generate response based on conversation context"""
        
        flow = self.conversation_flows.get(conversation.conversation_type, {})
        current_step = self._get_current_conversation_step(conversation)
        
        # Handle attachment acknowledgment
        if attachment:
            user_message += f" [User attached: {attachment.get('name', 'file')}]"
        
        if conversation.conversation_type == 'pre_screening':
            return self._handle_pre_screening_response(conversation, user_message, current_step)
        elif conversation.conversation_type == 'application_help':
            return self._handle_help_response(conversation, user_message, attachment)
        elif conversation.conversation_type == 'faq':
            return self._handle_faq_response(conversation, user_message)
        elif conversation.conversation_type == 'interview_prep':
            return self._handle_interview_prep_response(conversation, user_message)
        else:
            return {'response': "I'm here to help. Could you please clarify your question?"}
    
    def _handle_pre_screening_response(self, conversation: ChatbotConversation, user_message: str, 
                                    current_step: int) -> Dict[str, Any]:
        """Handle pre-screening conversation responses"""
        
        job = conversation.job_application.job if conversation.job_application else None
        extracted_info = {}
        next_actions = []
        
        # Extract information from user message
        if current_step == 0:  # Initial experience question
            skills = self._extract_skills_from_text(user_message)
            years_experience = self._extract_years_experience(user_message)
            
            extracted_info['skills_mentioned'] = skills
            extracted_info['years_experience'] = years_experience
            
            # Check if skills match job requirements
            if job and job.skills_required:
                matched_skills = set(skills) & set(job.skills_required)
                if len(matched_skills) >= len(job.skills_required) * 0.5:
                    response = f"That's great! I can see you have experience with {', '.join(list(matched_skills)[:3])}. "
                    response += "Now, could you describe a specific project where you used these skills?"
                else:
                    missing_skills = set(job.skills_required) - set(skills)
                    response = f"I notice you mentioned {', '.join(skills[:3])}. "
                    response += f"This role also requires experience with {', '.join(list(missing_skills)[:2])}. "
                    response += "Do you have experience with any of these technologies?"
            else:
                response = "Thank you for sharing! Could you tell me about a specific project you're proud of?"
                
        elif current_step == 1:  # Project description
            extracted_info['project_description'] = user_message
            response = "That sounds interesting! What was your specific role in this project and what was the outcome?"
            
        elif current_step == 2:  # Role and outcome
            extracted_info['project_role'] = user_message
            response = "Great! Now I'd like to know about your work style. How do you prefer to work in a team environment?"
            
        elif current_step == 3:  # Work style
            extracted_info['work_style'] = user_message
            response = "Thank you! One final question - what are your salary expectations for this role?"
            
        elif current_step == 4:  # Salary expectations
            extracted_info['salary_expectations'] = user_message
            
            # Complete pre-screening
            score = self._calculate_pre_screening_score(extracted_info, job)
            extracted_info['pre_screening_score'] = score
            
            if score >= 70:
                response = f"Excellent! Based on our conversation, you seem like a strong candidate (score: {score}/100). "
                response += "I'll recommend your application for further review. You should hear back from our team within 2-3 business days."
                next_actions = ['escalate_to_hr', 'schedule_interview']
            elif score >= 50:
                response = f"Thank you for your time! Your profile shows some alignment with the role (score: {score}/100). "
                response += "Your application will be reviewed by our team, and we'll be in touch if there's a good match."
                next_actions = ['submit_for_review']
            else:
                response = f"Thank you for your interest. While your experience is valuable, this particular role may not be the best fit (score: {score}/100). "
                response += "I'd encourage you to check out other positions that might better match your skills."
                next_actions = ['polite_rejection']
        
        else:
            response = "Thank you for sharing all that information. Is there anything else you'd like to know about the position?"
        
        return {
            'response': response,
            'extracted_info': extracted_info,
            'next_actions': next_actions
        }
    
    def _extract_skills_from_text(self, text: str) -> List[str]:
        """Extract skills from user message"""
        
        # Common technical skills
        skill_keywords = [
            'python', 'java', 'javascript', 'react', 'node.js', 'sql', 'mongodb',
            'aws', 'docker', 'kubernetes', 'git', 'linux', 'machine learning',
            'data analysis', 'project management', 'leadership', 'communication'
        ]
        
        text_lower = text.lower()
        found_skills = []
        
        for skill in skill_keywords:
            if skill in text_lower:
                found_skills.append(skill)
        
        return found_skills
    
    def _extract_years_experience(self, text: str) -> int:
        """Extract years of experience from text"""
        
        import re
        
        patterns = [
            r'(\d+)\+?\s*years?',
            r'(\d+)\s*-\s*(\d+)\s*years?',
            r'(\d+)\s*year',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                if len(match.groups()) == 2:
                    # Range - take average
                    return (int(match.group(1)) + int(match.group(2))) // 2
                else:
                    return int(match.group(1))
        
        return 0
    
    def _calculate_pre_screening_score(self, extracted_info: Dict, job: Optional[JobPost]) -> int:
        """Calculate pre-screening score"""
        
        score = 0
        
        # Skills matching (40 points)
        if job and job.skills_required:
            user_skills = set(extracted_info.get('skills_mentioned', []))
            required_skills = set(job.skills_required)
            skill_matches = len(user_skills & required_skills)
            score += min((skill_matches / len(required_skills)) * 40, 40)
        else:
            score += 20  # Default if no job requirements
        
        # Experience (30 points)
        years_exp = extracted_info.get('years_experience', 0)
        if years_exp >= 5:
            score += 30
        elif years_exp >= 3:
            score += 25
        elif years_exp >= 1:
            score += 20
        else:
            score += 10
        
        # Project description quality (20 points)
        project_desc = extracted_info.get('project_description', '')
        if len(project_desc) > 100:
            score += 20
        elif len(project_desc) > 50:
            score += 15
        elif len(project_desc) > 20:
            score += 10
        
        # Communication quality (10 points)
        total_length = sum(len(str(v)) for v in extracted_info.values())
        if total_length > 200:
            score += 10
        elif total_length > 100:
            score += 7
        elif total_length > 50:
            score += 5
        
        return min(int(score), 100)
    
    def _get_current_conversation_step(self, conversation: ChatbotConversation) -> int:
        """Get current step in conversation flow"""
        
        # Count user messages to determine step
        user_messages = [msg for msg in conversation.messages if msg['role'] == 'user']
        return len(user_messages) - 1  # -1 because we're processing the current message
    
    def _check_conversation_resolution(self, conversation: ChatbotConversation):
        """Check if conversation should be marked as resolved"""
        
        # Check for timeout
        if timezone.now() > conversation.started_at + timedelta(minutes=self.session_timeout):
            conversation.resolution_status = 'abandoned'
            conversation.ended_at = timezone.now()
            conversation.save()
            return
        
        # Check for escalation actions
        if 'escalate_to_hr' in conversation.next_actions:
            conversation.resolution_status = 'escalated'
            conversation.ended_at = timezone.now()
            conversation.save()
            self._escalate_conversation(conversation)
        
        # Check for resolution
        if 'submit_for_review' in conversation.next_actions:
            conversation.resolution_status = 'resolved'
            conversation.ended_at = timezone.now()
            conversation.save()
    
    def _escalate_conversation(self, conversation: ChatbotConversation):
        """Escalate conversation to HR staff"""
        
        # Find HR users
        hr_users = User.objects.filter(user_type='hr')
        
        # Create notification for HR staff
        for hr_user in hr_users:
            from apps.workflow.models import Notification
            Notification.objects.create(
                user=hr_user,
                notification_type='system_alert',
                title='Chatbot Conversation Escalated',
                message=f'Pre-screening conversation {conversation.session_id} requires human review.',
                action_url=f'/hr-dashboard?conversation={conversation.session_id}'
            )
    
    def _get_pre_screening_flow(self) -> List[Dict]:
        """Get pre-screening conversation flow"""
        return [
            {'step': 'experience_inquiry', 'type': 'open_ended'},
            {'step': 'project_details', 'type': 'open_ended'},
            {'step': 'role_outcome', 'type': 'open_ended'},
            {'step': 'work_style', 'type': 'open_ended'},
            {'step': 'salary_expectations', 'type': 'open_ended'},
        ]
    
    def _get_application_help_flow(self) -> List[Dict]:
        """Get application help conversation flow"""
        return [
            {'step': 'identify_issue', 'type': 'multiple_choice'},
            {'step': 'provide_solution', 'type': 'informative'},
            {'step': 'confirm_resolution', 'type': 'yes_no'},
        ]
    
    def _get_faq_flow(self) -> List[Dict]:
        """Get FAQ conversation flow"""
        return [
            {'step': 'identify_question', 'type': 'open_ended'},
            {'step': 'provide_answer', 'type': 'informative'},
            {'step': 'follow_up', 'type': 'yes_no'},
        ]
    
    def _get_interview_prep_flow(self) -> List[Dict]:
        """Get interview preparation conversation flow"""
        return [
            {'step': 'identify_role', 'type': 'multiple_choice'},
            {'step': 'provide_tips', 'type': 'informative'},
            {'step': 'practice_questions', 'type': 'interactive'},
        ]
    
    def _generate_help_response(self, initial_query: str) -> str:
        """Generate help response for application assistance"""
        
        return (
            "I'm here to help with your application! Common issues I can assist with include:\n\n"
            "• Uploading your resume/CV\n"
            "• Completing the application form\n"
            "• Understanding job requirements\n"
            "• Application status updates\n\n"
            "What specific issue are you experiencing?"
        )
    
    def _generate_faq_response(self, initial_query: str) -> str:
        """Generate FAQ response"""
        
        return (
            "I can answer frequently asked questions about:\n\n"
            "• Application process\n"
            "• Job requirements\n"
            "• Company culture\n"
            "• Benefits and compensation\n"
            "• Interview process\n\n"
            "What would you like to know?"
        )
    
    def _generate_interview_prep_response(self, initial_query: str, job_application: Optional[Application]) -> str:
        """Generate interview preparation response"""
        
        if job_application:
            job = job_application.job
            return (
                f"I can help you prepare for your {job.title} interview! "
                "I can provide:\n\n"
                   "• Common interview questions for this role\n"
                   "• Tips based on the job requirements\n"
                   "• Practice questions\n"
                   "• Company-specific advice\n\n"
                   "What aspect of interview preparation would you like help with?"
            )
        else:
            return (
                "I'd be happy to help you prepare for interviews! "
                "I can provide tips, practice questions, and role-specific advice. "
                "What type of position are you interviewing for?"
            )
    
    def _handle_help_response(self, conversation: ChatbotConversation, user_message: str, attachment: Optional[Dict] = None) -> Dict[str, Any]:
        """Handle help conversation responses"""
        
        # Handle attachment acknowledgment
        if attachment:
            return {
                'response': f"Thank you for attaching {attachment.get('name', 'your file')}. I've received your document. Is there anything specific about this file you need help with, or would you like assistance with something else?",
                'extracted_info': {'attachment_received': True}
            }
        
        # Simple keyword-based help responses
        if 'resume' in user_message.lower() or 'cv' in user_message.lower():
            response = (
                "For resume issues: Ensure your file is in PDF or DOCX format and under 5MB. "
                "Make sure it includes your contact information, work experience, and education."
            )
        elif 'form' in user_message.lower():
            response = (
                "For form issues: Make sure all required fields are filled out. "
                "Check that your email and phone number are correct. "
                "If you're still having trouble, try refreshing the page."
            )
        elif 'status' in user_message.lower():
            response = (
                "To check your application status: Log into your dashboard and view 'My Applications'. "
                "You'll see real-time updates on your application progress."
            )
        else:
            response = "I understand you need help. Could you provide more details about the specific issue you're experiencing?"
        
        return {'response': response}
    
    def _handle_faq_response(self, conversation: ChatbotConversation, user_message: str) -> Dict[str, Any]:
        """Handle FAQ responses using AI API"""
        
        # Build conversation context
        messages = [
            {"role": "user", "content": user_message}
        ]
        
        system_prompt = """You are a helpful recruitment FAQ assistant for the National Council for Population and Development (NCPD) in Kenya. 
        Provide helpful, concise answers about:
        - Application process
        - Job requirements  
        - Company culture
        - Benefits and compensation
        - Interview process
        - Eligibility criteria
        - Population and development programs
        
        If you don't know the answer, suggest contacting HR at hr@ncpd.go.ke. Be professional, friendly, and informative."""
        
        response = self._call_ai_api(messages, system_prompt)
        return {'response': response}
    
    def _handle_interview_prep_response(self, conversation: ChatbotConversation, user_message: str) -> Dict[str, Any]:
        """Handle interview preparation responses using AI API"""
        
        # Build conversation context from previous messages
        messages = []
        for msg in conversation.messages:
            if msg['role'] in ['user', 'assistant']:
                messages.append({
                    "role": msg['role'],
                    "content": msg['content']
                })
        
        # Add current message
        messages.append({"role": "user", "content": user_message})
        
        system_prompt = """You are an expert interview coach for the National Council for Population and Development (NCPD) in Kenya.
        Provide helpful interview preparation advice including:
        - Common interview questions for population and development roles
        - Tips for answering behavioral questions
        - Practice questions and guidance
        - Professional presentation advice
        - Role-specific preparation tips
        
        Be encouraging, practical, and specific to population and development work when relevant."""
        
        response = self._call_ai_api(messages, system_prompt)
        return {'response': response}
