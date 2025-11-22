#!/usr/bin/env python3
"""
Check if catalog pages have full course data
"""
import os
os.environ["FIRECRAWL_API_KEY"] = "fc-1213ec67816c4536b78d268eb1f04002"

from firecrawl import FirecrawlApp
import re

client = FirecrawlApp(api_key="fc-1213ec67816c4536b78d268eb1f04002")

# Test with SCS page
url = "http://coursecatalog.web.cmu.edu/schools-colleges/schoolofcomputerscience/courses/"

print("Checking if catalog pages have full course descriptions...\n")
print(f"URL: {url}\n")

result = client.scrape(url=url, formats=["markdown"], wait_for=5)

if result and result.markdown:
    markdown = result.markdown

    # Look for course descriptions
    # SCS course format might be like:
    # 15-112. Fundamentals of Programming and Computer Science. 12 units.
    # Some descriptive text...

    # Find a course section
    lines = markdown.split('\n')

    print("Looking for course descriptions...\n")

    # Count how many lines look like course descriptions
    desc_count = 0
    for i, line in enumerate(lines[:1000]):  # Check first 1000 lines
        # Look for course code followed by title
        if re.match(r'^\d{2}-\d{3}\.', line):
            print(f"Found course: {line[:80]}")

            # Check next few lines for description
            desc_lines = []
            for j in range(i+1, min(i+5, len(lines))):
                next_line = lines[j].strip()
                if next_line and not re.match(r'^\d{2}-\d{3}\.', next_line) and not next_line.startswith('#'):
                    desc_lines.append(next_line)

            if desc_lines:
                print(f"  Description: {' '.join(desc_lines[:3])}")
                desc_count += 1

            if desc_count >= 5:  # Show first 5 examples
                break

    print(f"\n✓ Found {desc_count} courses with descriptions in this page")
