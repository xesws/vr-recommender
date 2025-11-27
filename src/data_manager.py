import json
import os
import threading
import time
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor

# Import fetchers from their locations
import sys
# Add project root to path to allow imports from data_collection
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Add module source directories to path
sys.path.insert(0, os.path.join(project_root, "data_collection", "src"))
sys.path.insert(0, os.path.join(project_root, "skill_extraction", "src"))
sys.path.insert(0, os.path.join(project_root, "knowledge_graph", "src"))

if project_root not in sys.path:
    sys.path.insert(0, project_root)

from data_collection.course_fetcher_improved import CMUCourseFetcherImproved
from data_collection.vr_app_fetcher_improved import VRAppFetcherImproved
from skill_extraction.pipeline import SkillExtractionPipeline
from knowledge_graph.builder import KnowledgeGraphBuilder

from src.config_manager import ConfigManager

# Import DB Repositories
try:
    from src.db.repositories import (
        CoursesRepository,
        VRAppsRepository,
        SkillsRepository,
        CourseSkillsRepository,
        AppSkillsRepository
    )
    MONGO_AVAILABLE = True
except ImportError:
    MONGO_AVAILABLE = False

class JobManager:
    """Manages background data update jobs."""
    
    def __init__(self):
        self.current_job: Optional[Dict[str, Any]] = None
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.logs: List[str] = []
        self.log_lock = threading.Lock()
        
        # Define data paths
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = os.path.join(self.base_dir, "data_collection", "data")

    def get_data_stats(self) -> Dict[str, Any]:
        """Get stats about data files and DB."""
        stats = {
            "courses": self._get_file_info("courses.json"),
            "vr_apps": self._get_file_info("vr_apps.json"),
            "skills": self._get_file_info("skills.json")
        }
        
        if MONGO_AVAILABLE:
            try:
                stats["db_courses"] = CoursesRepository().count()
                stats["db_apps"] = VRAppsRepository().count()
                stats["db_skills"] = SkillsRepository().count()
            except:
                stats["db_status"] = "unavailable"
        
        # Add job status
        if self.current_job:
            stats["job"] = self.current_job
            with self.log_lock:
                # Return last 20 logs
                stats["job"]["logs"] = self.logs[-20:]
        
        return stats

    def _get_file_info(self, filename: str) -> Dict[str, Any]:
        """Get metadata for a JSON data file."""
        filepath = os.path.join(self.data_dir, filename)
        if not os.path.exists(filepath):
            return {"exists": False, "count": 0, "last_updated": None}
            
        try:
            stat = os.stat(filepath)
            last_updated = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            
            # Read count (lightweight check)
            with open(filepath, 'r') as f:
                data = json.load(f)
                count = len(data) if isinstance(data, list) else 0
                
            return {
                "exists": True,
                "count": count,
                "last_updated": last_updated,
                "size_kb": round(stat.st_size / 1024, 1)
            }
        except Exception as e:
            return {"exists": True, "error": str(e)}

    def start_update_job(self, job_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Start a background update job."""
        if self.current_job and self.current_job["status"] == "RUNNING":
            return {"error": "A job is already running", "job_id": self.current_job["id"]}
            
        job_id = str(uuid.uuid4())
        self.current_job = {
            "id": job_id,
            "type": job_type,
            "status": "RUNNING",
            "start_time": datetime.now().isoformat(),
            "params": params
        }
        
        # Reset logs
        with self.log_lock:
            self.logs = [f"Starting {job_type} update job (ID: {job_id})..."]
            
        # Submit to thread pool
        self.executor.submit(self._run_job, job_type, params)
        
        return {"success": True, "job_id": job_id}

    def _log(self, message: str):
        """Thread-safe logging."""
        with self.log_lock:
            timestamp = datetime.now().strftime('%H:%M:%S')
            self.logs.append(f"[{timestamp}] {message}")
            print(f"[Job] {message}") # Also print to console

    def _run_job(self, job_type: str, params: Dict[str, Any]):
        """Execute the job logic."""
        try:
            if job_type == "courses":
                self._update_courses(params)
            elif job_type == "vr_apps":
                self._update_vr_apps(params)
            elif job_type == "skills":
                self._extract_skills(params)
            elif job_type == "graph":
                self._build_graph(params)
            else:
                self._log(f"Unknown job type: {job_type}")
                
            self.current_job["status"] = "COMPLETED"
            self._log("Job completed successfully.")
            
        except Exception as e:
            self.current_job["status"] = "FAILED"
            self.current_job["error"] = str(e)
            self._log(f"❌ Job failed: {str(e)}")
            import traceback
            traceback.print_exc()

    def _extract_skills(self, params: Dict[str, Any]):
        """Run skill extraction pipeline."""
        top_n = params.get("top_n")
        self._log(f"Starting Skill Extraction (Top N: {top_n if top_n else 'ALL'})...")
        
        courses_path = os.path.join(self.data_dir, "courses.json")
        apps_path = os.path.join(self.data_dir, "vr_apps.json")
        
        try:
            # Inject logger
            pipeline = SkillExtractionPipeline(logger=self._log)
            
            self._log("Processing courses and apps...")
            pipeline.run(courses_path, apps_path, self.data_dir, top_n=top_n)
            
            self._log("Skill extraction complete. Results saved to JSON.")

            # Sync to MongoDB
            if MONGO_AVAILABLE:
                self._sync_skills_to_mongo()
            
        except Exception as e:
            raise e

    def _build_graph(self, params: Dict[str, Any]):
        """Run knowledge graph builder."""
        clear_db = params.get("clear", True)
        self._log(f"Starting Graph Build (Clear DB: {clear_db})...")
        
        try:
            # Inject logger
            builder = KnowledgeGraphBuilder(logger=self._log)
            
            self._log("Building graph in Neo4j...")
            # Builder now prefers MongoDB automatically
            builder.build(data_dir=self.data_dir, clear=clear_db)
            
            self._log("Graph build complete.")
            
        except Exception as e:
            raise e

    def _update_courses(self, params: Dict[str, Any]):
        """Update course data."""
        limit = params.get("limit", 100) # Default limit
        department = params.get("department")
        semester = params.get("semester", "f25")
        
        self._log(f"Initializing Course Fetcher (Limit: {limit}, Dept: {department}, Term: {semester})...")
        
        try:
            # Inject logger
            config = ConfigManager()
            fetcher = CMUCourseFetcherImproved(logger=self._log, api_key=config.firecrawl_api_key)
            
            # Use the fetcher
            self._log("Fetching courses from CMU catalog...")
            courses = fetcher.fetch_courses(
                max_courses=limit, 
                use_extracted_codes=True, 
                department=department,
                semester=semester
            )
            
            if not courses:
                self._log("⚠ No courses found.")
                return
                
            self._log(f"Fetched {len(courses)} courses.")
            
            # Save JSON
            save_path = os.path.join(self.data_dir, "courses.json")
            fetcher.save_courses(courses, path=save_path)
            self._log(f"Saved to {save_path}")

            # Sync to MongoDB
            if MONGO_AVAILABLE:
                self._log("Syncing courses to MongoDB...")
                count = CoursesRepository().bulk_upsert(courses)
                self._log(f"✓ Synced {count} courses to MongoDB")
            
        except Exception as e:
            raise e

    def _update_vr_apps(self, params: Dict[str, Any]):
        """Update VR App data."""
        categories = params.get("categories", ["education", "training", "productivity"])
        
        self._log(f"Initializing VR App Fetcher (Categories: {categories})...")
        
        try:
            config = ConfigManager()
            fetcher = VRAppFetcherImproved(api_key=config.tavily_api_key)
            
            self._log("Fetching VR apps via Tavily...")
            apps = fetcher.fetch_apps(categories=categories)
            
            if not apps:
                self._log("⚠ No apps found.")
                return
                
            self._log(f"Fetched {len(apps)} apps.")
            
            # Save JSON
            save_path = os.path.join(self.data_dir, "vr_apps.json")
            fetcher.save_apps(apps, path=save_path)
            self._log(f"Saved to {save_path}")

            # Sync to MongoDB
            if MONGO_AVAILABLE:
                self._log("Syncing VR apps to MongoDB...")
                count = VRAppsRepository().bulk_upsert(apps)
                self._log(f"✓ Synced {count} apps to MongoDB")
            
        except Exception as e:
            raise e

    def _sync_skills_to_mongo(self):
        """Helper to sync extracted skills and mappings to MongoDB."""
        self._log("Syncing skills and mappings to MongoDB...")
        
        # Load from JSON
        try:
            with open(os.path.join(self.data_dir, "skills.json")) as f:
                skills = json.load(f)
            with open(os.path.join(self.data_dir, "course_skills.json")) as f:
                c_skills = json.load(f)
            with open(os.path.join(self.data_dir, "app_skills.json")) as f:
                a_skills = json.load(f)

            # Write to Mongo
            s_count = SkillsRepository().bulk_upsert(skills)
            cs_count = CourseSkillsRepository().bulk_upsert(c_skills)
            as_count = AppSkillsRepository().bulk_upsert(a_skills)
            
            self._log(f"✓ MongoDB Sync: {s_count} skills, {cs_count} course-skills, {as_count} app-skills")
        except Exception as e:
            self._log(f"⚠ MongoDB Sync failed: {e}")