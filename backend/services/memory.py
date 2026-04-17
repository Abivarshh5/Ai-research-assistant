import logging
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

class SessionManager:
    """
    Lightweight in-memory session manager for Research State.
    In a multi-user production environment, this should be backed by Redis or a DB.
    """
    def __init__(self):
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a session by ID."""
        return self._sessions.get(session_id)

    def save_session(self, session_id: str, state: Dict[str, Any]):
        """Persists or updates a session state."""
        self._sessions[session_id] = state
        logger.debug(f"Session {session_id} saved.")

    def delete_session(self, session_id: str):
        """Clears a session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.debug(f"Session {session_id} deleted.")

# Global instance
memory_store = SessionManager()
