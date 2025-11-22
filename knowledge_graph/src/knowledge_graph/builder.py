"""Knowledge graph builder pipeline"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from stage3.src.knowledge_graph.connection import Neo4jConnection
from stage3.src.knowledge_graph.schema import KnowledgeGraphSchema
from stage3.src.knowledge_graph.nodes import NodeCreator
from stage3.src.knowledge_graph.relationships import RelationshipCreator


class KnowledgeGraphBuilder:
    """Main orchestrator for building the knowledge graph"""

    def __init__(self):
        """Initialize the builder with all components"""
        print("="*60)
        print("KNOWLEDGE GRAPH BUILDER")
        print("="*60)

        try:
            self.conn = Neo4jConnection()
            self.schema = KnowledgeGraphSchema(self.conn)
            self.nodes = NodeCreator(self.conn)
            self.relations = RelationshipCreator(self.conn)
        except Exception as e:
            print(f"\n✗ Failed to initialize: {e}")
            raise

    def build(self, data_dir: str = "stage1/data", clear: bool = False, min_shared_skills: int = 1):
        """
        Build the complete knowledge graph

        Args:
            data_dir: Directory containing JSON data files
            clear: Whether to clear existing data
            min_shared_skills: Minimum shared skills for recommendations
        """
        print("\n" + "="*60)
        print("BUILDING KNOWLEDGE GRAPH")
        print("="*60)

        try:
            # Clear database if requested
            if clear:
                self.schema.clear_database()

            # 1. Initialize schema (constraints and indexes)
            print("\n[1/4] Initializing schema...")
            self.schema.init_constraints()
            self.schema.init_indexes()

            # 2. Create nodes
            print("\n[2/4] Creating nodes...")
            self.nodes.create_courses(f"{data_dir}/courses.json")
            self.nodes.create_apps(f"{data_dir}/vr_apps.json")
            self.nodes.create_skills(f"{data_dir}/skills.json")

            # 3. Create relationships
            print("\n[3/4] Creating relationships...")
            self.relations.create_course_skill_relations(f"{data_dir}/course_skills.json")
            self.relations.create_app_skill_relations(f"{data_dir}/app_skills.json")

            # 4. Compute recommendations
            print("\n[4/4] Computing recommendations...")
            self.relations.compute_recommendations(min_shared_skills)

            # 5. Print statistics
            self._print_stats()

            print("\n" + "="*60)
            print("BUILD COMPLETE")
            print("="*60)

        except Exception as e:
            print(f"\n✗ Build failed: {e}")
            raise
        finally:
            self.cleanup()

    def _print_stats(self):
        """Print comprehensive knowledge graph statistics"""
        print("\n" + "="*60)
        print("KNOWLEDGE GRAPH STATISTICS")
        print("="*60)

        # Node counts
        node_counts = self.nodes.get_node_counts()
        print("\n📊 Nodes:")
        print(f"   Courses: {node_counts.get('courses', 0)}")
        print(f"   VR Apps: {node_counts.get('apps', 0)}")
        print(f"   Skills: {node_counts.get('skills', 0)}")
        total_nodes = sum(node_counts.values())
        print(f"   Total: {total_nodes}")

        # Relationship counts
        rel_counts = self.relations.get_relationship_counts()
        print("\n🔗 Relationships:")
        print(f"   TEACHES: {rel_counts.get('teaches', 0)}")
        print(f"   DEVELOPS: {rel_counts.get('develops', 0)}")
        print(f"   RECOMMENDS: {rel_counts.get('recommends', 0)}")
        total_rels = sum(rel_counts.values())
        print(f"   Total: {total_rels}")

        # Additional insights
        print("\n💡 Insights:")

        # Top skills by source count
        result = self.conn.query("""
            MATCH (s:Skill)
            RETURN s.name as name, s.source_count as count, s.category as category
            ORDER BY s.source_count DESC
            LIMIT 5
        """)
        if result:
            print("   Top 5 skills by mentions:")
            for i, record in enumerate(result, 1):
                print(f"      {i}. {record['name']} ({record['category']}): {record['count']} mentions")

        # Courses with most skills
        result = self.conn.query("""
            MATCH (c:Course)-[r:TEACHES]->(s:Skill)
            WITH c, count(s) as skill_count
            RETURN c.title as title, skill_count
            ORDER BY skill_count DESC
            LIMIT 5
        """)
        if result:
            print("\n   Courses teaching most skills:")
            for i, record in enumerate(result, 1):
                print(f"      {i}. {record['title']}: {record['skill_count']} skills")

        # Top VR apps by skills
        result = self.conn.query("""
            MATCH (a:VRApp)-[r:DEVELOPS]->(s:Skill)
            WITH a, count(s) as skill_count
            RETURN a.name as name, skill_count
            ORDER BY skill_count DESC
            LIMIT 5
        """)
        if result:
            print("\n   VR apps developing most skills:")
            for i, record in enumerate(result, 1):
                print(f"      {i}. {record['name']}: {record['skill_count']} skills")

        # Course-VR app recommendations
        result = self.conn.query("""
            MATCH (c:Course)-[r:RECOMMENDS]->(a:VRApp)
            RETURN count(*) as total_recommendations,
                   avg(r.skill_count) as avg_shared_skills,
                   max(r.skill_count) as max_shared_skills
        """)
        if result and result[0]['total_recommendations'] > 0:
            r = result[0]
            print(f"\n   Total course-app recommendations: {r['total_recommendations']}")
            print(f"   Average shared skills per recommendation: {r['avg_shared_skills']:.1f}")
            print(f"   Maximum shared skills: {r['max_shared_skills']}")

    def cleanup(self):
        """Clean up resources"""
        if hasattr(self, 'conn'):
            self.conn.close()

    def query(self, cypher: str, params: dict = None):
        """
        Execute a custom query

        Args:
            cypher: Cypher query
            params: Query parameters

        Returns:
            Query results
        """
        return self.conn.query(cypher, params)

    def test_build(self, data_dir: str = "stage1/data"):
        """
        Test the build process with a small dataset

        Args:
            data_dir: Directory containing JSON data files
        """
        print("\n🧪 TEST BUILD")
        print("="*60)

        # Check data files exist
        required_files = [
            f"{data_dir}/courses.json",
            f"{data_dir}/vr_apps.json",
            f"{data_dir}/skills.json",
            f"{data_dir}/course_skills.json",
            f"{data_dir}/app_skills.json"
        ]

        for file_path in required_files:
            if not os.path.exists(file_path):
                print(f"✗ Missing required file: {file_path}")
                return False

        print("✓ All required data files present")

        # Test Neo4j connection
        if not self.conn.test_connection():
            print("✗ Neo4j connection test failed")
            return False

        print("✓ Neo4j connection successful")

        # Test basic query
        try:
            result = self.conn.query("RETURN 'Connection test successful' as message")
            print(f"✓ {result[0]['message']}")
        except Exception as e:
            print(f"✗ Query test failed: {e}")
            return False

        print("\n✓ All tests passed")
        return True
