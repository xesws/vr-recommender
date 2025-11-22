#!/usr/bin/env python3
"""
Debug: See what Firecrawl actually gets from catalog pages
"""
import os
os.environ["FIRECRAWL_API_KEY"] = "fc-1213ec67816c4536b78d268eb1f04002"

from firecrawl import FirecrawlApp

client = FirecrawlApp(api_key="fc-1213ec67816c4536b78d268eb1f04002")

url = "http://coursecatalog.web.cmu.edu/schools-colleges/schoolofcomputerscience/courses/"

print(f"Fetching raw content from:\n{url}\n")
print("=" * 80)

result = client.scrape(url=url, formats=["markdown", "html"], wait_for=10)

if result:
    print("\n--- HTML OUTPUT (first 1000 chars) ---")
    if result.html:
        print(result.html[:1000])
    else:
        print("(No HTML)")

    print("\n\n--- MARKDOWN OUTPUT (first 2000 chars) ---")
    if result.markdown:
        print(result.markdown[:2000])
    else:
        print("(No Markdown)")

    print("\n\n--- MARKDOWN OUTPUT (last 1000 chars) ---")
    if result.markdown:
        print(result.markdown[-1000:])
    else:
        print("(No Markdown)")

    print("\n\n--- METADATA ---")
    if hasattr(result, 'metadata'):
        print(result.metadata)

else:
    print("❌ No result received")
