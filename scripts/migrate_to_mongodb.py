"""
Migration script: JSON files + SQLite -> MongoDB
Run once to migrate all existing data.
"""
import json
import sqlite3
from pathlib import Path
import sys
import os
from dotenv import load_dotenv

# Add project root to path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

# Load environment variables from .env file explicitly
load_dotenv(os.path.join(project_root, ".env"))

# Re-import repositories after loading env to ensure MongoConnection picks it up
from src.db.repositories import (
    VRAppsRepository,
    CoursesRepository,
    SkillsRepository,
    InteractionLogsRepository,
    CourseSkillsRepository,
    AppSkillsRepository
)

DATA_DIR = Path(project_root) / "data_collection" / "data"
SQLITE_DB = Path(project_root) / "vr_recommender.db"

def migrate_vr_apps():
    print("Migrating VR Apps...")
    repo = VRAppsRepository()
    json_path = DATA_DIR / "vr_apps.json"
    if json_path.exists():
        try:
            with open(json_path) as f:
                apps = json.load(f)
            if isinstance(apps, list):
                count = repo.bulk_upsert(apps)
                print(f"  ✓ Migrated {count} VR apps")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    else:
        print(f"  ⚠ Warning: {json_path} not found")

def migrate_courses():
    print("Migrating Courses...")
    repo = CoursesRepository()
    json_path = DATA_DIR / "courses.json"
    if json_path.exists():
        try:
            with open(json_path) as f:
                courses = json.load(f)
            if isinstance(courses, list):
                count = repo.bulk_upsert(courses)
                print(f"  ✓ Migrated {count} courses")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    else:
        print(f"  ⚠ Warning: {json_path} not found")

def migrate_skills():
    print("Migrating Skills...")
    repo = SkillsRepository()
    json_path = DATA_DIR / "skills.json"
    if json_path.exists():
        try:
            with open(json_path) as f:
                skills = json.load(f)
            if isinstance(skills, list):
                count = repo.bulk_upsert(skills)
                print(f"  ✓ Migrated {count} skills")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    else:
        print(f"  ⚠ Warning: {json_path} not found")

def migrate_relations():
    print("Migrating Relations...")
    
    # Course-Skills
    repo_cs = CourseSkillsRepository()
    json_path = DATA_DIR / "course_skills.json"
    if json_path.exists():
        try:
            with open(json_path) as f:
                mappings = json.load(f)
            if isinstance(mappings, list):
                count = repo_cs.bulk_upsert(mappings)
                print(f"  ✓ Migrated {count} course-skill mappings")
        except Exception as e:
            print(f"  ❌ Error migrating course_skills: {e}")
    else:
        print(f"  ⚠ Warning: {json_path} not found")

    # App-Skills
    repo_as = AppSkillsRepository()
    json_path = DATA_DIR / "app_skills.json"
    if json_path.exists():
        try:
            with open(json_path) as f:
                mappings = json.load(f)
            if isinstance(mappings, list):
                count = repo_as.bulk_upsert(mappings)
                print(f"  ✓ Migrated {count} app-skill mappings")
        except Exception as e:
            print(f"  ❌ Error migrating app_skills: {e}")
    else:
        print(f"  ⚠ Warning: {json_path} not found")

def migrate_sqlite_logs():
    print("Migrating SQLite interaction logs...")
    if not SQLITE_DB.exists():
        print(f"  ⚠ Warning: {SQLITE_DB} not found, skipping logs")
        return

    repo = InteractionLogsRepository()
    try:
        conn = sqlite3.connect(SQLITE_DB)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='interaction_logs';")
        if not cursor.fetchone():
            print("  ⚠ SQLite table 'interaction_logs' not found.")
            conn.close()
            return

        cursor.execute("SELECT * FROM interaction_logs")
        rows = cursor.fetchall()

        count = 0
        for row in rows:
            try:
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
            except Exception:
                pass

        conn.close()
        print(f"  ✓ Migrated {count} interaction logs")
    except Exception as e:
        print(f"  ❌ Error reading SQLite DB: {e}")

def validate_migration():
    print("\nValidation Stats (MongoDB):")
    try:
        print(f"  VR Apps: {VRAppsRepository().count()}")
        print(f"  Courses: {CoursesRepository().count()}")
        print(f"  Skills: {SkillsRepository().count()}")
        print(f"  Course-Skills: {CourseSkillsRepository().count()}")
        print(f"  App-Skills: {AppSkillsRepository().count()}")
        print(f"  Logs: {InteractionLogsRepository().collection.count_documents({})}")
    except Exception as e:
        print(f"  ❌ Validation failed: {e}")

if __name__ == "__main__":
    print("=" * 50)
    print("Starting MongoDB Migration...")
    print("=" * 50)

    migrate_vr_apps()
    migrate_courses()
    migrate_skills()
    migrate_relations()
    migrate_sqlite_logs()

    validate_migration()

    print("\nMigration script finished.")