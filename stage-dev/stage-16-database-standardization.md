# Stage 16: Database Standardization (MongoDB Migration)

## Overview

Migrate all data storage from JSON files and SQLite to MongoDB, establishing a unified data access layer for production deployment.

**Status**: Planned
**Priority**: High
**Estimated Duration**: 1-2 weeks

---

## Current Problems

| Data Type | Current Storage | Problem |
|-----------|----------------|---------|
| Interaction Logs | SQLite (`vr_recommender.db`) | Not suitable for high concurrency |
| VR Apps | JSON (`data_collection/data/vr_apps.json`) | No persistence, no query capability |
| Courses | JSON (`data_collection/data/courses.json`) | No persistence |
| Skills | JSON (`data_collection/data/skills.json`) | No persistence |
| Course-Skills | JSON (`data_collection/data/course_skills.json`) | No persistence |
| App-Skills | JSON (`data_collection/data/app_skills.json`) | No persistence |
| Chat Sessions | JSON files (`chat_logs/`) | Not enabled, unreliable |

---

## Target Architecture

```
MongoDB (vr_recommender database)
├── vr_apps          # VR application data
├── courses          # CMU course data
├── skills           # Skill definitions
├── course_skills    # Course-Skill mappings
├── app_skills       # App-Skill mappings
├── interaction_logs # User interaction logs (from SQLite)
├── chat_sessions    # Chat history persistence
└── audit_logs       # Admin action logs (Stage 18)
```

---

## MongoDB Data Models

### Collection: `vr_apps`
```javascript
{
  _id: "InMind",  // app_id as primary key
  name: "InMind",
  category: "education",  // education | training | productivity | fitness
  description: "Educational VR application for neuroscience learning...",
  features: ["Interactive learning", "3D visualizations"],
  skills_developed: ["Learning", "Neuroscience", "AI"],
  rating: 4.2,
  price: "$0-19.99",
  created_at: ISODate("2024-11-21T00:00:00Z"),
  updated_at: ISODate("2024-11-21T00:00:00Z")
}
```

### Collection: `courses`
```javascript
{
  _id: "08-200",  // course_id as primary key
  title: "Introduction to Data Science",
  department: "School of Computer Science",
  description: "This course provides an introduction to...",
  units: 12,
  prerequisites: ["08-100"],
  learning_outcomes: ["Understand data analysis", "Apply ML techniques"],
  created_at: ISODate("2024-11-21T00:00:00Z"),
  updated_at: ISODate("2024-11-21T00:00:00Z")
}
```

### Collection: `skills`
```javascript
{
  _id: ObjectId("..."),
  name: "Machine Learning",
  aliases: ["ML", "machine learning", "深度学习"],
  category: "technical",  // technical | soft | domain
  source_count: 5,  // Number of courses/apps teaching this skill
  weight: 0.85,
  created_at: ISODate("2024-11-21T00:00:00Z")
}
```

### Collection: `course_skills`
```javascript
{
  _id: ObjectId("..."),
  course_id: "08-200",
  skill_name: "Machine Learning",
  weight: 0.9
}
// Index: { course_id: 1 }, { skill_name: 1 }
```

### Collection: `app_skills`
```javascript
{
  _id: ObjectId("..."),
  app_id: "InMind",
  skill_name: "Machine Learning",
  weight: 0.8
}
// Index: { app_id: 1 }, { skill_name: 1 }
```

### Collection: `interaction_logs`
```javascript
{
  _id: ObjectId("..."),
  user_id: "uuid-string",
  session_id: "uuid-string",
  timestamp: ISODate("2024-11-21T10:30:00Z"),
  query_text: "I want to learn machine learning for public policy",
  intent: "machine_learning",
  response_text: "Here are some VR apps for learning ML...",
  recommended_apps: [
    { app_id: "InMind", score: 0.85, reason: "Direct match" },
    { app_id: "Virtual Desktop", score: 0.45, reason: "Bridged via Programming" }
  ],
  metadata: {
    retrieval_source: "direct",
    latency_ms: 1500,
    model: "gemini-2.0-flash"
  }
}
// Index: { user_id: 1 }, { timestamp: -1 }, { intent: 1 }
```

