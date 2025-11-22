#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# Set API keys
os.environ["FIRECRAWL_API_KEY"] = "fc-1213ec67816c4536b78d268eb1f04002"
os.environ["TAVILY_API_KEY"] = "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"

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Test course fetcher
from data_collection.course_fetcher import CMUCourseFetcher

print("Testing CMU Course Fetcher...")
fetcher = CMUCourseFetcher()
courses = fetcher.fetch_courses()

print(f"\n✅ Successfully fetched {len(courses)} courses")

if courses:
    print("\nFirst 3 courses:")
    for course in courses[:3]:
        print(f"  • {course.course_id}: {course.title}")
        print(f"    Description: {course.description[:100]}...")

    # Save to file
    fetcher.save_courses(courses, "data/courses.json")
    print(f"\n✅ Saved to data/courses.json")
else:
    print("\n⚠ No courses fetched - this is expected if CMU website structure changed")
    print("   The course fetcher has multiple parsing strategies and will adapt")
