#!/usr/bin/env python3
"""
Main Data Collection Script
Fetches CMU courses and VR apps using Firecrawl and Tavily APIs
"""

import argparse
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data_collection.course_fetcher import CMUCourseFetcher
from data_collection.vr_app_fetcher import VRAppFetcher


def main():
    """Main entry point for data collection script"""
    parser = argparse.ArgumentParser(
        description="Fetch CMU courses and VR apps data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch both courses and VR apps
  python scripts/fetch_data.py --source all

  # Fetch only CMU courses
  python scripts/fetch_data.py --source courses

  # Fetch only VR apps
  python scripts/fetch_data.py --source apps

  # Specify custom output directory
  python scripts/fetch_data.py --output-dir /tmp/data
        """
    )

    parser.add_argument(
        "--source",
        choices=["courses", "apps", "all"],
        default="all",
        help="Data source to fetch (default: all)"
    )

    parser.add_argument(
        "--output-dir",
        default="data",
        help="Output directory for data files (default: data)"
    )

    parser.add_argument(
        "--vr-categories",
        nargs="+",
        default=["education", "training", "productivity"],
        help="VR app categories to search (default: education training productivity)"
    )

    args = parser.parse_args()

    print("=" * 70)
    print("Stage 1 - Data Collection Module")
    print("=" * 70)

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Check for API keys
    print("\n📋 Checking API keys...")
    missing_keys = []

    if args.source in ["courses", "all"]:
        if not os.getenv("FIRECRAWL_API_KEY"):
            missing_keys.append("FIRECRAWL_API_KEY")

    if args.source in ["apps", "all"]:
        if not os.getenv("TAVILY_API_KEY"):
            missing_keys.append("TAVILY_API_KEY")

    if missing_keys:
        print(f"❌ Missing required API keys: {', '.join(missing_keys)}")
        print("\nPlease set them in your environment or .env file:")
        print(f"  export FIRECRAWL_API_KEY=your-key")
        print(f"  export TAVILY_API_KEY=your-key")
        sys.exit(1)

    print("✓ API keys found")

    # Fetch courses
    if args.source in ["courses", "all"]:
        print("\n" + "=" * 70)
        print("📚 Fetching CMU Courses")
        print("=" * 70)

        try:
            fetcher = CMUCourseFetcher()
            courses = fetcher.fetch_courses()

            if courses:
                # Save courses
                courses_path = output_dir / "courses.json"
                fetcher.save_courses(courses, str(courses_path))
                print(f"\n✅ Successfully fetched {len(courses)} courses")
                print(f"   Saved to: {courses_path}")
            else:
                print("\n⚠ No courses fetched - this may be due to:")
                print("   - Network issues")
                print("   - Firecrawl API errors")
                print("   - Changes to CMU website structure")
                print("\n💡 You can try running the script again or check the logs above")
        except Exception as e:
            print(f"\n❌ Error fetching courses: {e}")
            import traceback
            traceback.print_exc()

    # Fetch VR apps
    if args.source in ["apps", "all"]:
        print("\n" + "=" * 70)
        print("🥽 Fetching VR Apps")
        print("=" * 70)

        try:
            fetcher = VRAppFetcher()
            apps = fetcher.fetch_apps(categories=args.vr_categories)

            if apps:
                # Save VR apps
                apps_path = output_dir / "vr_apps.json"
                fetcher.save_apps(apps, str(apps_path))
                print(f"\n✅ Successfully fetched {len(apps)} VR apps")
                print(f"   Saved to: {apps_path}")
            else:
                print("\n⚠ No VR apps fetched - this may be due to:")
                print("   - Network issues")
                print("   - Tavily API errors")
                print("   - No results for the specified categories")
                print("\n💡 You can try running the script again or check the logs above")
        except Exception as e:
            print(f"\n❌ Error fetching VR apps: {e}")
            import traceback
            traceback.print_exc()

    # Print summary
    print("\n" + "=" * 70)
    print("📊 Data Collection Summary")
    print("=" * 70)

    courses_path = output_dir / "courses.json"
    apps_path = output_dir / "vr_apps.json"

    if args.source in ["courses", "all"] and courses_path.exists():
        with open(courses_path, 'r', encoding='utf-8') as f:
            import json
            courses = json.load(f)
        print(f"\n📚 Courses: {len(courses)}")
        print(f"   File: {courses_path}")

        # Show first few courses
        if courses:
            print("\n   Sample courses:")
            for course in courses[:3]:
                print(f"     • {course['course_id']}: {course['title']}")

    if args.source in ["apps", "all"] and apps_path.exists():
        with open(apps_path, 'r', encoding='utf-8') as f:
            import json
            apps = json.load(f)
        print(f"\n🥽 VR Apps: {len(apps)}")
        print(f"   File: {apps_path}")

        # Show first few apps
        if apps:
            print("\n   Sample apps:")
            for app in apps[:3]:
                print(f"     • {app['name']} ({app['category']})")

    print("\n" + "=" * 70)
    print("✅ Data collection complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
