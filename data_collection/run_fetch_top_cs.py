#!/usr/bin/env python3
"""
Fetch only top 20 CS courses (15-XXX) which have working detail pages
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
print(f"Fetching top 20 CS courses with full details from detail pages...\n")

# Get top 20 CS courses
top_20_cs = cs_codes[:20]

print(f"Top 20 CS courses to fetch:")
for i, code in enumerate(top_20_cs, 1):
    print(f"  {i:2d}. {code}")

print(f"\n{'=' * 80}\n")

# Fetch only these 20 CS courses
fetcher = CMUCourseFetcherImproved()

# Manually process these 20 courses
courses = []
for i, code in enumerate(top_20_cs, 1):
    print(f"  [{i}/20] Processing {code}...", end=" ")

    course = fetcher._scrape_course_detail(code)
    if course:
        courses.append(course)
        print("✓ (detail)")
    else:
        print("⚠")

print(f"\n{'=' * 80}")
print(f"✓ Successfully fetched {len(courses)} CS courses with full details!")
print(f"{'=' * 80}\n")

if courses:
    # Save to file
    fetcher.save_courses(courses)

    print("Sample CS courses:")
    for course in courses[:5]:
        print(f"  • {course.course_id}: {course.title[:70]}...")
        print(f"    {course.department}")
        print(f"    {course.description[:100]}...")
        print()

    print(f"\n{'=' * 80}")
    print(f"✓ Saved {len(courses)} CS courses to data/courses.json")
    print(f"{'=' * 80}")
