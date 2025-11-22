#!/usr/bin/env python3
"""
Test if CS detail page pattern works for non-CS courses
"""
import os
os.environ["FIRECRAWL_API_KEY"] = "fc-1213ec67816c4536b78d268eb1f04002"

import sys
sys.path.insert(0, 'src')

from firecrawl import FirecrawlApp

client = FirecrawlApp(api_key="fc-1213ec67816c4536b78d268eb1f04002")

# Test various course codes with CS detail URL pattern
test_courses = [
    ("94-801", "Heinz"),  # Remove dash: 94801
    ("73-102", "Tepper"),  # Remove dash: 73102
    ("66-101", "Dietrich"),  # Remove dash: 66101
    ("15-112", "CS"),  # Remove dash: 15112 (should work)
]

print("Testing if CS detail page pattern works for non-CS courses...\n")

for code, dept in test_courses:
    code_no_dash = code.replace('-', '')
    url = f"https://csd.cmu.edu/course/{code_no_dash}/f25"

    print(f"[{code} - {dept}]")
    print(f"  URL: {url}")

    try:
        result = client.scrape(url=url, formats=["markdown"], wait_for=3)

        if result and result.markdown:
            if "Page Not Found" not in result.markdown[:500]:
                print(f"  ✓ Got content ({len(result.markdown)} chars)")

                # Check if it has course info
                if "units" in result.markdown.lower() or "description" in result.markdown.lower():
                    print(f"  ✓ Likely has course details")
                else:
                    print(f"  ⚠ Has content but may not have details")
            else:
                print(f"  ❌ Page Not Found")
        else:
            print(f"  ❌ No content")

    except Exception as e:
        print(f"  ❌ Error: {str(e)[:60]}")

    print()
