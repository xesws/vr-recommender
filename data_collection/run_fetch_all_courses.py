#!/usr/bin/env python3
"""
Fetch CMU courses from all departments
Supports --all or --top k modes
"""
import os
import argparse
import sys

# Set API key
os.environ["FIRECRAWL_API_KEY"] = "fc-1213ec67816c4536b78d268eb1f04002"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from data_collection.course_fetcher_improved import CMUCourseFetcherImproved

def main():
    parser = argparse.ArgumentParser(
        description='Fetch CMU courses from all departments',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --top 20         Fetch top 20 courses
  %(prog)s --all            Fetch ALL courses (962+)
  %(prog)s --top 50         Fetch top 50 courses
        """
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--all', action='store_true',
                      help='Fetch ALL available courses')
    group.add_argument('--top', type=int, metavar='K',
                      help='Fetch top K courses')

    args = parser.parse_args()

    # Determine max courses
    if args.all:
        max_courses = 999999  # Sentinel for ALL
        print("Mode: --all (fetch ALL courses)")
    else:
        max_courses = args.top
        print(f"Mode: --top {max_courses}")

    # Load course codes from the extracted list
    course_codes_file = "all_cmu_courses.txt"
    if not os.path.exists(course_codes_file):
        print(f"Error: {course_codes_file} not found!")
        print("Please run test_all_5_depts.py first to extract course codes.")
        sys.exit(1)

    with open(course_codes_file, 'r') as f:
        all_codes = [line.strip() for line in f if line.strip()]

    print(f"Loaded {len(all_codes)} course codes from {course_codes_file}")

    if args.top and args.top > len(all_codes):
        print(f"Warning: Only {len(all_codes)} courses available, fetching all")
        max_courses = len(all_codes)

    # Fetch courses
    print(f"\nFetching {max_courses if max_courses < 999999 else len(all_codes)} courses...\n")
    fetcher = CMUCourseFetcherImproved()
    courses = fetcher.fetch_courses(max_courses=max_courses)

    if courses:
        # Save to file
        fetcher.save_courses(courses)

        # Print summary by department
        by_dept = {}
        for course in courses:
            dept = course.department
            if dept not in by_dept:
                by_dept[dept] = []
            by_dept[dept].append(course)

        print(f"\n{'=' * 80}")
        print(f"✓ Successfully fetched and saved {len(courses)} CMU courses!")
        print(f"{'=' * 80}\n")

        print("Courses by department:")
        for dept in sorted(by_dept.keys()):
            count = len(by_dept[dept])
            print(f"  • {dept:45s} {count:3d} courses")

        print(f"\n{'=' * 80}")
    else:
        print("⚠ No courses fetched")
        sys.exit(1)

if __name__ == "__main__":
    main()
