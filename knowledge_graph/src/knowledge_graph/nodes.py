"""Node creation for Course, VRApp, and Skill entities"""

import json
import os
from typing import List, Dict


class NodeCreator:
    """Creates nodes in the knowledge graph"""

    def __init__(self, connection):
        """
        Initialize node creator

        Args:
            connection: Neo4jConnection instance
        """
        self.conn = connection

    def create_courses(self, courses_path: str):
        """
        Create Course nodes from JSON file

        Args:
            courses_path: Path to courses JSON file
        """
        print(f"\n[Nodes] Loading courses from {courses_path}...")

        if not os.path.exists(courses_path):
            raise FileNotFoundError(f"Courses file not found: {courses_path}")

        with open(courses_path, 'r', encoding='utf-8') as f:
            courses = json.load(f)

        # Filter out placeholder courses
        courses = [
            c for c in courses
            if c.get('description', '').strip() and 'not available' not in c.get('description', '')
        ]

        print(f"  Processing {len(courses)} courses...")

        cypher = """
        UNWIND $courses AS course
        MERGE (c:Course {course_id: course.course_id})
        SET c.title = course.title,
            c.department = course.department,
            c.description = course.description,
            c.units = course.units,
            c.created_at = timestamp()
        """

        try:
            self.conn.execute(cypher, {"courses": courses})
            print(f"✓ Created {len(courses)} Course nodes")
        except Exception as e:
            print(f"✗ Failed to create Course nodes: {e}")
            raise

    def create_apps(self, apps_path: str):
        """
        Create VRApp nodes from JSON file

        Args:
            apps_path: Path to VR apps JSON file
        """
        print(f"\n[Nodes] Loading VR apps from {apps_path}...")

        if not os.path.exists(apps_path):
            raise FileNotFoundError(f"VR apps file not found: {apps_path}")

        with open(apps_path, 'r', encoding='utf-8') as f:
            apps = json.load(f)

        print(f"  Processing {len(apps)} VR apps...")

        cypher = """
        UNWIND $apps AS app
        MERGE (a:VRApp {app_id: app.app_id})
        SET a.name = app.name,
            a.category = app.category,
            a.description = app.description,
            a.rating = app.rating,
            a.price = app.price,
            a.features = app.features,
            a.created_at = timestamp()
        """

        try:
            self.conn.execute(cypher, {"apps": apps})
            print(f"✓ Created {len(apps)} VRApp nodes")
        except Exception as e:
            print(f"✗ Failed to create VRApp nodes: {e}")
            raise

    def create_skills(self, skills_path: str):
        """
        Create Skill nodes from JSON file

        Args:
            skills_path: Path to skills JSON file
        """
        print(f"\n[Nodes] Loading skills from {skills_path}...")

        if not os.path.exists(skills_path):
            raise FileNotFoundError(f"Skills file not found: {skills_path}")

        with open(skills_path, 'r', encoding='utf-8') as f:
            skills = json.load(f)

        print(f"  Processing {len(skills)} skills...")

        cypher = """
        UNWIND $skills AS skill
        MERGE (s:Skill {name: skill.name})
        SET s.category = skill.category,
            s.aliases = skill.aliases,
            s.source_count = skill.source_count,
            s.weight = skill.weight,
            s.created_at = timestamp()
        """

        try:
            self.conn.execute(cypher, {"skills": skills})
            print(f"✓ Created {len(skills)} Skill nodes")
        except Exception as e:
            print(f"✗ Failed to create Skill nodes: {e}")
            raise

    def get_node_counts(self) -> Dict[str, int]:
        """
        Get counts of all node types

        Returns:
            Dictionary with node type counts
        """
        counts = {}

        try:
            result = self.conn.query("MATCH (c:Course) RETURN count(c) as count")
            counts['courses'] = result[0]['count'] if result else 0

            result = self.conn.query("MATCH (a:VRApp) RETURN count(a) as count")
            counts['apps'] = result[0]['count'] if result else 0

            result = self.conn.query("MATCH (s:Skill) RETURN count(s) as count")
            counts['skills'] = result[0]['count'] if result else 0

            return counts
        except Exception as e:
            print(f"Error getting node counts: {e}")
            return {}
