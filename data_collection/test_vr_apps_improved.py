#!/usr/bin/env python3
"""
Test improved VR app fetching strategy
"""
import os
import sys
from pathlib import Path
import re

# Set API keys
os.environ["FIRECRAWL_API_KEY"] = "fc-1213ec67816c4536b78d268eb1f04002"
os.environ["TAVILY_API_KEY"] = "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"

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from tavily import TavilyClient
from firecrawl import FirecrawlApp

print("=" * 70)
print("Testing Improved VR App Fetching Strategy")
print("=" * 70)

# Step 1: Use Tavily to find app store URLs
print("\n1. Finding Meta Quest app store URLs with Tavily...")
tavily_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

# Search for specific app store URLs
search_queries = [
    'site:oculus.com Meta Quest apps education',
    'site:sidequestvr.com educational VR apps',
    '"Meta Quest Store" education apps',
    '"best Meta Quest learning apps"',
]

app_urls = set()

for query in search_queries:
    print(f"\n  Query: {query}")
    results = tavily_client.search(
        query=query,
        search_depth="advanced",
        max_results=5,
        include_answer=False
    )

    # Extract URLs from results
    for result in results.get("results", []):
        url = result.get("url", "")
        title = result.get("title", "")

        # Check if it's an app page (not just an article)
        if any(keyword in url.lower() for keyword in ['oculus.com/app', 'sidequest', 'metaquest']):
            if url not in app_urls:
                app_urls.add(url)
                print(f"    ✓ Found: {title[:60]}")
                print(f"      URL: {url}")

print(f"\n✅ Found {len(app_urls)} unique app store URLs")

# Step 2: Scrape these URLs with Firecrawl
print("\n2. Scraping app store pages with Firecrawl...")
firecrawl_client = FirecrawlApp(api_key=os.environ["FIRECRAWL_API_KEY"])

for url in list(app_urls)[:5]:  # Test with first 5 URLs
    print(f"\n  Scraping: {url}")
    try:
        result = firecrawl_client.scrape(
            url=url,
            formats=["markdown"],
            wait_for=5
        )

        if result and result.markdown:
            markdown = result.markdown
            print(f"    ✓ Got content ({len(markdown)} chars)")
            print(f"    Preview: {markdown[:200]}...")

            # Try to extract app name
            app_name_match = re.search(r'^# (.+)$', markdown, re.MULTILINE)
            if app_name_match:
                app_name = app_name_match.group(1).strip()
                print(f"    📱 App name: {app_name}")

    except Exception as e:
        print(f"    ⚠ Error: {e}")
