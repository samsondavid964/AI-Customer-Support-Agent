from typing import Dict, List
from datetime import datetime
from config.config import CONFIDENCE_THRESHOLD

class ResponseGenerator:
    def __init__(self):
        self.templates = {
            'greeting': [
                "Hello! I'm the TeachPro assistant. How can I help you today?",
                "Welcome to TeachPro! How may I assist you?",
                "Hi there! I'm here to help with your TeachPro questions."
            ],
            'schedule': [
                "I can help you schedule a session. What subject and grade level are you interested in?",
                "Let's find a suitable time for your tutoring session. What's your preferred subject?",
                "I'll help you book a session. Could you tell me which subject you're interested in?"
            ],
            'pricing': [
                "Our pricing varies by subject and grade level. Which program are you interested in?",
                "I'd be happy to provide pricing information. Could you specify the subject and grade level?",
                "Let me get the pricing details for you. What type of program are you looking for?"
            ],
            'program_info': [
                "Our programs are designed to help students excel. What specific information would you like to know?",
                "I can provide detailed information about our programs. What aspects are you most interested in?",
                "Let me tell you about our programs. What would you like to know specifically?"
            ],
            'teacher_info': [
                "Our teachers are highly qualified professionals. What subject are you interested in?",
                "I can provide information about our teachers. Which subject area are you looking for?",
                "Let me tell you about our teaching staff. What subject are you interested in?"
            ],
            'escalation': [
                "I understand you'd like to speak with a human representative. I'll connect you with our team right away.",
                "I'll escalate your request to our support team. They'll be in touch with you shortly.",
                "Let me connect you with our human support team. They'll be able to assist you better."
            ],
            'fallback': [
                "I'm not sure I understand. Could you please rephrase your question?",
                "I want to make sure I help you correctly. Could you provide more details?",
                "I'm having trouble understanding. Could you please clarify your question?"
            ]
        }

    def generate_response(self, 
                         message_analysis: Dict,
                         vector_store_results: List[Dict] = None,
                         sheet_data: List[Dict] = None) -> str:
        """
        Generate an appropriate response based on message analysis and available data
        """
        # Check for escalation first
        if message_analysis['requires_escalation']:
            return self._get_template_response('escalation')

        # Get base response based on intent
        intent = message_analysis['intent']
        response = self._get_template_response(intent)

        # Enhance response with vector store results if available
        if vector_store_results:
            response = self._enhance_with_vector_store(response, vector_store_results)

        # Enhance response with sheet data if available
        if sheet_data:
            response = self._enhance_with_sheet_data(response, sheet_data)

        # Add relevant entities to response
        response = self._add_entity_context(response, message_analysis['entities'])

        return response

    def _get_template_response(self, intent: str) -> str:
        """
        Get a random template response for the given intent
        """
        import random
        templates = self.templates.get(intent, self.templates['fallback'])
        return random.choice(templates)

    def _enhance_with_vector_store(self, base_response: str, results: List[Dict]) -> str:
        """
        Enhance the response with relevant information from vector store
        """
        if not results:
            return base_response

        # Add the most relevant result to the response
        most_relevant = results[0]
        return f"{base_response}\n\n{most_relevant.get('content', '')}"

    def _enhance_with_sheet_data(self, base_response: str, sheet_data: List[Dict]) -> str:
        """
        Enhance the response with relevant information from Google Sheets
        """
        if not sheet_data:
            return base_response

        # Add relevant sheet data to the response
        additional_info = "\n".join([str(row) for row in sheet_data[:2]])  # Limit to 2 rows
        return f"{base_response}\n\nAdditional information:\n{additional_info}"

    def _add_entity_context(self, response: str, entities: Dict) -> str:
        """
        Add relevant entity context to the response
        """
        context_parts = []

        if entities['dates']:
            context_parts.append(f"Available dates: {', '.join(entities['dates'])}")
        if entities['times']:
            context_parts.append(f"Preferred times: {', '.join(entities['times'])}")
        if entities['subjects']:
            context_parts.append(f"Subjects: {', '.join(entities['subjects'])}")
        if entities['grades']:
            context_parts.append(f"Grade levels: {', '.join(entities['grades'])}")

        if context_parts:
            return f"{response}\n\nI noticed you mentioned: {'; '.join(context_parts)}"
        return response

    def generate_schedule_confirmation(self, event_details: Dict) -> str:
        """
        Generate a confirmation message for scheduled events
        """
        return f"""
        I've scheduled your session:
        
        Subject: {event_details.get('subject', 'Not specified')}
        Date: {event_details.get('date', 'Not specified')}
        Time: {event_details.get('time', 'Not specified')}
        Teacher: {event_details.get('teacher', 'To be assigned')}
        
        You'll receive a confirmation email shortly. Is there anything else you'd like to know?
        """ 