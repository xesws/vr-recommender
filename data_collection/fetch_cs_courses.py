#!/usr/bin/env python3
"""
Fetch only CS courses (15-XXX) which have working detail pages
"""
import os
os.environ["FIRECRAWL_API_KEY"] = "fc-1213ec67816c4536b78d268eb1f04002"

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from data_collection.course_fetcher_improved import CMUCourseFetcherImproved

# Load all course codes
with open("all_cmu_courses.txt", 'r') as f:
    all_codes = [line.strip() for line in f if line.strip()]

# Filter for CS courses only
cs_codes = [code for code in all_codes if code.startswith('15-')]

print(f"Found {len(cs_codes)} CS courses (15-XXX) out of {len(all_codes)} total courses")
print("\nFetching all CS courses with full details from detail pages...\n")

# Fetch CS courses
fetcher = CMUCourseFetcherImproved()
courses = fetcher.fetch_courses(max_courses=999999)

# Filter to only CS courses
cs_courses = [c for c in courses if c.course_id.startswith('15-')]

print(f"\n{'=' * 80}")
print(f"✓ Fetched {len(cs_courses)} CS courses with full details!")
print(f"{'=' * 80}\n")

if cs_courses:
    # Save to file
    fetcher.save_courses(cs_courses)

    print("Sample CS courses:")
    for course in cs_courses[:10]:
        print(f"  • {course.course_id}: {course.title[:60]}...")
        print(f"    {course.department}")
        print()

    print(f"\n{'=' * 80}")
    print(f"✓ Saved {len(cs_courses)} CS courses to data/courses.json")
    print(f"{'=' * 80}")
