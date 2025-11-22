#!/usr/bin/env python3
"""
Check what course data format is in the SCS catalog page
"""
import os
os.environ["FIRECRAWL_API_KEY"] = "fc-1213ec67816c4536b78d268eb1f04002"

from firecrawl import FirecrawlApp
import re

client = FirecrawlApp(api_key="fc-1213ec67816c4536b78d268eb1f04002")

url = "http://coursecatalog.web.cmu.edu/schools-colleges/schoolofcomputerscience/courses/"

print("Checking SCS catalog page for course descriptions...\n")
result = client.scrape(url=url, formats=["markdown"], wait_for=5)

if result and result.markdown:
    markdown = result.markdown

    # Look for course entries
    lines = markdown.split('\n')

    print("Searching for actual course entries (not links)...\n")

    for i, line in enumerate(lines[:2000]):  # Check first 2000 lines
        # Look for lines with course codes followed by title
        # Format might be: "15-112. Fundamentals of Programming and Computer Science"
        if re.match(r'^\d{2}-\d{3}\.\s', line):
            print(f"Found course entry:")
            print(f"  Line {i}: {line}")

            # Show next few lines for description
            print(f"  Next lines:")
            for j in range(1, 6):
                if i+j < len(lines):
                    next_line = lines[i+j].strip()
                    if next_line and not next_line.startswith('**') and not next_line.startswith('#'):
                        print(f"    {next_line[:100]}")
            print()

            # Only show first 3 examples
            if i > 500:
                break
