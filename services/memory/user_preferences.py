from typing import Dict, Optional
from datetime import datetime
from supabase import Client
import uuid

class UserPreferences:
    def __init__(self, supabase_client: Client):
        """Initialize user preferences with Supabase client."""
        self.supabase = supabase_client
        self.table = "user_preferences"

    def _telegram_id_to_uuid(self, telegram_id: int) -> str:
        """Convert a Telegram user ID to a UUID v5 using a namespace."""
        # Use a fixed namespace UUID for consistency
        namespace = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')
        # Convert the telegram_id to a string and use it as the name
        return str(uuid.uuid5(namespace, str(telegram_id)))

    def save_preferences(self, user_id: int, preferences: Dict) -> None:
        """Save or update user preferences."""
        try:
            # Convert Telegram user_id to UUID
            user_uuid = self._telegram_id_to_uuid(user_id)
            
            self.supabase.table(self.table)\
                .upsert({
                    "user_id": user_uuid,
                    "preferences": preferences,
                    "updated_at": datetime.utcnow().isoformat()
                })\
                .execute()
        except Exception as e:
            print(f"Error saving user preferences: {str(e)}")
            raise

    def get_preferences(self, user_id: int) -> Optional[Dict]:
        """Get user preferences."""
        try:
            # Convert Telegram user_id to UUID
            user_uuid = self._telegram_id_to_uuid(user_id)
            
            response = self.supabase.table(self.table)\
                .select("*")\
                .eq("user_id", user_uuid)\
                .execute()
            
            # Return preferences if found, otherwise return None
            if response.data and len(response.data) > 0:
                return response.data[0].get("preferences")
            return None
        except Exception as e:
            print(f"Error retrieving user preferences: {str(e)}")
            return None

    def update_preference(self, user_id: int, key: str, value: any) -> None:
        """Update a single preference value."""
        try:
            # Get current preferences
            current_prefs = self.get_preferences(user_id) or {}
            
            # Update the specific preference
            current_prefs[key] = value
            
            # Save updated preferences
            self.save_preferences(user_id, current_prefs)
        except Exception as e:
            print(f"Error updating user preference: {str(e)}")
            raise

    def delete_preferences(self, user_id: int) -> None:
        """Delete user preferences."""
        try:
            # Convert Telegram user_id to UUID
            user_uuid = self._telegram_id_to_uuid(user_id)
            
            self.supabase.table(self.table)\
                .delete()\
                .eq("user_id", user_uuid)\
                .execute()
        except Exception as e:
            print(f"Error deleting user preferences: {str(e)}")
            raise 