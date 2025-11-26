"""Knowledge graph builder pipeline"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from knowledge_graph.connection import Neo4jConnection
from knowledge_graph.schema import KnowledgeGraphSchema
from knowledge_graph.nodes import NodeCreator
from knowledge_graph.relationships import RelationshipCreator

# Try to import Repositories (fails if dependencies not installed)
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
    print("⚠ MongoDB repositories not found. Falling back to JSON files only.")


class KnowledgeGraphBuilder:
    """Main orchestrator for building the knowledge graph"""

    def __init__(self, logger=None):
        """Initialize the builder with all components"""
        self.logger = logger if logger else print
        self.logger("="*60)
        self.logger("KNOWLEDGE GRAPH BUILDER")
        self.logger("="*60)

        try:
            self.conn = Neo4jConnection()
            self.schema = KnowledgeGraphSchema(self.conn)
            self.nodes = NodeCreator(self.conn)
            self.relations = RelationshipCreator(self.conn)
        except Exception as e:
            self.logger(f"\n✗ Failed to initialize: {e}")
            raise

    def build(self, data_dir: str = "stage1/data", clear: bool = False, min_shared_skills: int = 1):
        """
        Build the complete knowledge graph

        Args:
            data_dir: Directory containing JSON data files (fallback)
            clear: Whether to clear existing data
            min_shared_skills: Minimum shared skills for recommendations
        """
        self.logger("\n" + "="*60)
        self.logger("BUILDING KNOWLEDGE GRAPH")
        self.logger("="*60)

        try:
            # Clear database if requested
            if clear:
                self.logger("[WARN] Clearing database...")
                self.schema.clear_database()

            # 1. Initialize schema (constraints and indexes)
            self.logger("\n[1/4] Initializing schema...")
            self.schema.init_constraints()
            self.schema.init_indexes()

            # Load Data Strategy: Try MongoDB first, then JSON
            courses, apps, skills = [], [], []
            course_skills, app_skills = [], []
            
            data_loaded_from_mongo = False

            if MONGO_AVAILABLE:
                try:
                    self.logger("\n[Data Load] Attempting to load from MongoDB...")
                    courses = CoursesRepository().find_all()
                    apps = VRAppsRepository().find_all()
                    skills = SkillsRepository().find_all()
                    course_skills = CourseSkillsRepository().find_all()
                    app_skills = AppSkillsRepository().find_all()
                    
                    if courses and apps:
                        data_loaded_from_mongo = True
                        self.logger(f"✓ Loaded from MongoDB: {len(courses)} courses, {len(apps)} apps, {len(skills)} skills")
                    else:
                        self.logger("⚠ MongoDB returned empty data. Falling back to JSON.")
                except Exception as e:
                    self.logger(f"⚠ MongoDB load failed: {e}. Falling back to JSON.")

            # Fallback to JSON if needed
            if not data_loaded_from_mongo:
                self.logger(f"\n[Data Load] Loading from JSON files in {data_dir}...")
                # We pass the file paths to Creators, which support both paths and lists
                # But to keep logic uniform, let's stick to passing data if possible, 
                # or let Creators handle paths if data is empty.
                # Ideally, we just pass what we have.
                
                # If we are here, courses/apps are empty or None. 
                # We will pass the file paths string to the creators.
                courses = f"{data_dir}/courses.json"
                apps = f"{data_dir}/vr_apps.json"
                skills = f"{data_dir}/skills.json"
                course_skills = f"{data_dir}/course_skills.json"
                app_skills = f"{data_dir}/app_skills.json"

            # 2. Create nodes
            self.logger("\n[2/4] Creating nodes...")
            self.nodes.create_courses(courses)
            self.nodes.create_apps(apps)
            self.nodes.create_skills(skills)

            # 3. Create relationships
            self.logger("\n[3/4] Creating relationships...")
            self.relations.create_course_skill_relations(course_skills)
            self.relations.create_app_skill_relations(app_skills)

            # 4. Compute recommendations
            self.logger(f"\n[4/4] Computing recommendations (min_shared_skills={min_shared_skills})...")
            self.relations.compute_recommendations(min_shared_skills)

            # 5. Print statistics
            self._print_stats()

            self.logger("\n" + "="*60)
            self.logger("BUILD COMPLETE")
            self.logger("="*60)

        except Exception as e:
            self.logger(f"\n✗ Build failed: {e}")
            raise
        finally:
            self.cleanup()

    def _print_stats(self):
        """Print comprehensive knowledge graph statistics"""
        self.logger("\n" + "="*60)
        self.logger("KNOWLEDGE GRAPH STATISTICS")
        self.logger("="*60)

        # Node counts
        node_counts = self.nodes.get_node_counts()
        self.logger("\n📊 Nodes:")
        self.logger(f"   Courses: {node_counts.get('courses', 0)}")
        self.logger(f"   VR Apps: {node_counts.get('apps', 0)}")
        self.logger(f"   Skills: {node_counts.get('skills', 0)}")
        total_nodes = sum(node_counts.values())
        self.logger(f"   Total: {total_nodes}")

        # Relationship counts
        rel_counts = self.relations.get_relationship_counts()
        self.logger("\n🔗 Relationships:")
        self.logger(f"   TEACHES: {rel_counts.get('teaches', 0)}")
        self.logger(f"   DEVELOPS: {rel_counts.get('develops', 0)}")
        self.logger(f"   RECOMMENDS: {rel_counts.get('recommends', 0)}")
        total_rels = sum(rel_counts.values())
        self.logger(f"   Total: {total_rels}")

        # Additional insights
        self.logger("\n💡 Insights:")

        try:
            # Top skills by source count
            result = self.conn.query("""
                MATCH (s:Skill)
                RETURN s.name as name, s.source_count as count, s.category as category
                ORDER BY s.source_count DESC
                LIMIT 5
            """ 
            )
            if result:
                self.logger("   Top 5 skills by mentions:")
                for i, record in enumerate(result, 1):
                    self.logger(f"      {i}. {record['name']} ({record['category']}): {record['count']} mentions")

            # Courses with most skills
            result = self.conn.query("""
                MATCH (c:Course)-[r:TEACHES]->(s:Skill)
                WITH c, count(s) as skill_count
                RETURN c.title as title, skill_count
                ORDER BY skill_count DESC
                LIMIT 5
            """ 
            )
            if result:
                self.logger("\n   Courses teaching most skills:")
                for i, record in enumerate(result, 1):
                    self.logger(f"      {i}. {record['title']}: {record['skill_count']} skills")

            # Top VR apps by skills
            result = self.conn.query("""
                MATCH (a:VRApp)-[r:DEVELOPS]->(s:Skill)
                WITH a, count(s) as skill_count
                RETURN a.name as name, skill_count
                ORDER BY skill_count DESC
                LIMIT 5
            """ 
            )
            if result:
                self.logger("\n   VR apps developing most skills:")
                for i, record in enumerate(result, 1):
                    self.logger(f"      {i}. {record['name']}: {record['skill_count']} skills")

            # Course-VR app recommendations
            result = self.conn.query("""
                MATCH (c:Course)-[r:RECOMMENDS]->(a:VRApp)
                RETURN count(*) as total_recommendations,
                       avg(r.skill_count) as avg_shared_skills,
                       max(r.skill_count) as max_shared_skills
            """ 
            )
            if result and result[0]['total_recommendations'] > 0:
                r = result[0]
                self.logger(f"\n   Total course-app recommendations: {r['total_recommendations']}")
                self.logger(f"   Average shared skills per recommendation: {r['avg_shared_skills']:.1f}")
                self.logger(f"   Maximum shared skills: {r['max_shared_skills']}")
        except Exception as e:
            self.logger(f"\n⚠ Failed to generate some insights: {e}")

    def cleanup(self):
        """Clean up resources"""
        if hasattr(self, 'conn'):
            self.conn.close()

    def query(self, cypher: str, params: dict = None):
        """Execute a custom query"""
        return self.conn.query(cypher, params)