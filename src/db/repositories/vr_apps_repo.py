from datetime import datetime
from typing import List, Optional, Dict, Any
from ..mongo_connection import mongo

class VRAppsRepository:
    def __init__(self):
        self.collection = mongo.get_collection('vr_apps')

    def find_all(self) -> List[Dict]:
        return list(self.collection.find())

    def find_by_id(self, app_id: str) -> Optional[Dict]:
        return self.collection.find_one({"_id": app_id})

    def find_by_category(self, category: str) -> List[Dict]:
        return list(self.collection.find({"category": category}))

    def find_by_skill(self, skill_name: str) -> List[Dict]:
        return list(self.collection.find({"skills_developed": skill_name}))

    def insert(self, app: Dict) -> str:
        # Ensure _id is set (prefer app_id)
        if 'app_id' in app and '_id' not in app:
            app['_id'] = app['app_id']
        
        app['created_at'] = datetime.utcnow()
        app['updated_at'] = datetime.utcnow()
        self.collection.insert_one(app)
        return app['_id']

    def upsert(self, app: Dict) -> str:
        # Ensure _id is set
        app_id = app.get('_id') or app.get('app_id')
        if not app_id:
            # If no ID, we can't really upsert easily unless we generate one, 
            # but for apps we usually have a name or ID.
            raise ValueError("App must have _id or app_id for upsert")
            
        if '_id' not in app:
            app['_id'] = app_id
            
        app['updated_at'] = datetime.utcnow()
        
        # Use $set for update fields and $setOnInsert for creation fields
        update_doc = app.copy()
        if '_id' in update_doc:
            del update_doc['_id'] # Don't update _id
            
        self.collection.update_one(
            {"_id": app_id},
            {"$set": update_doc, "$setOnInsert": {"created_at": datetime.utcnow()}},
            upsert=True
        )
        return app_id

    def bulk_upsert(self, apps: List[Dict]) -> int:
        from pymongo import UpdateOne
        if not apps:
            return 0
            
        operations = []
        for app in apps:
            app_id = app.get('_id') or app.get('app_id')
            if not app_id:
                continue # Skip items without ID
            
            app_copy = app.copy()
            if '_id' not in app_copy:
                app_copy['_id'] = app_id
            
            app_copy['updated_at'] = datetime.utcnow()
            
            # Prepare doc for update (exclude _id)
            update_doc = app_copy.copy()
            del update_doc['_id']

            operations.append(UpdateOne(
                {"_id": app_id},
                {"$set": update_doc, "$setOnInsert": {"created_at": datetime.utcnow()}},
                upsert=True
            ))
            
        if operations:
            result = self.collection.bulk_write(operations)
            return result.upserted_count + result.modified_count
        return 0

    def count(self) -> int:
        return self.collection.count_documents({})
