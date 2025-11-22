#!/usr/bin/env python3
"""
Test the fixed fetcher - should NOT try to scrape detail pages for non-CS courses
"""
import os
os.environ["FIRECRAWL_API_KEY"] = "fc-1213ec67816c4536b78d268eb1f04002"

import sys
sys.path.insert(0, 'src')

from data_collection.course_fetcher_improved import CMUCourseFetcherImproved

# Test with a mix of CS and non-CS courses
test_codes = [
    "15-112",  # CS - SHOULD try detail page
    "94-801",  # Heinz - should NOT try detail page (returns None immediately)
    "73-102",  # Tepper - should NOT try detail page
    "15-213",  # CS - SHOULD try detail page
    "66-101",  # Dietrich - should NOT try detail page
]

print("Testing credit-saving fix...\n")
print("Expected behavior:")
print("  • 15-112, 15-213: Try detail pages (use Firecrawl credits)")
print("  • 94-801, 73-102, 66-101: Skip detail pages (NO credits used)")
print()

fetcher = CMUCourseFetcherImproved()

for code in test_codes:
    prefix = code.split('-')[0]
    will_scrape = prefix in fetcher.detail_url_patterns

    print(f"[{code}] Dept prefix: {prefix}")
    print(f"  Will attempt detail page: {will_scrape}")

    if will_scrape:
        print(f"  ⚡ Will use Firecrawl credits for detail page")
    else:
        print(f"  ✓ Skips detail page (no credits used)")

    print()
