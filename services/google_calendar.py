from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from config.config import (
    GOOGLE_CREDENTIALS_PATH,
    CALENDAR_ID,
    TIMEZONE
)

class GoogleCalendarService:
    def __init__(self, credentials_path: str, calendar_id: str):
        self.credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=['https://www.googleapis.com/auth/calendar']
        )
        self.service = build('calendar', 'v3', credentials=self.credentials)
        self.calendar_id = calendar_id

    def create_event(self, summary: str, start_time: datetime, end_time: datetime,
                    description: str = None, attendees: list = None):
        """
        Create a new calendar event
        """
        try:
            event = {
                'summary': summary,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': TIMEZONE,
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': TIMEZONE,
                },
            }

            if description:
                event['description'] = description

            if attendees:
                event['attendees'] = [{'email': email} for email in attendees]

            event = self.service.events().insert(
                calendarId=self.calendar_id,
                body=event,
                sendUpdates='all'
            ).execute()

            return event
        except Exception as e:
            print(f"Error creating calendar event: {str(e)}")
            return None

    def get_available_slots(self, date: datetime, duration_minutes: int = 60):
        """
        Get available time slots for a given date
        """
        try:
            # Get events for the specified date
            start_of_day = datetime(date.year, date.month, date.day)
            end_of_day = start_of_day + timedelta(days=1)

            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=start_of_day.isoformat(),
                timeMax=end_of_day.isoformat(),
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])
            
            # Calculate available slots
            busy_times = [(datetime.fromisoformat(event['start']['dateTime']),
                          datetime.fromisoformat(event['end']['dateTime']))
                         for event in events]

            available_slots = []
            current_time = start_of_day

            while current_time < end_of_day:
                slot_end = current_time + timedelta(minutes=duration_minutes)
                is_available = True

                for busy_start, busy_end in busy_times:
                    if (current_time < busy_end and slot_end > busy_start):
                        is_available = False
                        current_time = busy_end
                        break

                if is_available:
                    available_slots.append((current_time, slot_end))
                    current_time = slot_end
                else:
                    current_time += timedelta(minutes=15)

            return available_slots
        except Exception as e:
            print(f"Error getting available slots: {str(e)}")
            return []

    def delete_event(self, event_id: str):
        """
        Delete a calendar event
        """
        try:
            self.service.events().delete(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            return True
        except Exception as e:
            print(f"Error deleting calendar event: {str(e)}")
            return False 