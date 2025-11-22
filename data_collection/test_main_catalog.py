#!/usr/bin/env python3
"""
Test the main CMU course catalog and Heinz API
"""
import os
os.environ["FIRECRAWL_API_KEY"] = "fc-1213ec67816c4536b78d268eb1f04002"

from firecrawl import FirecrawlApp
import json

client = FirecrawlApp(api_key="fc-1213ec67816c4536b78d268eb1f04002")

print("=" * 80)
print("Testing CMU's Centralized Course Catalog")
print("=" * 80 + "\n")

# Test 1: Main catalog
print("1. Main CMU Course Catalog: http://coursecatalog.web.cmu.edu/\n")
result = client.scrape(
    url="http://coursecatalog.web.cmu.edu/",
    formats=["markdown"],
    wait_for=5
)

if result and result.markdown:
    markdown = result.markdown
    print(f"✓ Received {len(markdown)} characters")
    print("\nFirst 1500 characters:")
    print("-" * 80)
    print(markdown[:1500])
    print("-" * 80)

    # Save to file
    with open("debug_main_catalog.md", 'w') as f:
        f.write(markdown)
    print("\n✓ Saved to debug_main_catalog.md")

    # Check for course codes
    import re
    patterns = [
        (r'\b15-\d{3}\b', 'CS (15)'),
        (r'\b9[045]-\d{3}\b', 'Heinz (94/90/95)'),
        (r'\b73-\d{3}\b', 'Tepper (73)'),
        (r'\b51-\d{3}\b', 'Dietrich (51)'),
        (r'\b21-\d{3}\b', 'Science (21)'),
        (r'\b36-\d{3}\b', 'Engineering (36)'),
        (r'\b19-\d{3}\b', 'Fine Arts (19)'),
    ]

    print("\nCourse code pattern matches:")
    for pattern, desc in patterns:
        matches = re.findall(pattern, markdown)
        if matches:
            print(f"  {desc}: {len(matches)} courses")
            print(f"    Examples: {matches[:5]}")

# Test 2: Heinz API
print("\n\n" + "=" * 80)
print("2. Heinz College API: https://api.heinz.cmu.edu/courses_api/course_list/")
print("=" * 80 + "\n")

import requests
try:
    response = requests.get("https://api.heinz.cmu.edu/courses_api/course_list/")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Received {len(data)} courses from API")

        # Save API data
        with open("debug_heinz_api.json", 'w') as f:
            json.dump(data, f, indent=2)
        print("✓ Saved to debug_heinz_api.json")

        # Show sample courses
        print("\nFirst 5 courses:")
        for i, course in enumerate(data[:5]):
            print(f"  {i+1}. {course.get('course_id', 'N/A')}: {course.get('title', 'N/A')[:60]}...")

        # Check unique departments
        dept_counts = {}
        for course in data:
            course_id = course.get('course_id', '')
            if course_id:
                prefix = course_id.split('-')[0]
                dept_counts[prefix] = dept_counts.get(prefix, 0) + 1

        print("\nCourses by department prefix:")
        for prefix in sorted(dept_counts.keys()):
            print(f"  {prefix}-XXX: {dept_counts[prefix]} courses")

    else:
        print(f"❌ Failed with status code: {response.status_code}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 80)
