import asyncio
from datetime import datetime
from telegram import Update, ChatAction
from telegram.error import TelegramError
from telegram.ext import ContextTypes

class TelegramBot:
    def __init__(self, telegram_token: str, llm_service: LLMService, vector_store: VectorStore, sheet_service: SheetService):
        """Initialize the Telegram bot with required services."""
        # Configure request with longer timeouts and retries
        request = Request(
            connection_pool_size=8,
            connect_timeout=30.0,
            read_timeout=30.0,
            write_timeout=30.0
        )
        self.bot = Bot(token=telegram_token, request=request)
        self.llm_service = llm_service
        self.vector_store = vector_store
        self.sheet_service = sheet_service
        self.sessions = {}
        self.logger = logging.getLogger(__name__)

    async def start_typing(self, chat_id: int):
        """Send typing indicator to the chat."""
        try:
            await self.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
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
                context = await self.get_context(analysis, user_id)

                # Generate response
                response = self.llm_service.generate_response(
                    text,
                    self.sessions[user_id]['conversation_history'],
                    context
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

            # Log escalation details
            self.logger.info(f"Escalation required for user {message.from_user.id}")
            self.logger.info(f"Message: {message.text}")
            self.logger.info(f"Analysis: {analysis}")

            # Notify user
            await message.reply_text(
                "I've noted your request and will ensure it gets the attention it needs. "
                "A team member will review this and get back to you soon."
            )

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

    def run(self):
        """Run the bot."""
        try:
            application = Application.builder().token(self.bot.token).build()
            
            # Add error handler
            async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
                self.logger.error(f"Exception while handling an update: {context.error}")
                if update and update.effective_message:
                    await update.effective_message.reply_text(
                        "I apologize, but I encountered an error. Please try again in a moment."
                    )
            
            application.add_error_handler(error_handler)
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
            
            # Run with more resilient polling settings
            application.run_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True,
                pool_timeout=30.0,
                read_timeout=30.0,
                write_timeout=30.0,
                connect_timeout=30.0
            )
        except Exception as e:
            self.logger.error(f"Error running bot: {str(e)}")
            raise 