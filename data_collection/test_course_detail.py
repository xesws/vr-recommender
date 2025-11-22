#!/usr/bin/env python3
"""
Test scraping individual course detail pages
"""
import os
import sys
from pathlib import Path

os.environ["FIRECRAWL_API_KEY"] = "fc-1213ec67816c4536b78d268eb1f04002"

from firecrawl import FirecrawlApp

print("=" * 70)
print("Testing Individual Course Detail Page Scraping")
print("=" * 70)

firecrawl_client = FirecrawlApp(api_key=os.environ["FIRECRAWL_API_KEY"])

# Test specific course detail pages
course_urls = [
    "https://csd.cmu.edu/course/15104/f25",  # Introduction to Computing for Creative Practice
    "https://csd.cmu.edu/course/15110/f25",  # Principles of Computing
    "https://csd.cmu.edu/course/15090/f25",  # Computer Science Practicum
]

for url in course_urls:
    print(f"\n{'='*70}")
    print(f"Scraping: {url}")
    print('='*70)

    try:
        result = firecrawl_client.scrape(
            url=url,
            formats=["markdown"],
            wait_for=5
        )

        if result and result.markdown:
            markdown = result.markdown
            print(f"\n✓ Got content ({len(markdown)} chars)")
            print(f"\nContent preview:")
            print("-" * 70)
            # Show first 1500 chars which should include course title and description
            print(markdown[:1500])
            print("-" * 70)
        else:
            print("⚠ No content")

    except Exception as e:
        print(f"❌ Error: {e}")
