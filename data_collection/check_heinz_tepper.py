#!/usr/bin/env python3
"""
Check Heinz and Tepper department pages for course codes
"""
import os
os.environ["FIRECRAWL_API_KEY"] = "fc-1213ec67816c4536b78d268eb1f04002"

from firecrawl import FirecrawlApp
import re

client = FirecrawlApp(api_key="fc-1213ec67816c4536b78d268eb1f04002")

dept_urls = [
    ("Heinz College", "http://coursecatalog.web.cmu.edu/schools-colleges/heinzcollegeofinformationsystemsandpublicpolicy/"),
    ("Tepper School", "http://coursecatalog.web.cmu.edu/schools-colleges/tepper/"),
]

print("Checking Heinz and Tepper department pages for course codes...\n")

for dept_name, url in dept_urls:
    print(f"[{dept_name}]")
    print(f"  URL: {url}")

    try:
        result = client.scrape(url=url, formats=["markdown"], wait_for=5)

        if result and result.markdown:
            markdown = result.markdown
            print(f"  ✓ Received {len(markdown):,} characters")

            # Look for course codes
            patterns = [
                (r'\b9[045]-\d{3}\b', 'Heinz codes (94/90/95)'),
                (r'\b73-\d{3}\b', 'Tepper codes (73)'),
                (r'\b\d{2}-\d{3}\b', 'All XX-XXX codes'),
            ]

            for pattern, desc in patterns:
                codes = re.findall(pattern, markdown)
                if codes:
                    print(f"  ✓ {desc}: {len(codes)} matches")
                    print(f"    Samples: {codes[:5]}")

        else:
            print(f"  ❌ No content received")

    except Exception as e:
        print(f"  ❌ Error: {e}")

    print()

# Also check if there are course detail pages for Heinz
print("=" * 80)
print("Testing Heinz course detail page (94-801)")
print("=" * 80 + "\n")

# Try the Heinz URL pattern from the working CS courses
# Based on what we found earlier, let's try constructing URLs for Heinz courses
test_code = "94-801"
code_no_dash = test_code.replace('-', '')

# Test different URL patterns
url_patterns = [
    f"https://csd.cmu.edu/course/{code_no_dash}/f25",
    f"https://www.heinz.cmu.edu/heinz-courses/course-detail/{code_no_dash}/f25",
    f"http://coursecatalog.web.cmu.edu/course/{code_no_dash}/f25",
    f"http://coursecatalog.web.cmu.edu/heinzcollegeofinformationsystemsandpublicpolicy/{code_no_dash}/",
]

for pattern in url_patterns:
    print(f"\nTesting pattern: {pattern}")
    result = client.scrape(url=pattern, formats=["markdown"], wait_for=3)

    if result and result.markdown:
        if "Page Not Found" not in result.markdown[:500]:
            print(f"  ✓ Possible course page ({len(result.markdown)} chars)")
            print(f"    First 200 chars: {result.markdown[:200]}")
        else:
            print(f"  ❌ Page Not Found")
    else:
        print(f"  ❌ No content")
