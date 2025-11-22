#!/usr/bin/env python3
import os
os.environ["FIRECRAWL_API_KEY"] = "fc-1213ec67816c4536b78d268eb1f04002"

import sys
sys.path.insert(0, 'src')

from data_collection.course_fetcher_improved import CMUCourseFetcherImproved

fetcher = CMUCourseFetcherImproved()

# Test with specific courses we know work
known_codes = ["15104", "15110", "15090"]

courses = []
for code in known_codes:
    print(f"Scraping {code}...")
    course = fetcher._scrape_course_detail(code)
    if course:
        courses.append(course)
        print(f"  ✓ {course.title}")
        print(f"    {course.description[:150]}...")
    else:
        print(f"  ✗ Failed")

print(f"\nTotal courses: {len(courses)}")

# Save to file
fetcher.save_courses(courses, "data/courses.json")
