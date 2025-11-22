#!/usr/bin/env python3
"""
Test script for all-department course fetcher
Tests extraction from all CMU departments
"""
import os
os.environ["FIRECRAWL_API_KEY"] = "fc-1213ec67816c4536b78d268eb1f04002"

import sys
sys.path.insert(0, 'src')

from data_collection.course_fetcher_improved import CMUCourseFetcherImproved

def test_department_extraction():
    """Test extracting course codes from all departments"""
    print("Testing course code extraction from all CMU departments...\n")

    fetcher = CMUCourseFetcherImproved()

    print(f"Configured department URLs:")
    for prefix, url in fetcher.department_urls.items():
        print(f"  [{prefix}] {url}")
    print()

    # Extract course codes from all departments
    all_codes = fetcher._extract_course_codes_from_all_departments()

    print(f"\n✓ Total unique course codes found: {len(all_codes)}")

    if all_codes:
        print("\nSample course codes:")
        for i, code in enumerate(all_codes[:20], 1):
            print(f"  {i:2d}. {code}")

        if len(all_codes) > 20:
            print(f"  ... and {len(all_codes) - 20} more")

        # Group by department prefix
        by_prefix = {}
        for code in all_codes:
            prefix = code.split('-')[0]
            if prefix not in by_prefix:
                by_prefix[prefix] = []
            by_prefix[prefix].append(code)

        print("\nCourses by department:")
        for prefix in sorted(by_prefix.keys()):
            dept_name = fetcher._infer_department(f"{prefix}-000")
            print(f"  [{prefix}] {dept_name}: {len(by_prefix[prefix])} courses")

        return all_codes
    else:
        print("\n⚠ No course codes found!")
        return []

def test_sample_scrape():
    """Test scraping a few sample courses"""
    print("\n" + "=" * 80)
    print("Testing sample course detail scraping...")
    print("=" * 80 + "\n")

    fetcher = CMUCourseFetcherImproved()

    # Test with a few known good courses
    test_codes = ["15104", "15110", "94801"]

    print(f"Testing {len(test_codes)} sample courses:\n")

    for code in test_codes:
        print(f"Testing {code}...", end=" ")

        # Convert to dash format for internal use
        if len(code) == 5:
            code_with_dash = f"{code[:2]}-{code[2:]}"
        else:
            code_with_dash = code

        course = fetcher._scrape_course_detail(code_with_dash)

        if course:
            print("✓")
            print(f"  Title: {course.title}")
            print(f"  Dept: {course.department}")
            print(f"  Units: {course.units}")
        else:
            print("⚠")
    print()

if __name__ == "__main__":
    print("=" * 80)
    print("CMU Course Fetcher - All Departments Test")
    print("=" * 80 + "\n")

    # Test 1: Extract course codes from all departments
    all_codes = test_department_extraction()

    if all_codes:
        # Test 2: Try scraping a few samples
        test_sample_scrape()

        # Ask user if they want to proceed with full fetch
        print("\n" + "=" * 80)
        print(f"Found {len(all_codes)} unique courses across all departments.")
        print("\nWould you like to:")
        print("  1. Fetch all courses (this will take 10-30 minutes)")
        print("  2. Fetch only first 50 courses (for testing)")
        print("  3. Exit")

        try:
            choice = input("\nEnter choice (1-3): ").strip()
        except KeyboardInterrupt:
            print("\n\nExiting...")
            sys.exit(0)

        if choice == "1":
            print("\nFetching ALL courses...")
            courses = fetcher.fetch_courses(max_courses=999999)
        elif choice == "2":
            print("\nFetching first 50 courses...")
            courses = fetcher.fetch_courses(max_courses=50)
        else:
            print("Exiting...")
            sys.exit(0)

        if courses:
            fetcher.save_courses(courses)
            print(f"\n✓ Success! Fetched and saved {len(courses)} courses to data/courses.json")
    else:
        print("\n⚠ Test failed - no course codes extracted")
        sys.exit(1)
