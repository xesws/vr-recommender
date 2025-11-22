#!/usr/bin/env python3
"""Main script to run skill extraction pipeline"""

import argparse
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from skill_extraction.src.skill_extraction.pipeline import SkillExtractionPipeline


def main():
    """Main entry point for skill extraction"""
    parser = argparse.ArgumentParser(
        description="Extract skills from courses and VR apps using LLM"
    )
    parser.add_argument(
        "--courses",
        default="data_collection/data/courses.json",
        help="Path to courses JSON file (default: data_collection/data/courses.json)"
    )
    parser.add_argument(
        "--apps",
        default="data_collection/data/vr_apps.json",
        help="Path to VR apps JSON file (default: data_collection/data/vr_apps.json)"
    )
    parser.add_argument(
        "--output-dir",
        default="data_collection/data",
        help="Output directory for results (default: data_collection/data)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Batch size for progress updates (default: 10)"
    )
    parser.add_argument(
        "--top",
        type=int,
        help="Process only top N courses and VR apps (default: all)"
    )

    args = parser.parse_args()

    try:
        # Run pipeline
        pipeline = SkillExtractionPipeline()
        skills, course_map, app_map = pipeline.run(
            args.courses,
            args.apps,
            args.output_dir,
            top_n=args.top
        )

        # Print summary
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print(f"✓ Extracted {len(skills)} unique skills")
        print(f"✓ Created {len(course_map)} course-skill mappings")
        print(f"✓ Created {len(app_map)} app-skill mappings")

        # Category breakdown
        category_counts = {}
        for skill in skills:
            cat = skill.category
            category_counts[cat] = category_counts.get(cat, 0) + 1

        print("\nCategory breakdown:")
        for category, count in sorted(category_counts.items()):
            print(f"  {category}: {count} skills")

        # Top skills
        top_skills = sorted(skills, key=lambda s: s.source_count, reverse=True)[:10]
        print("\nTop 10 most frequent skills:")
        for skill in top_skills:
            print(f"  {skill.name} ({skill.category}): {skill.source_count} mentions")

        return 0

    except FileNotFoundError as e:
        print(f"\nError: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
