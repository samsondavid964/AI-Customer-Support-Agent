from typing import Dict, Optional
from datetime import datetime, timedelta
import threading
import time

class SessionManager:
    def __init__(self, timeout_seconds: int = 3600):
        """Initialize session manager with timeout duration."""
        self.sessions: Dict[int, Dict] = {}
        self.timeout = timeout_seconds
        self.cleanup_thread = None
        self.running = False

    def start(self):
        """Start the session cleanup thread."""
        if not self.cleanup_thread:
            self.running = True
            self.cleanup_thread = threading.Thread(target=self._cleanup_sessions)
            self.cleanup_thread.daemon = True
            self.cleanup_thread.start()

    def stop(self):
        """Stop the session cleanup thread."""
        self.running = False
        if self.cleanup_thread:
            self.cleanup_thread.join()

    def create_session(self, user_id: int) -> None:
        """Create a new session for a user."""
        self.sessions[user_id] = {
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow()
        }

    def update_activity(self, user_id: int) -> None:
        """Update the last activity timestamp for a user's session."""
        if user_id in self.sessions:
            self.sessions[user_id]["last_activity"] = datetime.utcnow()

    def is_session_active(self, user_id: int) -> bool:
        """Check if a user's session is still active."""
        if user_id not in self.sessions:
            return False
        
        last_activity = self.sessions[user_id]["last_activity"]
        return (datetime.utcnow() - last_activity).total_seconds() < self.timeout

    def get_session_info(self, user_id: int) -> Optional[Dict]:
        """Get session information for a user."""
        if user_id in self.sessions and self.is_session_active(user_id):
            return self.sessions[user_id]
        return None

    def end_session(self, user_id: int) -> None:
        """End a user's session."""
        if user_id in self.sessions:
            del self.sessions[user_id]

    def _cleanup_sessions(self) -> None:
        """Periodically clean up expired sessions."""
        while self.running:
            try:
                current_time = datetime.utcnow()
                expired_users = [
                    user_id for user_id, session in self.sessions.items()
                    if (current_time - session["last_activity"]).total_seconds() >= self.timeout
                ]
                
                for user_id in expired_users:
                    del self.sessions[user_id]
                
                # Wait for 5 minutes before next cleanup
                time.sleep(300)
            except Exception as e:
                print(f"Error in session cleanup: {str(e)}")
                time.sleep(60)  # Wait a minute before retrying 