#!/usr/bin/env python3
"""
Search for CMU course catalog URLs
"""
import os
os.environ["TAVILY_API_KEY"] = "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"

from tavily import TavilyClient

client = TavilyClient(api_key="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")

# Search for CMU course catalog URLs
searches = [
    "site:cmu.edu course catalog",
    "site:cmu.edu course listing",
    "site:heinz.cmu.edu courses",
    "site:cmu.edu/tepper courses",
    "site:cmu.edu/dietrich courses",
    "site:cmu.edu/mcs courses",
    "site:cmu.edu/engineering courses",
    "CMU course search system",
]

print("Searching for CMU course catalog URLs...\n")

for query in searches:
    print(f"Query: {query}")
    results = client.search(query, max_results=5, search_depth="advanced", include_answer=True)

    if results.get('answer'):
        print(f"  Answer: {results['answer'][:200]}...")

    print("  URLs:")
    for result in results.get('results', [])[:5]:
        print(f"    • {result['url']}")
        if result.get('content'):
            print(f"      {result['content'][:100]}...")
    print()
