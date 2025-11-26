from datetime import datetime
from typing import List, Optional, Dict, Any
from ..mongo_connection import mongo

class SkillsRepository:
    def __init__(self):
        self.collection = mongo.get_collection('skills')

    def find_all(self) -> List[Dict]:
        return list(self.collection.find())

    def find_by_name(self, name: str) -> Optional[Dict]:
        return self.collection.find_one({"name": name})

    def bulk_upsert(self, skills: List[Dict]) -> int:
        from pymongo import UpdateOne
        if not skills:
            return 0
            
        operations = []
        for skill in skills:
            # Skills might not have a clear ID in JSON, usually 'name' is unique
            skill_name = skill.get('name')
            if not skill_name:
                continue
            
            skill_copy = skill.copy()
            skill_copy['updated_at'] = datetime.utcnow()
            
            operations.append(UpdateOne(
                {"name": skill_name}, # Match by name
                {"$set": skill_copy, "$setOnInsert": {"created_at": datetime.utcnow()}},
                upsert=True
            ))
            
        if operations:
            result = self.collection.bulk_write(operations)
            return result.upserted_count + result.modified_count
        return 0

    def count(self) -> int:
        return self.collection.count_documents({})
