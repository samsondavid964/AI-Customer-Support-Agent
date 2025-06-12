import os
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from dotenv import load_dotenv
from supabase import create_client, Client
from services.vector_store import VectorStore
from services.google_sheets import GoogleSheetsService
from services.google_calendar import GoogleCalendarService
from services.gmail_service import GmailService
from services.llm_service import LLMService
from services.conversation_logger import ConversationLogger
from services.memory.conversation_memory import ConversationMemory
from services.memory.user_preferences import UserPreferences
from services.memory.session_manager import SessionManager
from typing import Dict, List, Optional
import asyncio
import warnings

# Suppress Google API client warnings
warnings.filterwarnings('ignore', message='file_cache is only supported with oauth2client<4.0.0')

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def check_required_env_vars():
    """Check if all required environment variables are set."""
    required_vars = [
        'TELEGRAM_BOT_TOKEN',
        'SUPABASE_URL',
        'SUPABASE_KEY',
        'OPENAI_API_KEY',
        'GOOGLE_CREDENTIALS_PATH',
        'GOOGLE_SHEETS_ID',
        'CALENDAR_ID',
        'GMAIL_EMAIL',
        'GMAIL_APP_PASSWORD',
        'HUMAN_ESCALATION_EMAIL'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

class TeachProBot:
    def __init__(self):
        """Initialize the bot with all required services."""
        try:
            # Check environment variables
            check_required_env_vars()
            
            # Initialize Supabase client
            self.supabase: Client = create_client(
                os.getenv('SUPABASE_URL'),
                os.getenv('SUPABASE_KEY')
            )

            # Initialize services
            self.vector_store = VectorStore(
                os.getenv('SUPABASE_URL'),
                os.getenv('SUPABASE_KEY')
            )
            self.sheets_service = GoogleSheetsService(
                os.getenv('GOOGLE_CREDENTIALS_PATH'),
                os.getenv('GOOGLE_SHEETS_ID')
            )
            self.calendar_service = GoogleCalendarService(
                os.getenv('GOOGLE_CREDENTIALS_PATH'),
                os.getenv('CALENDAR_ID')
            )
            self.gmail_service = GmailService(
                os.getenv('GMAIL_EMAIL'),
                os.getenv('GMAIL_APP_PASSWORD'),
                os.getenv('HUMAN_ESCALATION_EMAIL')
            )
            self.llm_service = LLMService(os.getenv('OPENAI_API_KEY'))
            self.conversation_logger = ConversationLogger(self.sheets_service)

            # Initialize memory services
            self.conversation_memory = ConversationMemory(self.supabase)
            self.user_preferences = UserPreferences(self.supabase)
            self.session_manager = SessionManager(timeout_seconds=3600)  # 1 hour timeout
            
        except Exception as e:
            logger.error(f"Error initializing bot: {str(e)}")
            raise

    def start(self, update: Update, context: CallbackContext):
        """Handle the /start command."""
        try:
            user_id = update.effective_user.id
            
            # Create new session
            self.session_manager.create_session(user_id)
            
            # Initialize user preferences if needed
            prefs = self.user_preferences.get_preferences(user_id)
            if not prefs:
                self.user_preferences.save_preferences(user_id, {
                    "name": f"{update.effective_user.first_name} {update.effective_user.last_name if update.effective_user.last_name else ''}",
                    "username": update.effective_user.username,
                    "language": "en",
                    "notifications_enabled": True
                })

            welcome_message = (
                "Hello! I'm your TeachPro assistant. I can help you with:\n"
                "• Information about our tutoring services\n"
                "• Scheduling sessions\n"
                "• Answering questions about our programs\n"
                "• Connecting you with our support team when needed\n\n"
                "How can I help you today?"
            )
            update.message.reply_text(welcome_message)
        except Exception as e:
            logger.error(f"Error in start command: {str(e)}")
            update.message.reply_text(
                "I apologize, but I'm having trouble starting the conversation. "
                "Please try again later or contact our support team."
            )

    def handle_message(self, update: Update, context: CallbackContext):
        """Handle incoming messages."""
        try:
            user_id = update.effective_user.id
            message = update.message.text

            # Check if session is active, create new one if not
            if not self.session_manager.is_session_active(user_id):
                self.session_manager.create_session(user_id)

            # Update session activity
            self.session_manager.update_activity(user_id)

            # Save message to conversation memory
            self.conversation_memory.save_message(user_id, {
                "role": "user",
                "content": message
            })

            # Get conversation history
            conversation_history = self.conversation_memory.get_recent_history(user_id)

            # Get user preferences
            user_prefs = self.user_preferences.get_preferences(user_id)

            # Analyze message using LLM
            analysis = self.llm_service.analyze_message(
                message,
                conversation_history
            )

            # Get relevant information from vector store
            vector_results = self.vector_store.search(message)

            # Get relevant information from sheets
            sheet_data = self.sheets_service.search_sheet(message)

            # Prepare context for LLM
            context = {
                "intent": analysis.get("intent"),
                "entities": analysis.get("entities", {}),
                "vector_store_results": vector_results,
                "sheet_data": sheet_data,
                "escalation_required": analysis.get("escalation_required", False),
                "user_preferences": user_prefs
            }

            # Generate response
            response = self.llm_service.generate_response(
                message,
                conversation_history,
                context
            )

            # Save response to conversation memory
            self.conversation_memory.save_message(user_id, {
                "role": "assistant",
                "content": response
            })

            # Send response
            update.message.reply_text(response)

            # Check if we should log this conversation
            if self._should_log_conversation(analysis):
                self._log_conversation(user_id, update.effective_user)
                # Clear conversation memory after logging
                self.conversation_memory.clear_history(user_id)

            # Handle escalation if needed
            if analysis.get("escalation_required"):
                self._handle_escalation(update, context)

        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            update.message.reply_text(
                "I apologize, but I'm having trouble processing your request. "
                "Please try again later or contact our support team."
            )

    def _should_log_conversation(self, analysis: Dict) -> bool:
        """Determine if the conversation should be logged."""
        return (
            analysis.get("intent") in ["schedule_complete", "end_conversation"] or
            analysis.get("escalation_required", False)
        )

    def _log_conversation(self, user_id: int, user: Update.effective_user):
        """Log the conversation to Google Sheets."""
        try:
            # Get conversation history
            conversation_history = self.conversation_memory.get_recent_history(user_id)
            
            parent_info = {
                "name": f"{user.first_name} {user.last_name if user.last_name else ''}",
                "username": user.username,
                "user_id": user_id
            }
            
            self.conversation_logger.log_conversation(
                parent_info,
                conversation_history
            )
            
        except Exception as e:
            logger.error(f"Error logging conversation: {str(e)}")

    def _handle_escalation(self, update: Update, context: Dict):
        """Handle escalation to human support."""
        try:
            # Get conversation history
            conversation_history = self.conversation_memory.get_recent_history(
                update.effective_user.id
            )
            
            # Prepare parent info
            parent_info = {
                "name": f"{update.effective_user.first_name} {update.effective_user.last_name if update.effective_user.last_name else ''}",
                "username": update.effective_user.username if update.effective_user.username else 'N/A',
                "user_id": update.effective_user.id
            }

            # Prepare conversation context
            conversation_context = f"""
            Last Message: {update.message.text}
            
            Analysis:
            - Intent: {context.get('intent', 'unknown')}
            - Entities: {context.get('entities', {})}
            - Requires Escalation: {context.get('escalation_required', False)}
            """

            # Send escalation email with conversation history
            self.gmail_service.send_escalation_email(
                parent_info=parent_info,
                conversation_context=conversation_context,
                conversation_history=conversation_history
            )

            # Notify parent
            update.message.reply_text(
                "I'll connect you with our support team who will assist you shortly."
            )

        except Exception as e:
            logger.error(f"Error handling escalation: {str(e)}")
            update.message.reply_text(
                "I apologize, but I'm having trouble connecting you with our support team. "
                "Please try contacting us directly at support@teachpro.com"
            )

    def _format_conversation_history(self, history: List[Dict]) -> str:
        """Format conversation history for email."""
        formatted = []
        for msg in history:
            role = "Parent" if msg["role"] == "user" else "Assistant"
            formatted.append(f"{role}: {msg['content']}")
        return "\n".join(formatted)

def main():
    """Start the bot."""
    try:
        # Create bot instance
        bot = TeachProBot()
        
        # Create updater
        updater = Updater(os.getenv('TELEGRAM_BOT_TOKEN'))

        # Get the dispatcher to register handlers
        dispatcher = updater.dispatcher

        # Add handlers
        dispatcher.add_handler(CommandHandler("start", bot.start))
        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, bot.handle_message))

        # Start the bot
        updater.start_polling()
        updater.idle()
            
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        raise

if __name__ == '__main__':
    main() 