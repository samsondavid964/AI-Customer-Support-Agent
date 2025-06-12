from google.oauth2 import service_account
from googleapiclient.discovery import build
from config.config import (
    GOOGLE_CREDENTIALS_PATH,
    GOOGLE_SHEETS_ID
)

class GoogleSheetsService:
    def __init__(self, credentials_path: str, sheets_id: str):
        self.credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        self.service = build('sheets', 'v4', credentials=self.credentials)
        self.sheets_id = sheets_id

    def get_sheet_data(self, range_name: str):
        """
        Get data from a specific range in the Google Sheet
        """
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheets_id,
                range=range_name
            ).execute()
            
            return result.get('values', [])
        except Exception as e:
            print(f"Error getting sheet data: {str(e)}")
            return []

    def search_sheet(self, search_term: str, sheet_name: str = 'Sheet1'):
        """
        Search for a term in the entire sheet
        """
        try:
            # Get all data from the sheet
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheets_id,
                range=f'{sheet_name}!A:Z'
            ).execute()
            
            values = result.get('values', [])
            matches = []

            # Search through the data
            for row in values:
                if any(search_term.lower() in str(cell).lower() for cell in row):
                    matches.append(row)

            return matches
        except Exception as e:
            print(f"Error searching sheet: {str(e)}")
            return []

    def get_sheet_metadata(self):
        """
        Get metadata about the spreadsheet
        """
        try:
            result = self.service.spreadsheets().get(
                spreadsheetId=self.sheets_id
            ).execute()
            
            return {
                'title': result.get('properties', {}).get('title'),
                'sheets': [sheet.get('properties', {}).get('title') 
                          for sheet in result.get('sheets', [])]
            }
        except Exception as e:
            print(f"Error getting sheet metadata: {str(e)}")
            return {}

    def append_row(self, sheet_name: str, row_data: list):
        """
        Append a row to the specified sheet
        """
        try:
            # Ensure the sheet exists first
            if not self.ensure_sheet_exists(sheet_name):
                raise Exception(f"Failed to create or verify sheet: {sheet_name}")

            # Prepare the request body
            body = {
                'values': [row_data]
            }

            # Make the API call
            result = self.service.spreadsheets().values().append(
                spreadsheetId=self.sheets_id,
                range=f'{sheet_name}!A:E',  # Assuming columns A through E
                valueInputOption='USER_ENTERED',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()

            return result
        except Exception as e:
            print(f"Error appending row to sheet: {str(e)}")
            return None

    def ensure_sheet_exists(self, sheet_name: str):
        """
        Ensure the specified sheet exists, create it if it doesn't
        """
        try:
            # Get current sheets
            metadata = self.get_sheet_metadata()
            existing_sheets = metadata.get('sheets', [])

            if sheet_name not in existing_sheets:
                # Create new sheet
                request = {
                    'addSheet': {
                        'properties': {
                            'title': sheet_name
                        }
                    }
                }

                body = {
                    'requests': [request]
                }

                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=self.sheets_id,
                    body=body
                ).execute()

                # Add headers to the new sheet
                headers = ['Timestamp', 'Parent Name', 'Topic', 'Help Provided', 'Task Completed']
                self.append_row(sheet_name, headers)

            return True
        except Exception as e:
            print(f"Error ensuring sheet exists: {str(e)}")
            return False 