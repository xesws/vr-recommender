"""
MongoDB connection management with connection pooling.
Supports local MongoDB and AWS DocumentDB.
"""
import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv

# Load env explicitly to ensure it's available when imported
load_dotenv()

class MongoConnection:
    _instance = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._client is None:
            self._connect()

    def _connect(self):
        uri = os.getenv("MONGODB_URI")
        db_name = os.getenv("MONGODB_DB", "vr_recommender")

        if not uri:
             print("⚠ Warning: MONGODB_URI not found in env, defaulting to localhost")
             uri = "mongodb://localhost:27017/"

        # Connection options for production
        self._client = MongoClient(
            uri,
            maxPoolSize=50,
            minPoolSize=10,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000
        )
        
        # If URI has a database name in it (standard for some providers), pymongo uses it by default if get_default_database is called.
        # However, we want to be explicit.
        # For Atlas, the db name in URI is 'test' by default unless specified.
        # We will stick to our named DB 'vr_recommender' unless the URI forces one.
        
        self.db = self._client[db_name]

        # Test connection (lazy)
        try:
            # The ismaster command is cheap and does not require auth.
            self._client.admin.command('ismaster')
            print(f"✓ Connected to MongoDB: {db_name}")
        except ConnectionFailure as e:
            print(f"⚠ MongoDB connection failed: {e}")
            
    def get_collection(self, name: str):
        return self.db[name]

    def close(self):
        if self._client:
            self._client.close()

# Global instance
mongo = MongoConnection()