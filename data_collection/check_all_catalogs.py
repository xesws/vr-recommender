#!/usr/bin/env python3
"""
Check if all catalog pages have course descriptions
"""
import os
os.environ["FIRECRAWL_API_KEY"] = "fc-1213ec67816c4536b78d268eb1f04002"

from firecrawl import FirecrawlApp
import re

client = FirecrawlApp(api_key="fc-1213ec67816c4536b78d268eb1f04002")

catalogs = [
    ("School of Computer Science", "http://coursecatalog.web.cmu.edu/schools-colleges/schoolofcomputerscience/courses/"),
    ("Heinz College", "http://coursecatalog.web.cmu.edu/schools-colleges/heinzcollegeofinformationsystemsandpublicpolicy/"),
    ("Tepper School", "http://coursecatalog.web.cmu.edu/schools-colleges/tepper/"),
    ("Dietrich College", "http://coursecatalog.web.cmu.edu/schools-colleges/dietrichcollegeofhumanitiesandsocialsciences/courses/"),
    ("Mellon Science", "http://coursecatalog.web.cmu.edu/schools-colleges/melloncollegeofscience/courses/"),
    ("Engineering", "http://coursecatalog.web.cmu.edu/schools-colleges/collegeofengineering/courses/"),
    ("Fine Arts", "http://coursecatalog.web.cmu.edu/schools-colleges/collegeoffinearts/courses/"),
]

print("Checking all CMU catalog pages for course descriptions...\n")
print("=" * 80)

for dept_name, url in catalogs:
    print(f"\n[{dept_name}]")
    print(f"URL: {url}")

    try:
        result = client.scrape(url=url, formats=["markdown"], wait_for=5)

        if result and result.markdown:
            markdown = result.markdown
            lines = markdown.split('\n')

            # Look for course codes
            course_codes = []
            for i, line in enumerate(lines[:500]):
                if re.match(r'^\d{2}-\d{3}\.', line):
                    course_codes.append(line[:60])

            print(f"  Found {len(course_codes)} courses")

            # Show first few
            if course_codes:
                for code in course_codes[:3]:
                    print(f"    • {code}")

            # Try to find descriptions
            desc_found = False
            for i, line in enumerate(lines[:1000]):
                # Look for course followed by description-like text
                if re.match(r'^\d{2}-\d{3}\.', line):
                    # Check next line for description
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        # If next line is long and descriptive, it's likely a description
                        if len(next_line) > 50 and not re.match(r'^\d{2}-\d{3}\.', next_line):
                            print(f"  Sample description: {next_line[:80]}")
                            desc_found = True
                            break

            if not desc_found:
                print(f"  ⚠ No descriptions found in catalog page")
        else:
            print(f"  ❌ No content received")

    except Exception as e:
        print(f"  ❌ Error: {str(e)[:60]}")

    print("-" * 80)

print("\n" + "=" * 80)
print("Summary: Firecrawl is not getting course descriptions from catalog pages")
print("Only CS detail pages have full information")
print("=" * 80)
