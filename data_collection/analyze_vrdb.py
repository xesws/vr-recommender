#!/usr/bin/env python3
"""
Analyze VRDB structure and extract app list
"""
import os
import sys
from pathlib import Path
import re

os.environ["FIRECRAWL_API_KEY"] = "fc-1213ec67816c4536b78d268eb1f04002"

from firecrawl import FirecrawlApp

print("=" * 70)
print("Analyzing VRDB Structure for App Lists")
print("=" * 70)

firecrawl_client = FirecrawlApp(api_key=os.environ["FIRECRAWL_API_KEY"])

url = "https://vrdb.app/genre/learning"
print(f"\nScraping: {url}")

result = firecrawl_client.scrape(
    url=url,
    formats=["html", "markdown"],
    wait_for=5
)

if result and result.html:
    html = result.html
    print(f"\n✓ Got HTML content ({len(html)} chars)")

    # Save to file for analysis
    with open("/tmp/vrdb_learning.html", "w") as f:
        f.write(html)

    # Look for app cards/entries in HTML
    # Common patterns: app cards might be in divs with class, or use data attributes
    print("\nLooking for app entries...")

    # Check for JSON data or structured content
    if "VRDB" in html:
        print("✓ Contains VRDB data")

    # Extract app names (look for patterns like ## App Name or bold text)
    markdown = result.markdown if result.markdown else ""
    if markdown:
        # Look for app name patterns in markdown
        # Apps might be formatted as headers or list items
        lines = markdown.split('\n')

        app_count = 0
        for i, line in enumerate(lines[:200]):  # Check first 200 lines
            # Pattern: ### App Name or **App Name**
            if line.startswith('### ') and len(line) > 10:
                app_name = line[4:].strip()
                if not app_name.startswith('#') and 'NEW' not in app_name.upper():
                    app_count += 1
                    print(f"  {app_count}. {app_name}")

        print(f"\n✅ Found {app_count} potential apps in first 200 lines")

    # Save markdown for inspection
    if markdown:
        with open("/tmp/vrdb_learning.md", "w") as f:
            f.write(markdown)
        print(f"\n✅ Saved markdown to /tmp/vrdb_learning.md")
        print(f"    First 1000 chars:\n{markdown[:1000]}")

    # Try to find app detail pages
    print("\nLooking for app detail page links...")
    detail_links = re.findall(r'href="(https://vrdb\.app/app/[^"]+)"', html)
    if detail_links:
        print(f"✓ Found {len(detail_links)} app detail links")
        for link in detail_links[:3]:
            print(f"  - {link}")