### Collection: `chat_sessions`
```javascript
{
  _id: "session-uuid",
  user_id: "user-uuid",
  messages: [
    { role: "user", content: "I want to learn ML", timestamp: ISODate("...") },
    { role: "assistant", content: "Here are recommendations...", timestamp: ISODate("...") }
  ],
  started_at: ISODate("2024-11-21T10:00:00Z"),
  ended_at: ISODate("2024-11-21T10:30:00Z"),
  message_count: 4
}
// Index: { user_id: 1 }, { started_at: -1 }
```

---

## Implementation Plan

### Task 1: Set Up MongoDB Connection Layer

**New File**: `src/db/mongo_connection.py`

```python
"""
MongoDB connection management with connection pooling.
Supports local MongoDB and AWS DocumentDB.
"""
import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

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
        uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
        db_name = os.getenv("MONGODB_DB", "vr_recommender")

        # Connection options for production
        self._client = MongoClient(
            uri,
            maxPoolSize=50,
            minPoolSize=10,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000
        )
        self.db = self._client[db_name]

        # Test connection
        try:
            self._client.admin.command('ping')
            print(f"Connected to MongoDB: {db_name}")
        except ConnectionFailure as e:
            print(f"MongoDB connection failed: {e}")
            raise

    def get_collection(self, name: str):
        return self.db[name]

    def close(self):
        if self._client:
            self._client.close()

# Global instance
mongo = MongoConnection()
```

### Task 2: Create Repository Layer

**New Directory**: `src/db/repositories/`

#### `src/db/repositories/__init__.py`
```python
from .vr_apps_repo import VRAppsRepository
from .courses_repo import CoursesRepository
from .skills_repo import SkillsRepository
from .logs_repo import InteractionLogsRepository
from .sessions_repo import ChatSessionsRepository

__all__ = [
    'VRAppsRepository',
    'CoursesRepository',
    'SkillsRepository',
    'InteractionLogsRepository',
    'ChatSessionsRepository'
]
```

#### `src/db/repositories/vr_apps_repo.py`
```python
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
        app['_id'] = app.pop('app_id', app.get('_id'))
        app['created_at'] = datetime.utcnow()
        app['updated_at'] = datetime.utcnow()
        self.collection.insert_one(app)
        return app['_id']

    def upsert(self, app: Dict) -> str:
        app_id = app.pop('app_id', app.get('_id'))
        app['updated_at'] = datetime.utcnow()
        self.collection.update_one(
            {"_id": app_id},
            {"$set": app, "$setOnInsert": {"created_at": datetime.utcnow()}},
            upsert=True
        )
        return app_id

    def bulk_upsert(self, apps: List[Dict]) -> int:
        from pymongo import UpdateOne
        operations = []
        for app in apps:
            app_id = app.pop('app_id', app.get('_id'))
            app['updated_at'] = datetime.utcnow()
            operations.append(UpdateOne(
                {"_id": app_id},
                {"$set": app, "$setOnInsert": {"created_at": datetime.utcnow()}},
                upsert=True
            ))
        if operations:
            result = self.collection.bulk_write(operations)
            return result.upserted_count + result.modified_count
        return 0

    def count(self) -> int:
        return self.collection.count_documents({})
```

#### `src/db/repositories/logs_repo.py`
```python
from datetime import datetime
from typing import List, Optional, Dict
from ..mongo_connection import mongo

class InteractionLogsRepository:
    def __init__(self):
        self.collection = mongo.get_collection('interaction_logs')
        self._ensure_indexes()

    def _ensure_indexes(self):
        self.collection.create_index("user_id")
        self.collection.create_index([("timestamp", -1)])
        self.collection.create_index("intent")

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
        result = list(self.collection.aggregate(pipeline))
        return result[0] if result else {}

    def get_popular_intents(self, limit: int = 10) -> List[Dict]:
        pipeline = [
            {"$group": {"_id": "$intent", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": limit}
        ]
        return list(self.collection.aggregate(pipeline))
```

### Task 3: Create Migration Scripts

**New File**: `scripts/migrate_to_mongodb.py`

