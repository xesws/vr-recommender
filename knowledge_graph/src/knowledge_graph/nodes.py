"""Node creation for Course, VRApp, and Skill entities"""

import json
import os
from typing import List, Dict, Union


class NodeCreator:
    """Creates nodes in the knowledge graph"""

    def __init__(self, connection):
        """
        Initialize node creator

        Args:
            connection: Neo4jConnection instance
        """
        self.conn = connection

    def create_courses(self, courses_source: Union[str, List[Dict]]):
        """
        Create Course nodes from JSON file or List of dicts

        Args:
            courses_source: Path to courses JSON file OR List of course dictionaries
        """
        courses = []
        if isinstance(courses_source, str):
            print(f"\n[Nodes] Loading courses from {courses_source}...")

            if not os.path.exists(courses_source):
                raise FileNotFoundError(f"Courses file not found: {courses_source}")

            with open(courses_source, 'r', encoding='utf-8') as f:
                courses = json.load(f)
        else:
            print(f"\n[Nodes] Loading courses from memory/DB...")
            courses = courses_source

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

    def create_apps(self, apps_source: Union[str, List[Dict]]):
        """
        Create VRApp nodes from JSON file or List of dicts

        Args:
            apps_source: Path to VR apps JSON file OR List of app dictionaries
        """
        apps = []
        if isinstance(apps_source, str):
            print(f"\n[Nodes] Loading VR apps from {apps_source}...")
            if not os.path.exists(apps_source):
                raise FileNotFoundError(f"VR apps file not found: {apps_source}")
            with open(apps_source, 'r', encoding='utf-8') as f:
                apps = json.load(f)
        else:
            print(f"\n[Nodes] Loading VR apps from memory/DB...")
            apps = apps_source

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

    def create_skills(self, skills_source: Union[str, List[Dict]]):
        """
        Create Skill nodes from JSON file or List of dicts

        Args:
            skills_source: Path to skills JSON file OR List of skill dictionaries
        """
        skills = []
        if isinstance(skills_source, str):
            print(f"\n[Nodes] Loading skills from {skills_source}...")
            if not os.path.exists(skills_source):
                raise FileNotFoundError(f"Skills file not found: {skills_source}")
            with open(skills_source, 'r', encoding='utf-8') as f:
                skills = json.load(f)
        else:
            print(f"\n[Nodes] Loading skills from memory/DB...")
            skills = skills_source

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