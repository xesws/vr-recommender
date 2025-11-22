#!/usr/bin/env python3
"""
Test different URL patterns for course detail pages (limited to 3 tests)
"""
import os
os.environ["FIRECRAWL_API_KEY"] = "fc-1213ec67816c4536b78d268eb1f04002"

from firecrawl import FirecrawlApp

client = FirecrawlApp(api_key="fc-1213ec67816c4536b78d268eb1f04002")

# Test Heinz, Tepper, and Science courses with potential URL patterns
test_urls = [
    # Heinz - try different patterns
    ("94-801", "https://api.heinz.cmu.edu/courses_api/course_detail/94-801/"),
    # Tepper - try course catalog page
    ("73-102", "http://coursecatalog.web.cmu.edu/course/73102/"),
    # Science - try MCS site
    ("21-120", "https://www.cmu.edu/mcs/academics/courses/21-120"),
]

count = 0
max_tests = 3

print("Testing different URL patterns for detail pages (max 3 tests)...\n")

for code, url in test_urls:
    if count >= max_tests:
        print("Reached max tests limit")
        break

    count += 1
    print(f"[Test {count}/{max_tests}] {code}")
    print(f"  URL: {url}")

    try:
        result = client.scrape(url=url, formats=["markdown"], wait_for=3)

        if result and result.markdown:
            if "Page Not Found" not in result.markdown[:500]:
                print(f"  ✓ Got content ({len(result.markdown)} chars)")
                print(f"  Preview: {result.markdown[:150]}...")
            else:
                print(f"  ❌ Page Not Found")
        else:
            print(f"  ❌ No content")
    except Exception as e:
        print(f"  ❌ Error: {str(e)[:80]}")

    print()

print("Done!")
