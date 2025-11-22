#!/usr/bin/env python3
"""
Find working course detail page URLs for different departments
"""
from tavily import TavilyClient

client = TavilyClient(api_key="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")

# Search for working URLs for specific courses from different departments
queries = [
    ("94-801", "heinz"),
    ("73-102", "tepper"),
    ("66-101", "dietrich"),
    ("21-120", "science"),
    ("62-106", "fine arts"),
]

print("Finding working course detail page URLs...\n")

for code, dept in queries:
    query = f"{code} {dept} course detail page URL"
    print(f"[{code} - {dept}] Searching for detail page URL...")

    results = client.search(query, max_results=5, search_depth="basic")

    for result in results.get('results', [])[:2]:
        url = result['url']
        # Look for URLs that might be detail pages
        if 'course' in url.lower() and code.replace('-', '') in url.replace('-', ''):
            print(f"  ✓ Found: {url}")
        elif 'course' in url.lower():
            print(f"  ? Possible: {url}")

    print()
