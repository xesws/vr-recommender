"""Skill deduplication and merging logic"""

import sys
import os

# Add stage2/src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from typing import List, Dict
from src.models import Skill


class SkillDeduplicator:
    """Deduplicates and merges similar skills"""

    def __init__(self, normalizer):
        """
        Initialize with a SkillNormalizer instance

        Args:
            normalizer: SkillNormalizer instance
        """
        self.normalizer = normalizer

    def deduplicate(self, skills: List[Dict]) -> List[Skill]:
        """
        Merge similar skills into unique Skill objects

        Args:
            skills: List of skill dictionaries with name, category, weight

        Returns:
            List of unique Skill objects with merged data
        """
        merged = {}

        for skill in skills:
            if not isinstance(skill, dict) or "name" not in skill:
                continue

            name = self.normalizer.normalize(skill["name"])

            # Get normalized category
            category = skill.get("category", "technical")
            if not category or category not in ["technical", "soft", "domain"]:
                category = self.normalizer.get_category(name)

            weight = float(skill.get("weight", 0.5))

            if name in merged:
                # Merge with existing skill
                existing = merged[name]

                # Update count
                existing["source_count"] += 1

                # Update weight: keep the maximum weight (most important mention)
                existing["weight"] = max(existing["weight"], weight)

                # Add alias if different from normalized name
                original_name = skill["name"].strip()
                if original_name.lower() != name.lower():
                    if original_name not in existing["aliases"]:
                        existing["aliases"].append(original_name)

                # Ensure category consistency
                if category in ["technical", "soft", "domain"]:
                    existing["category"] = category
            else:
                # Create new merged skill
                merged[name] = {
                    "name": name,
                    "aliases": [],
                    "category": category,
                    "source_count": 1,
                    "weight": weight
                }

                # Add alias if different from normalized name
                original_name = skill["name"].strip()
                if original_name.lower() != name.lower():
                    merged[name]["aliases"].append(original_name)

        # Convert to Skill objects
        result = []
        for skill_data in merged.values():
            result.append(Skill(
                name=skill_data["name"],
                aliases=skill_data["aliases"],
                category=skill_data["category"],
                source_count=skill_data["source_count"],
                weight=skill_data["weight"]
            ))

        return result

    def merge_skill_lists(self, skill_lists: List[List[Dict]]) -> List[Skill]:
        """
        Merge multiple lists of skills into unique Skill objects

        Args:
            skill_lists: List of skill list dictionaries

        Returns:
            List of unique Skill objects
        """
        all_skills = []
        for skill_list in skill_lists:
            if isinstance(skill_list, list):
                all_skills.extend(skill_list)

        return self.deduplicate(all_skills)
