"""
Database module - MongoDB implementation.
Replaces previous SQLite implementation.
"""
from src.db.mongo_connection import MongoConnection

class Database:
    def __init__(self):
        self.mongo = MongoConnection()
        self.db = self.mongo.db

    def get_collection(self, name: str):
        return self.db[name]

    def test_connection(self) -> bool:
        try:
            self.mongo._client.admin.command('ismaster')
            return True
        except:
            return False

# Backward compatibility instance
db = Database()