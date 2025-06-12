from typing import Dict, List
from datetime import datetime
from services.google_sheets import GoogleSheetsService

class ConversationLogger:
    def __init__(self, sheets_service: GoogleSheetsService):
        self.sheets_service = sheets_service
        self.conversation_sheet = "Conversations"  # Sheet name for logging conversations

    def log_conversation(self, 
                        parent_info: Dict,
                        conversation_history: List[Dict],
                        task_completed: bool = False) -> bool:
        """
        Log a conversation to Google Sheets
        """
        try:
            # Extract conversation details
            parent_name = parent_info.get('name', 'Unknown')
            
            # Analyze conversation to determine topic and help provided
            topic = self._extract_topic(conversation_history)
            help_provided = self._summarize_help(conversation_history)
            
            # Prepare row data
            row_data = [
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # Timestamp
                parent_name,
                topic,
                help_provided,
                "Yes" if task_completed else "No"  # Task completion status
            ]

            # Append to sheet
            self.sheets_service.append_row(
                sheet_name=self.conversation_sheet,
                row_data=row_data
            )

            return True
        except Exception as e:
            print(f"Error logging conversation: {str(e)}")
            return False

    def _extract_topic(self, conversation_history: List[Dict]) -> str:
        """
        Extract the main topic from conversation history
        """
        # Simple implementation - can be enhanced with more sophisticated analysis
        if not conversation_history:
            return "Unknown"
        
        # Look for topic-related keywords in the first few messages
        topic_keywords = {
            'schedule': ['schedule', 'booking', 'appointment', 'session'],
            'pricing': ['price', 'cost', 'fee', 'payment'],
            'curriculum': ['curriculum', 'syllabus', 'course', 'subject'],
            'support': ['help', 'support', 'assist', 'issue']
        }
        
        for msg in conversation_history[:3]:  # Check first 3 messages
            content = msg.get('content', '').lower()
            for topic, keywords in topic_keywords.items():
                if any(keyword in content for keyword in keywords):
                    return topic.capitalize()
        
        return "General Inquiry"

    def _summarize_help(self, conversation_history: List[Dict]) -> str:
        """
        Summarize the help provided in the conversation
        """
        if not conversation_history:
            return "No conversation recorded"
        
        # Simple implementation - can be enhanced with more sophisticated analysis
        summary = []
        for msg in conversation_history:
            if msg.get('role') == 'assistant':
                content = msg.get('content', '')
                if len(content) > 50:  # Only include substantial responses
                    summary.append(content[:100] + "...")  # Truncate long responses
        
        return " | ".join(summary) if summary else "No substantial help provided" 