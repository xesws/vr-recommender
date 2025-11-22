#!/usr/bin/env python3
"""
Test improved course fetching - scrape course detail pages
"""
import os
import sys
from pathlib import Path
import re

os.environ["FIRECRAWL_API_KEY"] = "fc-1213ec67816c4536b78d268eb1f04002"

from firecrawl import FirecrawlApp

print("=" * 70)
print("Testing Course Detail Page Scraping")
print("=" * 70)

firecrawl_client = FirecrawlApp(api_key=os.environ["FIRECRAWL_API_KEY"])

# Try the course catalog with full details
url = "https://coursecatalog.web.cmu.edu/"
print(f"\nScraping course catalog: {url}")

try:
    result = firecrawl_client.scrape(
        url=url,
        formats=["markdown", "html"],
        wait_for=5
    )

    if result and result.markdown:
        markdown = result.markdown
        print(f"✓ Got content ({len(markdown)} chars)")
        print(f"\nFirst 1000 chars:")
        print("-" * 70)
        print(markdown[:1000])
        print("-" * 70)

        # Look for course patterns
        lines = markdown.split('\n')
        course_count = 0
        for line in lines[:100]:
            if re.match(r'^\d{2}-\d{3}', line):  # Course code pattern
                course_count += 1
                print(f"Found course: {line[:80]}")

        print(f"\n✓ Found {course_count} courses in first 100 lines")

        # Save for inspection
        with open("/tmp/course_catalog.md", "w") as f:
            f.write(markdown)

    if result and result.html:
        print(f"\n✓ Also got HTML ({len(result.html)} chars)")
        # Look for detail page links
        links = re.findall(r'href="(/[^"]*course[^"]*)"', result.html)
        if links:
            print(f"Found {len(links)} course-related links")
            for link in links[:5]:
                print(f"  {link}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
