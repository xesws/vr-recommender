#!/usr/bin/env python3
"""
Test scraping VRDB.app for structured VR app data
"""
import os
import sys
from pathlib import Path

os.environ["FIRECRAWL_API_KEY"] = "fc-1213ec67816c4536b78d268eb1f04002"

from firecrawl import FirecrawlApp

print("=" * 70)
print("Testing VRDB.app Structured Data Extraction")
print("=" * 70)

firecrawl_client = FirecrawlApp(api_key=os.environ["FIRECRAWL_API_KEY"])

# Scrape VRDB categories
urls = [
    "https://vrdb.app/genre/learning",
    "https://vrdb.app/apps?genre=productivity",
    "https://vrdb.app/genre/hands-on-training"
]

for url in urls:
    print(f"\nScraping: {url}")
    try:
        result = firecrawl_client.scrape(
            url=url,
            formats=["markdown", "html"],
            wait_for=5
        )

        if result and result.markdown:
            markdown = result.markdown
            print(f"✓ Got content ({len(markdown)} chars)")
            print(f"Preview (first 500 chars):")
            print("-" * 70)
            print(markdown[:500])
            print("-" * 70)
        else:
            print("⚠ No markdown content")

    except Exception as e:
        print(f"❌ Error: {e}")
