#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# Set API key
os.environ["FIRECRAWL_API_KEY"] = "fc-1213ec67816c4536b78d268eb1f04002"

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from firecrawl import FirecrawlApp

print("Testing different CMU course catalog URLs...")
client = FirecrawlApp(api_key=os.environ["FIRECRAWL_API_KEY"])

urls_to_try = [
    "https://www.cmu.edu/hub/registrar/course-schedule/",
    "https://www.cmu.edu/registrar/schedule-of-classes/",
    "https://csd.cmu.edu/academics/courses",
    "https://www.heinz.cmu.edu/academic-programs/courses",
    "https://www.cmu.edu/academic-programs/",
    "https://coursecatalog.web.cmu.edu/",
    "https://www.cmu.edu/registrar/students/course-schedules/",
]

for url in urls_to_try:
    print(f"\n{'='*70}")
    print(f"Testing: {url}")
    print('='*70)

    try:
        result = client.scrape(
            url=url,
            formats=["markdown"],
            wait_for=5
        )

        if result and result.markdown and "course" in result.markdown.lower() and len(result.markdown) > 200:
            print(f"✅ SUCCESS! Found content with course data")
            print(f"Markdown length: {len(result.markdown)}")
            print(f"First 500 chars:\n{result.markdown[:500]}")

            # Save this URL result
            with open("/tmp/course_url_found.json", "w") as f:
                f.write(result.markdown)
            print(f"\n✅ Saved to /tmp/course_url_found.json")
            break
        else:
            print(f"⚠ URL exists but may not have course data")
            print(f"Markdown length: {len(result.markdown) if result.markdown else 0}")
            if result.markdown:
                print(f"First 200 chars: {result.markdown[:200]}")

    except Exception as e:
        print(f"❌ Error: {e}")
