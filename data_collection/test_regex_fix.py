#!/usr/bin/env python3
"""
Test the regex pattern on actual catalog content
"""
import os
os.environ["FIRECRAWL_API_KEY"] = "fc-1213ec67816c4536b78d268eb1f04002"

from firecrawl import FirecrawlApp
import re

client = FirecrawlApp(api_key="fc-1213ec67816c4536b78d268eb1f04002")

url = "http://coursecatalog.web.cmu.edu/schools-colleges/schoolofcomputerscience/courses/"

print("Testing regex patterns on catalog content...\n")

result = client.scrape(url=url, formats=["markdown"], wait_for=5)

if result and result.markdown:
    markdown = result.markdown

    # OLD pattern (from course_fetcher_improved.py line 251)
    old_pattern = r'\b(\d{2}-\d{3})\b'
    old_matches = re.findall(old_pattern, markdown)
    print(f"OLD pattern {old_pattern}:")
    print(f"  Found {len(old_matches)} matches")
    print(f"  Examples: {old_matches[:5]}")

    # NEW pattern - should match 2 digits, dash, 1-3 digits
    new_pattern = r'\b(\d{2}-\d{1,3})\b'
    new_matches = re.findall(new_pattern, markdown)
    print(f"\nNEW pattern {new_pattern}:")
    print(f"  Found {len(new_matches)} matches")
    print(f"  Examples: {new_matches[:10]}")

    # Show actual course lines
    print(f"\n--- Actual course lines in markdown ---")
    lines = markdown.split('\n')
    course_lines = []
    for line in lines:
        # Look for course codes
        if re.search(r'\d{2}-\d{1,3}', line):
            course_lines.append(line.strip())

    print(f"Found {len(course_lines)} course lines")
    print("\nFirst 5 course lines:")
    for line in course_lines[:5]:
        print(f"  {line[:120]}")
