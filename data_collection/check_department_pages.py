#!/usr/bin/env python3
"""
Check what's in department pages to understand why we can't extract codes
"""
import os
os.environ["FIRECRAWL_API_KEY"] = "fc-1213ec67816c4536b78d268eb1f04002"

from firecrawl import FirecrawlApp

client = FirecrawlApp(api_key="fc-1213ec67816c4536b78d268eb1f04002")

# Test different department pages
test_urls = [
    ("Heinz College", "https://www.heinz.cmu.edu/programs/courses"),
    ("Tepper", "https://www.cmu.edu/tepper/academic/courses/course-catalog.html"),
    ("Dietrich", "https://www.cmu.edu/dietrich/academics/courses/index.html"),
    ("Science", "https://www.cmu.edu/mcs/academics/courses/index.html"),
    ("Engineering", "https://www.cmu.edu/engineering/academics/courses/index.html"),
]

for name, url in test_urls:
    print(f"\n{'=' * 80}")
    print(f"Checking: {name}")
    print(f"URL: {url}")
    print('=' * 80)

    try:
        result = client.scrape(url=url, formats=["markdown"], wait_for=5)

        if not result or not result.markdown:
            print("❌ No content received\n")
            continue

        markdown = result.markdown
        print(f"✓ Received {len(markdown)} characters of markdown\n")

        # Show first 1000 characters
        print("First 1000 characters:")
        print("-" * 80)
        print(markdown[:1000])
        print("-" * 80)

        # Look for patterns
        import re
        patterns = [
            (r'\b\d{2}-\d{3}\b', 'XX-XXX format'),
            (r'\b\d{2}\d{3}\b', 'XXXXX format'),
            (r'\b9[045]-\d{3}\b', 'Heinz format (94, 90, 95)'),
            (r'\b73-\d{3}\b', 'Tepper format'),
            (r'\b51-\d{3}\b', 'Dietrich format'),
            (r'\b21-\d{3}\b', 'Science format'),
        ]

        print("\nPattern matches:")
        for pattern, desc in patterns:
            matches = re.findall(pattern, markdown)
            if matches:
                print(f"  {desc}: {len(matches)} matches")
                print(f"    Examples: {matches[:5]}")

        # Save to file for inspection
        filename = f"debug_{name.lower().replace(' ', '_')}.md"
        with open(filename, 'w') as f:
            f.write(markdown)
        print(f"\n✓ Saved full content to {filename}")

    except Exception as e:
        print(f"❌ Error: {e}\n")
