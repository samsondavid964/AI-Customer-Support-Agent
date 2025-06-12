import os
import logging
import asyncio
import warnings
from typing import Dict, List, Optional

from dotenv import load_dotenv
from supabase import create_client, Client
from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, filters, ContextTypes

from services.vector_store import VectorStore
from services.google_sheets import GoogleSheetsService
from services.google_calendar import GoogleCalendarService
from services.gmail_service import GmailService
from services.llm_service import LLMService
from services.conversation_logger import ConversationLogger
from services.memory.conversation_memory import ConversationMemory
from services.memory.user_preferences import UserPreferences
from services.memory.session_manager import SessionManager
from services.telegram_bot import TelegramBot

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
            
            # Initialize Telegram bot
            self.telegram_bot = TelegramBot(
                os.getenv('TELEGRAM_BOT_TOKEN'),
                self.llm_service,
                self.vector_store,
                self.sheets_service,
                self.gmail_service
            )
            
        except Exception as e:
            logger.error(f"Error initializing bot: {str(e)}")
            raise

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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
            await update.message.reply_text(welcome_message)
        except Exception as e:
            logger.error(f"Error in start command: {str(e)}")
            await update.message.reply_text(
                "I apologize, but I'm having trouble starting the conversation. "
                "Please try again later or contact our support team."
            )

    async def run(self):
        """Run the bot."""
        try:
            await self.telegram_bot.run()
        except Exception as e:
            logger.error(f"Error running bot: {str(e)}")
            raise

async def main():
    """Main function to run the bot."""
    try:
        bot = TeachProBot()
        await bot.run()
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        raise

if __name__ == '__main__':
    asyncio.run(main()) 