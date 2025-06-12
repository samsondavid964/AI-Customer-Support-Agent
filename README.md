# TeachPro AI Tutoring Agent

An intelligent AI agent for TeachPro that handles parent inquiries via Telegram, manages schedules, and provides comprehensive support.

## Features

- Telegram-based conversation interface
- Intelligent response generation using Supabase vector store
- Google Calendar integration for schedule management
- Gmail integration for human escalation
- Dynamic learning and adaptation
- Google Sheets integration for additional information

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up environment variables in `.env`:
   ```
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   OPENAI_API_KEY=your_openai_api_key_here
   GOOGLE_CREDENTIALS_PATH=path_to_credentials.json
   ```

4. Set up Google Cloud Project and enable necessary APIs:
   - Google Calendar API
   - Gmail API
   - Google Sheets API

5. Download Google credentials and place them in the project directory

## Project Structure

```
teachpro_agent/
├── config/
│   └── config.py
├── services/
│   ├── telegram_service.py
│   ├── vector_store.py
│   ├── google_calendar.py
│   ├── gmail_service.py
│   └── google_sheets.py
├── utils/
│   ├── message_processor.py
│   └── response_generator.py
├── main.py
└── requirements.txt
```

## Usage

Run the bot:
```bash
python main.py
```

## Configuration

The bot can be configured through the `config.py` file and environment variables. See the configuration section in the documentation for more details. 