```python
"""
Migration script: JSON files + SQLite -> MongoDB
Run once to migrate all existing data.
"""
import json
import sqlite3
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db.repositories import (
    VRAppsRepository,
    CoursesRepository,
    SkillsRepository,
    InteractionLogsRepository
)

DATA_DIR = Path(__file__).parent.parent / "data_collection" / "data"
SQLITE_DB = Path(__file__).parent.parent / "vr_recommender.db"

def migrate_vr_apps():
    print("Migrating VR Apps...")
    repo = VRAppsRepository()

    json_path = DATA_DIR / "vr_apps.json"
    if json_path.exists():
        with open(json_path) as f:
            apps = json.load(f)
        count = repo.bulk_upsert(apps)
        print(f"  Migrated {count} VR apps")
    else:
        print(f"  Warning: {json_path} not found")

def migrate_courses():
    print("Migrating Courses...")
    repo = CoursesRepository()

    json_path = DATA_DIR / "courses.json"
    if json_path.exists():
        with open(json_path) as f:
            courses = json.load(f)
        count = repo.bulk_upsert(courses)
        print(f"  Migrated {count} courses")

def migrate_skills():
    print("Migrating Skills...")
    repo = SkillsRepository()

    json_path = DATA_DIR / "skills.json"
    if json_path.exists():
        with open(json_path) as f:
            skills = json.load(f)
        count = repo.bulk_upsert(skills)
        print(f"  Migrated {count} skills")

def migrate_sqlite_logs():
    print("Migrating SQLite interaction logs...")

    if not SQLITE_DB.exists():
        print(f"  Warning: {SQLITE_DB} not found, skipping")
        return

    repo = InteractionLogsRepository()
    conn = sqlite3.connect(SQLITE_DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM interaction_logs")
    rows = cursor.fetchall()

    count = 0
    for row in rows:
        log = {
            "user_id": row["user_id"],
            "session_id": row["session_id"],
            "timestamp": row["timestamp"],
            "query_text": row["query_text"],
            "intent": row["intent"],
            "response_text": row["response_text"],
            "recommended_apps": json.loads(row["recommended_apps"] or "[]"),
            "metadata": json.loads(row["metadata"] or "{}")
        }
        repo.insert(log)
        count += 1

    conn.close()
    print(f"  Migrated {count} interaction logs")

def validate_migration():
    print("\nValidation:")
    print(f"  VR Apps: {VRAppsRepository().count()}")
    print(f"  Courses: {CoursesRepository().count()}")
    print(f"  Skills: {SkillsRepository().count()}")
    print(f"  Interaction Logs: {InteractionLogsRepository().collection.count_documents({})}")

if __name__ == "__main__":
    print("=" * 50)
    print("MongoDB Migration Script")
    print("=" * 50)

    migrate_vr_apps()
    migrate_courses()
    migrate_skills()
    migrate_sqlite_logs()

    validate_migration()

    print("\nMigration complete!")
```

### Task 4: Modify Existing Files

#### Update `src/database.py`

Replace SQLite with MongoDB:

```python
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
            self.mongo._client.admin.command('ping')
            return True
        except:
            return False

# Backward compatibility
db = Database()
```

#### Update `src/logging_service.py`

```python
"""
Interaction logging service - MongoDB implementation.
"""
from datetime import datetime
from typing import List, Dict, Optional
from src.db.repositories.logs_repo import InteractionLogsRepository

class InteractionLogger:
    def __init__(self):
        self.repo = InteractionLogsRepository()

    def log_interaction(
        self,
        user_id: str,
        session_id: str,
        query_text: str,
        intent: str,
        response_text: str,
        recommended_apps: List[Dict],
        metadata: Dict = None
    ) -> str:
        log = {
            "user_id": user_id,
            "session_id": session_id,
            "query_text": query_text,
            "intent": intent,
            "response_text": response_text,
            "recommended_apps": recommended_apps,
            "metadata": metadata or {}
        }
        return self.repo.insert(log)

    def get_recent_logs(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        return self.repo.find_recent(limit, offset)

    def get_user_logs(self, user_id: str, limit: int = 50) -> List[Dict]:
        return self.repo.find_by_user(user_id, limit)

    def get_stats(self) -> Dict:
        return self.repo.get_stats()

    def get_popular_intents(self, limit: int = 10) -> List[Dict]:
        return self.repo.get_popular_intents(limit)
```

#### Update `src/chat/session.py`

