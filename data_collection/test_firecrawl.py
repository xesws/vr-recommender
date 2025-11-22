#!/usr/bin/env python3
import os
import sys
from pathlib import Path
import json

# Set API key
os.environ["FIRECRAWL_API_KEY"] = "fc-1213ec67816c4536b78d268eb1f04002"

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from firecrawl import FirecrawlApp

print("Testing Firecrawl API...")
client = FirecrawlApp(api_key=os.environ["FIRECRAWL_API_KEY"])

url = "https://www.cmu.edu/hub/registrar/course-schedule/"
print(f"Scraping: {url}")

try:
    result = client.scrape(
        url=url,
        formats=["markdown", "html"],
        wait_for=5
    )

    print("\n✅ Scraping successful!")
    print(f"\nResult type: {type(result)}")
    print(f"Result attributes: {dir(result)}")

    # Try to access content
    if hasattr(result, 'markdown'):
        print(f"\nHas markdown: Yes")
        print(f"Markdown length: {len(result.markdown) if result.markdown else 0}")

    if hasattr(result, 'html'):
        print(f"\nHas html: Yes")
        print(f"HTML length: {len(result.html) if result.html else 0}")

    # Save raw result
    with open("/tmp/firecrawl_result.json", "w") as f:
        json.dump({
            "markdown": result.markdown if hasattr(result, 'markdown') else None,
            "html": result.html if hasattr(result, 'html') else None,
            "content": result.content if hasattr(result, 'content') else None
        }, f, indent=2)

    print(f"\n✅ Saved raw result to /tmp/firecrawl_result.json")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
