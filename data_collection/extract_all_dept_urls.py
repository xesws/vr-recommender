#!/usr/bin/env python3
"""
Extract all department course listing URLs from main catalog
"""
import os
os.environ["FIRECRAWL_API_KEY"] = "fc-1213ec67816c4536b78d268eb1f04002"

from firecrawl import FirecrawlApp
import re

client = FirecrawlApp(api_key="fc-1213ec67816c4536b78d268eb1f04002")

print("Extracting department course URLs from main CMU catalog...\n")

result = client.scrape(
    url="http://coursecatalog.web.cmu.edu/",
    formats=["markdown"],
    wait_for=5
)

if result and result.markdown:
    markdown = result.markdown

    # Find all links to courses pages
    course_link_pattern = r'\[.*?courses?.*?\]\((http://coursecatalog\.web\.cmu\.edu/schools-colleges/[^/]+/courses?/?)\)'
    matches = re.findall(course_link_pattern, markdown, re.IGNORECASE)

    # Get unique URLs
    unique_urls = list(set(matches))

    print(f"Found {len(unique_urls)} department course listing URLs:\n")

    for url in sorted(unique_urls):
        # Extract department name from URL
        dept = url.replace('http://coursecatalog.web.cmu.edu/schools-colleges/', '').replace('/courses', '').replace('/', ' ')
        dept = dept.replace('schoolofcomputerscience', 'School of Computer Science')
        dept = dept.replace('heinzcollegeofinformationsystemsandpublicpolicy', 'Heinz College')
        dept = dept.replace('tepper', 'Tepper School of Business')
        dept = dept.replace('dietrichcollegeofhumanitiesandsocialsciences', 'Dietrich College')
        dept = dept.replace('melloncollegeofscience', 'Mellon College of Science')
        dept = dept.replace('collegeofengineering', 'College of Engineering')
        dept = dept.replace('collegeoffinearts', 'College of Fine Arts')
        dept = dept.replace('intercollegeprograms', 'Interdisciplinary Programs')
        dept = dept.title()

        print(f"  • {dept}")
        print(f"    {url}")

    # Save URLs to file
    with open("department_course_urls.txt", 'w') as f:
        for url in unique_urls:
            f.write(url + "\n")

    print(f"\n✓ Saved {len(unique_urls)} URLs to department_course_urls.txt")

    # Now test one of them
    print(f"\n{'=' * 80}")
    print("Testing extraction from SCS courses page:")
    print(f"{'=' * 80}")

    scs_url = "http://coursecatalog.web.cmu.edu/schools-colleges/schoolofcomputerscience/courses/"
    print(f"URL: {scs_url}\n")

    result2 = client.scrape(url=scs_url, formats=["markdown"], wait_for=5)

    if result2 and result2.markdown:
        markdown2 = result2.markdown
        print(f"✓ Received {len(markdown2)} characters\n")

        # Extract course codes
        codes = re.findall(r'\b(15-\d{3})\b', markdown2)
        print(f"Found {len(codes)} course codes")
        print(f"Sample codes: {codes[:10]}")
