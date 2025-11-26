"""Chat session management - MongoDB implementation."""
from datetime import datetime
from typing import List, Dict
from src.db.repositories.sessions_repo import ChatSessionsRepository

class ChatSession:
    """Chat session management."""

    def __init__(self, session_id: str, user_id: str = "anonymous"):
        """
        Initialize a chat session.

        Args:
            session_id: Unique session identifier
            user_id: User identifier
        """
        self.session_id = session_id
        self.user_id = user_id
        self.repo = ChatSessionsRepository()
        self._load_or_create()

    def _load_or_create(self):
        """Load session from DB or create if new."""
        # This ensures the session document exists
        self.repo.get_or_create(self.session_id, self.user_id)
        
    def add_message(self, role: str, content: str):
        """
        Add a message to the session.

        Args:
            role: Message role (e.g., 'user', 'assistant')
            content: Message content
        """
        self.repo.add_message(self.session_id, role, content)

    def get_context(self, last_n: int = 5) -> str:
        """
        Get recent messages as context string.

        Args:
            last_n: Number of recent messages to include

        Returns:
            Formatted context string
        """
        messages = self.repo.get_messages(self.session_id, limit=last_n)
        # Messages from repo are dicts, need to format them
        return "\n".join([f"{m['role']}: {m['content']}" for m in messages])

    def get_messages(self, limit: int = 20) -> List[Dict]:
        """Get raw messages list."""
        return self.repo.get_messages(self.session_id, limit=limit)

    def should_trigger_recommendation(self, message: str) -> bool:
        """
        Check if message should trigger VR app recommendation.

        Args:
            message: User message

        Returns:
            True if recommendation should be triggered
        """
        triggers = [
            "recommend", "suggest", "find", "vr app", "application",
            "应用", "推荐", "learn", "study", "want to", "looking for",
            "help me", "what should", "how to"
        ]
        return any(t in message.lower() for t in triggers)

    def clear_history(self):
        """Clear session history (Not implemented for persistent DB)."""
        # In a persistent DB, we typically don't delete history unless requested.
        # For now, we can just mark it ended or do nothing.
        pass

    def get_message_count(self) -> int:
        """Get total number of messages in session."""
        doc = self.repo.collection.find_one({"_id": self.session_id}, {"message_count": 1})
        return doc.get("message_count", 0) if doc else 0