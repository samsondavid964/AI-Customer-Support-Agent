import os
from dotenv import load_dotenv
from services.gmail_service import GmailService

def test_email_service():
    """Test the Gmail service configuration."""
    # Load environment variables
    load_dotenv()

    # Initialize Gmail service
    gmail_service = GmailService(
        gmail_email=os.getenv('GMAIL_EMAIL'),
        gmail_app_password=os.getenv('GMAIL_APP_PASSWORD'),
        escalation_email=os.getenv('HUMAN_ESCALATION_EMAIL')
    )

    # Test sending a notification email
    success = gmail_service.send_notification_email(
        subject="Test Email from TeachPro Bot",
        body="This is a test email to verify the Gmail service configuration is working correctly.",
        recipient=os.getenv('HUMAN_ESCALATION_EMAIL')
    )

    if success:
        print("✅ Test email sent successfully!")
    else:
        print("❌ Failed to send test email. Please check the error messages above.")

if __name__ == "__main__":
    test_email_service() 