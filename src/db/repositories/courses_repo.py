from datetime import datetime
from typing import List, Optional, Dict, Any
from ..mongo_connection import mongo

class CoursesRepository:
    def __init__(self):
        self.collection = mongo.get_collection('courses')

    def find_all(self) -> List[Dict]:
        return list(self.collection.find())

    def find_by_id(self, course_id: str) -> Optional[Dict]:
        return self.collection.find_one({"_id": course_id})

    def find_by_department(self, department: str) -> List[Dict]:
        return list(self.collection.find({"department": department}))

    def insert(self, course: Dict) -> str:
        if 'course_id' in course and '_id' not in course:
            course['_id'] = course['course_id']
            
        course['created_at'] = datetime.utcnow()
        course['updated_at'] = datetime.utcnow()
        self.collection.insert_one(course)
        return course['_id']

    def bulk_upsert(self, courses: List[Dict]) -> int:
        from pymongo import UpdateOne
        if not courses:
            return 0
            
        operations = []
        for course in courses:
            course_id = course.get('_id') or course.get('course_id') or course.get('number') # Handle 'number' common in course data
            if not course_id:
                continue
            
            course_copy = course.copy()
            course_copy['_id'] = course_id # standardize on _id
            course_copy['updated_at'] = datetime.utcnow()
            
            update_doc = course_copy.copy()
            del update_doc['_id']

            operations.append(UpdateOne(
                {"_id": course_id},
                {"$set": update_doc, "$setOnInsert": {"created_at": datetime.utcnow()}},
                upsert=True
            ))
            
        if operations:
            result = self.collection.bulk_write(operations)
            return result.upserted_count + result.modified_count
        return 0

    def count(self) -> int:
        return self.collection.count_documents({})
