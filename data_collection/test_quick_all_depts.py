#!/usr/bin/env python3
"""
Quick test: Extract course codes from all departments
"""
import os
os.environ["FIRECRAWL_API_KEY"] = "fc-1213ec67816c4536b78d268eb1f04002"

import sys
sys.path.insert(0, 'src')

from data_collection.course_fetcher_improved import CMUCourseFetcherImproved

print("=" * 80)
print("Quick Test: Extracting course codes from ALL CMU departments")
print("=" * 80 + "\n")

fetcher = CMUCourseFetcherImproved()

print("Configured departments:")
for prefix, url in fetcher.department_urls.items():
    dept_name = fetcher._infer_department(f"{prefix}-000")
    print(f"  [{prefix:2s}] {dept_name:35s} -> {url}")
print()

# Test extraction from each department
print("Extracting course codes from each department:\n")

all_codes = []
for prefix, url in fetcher.department_urls.items():
    print(f"[{prefix}] ", end="", flush=True)
    codes = fetcher._extract_course_codes_from_url(url, prefix)
    dept_name = fetcher._infer_department(f"{prefix}-000")

    if codes:
        print(f"✓ Found {len(codes):3d} codes -> {dept_name}")
        all_codes.extend(codes)
    else:
        print(f"⚠ 0 codes")

print(f"\n{'=' * 80}")
print(f"Total unique course codes: {len(all_codes)}")
print(f"{'=' * 80}\n")

if all_codes:
    print("Sample course codes (first 20):")
    for i, code in enumerate(sorted(all_codes)[:20], 1):
        prefix = code.split('-')[0]
        dept = fetcher._infer_department(code)
        print(f"  {i:2d}. {code:10s} ({dept})")

    # Group by department
    by_dept = {}
    for code in all_codes:
        prefix = code.split('-')[0]
        dept = fetcher._infer_department(code)
        if dept not in by_dept:
            by_dept[dept] = []
        by_dept[dept].append(code)

    print("\nCourses by department:")
    for dept in sorted(by_dept.keys()):
        count = len(by_dept[dept])
        prefix_list = sorted(set(code.split('-')[0] for code in by_dept[dept]))
        print(f"  • {dept:40s} {count:3d} courses (prefixes: {','.join(prefix_list)})")
