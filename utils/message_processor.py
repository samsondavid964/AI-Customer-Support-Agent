from typing import Dict, List, Tuple
import re
from datetime import datetime
from config.config import ESCALATION_KEYWORDS

class MessageProcessor:
    def __init__(self):
        self.conversation_history = {}

    def process_message(self, message: str, user_id: str) -> Dict:
        """
        Process incoming message and extract relevant information
        """
        # Initialize conversation history for new users
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []

        # Add message to conversation history
        self.conversation_history[user_id].append({
            'message': message,
            'timestamp': datetime.now().isoformat()
        })

        # Analyze message
        analysis = {
            'requires_escalation': self._check_escalation(message),
            'intent': self._detect_intent(message),
            'entities': self._extract_entities(message),
            'sentiment': self._analyze_sentiment(message)
        }

        return analysis

    def _check_escalation(self, message: str) -> bool:
        """
        Check if message requires human escalation
        """
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in ESCALATION_KEYWORDS)

    def _detect_intent(self, message: str) -> str:
        """
        Detect the intent of the message
        """
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['schedule', 'book', 'appointment']):
            return 'schedule'
        elif any(word in message_lower for word in ['price', 'cost', 'fee']):
            return 'pricing'
        elif any(word in message_lower for word in ['program', 'course', 'curriculum']):
            return 'program_info'
        elif any(word in message_lower for word in ['teacher', 'tutor', 'instructor']):
            return 'teacher_info'
        else:
            return 'general_inquiry'

    def _extract_entities(self, message: str) -> Dict:
        """
        Extract relevant entities from the message
        """
        entities = {
            'dates': self._extract_dates(message),
            'times': self._extract_times(message),
            'subjects': self._extract_subjects(message),
            'grades': self._extract_grades(message)
        }
        return entities

    def _extract_dates(self, message: str) -> List[str]:
        """
        Extract dates from message
        """
        # Basic date pattern matching
        date_pattern = r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4}'
        return re.findall(date_pattern, message)

    def _extract_times(self, message: str) -> List[str]:
        """
        Extract times from message
        """
        # Basic time pattern matching
        time_pattern = r'\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?|\d{1,2}\s*(?:AM|PM|am|pm)'
        return re.findall(time_pattern, message)

    def _extract_subjects(self, message: str) -> List[str]:
        """
        Extract subject mentions from message
        """
        subjects = ['math', 'science', 'english', 'history', 'physics', 'chemistry', 'biology']
        return [subject for subject in subjects if subject in message.lower()]

    def _extract_grades(self, message: str) -> List[str]:
        """
        Extract grade levels from message
        """
        grade_pattern = r'grade\s+\d{1,2}|\d{1,2}(?:st|nd|rd|th)\s+grade'
        return re.findall(grade_pattern, message.lower())

    def _analyze_sentiment(self, message: str) -> str:
        """
        Basic sentiment analysis
        """
        positive_words = ['good', 'great', 'excellent', 'happy', 'thanks', 'thank']
        negative_words = ['bad', 'poor', 'terrible', 'unhappy', 'angry', 'upset']

        message_lower = message.lower()
        positive_count = sum(1 for word in positive_words if word in message_lower)
        negative_count = sum(1 for word in negative_words if word in message_lower)

        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'

    def get_conversation_history(self, user_id: str) -> List[Dict]:
        """
        Get conversation history for a user
        """
        return self.conversation_history.get(user_id, []) 