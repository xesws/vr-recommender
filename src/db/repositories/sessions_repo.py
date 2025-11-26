from datetime import datetime
from typing import List, Dict, Optional
from ..mongo_connection import mongo

class ChatSessionsRepository:
    def __init__(self):
        self.collection = mongo.get_collection('chat_sessions')
        self._ensure_indexes()
        
    def _ensure_indexes(self):
        try:
            self.collection.create_index("user_id")
            self.collection.create_index([("updated_at", -1)])
        except Exception as e:
            print(f"Warning: Could not create indexes for sessions: {e}")

    def get_or_create(self, session_id: str, user_id: str) -> Dict:
        existing = self.collection.find_one({"_id": session_id})
        if existing:
            return existing
        
        new_session = {
            "_id": session_id,
            "user_id": user_id,
            "messages": [],
            "started_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "message_count": 0
        }
        self.collection.insert_one(new_session)
        return new_session

    def add_message(self, session_id: str, role: str, content: str):
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow()
        }

        self.collection.update_one(
            {"_id": session_id},
            {
                "$push": {"messages": message},
                "$inc": {"message_count": 1},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )

    def get_messages(self, session_id: str, limit: int = 10) -> List[Dict]:
        session = self.collection.find_one({"_id": session_id}, {"messages": 1})
        if session and "messages" in session:
            return session["messages"][-limit:]
        return []

    def end_session(self, session_id: str):
        self.collection.update_one(
            {"_id": session_id},
            {"$set": {"ended_at": datetime.utcnow()}}
        )
