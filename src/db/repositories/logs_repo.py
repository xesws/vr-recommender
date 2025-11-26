from datetime import datetime
from typing import List, Optional, Dict
from ..mongo_connection import mongo

class InteractionLogsRepository:
    def __init__(self):
        self.collection = mongo.get_collection('interaction_logs')
        self._ensure_indexes()

    def _ensure_indexes(self):
        try:
            self.collection.create_index("user_id")
            self.collection.create_index([("timestamp", -1)])
            self.collection.create_index("intent")
        except Exception as e:
            print(f"Warning: Could not create indexes for logs: {e}")

    def insert(self, log: Dict) -> str:
        log['timestamp'] = log.get('timestamp', datetime.utcnow())
        result = self.collection.insert_one(log)
        return str(result.inserted_id)

    def find_recent(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        return list(
            self.collection.find()
            .sort("timestamp", -1)
            .skip(offset)
            .limit(limit)
        )

    def find_by_user(self, user_id: str, limit: int = 50) -> List[Dict]:
        return list(
            self.collection.find({"user_id": user_id})
            .sort("timestamp", -1)
            .limit(limit)
        )

    def get_stats(self) -> Dict:
        pipeline = [
            {"$group": {
                "_id": None,
                "total_interactions": {"$sum": 1},
                "unique_users": {"$addToSet": "$user_id"},
                "avg_latency": {"$avg": "$metadata.latency_ms"}
            }},
            {"$project": {
                "total_interactions": 1,
                "unique_users": {"$size": "$unique_users"},
                "avg_latency": {"$round": ["$avg_latency", 2]}
            }}
        ]
        try:
            result = list(self.collection.aggregate(pipeline))
            return result[0] if result else {}
        except Exception:
            return {}

    def get_popular_intents(self, limit: int = 10) -> List[Dict]:
        pipeline = [
            {"$group": {"_id": "$intent", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": limit}
        ]
        try:
            return list(self.collection.aggregate(pipeline))
        except Exception:
            return []
