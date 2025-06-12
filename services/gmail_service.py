import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from datetime import datetime
from config.config import (
    GMAIL_EMAIL,
    GMAIL_APP_PASSWORD,
    HUMAN_ESCALATION_EMAIL
)

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class GmailService:
    def __init__(self, gmail_email: str, gmail_app_password: str, escalation_email: str):
        """Initialize Gmail service with email and app password."""
        self.gmail_email = gmail_email
        self.gmail_app_password = gmail_app_password
        self.escalation_email = escalation_email
        logger.info(f"Initialized Gmail service with email: {gmail_email}")

    def _format_conversation_history(self, conversation_history: list) -> str:
        """Format conversation history for email."""
        if not conversation_history:
            return "No conversation history available."

        formatted_history = []
        for message in conversation_history:
            role = "User" if message.get("role") == "user" else "Assistant"
            content = message.get("content", "").strip()
            if content:
                formatted_history.append(f"{role}: {content}")

        return "\n\n".join(formatted_history)

    def send_escalation_email(self, parent_info: dict, conversation_context: str, conversation_history: list = None):
        """
        Send an escalation email to the human support team
        """
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.gmail_email
            msg['To'] = self.escalation_email
            msg['Subject'] = f'TeachPro: Escalation Request from {parent_info.get("name", "Unknown User")}'

            # Format the current time
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Create email body with improved formatting
            body = f"""
🔔 New Escalation Request

📅 Time: {current_time}

👤 Parent Information:
• Name: {parent_info.get('name', 'Not provided')}
• Username: @{parent_info.get('username', 'Not provided')}
• User ID: {parent_info.get('user_id', 'Not provided')}

💬 Conversation Summary:
{conversation_context}

📝 Full Conversation History:
{self._format_conversation_history(conversation_history) if conversation_history else "No conversation history available."}

⚠️ Action Required:
Please follow up with the parent as soon as possible. The conversation has been escalated due to a request for human assistance.

Best regards,
TeachPro Bot
            """
            
            msg.attach(MIMEText(body, 'plain'))

            # Connect to Gmail's SMTP server using SSL
            logger.debug("Attempting to connect to Gmail SMTP server using SSL...")
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            logger.debug("Attempting to login...")
            server.login(self.gmail_email, self.gmail_app_password)
            logger.debug("Login successful, sending message...")
            
            # Send email
            server.send_message(msg)
            logger.debug("Message sent successfully")
            server.quit()
            logger.info("Email sent successfully")

            return True
        except Exception as e:
            logger.error(f"Error sending escalation email: {str(e)}", exc_info=True)
            return False

    def send_notification_email(self, subject: str, body: str, recipient: str):
        """
        Send a general notification email
        """
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.gmail_email
            msg['To'] = recipient
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))

            # Connect to Gmail's SMTP server using SSL
            logger.debug("Attempting to connect to Gmail SMTP server using SSL...")
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            logger.debug("Attempting to login...")
            server.login(self.gmail_email, self.gmail_app_password)
            logger.debug("Login successful, sending message...")
            
            # Send email
            server.send_message(msg)
            logger.debug("Message sent successfully")
            server.quit()
            logger.info("Email sent successfully")

            return True
        except Exception as e:
            logger.error(f"Error sending notification email: {str(e)}", exc_info=True)
            return False 