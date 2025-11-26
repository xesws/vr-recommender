"""Relationship creation for knowledge graph"""

import json
import os
from typing import List, Dict, Union


class RelationshipCreator:
    """Creates relationships between nodes"""

    def __init__(self, connection):
        """
        Initialize relationship creator

        Args:
            connection: Neo4jConnection instance
        """
        self.conn = connection

    def create_course_skill_relations(self, mappings_source: Union[str, List[Dict]]):
        """
        Create TEACHES relationships between Course and Skill nodes

        Args:
            mappings_source: Path to course-skills mapping JSON file OR List of mappings
        """
        mappings = []
        if isinstance(mappings_source, str):
            print(f"\n[Relations] Loading course-skill mappings from {mappings_source}...")
            if not os.path.exists(mappings_source):
                raise FileNotFoundError(f"Course-skills mapping file not found: {mappings_source}")
            with open(mappings_source, 'r', encoding='utf-8') as f:
                mappings = json.load(f)
        else:
            print(f"\n[Relations] Loading course-skill mappings from memory/DB...")
            mappings = mappings_source

        print(f"  Processing {len(mappings)} course-skill mappings...")

        # Supports 'source_id' (JSON) or 'course_id' (MongoDB)
        cypher = """
        UNWIND $mappings AS m
        MATCH (c:Course {course_id: coalesce(m.source_id, m.course_id)})
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

    def create_app_skill_relations(self, mappings_source: Union[str, List[Dict]]):
        """
        Create DEVELOPS relationships between VRApp and Skill nodes

        Args:
            mappings_source: Path to app-skills mapping JSON file OR List of mappings
        """
        mappings = []
        if isinstance(mappings_source, str):
            print(f"\n[Relations] Loading app-skill mappings from {mappings_source}...")
            if not os.path.exists(mappings_source):
                raise FileNotFoundError(f"App-skills mapping file not found: {mappings_source}")
            with open(mappings_source, 'r', encoding='utf-8') as f:
                mappings = json.load(f)
        else:
            print(f"\n[Relations] Loading app-skill mappings from memory/DB...")
            mappings = mappings_source

        print(f"  Processing {len(mappings)} app-skill mappings...")

        # Supports 'source_id' (JSON) or 'app_id' (MongoDB)
        cypher = """
        UNWIND $mappings AS m
        MATCH (a:VRApp {app_id: coalesce(m.source_id, m.app_id)})
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
        """
        print(f"\n[Relations] Skipping direct RECOMMENDATION creation (Architecture Fix).")
        print(f"  System will rely on indirect (Course)->(Skill)<-(App) paths.")

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
