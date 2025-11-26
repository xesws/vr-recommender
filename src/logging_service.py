"""
Interaction logging service - MongoDB implementation.
"""
from typing import List, Dict, Optional, Any
from src.db.repositories.logs_repo import InteractionLogsRepository

class InteractionLogger:
    """Service to handle interaction logging to the database."""
    
    def __init__(self):
        self.repo = InteractionLogsRepository()

    def log_interaction(
        self,
        user_id: str,
        query: str,
        response: str,
        intent: str = "unknown",
        recommended_apps: List[Dict] = None,
        metadata: Dict[str, Any] = None,
        session_id: Optional[str] = None
    ) -> str:
        """
        Log a chat interaction.
        """
        try:
            log = {
                "user_id": user_id,
                "session_id": session_id,
                "query_text": query,
                "intent": intent,
                "response_text": response,
                "recommended_apps": recommended_apps or [],
                "metadata": metadata or {}
            }
            log_id = self.repo.insert(log)
            print(f"📝 Logged interaction for user {user_id[:8]}... (ID: {log_id})")
            return log_id
        except Exception as e:
            print(f"❌ Failed to log interaction: {e}")
            return ""

    def get_admin_logs(self, limit: int = 50, offset: int = 0, user_id: str = None) -> List[Dict]:
        """Get logs for admin dashboard."""
        logs = []
        if user_id:
            logs = self.repo.find_by_user(user_id, limit)
        else:
            logs = self.repo.find_recent(limit, offset)
            
        # Convert ObjectId to string for JSON serialization
        for log in logs:
            if '_id' in log:
                log['_id'] = str(log['_id'])
        return logs

    def get_admin_stats(self) -> Dict:
        """Get system stats."""
        return self.repo.get_stats()
