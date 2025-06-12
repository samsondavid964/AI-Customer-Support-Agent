import asyncio
import logging
from datetime import datetime
from typing import Dict

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    filters,
    CommandHandler
)

class TelegramBot:
    def __init__(self, telegram_token: str, llm_service, vector_store, sheet_service, gmail_service):
        """Initialize the Telegram bot with required services."""
        self.token = telegram_token
        self.llm_service = llm_service
        self.vector_store = vector_store
        self.sheet_service = sheet_service
        self.gmail_service = gmail_service
        self.sessions = {}
        self.logger = logging.getLogger(__name__)
        self.application = None

    async def start_typing(self, chat_id: int):
        """Send typing indicator to the chat."""
        try:
            await self.application.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        except Exception as e:
            self.logger.error(f"Error sending typing indicator: {str(e)}")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming messages."""
        try:
            message = update.message
            if not message or not message.text:
                return

            user_id = message.from_user.id
            chat_id = message.chat_id
            text = message.text

            # Start typing indicator
            await self.start_typing(chat_id)

            # Get or create session
            if user_id not in self.sessions:
                self.sessions[user_id] = {
                    'conversation_history': [],
                    'preferences': {},
                    'last_interaction': datetime.now()
                }

            # Update last interaction time
            self.sessions[user_id]['last_interaction'] = datetime.now()

            # Create a task to keep typing indicator active
            typing_task = asyncio.create_task(self.keep_typing(chat_id))

            try:
                # Analyze message
                analysis = self.llm_service.analyze_message(
                    text,
                    self.sessions[user_id]['conversation_history']
                )

                # Get relevant context
                context_data = await self.get_context(analysis, user_id)

                # Generate response
                response = self.llm_service.generate_response(
                    text,
                    self.sessions[user_id]['conversation_history'],
                    context_data
                )

                # Update conversation history
                self.sessions[user_id]['conversation_history'].append({
                    "role": "user",
                    "content": text
                })
                self.sessions[user_id]['conversation_history'].append({
                    "role": "assistant",
                    "content": response
                })

                # Keep conversation history within limits
                if len(self.sessions[user_id]['conversation_history']) > 10:
                    self.sessions[user_id]['conversation_history'] = self.sessions[user_id]['conversation_history'][-10:]

                # Cancel typing task
                typing_task.cancel()
                try:
                    await typing_task
                except asyncio.CancelledError:
                    pass

                # Send response with retry logic
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        await message.reply_text(
                            response,
                            read_timeout=30,
                            write_timeout=30,
                            connect_timeout=30
                        )
                        break
                    except Exception as e:
                        if attempt == max_retries - 1:
                            raise
                        await asyncio.sleep(1)  # Wait before retry

                # Handle escalation if needed
                if analysis.get('escalation_required', False):
                    await self.handle_escalation(update, context, analysis)

            finally:
                # Ensure typing task is cancelled
                if not typing_task.done():
                    typing_task.cancel()
                    try:
                        await typing_task
                    except asyncio.CancelledError:
                        pass

        except Exception as e:
            self.logger.error(f"Error handling message: {str(e)}")
            await message.reply_text(
                "I apologize, but I encountered an error processing your message. Please try again later.",
                read_timeout=30,
                write_timeout=30,
                connect_timeout=30
            )

    async def keep_typing(self, chat_id: int):
        """Keep the typing indicator active."""
        try:
            while True:
                await self.start_typing(chat_id)
                await asyncio.sleep(4)  # Telegram typing indicator lasts for 5 seconds
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error(f"Error in keep_typing: {str(e)}")

    async def handle_escalation(self, update: Update, context: ContextTypes.DEFAULT_TYPE, analysis: Dict):
        """Handle cases that need human attention."""
        try:
            message = update.message
            if not message:
                return

            # Get user information
            user_info = {
                'name': f"{message.from_user.first_name} {message.from_user.last_name if message.from_user.last_name else ''}",
                'username': message.from_user.username,
                'user_id': message.from_user.id
            }

            # Get conversation history for this user
            conversation_history = self.sessions.get(message.from_user.id, {}).get('conversation_history', [])

            # Log escalation details
            self.logger.info(f"Escalation required for user {message.from_user.id}")
            self.logger.info(f"Message: {message.text}")
            self.logger.info(f"Analysis: {analysis}")

            # Send escalation email
            email_sent = self.gmail_service.send_escalation_email(
                parent_info=user_info,
                conversation_context=message.text,
                conversation_history=conversation_history
            )

            # Notify user
            await message.reply_text(
                "I've noted your request and will ensure it gets the attention it needs. "
                "A team member will review this and get back to you soon."
            )

            if not email_sent:
                self.logger.error("Failed to send escalation email")

        except Exception as e:
            self.logger.error(f"Error handling escalation: {str(e)}")

    async def get_context(self, analysis: Dict, user_id: int) -> Dict:
        """Gather relevant context for the response."""
        try:
            context = {
                'intent': analysis.get('intent', 'unknown'),
                'entities': analysis.get('entities', {}),
                'vector_store_results': [],
                'sheet_data': {},
                'escalation_required': analysis.get('escalation_required', False)
            }

            # Get relevant information from vector store
            if analysis.get('intent') in ['question', 'help', 'information']:
                context['vector_store_results'] = self.vector_store.search(
                    analysis.get('entities', {}).get('query', ''),
                    limit=3
                )

            # Get relevant sheet data
            if analysis.get('intent') in ['schedule', 'booking', 'availability']:
                context['sheet_data'] = self.sheet_service.get_availability()

            return context

        except Exception as e:
            self.logger.error(f"Error gathering context: {str(e)}")
            return {
                'intent': 'unknown',
                'entities': {},
                'vector_store_results': [],
                'sheet_data': {},
                'escalation_required': True
            }

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle errors in the bot."""
        self.logger.error(f"Exception while handling an update: {context.error}")
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "I apologize, but I encountered an error. Please try again in a moment."
            )

    async def run(self):
        """Initializes and starts the bot, then runs it indefinitely."""
        self.logger.info("Starting bot...")
        try:
            # Build the application with custom settings
            self.application = (
                ApplicationBuilder()
                .token(self.token)
                .connect_timeout(30.0)
                .read_timeout(30.0)
                .write_timeout(30.0)
                .pool_timeout(30.0)
                .build()
            )
            
            # Add error handler
            self.application.add_error_handler(self.error_handler)
            
            # Add message handler
            self.application.add_handler(
                MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
            )

            # Add test command handler
            self.application.add_handler(
                CommandHandler("testemail", self.test_email)
            )
            
            # Initialize the application
            await self.application.initialize()
            
            # Start the polling process in the background
            await self.application.start()
            
            # Start polling without blocking the main event loop
            await self.application.updater.start_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True
            )
            
            self.logger.info("Bot is running. Press Ctrl+C to stop.")

            # Keep the main coroutine alive
            while True:
                await asyncio.sleep(3600)  # Sleep for an hour

        except Exception as e:
            self.logger.error(f"Error running bot: {str(e)}")
            raise
        finally:
            # Ensure proper shutdown if the loop is ever broken
            if self.application and self.application.updater.is_running:
                await self.application.updater.stop()
            if self.application:
                await self.application.stop()
                await self.application.shutdown()
            self.logger.info("Bot has been shut down.")

    async def test_email(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Test the email functionality."""
        try:
            message = update.message
            if not message:
                return

            # Get user information
            user_info = {
                'name': f"{message.from_user.first_name} {message.from_user.last_name if message.from_user.last_name else ''}",
                'username': message.from_user.username,
                'user_id': message.from_user.id
            }

            # Send a test notification email
            email_sent = self.gmail_service.send_notification_email(
                subject="Test Email from TeachPro Bot",
                body=f"""
This is a test email from the TeachPro Bot.

User Information:
• Name: {user_info['name']}
• Username: @{user_info['username']}
• User ID: {user_info['user_id']}

Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

If you're receiving this email, the email functionality is working correctly!
                """,
                recipient=self.gmail_service.escalation_email
            )

            if email_sent:
                await message.reply_text(
                    "✅ Test email sent successfully! Please check the escalation email inbox."
                )
            else:
                await message.reply_text(
                    "❌ Failed to send test email. Please check the logs for more information."
                )

        except Exception as e:
            self.logger.error(f"Error in test_email command: {str(e)}")
            await message.reply_text(
                "❌ An error occurred while testing the email functionality. Please check the logs."
            ) 