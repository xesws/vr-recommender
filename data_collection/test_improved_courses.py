#!/usr/bin/env python3
import os
os.environ["FIRECRAWL_API_KEY"] = "fc-1213ec67816c4536b78d268eb1f04002"

import sys
sys.path.insert(0, 'src')

from data_collection.course_fetcher_improved import CMUCourseFetcherImproved

fetcher = CMUCourseFetcherImproved()
courses = fetcher.fetch_courses(max_courses=30)

print(f'\nTotal: {len(courses)}')
print('\nFirst 5 courses:')
for course in courses[:5]:
    print(f"  • {course.course_id}: {course.title}")
    print(f"    Department: {course.department}")
    print(f"    Units: {course.units}")
    print(f"    Description: {course.description[:100]}...")
    print(f"    Topics: {', '.join(course.learning_outcomes[:3])}")
    print()

# Save to file
fetcher.save_courses(courses)
print(f"\n✅ Saved {len(courses)} high-quality courses to data/courses.json")
