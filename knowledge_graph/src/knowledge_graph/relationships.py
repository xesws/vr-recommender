"""Relationship creation for knowledge graph"""

import json
import os
from typing import List


class RelationshipCreator:
    """Creates relationships between nodes"""

    def __init__(self, connection):
        """
        Initialize relationship creator

        Args:
            connection: Neo4jConnection instance
        """
        self.conn = connection

    def create_course_skill_relations(self, course_skills_path: str):
        """
        Create TEACHES relationships between Course and Skill nodes

        Args:
            course_skills_path: Path to course-skills mapping JSON file
        """
        print(f"\n[Relations] Loading course-skill mappings from {course_skills_path}...")

        if not os.path.exists(course_skills_path):
            raise FileNotFoundError(f"Course-skills mapping file not found: {course_skills_path}")

        with open(course_skills_path, 'r', encoding='utf-8') as f:
            mappings = json.load(f)

        print(f"  Processing {len(mappings)} course-skill mappings...")

        cypher = """
        UNWIND $mappings AS m
        MATCH (c:Course {course_id: m.source_id})
        MATCH (s:Skill {name: m.skill_name})
        MERGE (c)-[r:TEACHES]->(s)
        SET r.weight = m.weight,
            r.created_at = timestamp()
        """

        try:
            self.conn.execute(cypher, {"mappings": mappings})

            # Count relationships created
            result = self.conn.query("MATCH ()-[r:TEACHES]->() RETURN count(r) as count")
            count = result[0]['count'] if result else 0
            print(f"✓ Created {count} TEACHES relationships")
        except Exception as e:
            print(f"✗ Failed to create TEACHES relationships: {e}")
            raise

    def create_app_skill_relations(self, app_skills_path: str):
        """
        Create DEVELOPS relationships between VRApp and Skill nodes

        Args:
            app_skills_path: Path to app-skills mapping JSON file
        """
        print(f"\n[Relations] Loading app-skill mappings from {app_skills_path}...")

        if not os.path.exists(app_skills_path):
            raise FileNotFoundError(f"App-skills mapping file not found: {app_skills_path}")

        with open(app_skills_path, 'r', encoding='utf-8') as f:
            mappings = json.load(f)

        print(f"  Processing {len(mappings)} app-skill mappings...")

        cypher = """
        UNWIND $mappings AS m
        MATCH (a:VRApp {app_id: m.source_id})
        MATCH (s:Skill {name: m.skill_name})
        MERGE (a)-[r:DEVELOPS]->(s)
        SET r.weight = m.weight,
            r.created_at = timestamp()
        """

        try:
            self.conn.execute(cypher, {"mappings": mappings})

            # Count relationships created
            result = self.conn.query("MATCH ()-[r:DEVELOPS]->() RETURN count(r) as count")
            count = result[0]['count'] if result else 0
            print(f"✓ Created {count} DEVELOPS relationships")
        except Exception as e:
            print(f"✗ Failed to create DEVELOPS relationships: {e}")
            raise

    def compute_recommendations(self, min_shared_skills: int = 1):
        """
        Compute RECOMMENDS relationships between Course and VRApp
        based on shared skills and their weights.
        
        NOTE: We are intentionally disabling the creation of direct :RECOMMENDS relationships
        to force the RAG system to traverse the skill nodes ((Course)-[:DEVELOPS]->(Skill)<-[:DEVELOPS]-(VRApp)).
        Direct links were causing the system to bypass the semantic layer.
        """
        print(f"\\n[Relations] Skipping direct RECOMMENDATION creation (Architecture Fix).")
        print(f"  System will rely on indirect (Course)->(Skill)<-(App) paths.")
        
        # cypher = """
        # MATCH (c:Course)-[t:TEACHES]->(s:Skill)<-[d:DEVELOPS]-(a:VRApp)
        # WITH c, a, collect(s.name) AS shared_skills,
        #      sum(t.weight * d.weight) AS score
        # WHERE size(shared_skills) >= $min_shared
        # MERGE (c)-[r:RECOMMENDS]->(a)
        # SET r.score = score,
        #     r.shared_skills = shared_skills,
        #     r.skill_count = size(shared_skills),
        #     r.created_at = timestamp()
        # """

        # try:
        #     self.conn.execute(cypher, {"min_shared": min_shared_skills})

        #     # Count relationships created
        #     result = self.conn.query("MATCH ()-[r:RECOMMENDS]->() RETURN count(r) as count")
        #     count = result[0]['count'] if result else 0
        #     print(f"✓ Computed {count} RECOMMENDS relationships")
        # except Exception as e:
        #     print(f"✗ Failed to compute RECOMMENDS relationships: {e}")
        #     raise

    def get_relationship_counts(self) -> dict:
        """
        Get counts of all relationship types

        Returns:
            Dictionary with relationship type counts
        """
        counts = {}

        try:
            result = self.conn.query("MATCH ()-[r:TEACHES]->() RETURN count(r) as count")
            counts['teaches'] = result[0]['count'] if result else 0

            result = self.conn.query("MATCH ()-[r:DEVELOPS]->() RETURN count(r) as count")
            counts['develops'] = result[0]['count'] if result else 0

            result = self.conn.query("MATCH ()-[r:RECOMMENDS]->() RETURN count(r) as count")
            counts['recommends'] = result[0]['count'] if result else 0

            return counts
        except Exception as e:
            print(f"Error getting relationship counts: {e}")
            return {}

    def clear_relationships(self):
        """Clear all relationships (keep nodes)"""
        print("\n[Relations] Clearing all relationships...")
        try:
            self.conn.execute("MATCH ()-[r]->() DELETE r")
            print("✓ All relationships cleared")
        except Exception as e:
            print(f"✗ Failed to clear relationships: {e}")
            raise
