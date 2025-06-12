from typing import Dict, List
from datetime import datetime, timedelta
from supabase import Client
import uuid

class ConversationMemory:
    def __init__(self, supabase_client: Client):
        """Initialize conversation memory with Supabase client."""
        self.supabase = supabase_client
        self.table = "conversation_history"
        self.default_history_limit = 20  # Increased from 5 to 20

    def _telegram_id_to_uuid(self, telegram_id: int) -> str:
        """Convert a Telegram user ID to a UUID v5 using a namespace."""
        # Use a fixed namespace UUID for consistency
        namespace = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')
        # Convert the telegram_id to a string and use it as the name
        return str(uuid.uuid5(namespace, str(telegram_id)))

    def save_message(self, user_id: int, message: Dict, metadata: Dict = None) -> None:
        """Save a message to the conversation history with optional metadata."""
        try:
            # Convert Telegram user_id to UUID
            user_uuid = self._telegram_id_to_uuid(user_id)
            
            # Prepare message data with metadata
            message_data = {
                "user_id": user_uuid,
                "role": message["role"],
                "content": message["content"],
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": metadata or {}
            }
            
            self.supabase.table(self.table).insert(message_data).execute()
        except Exception as e:
            print(f"Error saving message to conversation history: {str(e)}")
            raise

    def get_recent_history(self, user_id: int, limit: int = None) -> List[Dict]:
        """Get recent conversation history for a user."""
        try:
            # Convert Telegram user_id to UUID
            user_uuid = self._telegram_id_to_uuid(user_id)
            
            # Use default limit if none specified
            if limit is None:
                limit = self.default_history_limit
            
            response = self.supabase.table(self.table)\
                .select("*")\
                .eq("user_id", user_uuid)\
                .order("timestamp", desc=True)\
                .limit(limit)\
                .execute()
            
            # Convert to list of message dictionaries
            messages = []
            for record in response.data:
                messages.append({
                    "role": record["role"],
                    "content": record["content"],
                    "metadata": record.get("metadata", {}),
                    "timestamp": record["timestamp"]
                })
            
            # Reverse to get chronological order
            return list(reversed(messages))
        except Exception as e:
            print(f"Error retrieving conversation history: {str(e)}")
            return []

    def get_conversation_summary(self, user_id: int) -> Dict:
        """Get a summary of the conversation history."""
        try:
            # Get recent history
            history = self.get_recent_history(user_id)
            
            # Count messages by role
            message_counts = {
                "user": len([m for m in history if m["role"] == "user"]),
                "assistant": len([m for m in history if m["role"] == "assistant"])
            }
            
            # Get first and last message timestamps
            if history:
                first_message = history[0]
                last_message = history[-1]
                duration = datetime.fromisoformat(last_message["timestamp"]) - datetime.fromisoformat(first_message["timestamp"])
            else:
                duration = timedelta(0)
            
            return {
                "total_messages": len(history),
                "message_counts": message_counts,
                "first_message_time": history[0]["timestamp"] if history else None,
                "last_message_time": history[-1]["timestamp"] if history else None,
                "conversation_duration": str(duration)
            }
        except Exception as e:
            print(f"Error getting conversation summary: {str(e)}")
            return {}

    def clear_history(self, user_id: int) -> None:
        """Clear conversation history for a user."""
        try:
            # Convert Telegram user_id to UUID
            user_uuid = self._telegram_id_to_uuid(user_id)
            
            self.supabase.table(self.table)\
                .delete()\
                .eq("user_id", user_uuid)\
                .execute()
        except Exception as e:
            print(f"Error clearing conversation history: {str(e)}")
            raise 