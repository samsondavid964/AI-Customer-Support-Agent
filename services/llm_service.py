from typing import Dict, List, Optional
import openai
import json
from config.system_prompt import SYSTEM_PROMPT

class LLMService:
    def __init__(self, openai_api_key: str):
        """Initialize the LLM service with OpenAI API key."""
        self.client = openai.OpenAI(api_key=openai_api_key)
        self.model = "gpt-4o-mini"
        self.system_prompt = SYSTEM_PROMPT

    def generate_response(
        self,
        message: str,
        conversation_history: List[Dict],
        context: Dict
    ) -> str:
        """Generate a response using the LLM."""
        try:
            # Prepare messages for the chat
            messages = [
                {"role": "system", "content": self.system_prompt},
                *conversation_history[-5:],  # Last 5 messages for context
                {
                    "role": "user",
                    "content": f"""Message: {message}
                    
                    Context:
                    - Intent: {context.get('intent', 'unknown')}
                    - Entities: {context.get('entities', {})}
                    - Vector Store Results: {context.get('vector_store_results', [])}
                    - Sheet Data: {context.get('sheet_data', {})}
                    - Escalation Required: {context.get('escalation_required', False)}
                    
                    Please provide a helpful response based on the above information."""
                }
            ]

            # Generate response with adjusted parameters for gpt-4o-mini
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=300,  # Reduced from 500 to be more efficient
                top_p=0.9,  # Added top_p parameter
                frequency_penalty=0.1,  # Added frequency penalty
                presence_penalty=0.1  # Added presence penalty
            )

            return response.choices[0].message.content

        except Exception as e:
            print(f"Error generating response: {str(e)}")
            return "I apologize, but I'm having trouble processing your request right now. Please try again later."

    def analyze_message(
        self,
        message: str,
        conversation_history: List[Dict]
    ) -> Dict:
        """Analyze the message for intent, entities, and escalation needs."""
        try:
            # Prepare messages for analysis
            messages = [
                {"role": "system", "content": self.system_prompt},
                *conversation_history[-5:],
                {
                    "role": "user",
                    "content": f"""Analyze this message and provide a JSON response with:
                    1. intent: The main purpose of the message
                    2. entities: Any important information extracted
                    3. escalation_required: Whether this needs human attention
                    4. sentiment: The emotional tone of the message
                    
                    Message: {message}"""
                }
            ]

            # Get analysis with adjusted parameters for gpt-4o-mini
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=200,  # Reduced from 500 to be more efficient
                response_format={"type": "json_object"},
                top_p=0.9,
                frequency_penalty=0.1,
                presence_penalty=0.1
            )

            # Parse the JSON response
            try:
                analysis = json.loads(response.choices[0].message.content)
                return analysis
            except json.JSONDecodeError:
                print("Error parsing LLM response as JSON")
                return {
                    "intent": "unknown",
                    "entities": {},
                    "escalation_required": True,
                    "sentiment": "neutral"
                }

        except Exception as e:
            print(f"Error analyzing message: {str(e)}")
            return {
                "intent": "unknown",
                "entities": {},
                "escalation_required": True,
                "sentiment": "neutral"
            }

    def generate_schedule_confirmation(
        self,
        event_details: Dict
    ) -> str:
        """Generate a confirmation message for scheduled sessions."""
        try:
            messages = [
                {"role": "system", "content": self.system_prompt},
                {
                    "role": "user",
                    "content": f"""Generate a friendly and professional confirmation message for a scheduled tutoring session with these details:
                    - Student: {event_details.get('student_name')}
                    - Subject: {event_details.get('subject')}
                    - Date: {event_details.get('date')}
                    - Time: {event_details.get('time')}
                    - Tutor: {event_details.get('tutor_name')}
                    - Format: {event_details.get('format')}
                    
                    The message should be warm and professional, confirming all details and providing any necessary preparation instructions."""
                }
            ]

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=200,  # Reduced from 300 to be more efficient
                top_p=0.9,
                frequency_penalty=0.1,
                presence_penalty=0.1
            )

            return response.choices[0].message.content

        except Exception as e:
            print(f"Error generating schedule confirmation: {str(e)}")
            return "Your tutoring session has been scheduled. You will receive a confirmation email with all the details." 