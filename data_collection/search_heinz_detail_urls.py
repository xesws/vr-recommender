#!/usr/bin/env python3
"""
Search for Heinz course detail page URLs
"""
import os
os.environ["FIRECRAWL_API_KEY"] = "fc-1213ec67816c4536b78d268eb1f04002"

import sys
sys.path.insert(0, 'src')

from tavily import TavilyClient

client = TavilyClient(api_key="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")

# Search for Heinz course detail page URLs
queries = [
    "site:heinz.cmu.edu 94-801 course detail",
    "heinz.cmu.edu course 94801",
    "94-801 heinz course description",
]

print("Searching for Heinz course detail page URLs...\n")

for query in queries:
    print(f"Query: {query}")
    results = client.search(query, max_results=5, search_depth="advanced")

    for result in results.get('results', [])[:3]:
        print(f"  • {result['url']}")
        if result.get('content'):
            print(f"    {result['content'][:100]}...")
    print()
