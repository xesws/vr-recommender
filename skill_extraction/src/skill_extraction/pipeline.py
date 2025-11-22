"""Skill extraction pipeline orchestrator"""

import json
import os
import sys
from typing import List, Dict, Tuple

# Add stage2/src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from stage2.src.skill_extraction.extractor import SkillExtractor
from stage2.src.skill_extraction.normalizer import SkillNormalizer
from stage2.src.skill_extraction.deduplicator import SkillDeduplicator
from src.models import Skill, SkillMapping


class SkillExtractionPipeline:
    """Orchestrates the skill extraction process"""

    def __init__(self):
        """Initialize pipeline components"""
        self.extractor = SkillExtractor()
        self.normalizer = SkillNormalizer()
        self.deduplicator = SkillDeduplicator(self.normalizer)

    def process_courses(self, courses_path: str, batch_size: int = 10, top_n: int = None) -> Tuple[List[Dict], List[SkillMapping]]:
        """
        Process all courses to extract skills

        Args:
            courses_path: Path to courses JSON file
            batch_size: Number of courses to process before progress update
            top_n: Process only top N courses (optional)

        Returns:
            Tuple of (raw_skills, course_skill_mappings)
        """
        print(f"Loading courses from {courses_path}...")

        if not os.path.exists(courses_path):
            raise FileNotFoundError(f"Courses file not found: {courses_path}")

        with open(courses_path, 'r', encoding='utf-8') as f:
            courses = json.load(f)

        # Filter out placeholder courses
        courses = [c for c in courses if c.get('description', '').strip() and 'not available' not in c.get('description', '')]

        # Apply top_n limit
        if top_n:
            courses = courses[:top_n]
            print(f"  Limited to top {top_n} courses")

        print(f"Processing {len(courses)} courses...")

        all_skills = []
        course_skill_mappings = []

        for idx, course in enumerate(courses, 1):
            # Create text from course title and description
            title = course.get('title', '')
            description = course.get('description', '')
            course_id = course.get('course_id', f'course_{idx}')
            text = f"{title}. {description}"

            # Extract skills with progress indicator
            print(f"  [{idx}/{len(courses)}] Extracting skills from: {course_id}")
            skills = self.extractor.extract_from_text(text, "course")

            # Store raw skills and mappings
            for skill in skills:
                all_skills.append(skill)
                course_skill_mappings.append(SkillMapping(
                    source_id=course_id,
                    source_type="course",
                    skill_name=self.normalizer.normalize(skill["name"]),
                    weight=skill.get("weight", 0.5)
                ))

            # Progress update
            if idx % batch_size == 0:
                print(f"  ✓ Completed {idx}/{len(courses)} courses...")

        print(f"✓ Completed processing {len(courses)} courses")
        print(f"  Extracted {len(all_skills)} skill instances")
        print(f"  Created {len(course_skill_mappings)} course-skill mappings")

        return all_skills, course_skill_mappings

    def process_apps(self, apps_path: str, batch_size: int = 10, top_n: int = None) -> Tuple[List[Dict], List[SkillMapping]]:
        """
        Process all VR apps to extract skills

        Args:
            apps_path: Path to VR apps JSON file
            batch_size: Number of apps to process before progress update
            top_n: Process only top N apps (optional)

        Returns:
            Tuple of (raw_skills, app_skill_mappings)
        """
        print(f"Loading VR apps from {apps_path}...")

        if not os.path.exists(apps_path):
            raise FileNotFoundError(f"VR apps file not found: {apps_path}")

        with open(apps_path, 'r', encoding='utf-8') as f:
            apps = json.load(f)

        # Apply top_n limit
        if top_n:
            apps = apps[:top_n]
            print(f"  Limited to top {top_n} apps")

        print(f"Processing {len(apps)} VR apps...")

        all_skills = []
        app_skill_mappings = []

        for idx, app in enumerate(apps, 1):
            # Create text from app name, description, and features
            name = app.get('name', '')
            description = app.get('description', '')
            features = ', '.join(app.get('features', []))
            app_id = app.get('app_id', f'app_{idx}')
            text = f"{name}. {description}. Features: {features}"

            # Extract skills with progress indicator
            print(f"  [{idx}/{len(apps)}] Extracting skills from: {app_id}")
            skills = self.extractor.extract_from_text(text, "app")

            # Store raw skills and mappings
            for skill in skills:
                all_skills.append(skill)
                app_skill_mappings.append(SkillMapping(
                    source_id=app_id,
                    source_type="app",
                    skill_name=self.normalizer.normalize(skill["name"]),
                    weight=skill.get("weight", 0.5)
                ))

            # Progress update
            if idx % batch_size == 0:
                print(f"  ✓ Completed {idx}/{len(apps)} apps...")

        print(f"✓ Completed processing {len(apps)} VR apps")
        print(f"  Extracted {len(all_skills)} skill instances")
        print(f"  Created {len(app_skill_mappings)} app-skill mappings")

        return all_skills, app_skill_mappings

    def run(self, courses_path: str, apps_path: str, output_dir: str, top_n: int = None) -> Tuple[List[Skill], List[SkillMapping], List[SkillMapping]]:
        """
        Run the complete skill extraction pipeline

        Args:
            courses_path: Path to courses JSON file
            apps_path: Path to VR apps JSON file
            output_dir: Directory to save output files
            top_n: Process only top N courses and apps (optional)

        Returns:
            Tuple of (unique_skills, course_mappings, app_mappings)
        """
        print("="*60)
        print("STAGE 2: SKILL EXTRACTION PIPELINE")
        print("="*60)

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Show top_n info
        if top_n:
            print(f"\n[CONFIG] Processing top {top_n} courses and {top_n} VR apps")
        else:
            print(f"\n[CONFIG] Processing all courses and VR apps")

        # Process courses
        print("\n[1/2] Processing courses...")
        course_skills_raw, course_mappings = self.process_courses(courses_path, top_n=top_n)

        # Process VR apps
        print("\n[2/2] Processing VR apps...")
        app_skills_raw, app_mappings = self.process_apps(apps_path, top_n=top_n)

        # Merge and deduplicate skills
        print("\n[Deduplication] Merging and deduplicating skills...")
        all_skills_raw = course_skills_raw + app_skills_raw
        unique_skills = self.deduplicator.deduplicate(all_skills_raw)

        print(f"✓ Deduplication complete:")
        print(f"  Input: {len(all_skills_raw)} skill instances")
        print(f"  Output: {len(unique_skills)} unique skills")

        # Save results
        print(f"\n[Saving] Saving results to {output_dir}...")

        # Save skills
        skills_data = [
            {
                "name": s.name,
                "aliases": s.aliases,
                "category": s.category,
                "source_count": s.source_count,
                "weight": s.weight
            }
            for s in unique_skills
        ]

        with open(f"{output_dir}/skills.json", 'w', encoding='utf-8') as f:
            json.dump(skills_data, f, indent=2, ensure_ascii=False)

        # Save course mappings
        course_mappings_data = [
            {
                "source_id": m.source_id,
                "source_type": m.source_type,
                "skill_name": m.skill_name,
                "weight": m.weight
            }
            for m in course_mappings
        ]

        with open(f"{output_dir}/course_skills.json", 'w', encoding='utf-8') as f:
            json.dump(course_mappings_data, f, indent=2, ensure_ascii=False)

        # Save app mappings
        app_mappings_data = [
            {
                "source_id": m.source_id,
                "source_type": m.source_type,
                "skill_name": m.skill_name,
                "weight": m.weight
            }
            for m in app_mappings
        ]

        with open(f"{output_dir}/app_skills.json", 'w', encoding='utf-8') as f:
            json.dump(app_mappings_data, f, indent=2, ensure_ascii=False)

        print("\n" + "="*60)
        print("PIPELINE COMPLETE")
        print("="*60)
        print(f"✓ Extracted {len(unique_skills)} unique skills")
        print(f"✓ Created {len(course_mappings)} course-skill mappings")
        print(f"✓ Created {len(app_mappings)} app-skill mappings")
        print(f"✓ Files saved to: {output_dir}")

        return unique_skills, course_mappings, app_mappings
