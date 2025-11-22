#!/usr/bin/env python3
"""
Check catalog page structure for course entries
"""
import os
os.environ["FIRECRAWL_API_KEY"] = "fc-1213ec67816c4536b78d268eb1f04002"

from firecrawl import FirecrawlApp
import re

client = FirecrawlApp(api_key="fc-1213ec67816c4536b78d268eb1f04002")

# Check Dietrich College catalog
url = "http://coursecatalog.web.cmu.edu/schools-colleges/dietrichcollegeofhumanitiesandsocialsciences/courses/"

print("Checking catalog page for course structure...\n")
result = client.scrape(url=url, formats=["markdown"], wait_for=5)

if result and result.markdown:
    markdown = result.markdown
    lines = markdown.split('\n')

    print("Looking for course entries...\n")

    for i, line in enumerate(lines[:1000]):
        # Look for course code patterns
        if re.match(r'^\d{2}-\d{3}', line):
            print(f"Line {i}: {line}")

            # Show next 5 lines for context
            for j in range(1, 6):
                if i+j < len(lines):
                    next_line = lines[i+j].strip()
                    if next_line and not next_line.startswith('#'):
                        print(f"  -> {next_line[:80]}")
            print()

            # Show first 5 examples
            if i > 200:
                break
