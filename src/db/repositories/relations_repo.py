from datetime import datetime
from typing import List, Dict
from ..mongo_connection import mongo

class CourseSkillsRepository:
    def __init__(self):
        self.collection = mongo.get_collection('course_skills')
        self._ensure_indexes()

    def _ensure_indexes(self):
        try:
            self.collection.create_index("course_id")
            self.collection.create_index("skill_name")
        except Exception:
            pass

    def find_all(self) -> List[Dict]:
        return list(self.collection.find())

    def bulk_upsert(self, mappings: List[Dict]) -> int:
        from pymongo import UpdateOne
        if not mappings:
            return 0
            
        operations = []
        for m in mappings:
            # Map source_id to course_id if needed
            course_id = m.get('course_id') or m.get('source_id')
            skill_name = m.get('skill_name')
            
            if not course_id or not skill_name:
                continue
            
            m_copy = m.copy()
            m_copy['course_id'] = course_id
            if 'source_id' in m_copy:
                del m_copy['source_id'] # Clean up
                
            # Create a unique ID logic or just use upsert with query
            operations.append(UpdateOne(
                {"course_id": course_id, "skill_name": skill_name},
                {"$set": m_copy},
                upsert=True
            ))
            
        if operations:
            result = self.collection.bulk_write(operations)
            return result.upserted_count + result.modified_count
        return 0

    def count(self) -> int:
        return self.collection.count_documents({})


class AppSkillsRepository:
    def __init__(self):
        self.collection = mongo.get_collection('app_skills')
        self._ensure_indexes()

    def _ensure_indexes(self):
        try:
            self.collection.create_index("app_id")
            self.collection.create_index("skill_name")
        except Exception:
            pass

    def find_all(self) -> List[Dict]:
        return list(self.collection.find())

    def bulk_upsert(self, mappings: List[Dict]) -> int:
        from pymongo import UpdateOne
        if not mappings:
            return 0
            
        operations = []
        for m in mappings:
            # Map source_id to app_id if needed
            app_id = m.get('app_id') or m.get('source_id')
            skill_name = m.get('skill_name')
            
            if not app_id or not skill_name:
                continue
            
            m_copy = m.copy()
            m_copy['app_id'] = app_id
            if 'source_id' in m_copy:
                del m_copy['source_id']
                
            operations.append(UpdateOne(
                {"app_id": app_id, "skill_name": skill_name},
                {"$set": m_copy},
                upsert=True
            ))
            
        if operations:
            result = self.collection.bulk_write(operations)
            return result.upserted_count + result.modified_count
        return 0

    def count(self) -> int:
        return self.collection.count_documents({})
