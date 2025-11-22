#!/usr/bin/env python3
"""
Alternative VR app extraction - use structured app lists
"""
import os
import sys
from pathlib import Path
import re
import json

os.environ["FIRECRAWL_API_KEY"] = "fc-1213ec67816c4536b78d268eb1f04002"
os.environ["TAVILY_API_KEY"] = "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"

from tavily import TavilyClient

print("=" * 70)
print("Testing Structured VR App List Extraction")
print("=" * 70)

tavily_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

# Search for curated app lists
queries = [
    '"complete list of Meta Quest educational apps"',
    '"top VR learning apps for Quest 3"',
    '"best VR apps for education 2024"',
    '"Meta Quest productivity apps list"',
    '"VR training apps Meta Quest"',
]

for query in queries:
    print(f"\nQuery: {query}")
    results = tavily_client.search(
        query=query,
        search_depth="advanced",
        max_results=3,
        include_answer=True  # Try to get direct answer
    )

    # Check if Tavily provided a direct answer
    if results.get("answer"):
        print("  ✓ Direct answer from Tavily:")
        print(f"  {results['answer'][:300]}...")

    # Extract URLs
    for result in results.get("results", []):
        url = result.get("url", "")
        print(f"  URL: {url}")
        print(f"  Title: {result.get('title', '')[:60]}")
        print()
