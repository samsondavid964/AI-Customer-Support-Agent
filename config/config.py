import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Supabase Configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# OpenAI Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Google Services Configuration
GOOGLE_CREDENTIALS_PATH = os.getenv('GOOGLE_CREDENTIALS_PATH')
GOOGLE_SHEETS_ID = os.getenv('GOOGLE_SHEETS_ID')
HUMAN_ESCALATION_EMAIL = os.getenv('HUMAN_ESCALATION_EMAIL')

# Vector Store Configuration
VECTOR_STORE_COLLECTION = 'teachpro_docs'
EMBEDDING_MODEL = 'text-embedding-3-small'

# Response Configuration
MAX_RESPONSE_LENGTH = 1000
CONFIDENCE_THRESHOLD = 0.7

# Calendar Configuration
CALENDAR_ID = os.getenv('CALENDAR_ID')
TIMEZONE = 'UTC'

# Escalation Configuration
ESCALATION_KEYWORDS = [
    'human',
    'representative',
    'agent',
    'speak to someone',
    'help me',
    'urgent'
]

# Gmail Configuration
GMAIL_EMAIL = os.getenv('GMAIL_EMAIL')
GMAIL_APP_PASSWORD = os.getenv('GMAIL_APP_PASSWORD') 