```python
"""
Chat session management - MongoDB implementation.
"""
from datetime import datetime
from typing import List, Dict, Optional
from src.db.mongo_connection import mongo

class ChatSession:
    def __init__(self, session_id: str, user_id: str):
        self.session_id = session_id
        self.user_id = user_id
        self.collection = mongo.get_collection('chat_sessions')
        self._load_or_create()

    def _load_or_create(self):
        existing = self.collection.find_one({"_id": self.session_id})
        if existing:
            self.messages = existing.get('messages', [])
        else:
            self.messages = []
            self.collection.insert_one({
                "_id": self.session_id,
                "user_id": self.user_id,
                "messages": [],
                "started_at": datetime.utcnow(),
                "message_count": 0
            })

    def add_message(self, role: str, content: str):
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow()
        }
        self.messages.append(message)

        self.collection.update_one(
            {"_id": self.session_id},
            {
                "$push": {"messages": message},
                "$inc": {"message_count": 1},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )

    def get_context(self, max_messages: int = 10) -> List[Dict]:
        return self.messages[-max_messages:]

    def end_session(self):
        self.collection.update_one(
            {"_id": self.session_id},
            {"$set": {"ended_at": datetime.utcnow()}}
        )
```

### Task 5: Update Knowledge Graph Builder

Modify `knowledge_graph/src/knowledge_graph/builder.py` to read from MongoDB:

```python
# Add MongoDB data loading method
def load_data_from_mongodb(self):
    """Load courses and apps from MongoDB instead of JSON files."""
    from src.db.repositories import CoursesRepository, VRAppsRepository

    courses_repo = CoursesRepository()
    apps_repo = VRAppsRepository()

    self.courses = courses_repo.find_all()
    self.apps = apps_repo.find_all()

    print(f"Loaded {len(self.courses)} courses and {len(self.apps)} apps from MongoDB")
```

---

## Files to Create

| File | Purpose |
|------|---------|
| `src/db/__init__.py` | Package init |
| `src/db/mongo_connection.py` | MongoDB connection pool |
| `src/db/repositories/__init__.py` | Repository exports |
| `src/db/repositories/vr_apps_repo.py` | VR Apps CRUD |
| `src/db/repositories/courses_repo.py` | Courses CRUD |
| `src/db/repositories/skills_repo.py` | Skills CRUD |
| `src/db/repositories/logs_repo.py` | Interaction logs |
| `src/db/repositories/sessions_repo.py` | Chat sessions |
| `scripts/migrate_to_mongodb.py` | Data migration |
| `scripts/validate_mongodb.py` | Migration validation |

## Files to Modify

| File | Changes |
|------|---------|
| `src/database.py` | Replace SQLite with MongoDB |
| `src/logging_service.py` | Use logs_repo |
| `src/chat/session.py` | Persist to MongoDB |
| `src/data_manager.py` | Write to MongoDB after JSON |
| `knowledge_graph/.../builder.py` | Load from MongoDB |
| `requirements.txt` | Ensure pymongo is listed |

---

## Integration with Neo4j and ChromaDB

### Data Flow

```
MongoDB (Single Source of Truth)
     |
     | Sync triggered by data_manager.py
     |
     +-----> Neo4j (Graph: nodes + relationships)
     |       - Course nodes
     |       - VRApp nodes
     |       - Skill nodes
     |       - TEACHES, DEVELOPS relationships
     |
     +-----> ChromaDB (Vectors)
             - Skill embeddings only
```

### Sync Strategy

1. **On Data Update**: When `data_manager.py` saves to MongoDB, trigger sync
2. **Nightly Batch**: Full sync as backup
3. **One-Way Only**: MongoDB -> Neo4j/ChromaDB (never reverse)

---

## Environment Variables

```bash
# .env additions
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB=vr_recommender

# For AWS DocumentDB (production)
# MONGODB_URI=mongodb://user:pass@docdb-cluster.amazonaws.com:27017/?ssl=true&replicaSet=rs0&readPreference=secondaryPreferred
```

---

## Testing Checklist

- [ ] MongoDB connection works locally
- [ ] All repositories have working CRUD operations
- [ ] Migration script runs without errors
- [ ] Data counts match: JSON files vs MongoDB
- [ ] Interaction logging works via MongoDB
- [ ] Chat sessions persist across restarts
- [ ] RAG pipeline works with MongoDB data source
- [ ] Knowledge graph builder loads from MongoDB
- [ ] Admin dashboard displays MongoDB data
- [ ] No references to SQLite remain in active code

---

## Rollback Plan

1. Keep JSON files as backup for 30 days
2. Keep SQLite database file as backup
3. Feature flag to switch between storage backends:
   ```python
   USE_MONGODB = os.getenv("USE_MONGODB", "true").lower() == "true"
   ```
4. Rollback script to export MongoDB back to JSON if needed
