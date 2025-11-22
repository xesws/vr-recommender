#!/usr/bin/env python3
"""
Extract course codes from all 5 department pages
"""
import os
os.environ["FIRECRAWL_API_KEY"] = "fc-1213ec67816c4536b78d268eb1f04002"

from firecrawl import FirecrawlApp
import re

client = FirecrawlApp(api_key="fc-1213ec67816c4536b78d268eb1f04002")

# Department URLs from main catalog
dept_urls = [
    ("School of Computer Science", "http://coursecatalog.web.cmu.edu/schools-colleges/schoolofcomputerscience/courses/"),
    ("College of Engineering", "http://coursecatalog.web.cmu.edu/schools-colleges/collegeofengineering/courses/"),
    ("Dietrich College", "http://coursecatalog.web.cmu.edu/schools-colleges/dietrichcollegeofhumanitiesandsocialsciences/courses/"),
    ("Mellon College of Science", "http://coursecatalog.web.cmu.edu/schools-colleges/melloncollegeofscience/courses/"),
    ("College of Fine Arts", "http://coursecatalog.web.cmu.edu/schools-colleges/collegeoffinearts/courses/"),
]

print("=" * 80)
print("Extracting course codes from all CMU departments")
print("=" * 80 + "\n")

all_codes = []

for dept_name, url in dept_urls:
    print(f"[{dept_name}]")
    print(f"  URL: {url}")

    try:
        result = client.scrape(url=url, formats=["markdown"], wait_for=5)

        if result and result.markdown:
            markdown = result.markdown
            print(f"  ✓ Received {len(markdown):,} characters")

            # Extract course codes
            codes = re.findall(r'\b(\d{2}-\d{3})\b', markdown)

            # Remove duplicates while preserving order
            seen = set()
            unique_codes = []
            for code in codes:
                if code not in seen:
                    seen.add(code)
                    unique_codes.append(code)

            print(f"  ✓ Found {len(codes):,} total matches -> {len(unique_codes)} unique courses")

            # Show first 5 codes
            if unique_codes:
                print(f"    Samples: {', '.join(unique_codes[:5])}")
                all_codes.extend(unique_codes)
        else:
            print(f"  ❌ No content received")

    except Exception as e:
        print(f"  ❌ Error: {e}")

    print()

# Final summary
print("=" * 80)
print(f"Total unique course codes from all departments: {len(all_codes)}")
print("=" * 80)

# Group by prefix
by_prefix = {}
for code in all_codes:
    prefix = code.split('-')[0]
    if prefix not in by_prefix:
        by_prefix[prefix] = []
    by_prefix[prefix].append(code)

print("\nCourses by prefix:")
for prefix in sorted(by_prefix.keys()):
    count = len(by_prefix[prefix])
    dept = "School of Computer Science" if prefix == "15" else "Other"
    print(f"  {prefix}-XXX: {count:4d} courses ({dept})")

# Save to file
with open("all_cmu_courses.txt", 'w') as f:
    for code in sorted(set(all_codes)):
        f.write(code + "\n")

print(f"\n✓ Saved {len(all_codes)} unique course codes to all_cmu_courses.txt")
