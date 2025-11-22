#!/usr/bin/env python3
"""
Extract FULL course information directly from catalog pages - FIXED VERSION
This fixes the bug where only CS courses get full details
"""
import os
os.environ["FIRECRAWL_API_KEY"] = "fc-1213ec67816c4536b78d268eb1f04002"

from firecrawl import FirecrawlApp
import re
from typing import List, Dict
import json
import sys
sys.path.insert(0, 'src')

client = FirecrawlApp(api_key="fc-1213ec67816c4536b78d268eb1f04002")

# CMU department catalog URLs
department_catalogs = [
    ("School of Computer Science", "http://coursecatalog.web.cmu.edu/schools-colleges/schoolofcomputerscience/courses/"),
    ("Heinz College", "http://coursecatalog.web.cmu.edu/schools-colleges/heinzcollegeofinformationsystemsandpublicpolicy/"),
    ("Tepper School of Business", "http://coursecatalog.web.cmu.edu/schools-colleges/tepper/"),
    ("Dietrich College", "http://coursecatalog.web.cmu.edu/schools-colleges/dietrichcollegeofhumanitiesandsocialsciences/courses/"),
    ("Mellon College of Science", "http://coursecatalog.web.cmu.edu/schools-colleges/melloncollegeofscience/courses/"),
    ("College of Engineering", "http://coursecatalog.web.cmu.edu/schools-colleges/collegeofengineering/courses/"),
    ("College of Fine Arts", "http://coursecatalog.web.cmu.edu/schools-colleges/collegeoffinearts/courses/"),
]

# Department prefix to name mapping
department_mappings = {
    "02": "School of Computer Science",
    "03": "School of Computer Science",
    "05": "School of Computer Science",
    "07": "School of Computer Science",
    "08": "School of Computer Science",
    "10": "School of Computer Science",
    "11": "School of Computer Science",
    "14": "School of Computer Science",
    "15": "School of Computer Science",
    "16": "School of Computer Science",
    "17": "School of Computer Science",
    "18": "School of Computer Science",
    "94": "Heinz College",
    "90": "Heinz College",
    "95": "Heinz College",
    "67": "Heinz College",
    "73": "Tepper School of Business",
    "51": "Dietrich College",
    "66": "Dietrich College",
    "21": "Mellon College of Science",
    "38": "Mellon College of Science",
    "36": "College of Engineering",
    "24": "College of Engineering",
    "39": "College of Engineering",
    "19": "College of Fine Arts",
    "62": "College of Fine Arts",
    "99": "CMU",
}

def infer_department(course_code: str) -> str:
    """Infer department from course code"""
    prefix = course_code.split('-')[0]
    return department_mappings.get(prefix, 'CMU')

def extract_courses_from_catalog(url: str, expected_dept: str) -> List[Dict]:
    """
    Extract full course information from a catalog page

    Returns:
        List of course dicts with: course_id, title, description, units, etc.
    """
    print(f"  Fetching: {url}")
    result = client.scrape(url=url, formats=["markdown"], wait_for=5)

    if not result or not result.markdown:
        print(f"  ❌ No content received")
        return []

    markdown = result.markdown
    lines = markdown.split('\n')

    courses = []
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # Look for course code pattern (e.g., "15-112 Fundamentals of Programming...")
        # Match: digits-digits followed by a space and title
        match = re.match(r'^(\d{2}-\d{1,3})\s+(.+)$', line)

        if match:
            course_code = match.group(1)
            title_and_rest = match.group(2)

            # FIXED: Extract clean title by removing semester/units info
            # Split on patterns that indicate semester or units info
            title = title_and_rest

            # Remove semester info (Fall:, Spring:, Summer:, etc.)
            title = re.sub(r'(Fall|Spring|Summer|Fall and Spring|Summer and Fall|Intermittent):.*$',
                          '', title).strip()

            # Remove units info (e.g., ": 9 units" at the end)
            title = re.sub(r':\s*\d+\s*units?$', '', title).strip()

            # Extract units if present
            units = 12  # default
            units_match = re.search(r'(\d+)\s*units?', line, re.IGNORECASE)
            if units_match:
                units = int(units_match.group(1))

            # Collect description from following lines
            description_lines = []
            i += 1

            # Description continues until we hit:
            # - A line starting with a course code
            # - A line that's just a heading or units
            # - An empty line followed by another course code
            while i < len(lines):
                next_line = lines[i].strip()

                # Stop if we hit another course code
                if re.match(r'^\d{2}-\d{1,3}\s+', next_line):
                    break

                # Stop if we hit a units line or course header
                if re.match(r'^(Fall|Spring|Summer|Fall and Spring):', next_line) or \
                   re.match(r'^\d+\s*units?', next_line, re.IGNORECASE) or \
                   next_line.startswith('#'):
                    i += 1
                    continue

                # Add non-empty lines to description
                if next_line and not next_line.startswith('*'):
                    description_lines.append(next_line)

                i += 1

            description = ' '.join(description_lines).strip()

            # Limit description length
            if len(description) > 800:
                description = description[:800] + "..."

            # Infer department from course code
            department = infer_department(course_code)

            # Use expected department if inference gives CMU
            if department == 'CMU' and expected_dept:
                department = expected_dept

            course = {
                "course_id": course_code,
                "title": title,
                "department": department,
                "description": description,
                "units": units,
                "prerequisites": [],
                "learning_outcomes": []
            }

            courses.append(course)

            # Continue without incrementing i since we already incremented at the end of the loop
            continue

        i += 1

    return courses

def main():
    print("=" * 80)
    print("CMU Course Catalog - FULL COURSE EXTRACTION (FIXED)")
    print("=" * 80)
    print("\nThis extracts TITLE, DESCRIPTION, and UNITS from all department catalogs")
    print("NO MORE wasting Firecrawl credits on detail pages!\n")

    all_courses = []

    for dept_name, url in department_catalogs:
        print(f"\n[{dept_name}]")
        courses = extract_courses_from_catalog(url, dept_name)

        if courses:
            print(f"  ✓ Extracted {len(courses)} courses with full details")

            # Show first course as example
            first = courses[0]
            print(f"    Example: {first['course_id']} - {first['title'][:60]}")
            print(f"             {first['description'][:100]}...")

            all_courses.extend(courses)
        else:
            print(f"  ⚠ No courses found")

    print(f"\n{'=' * 80}")
    print(f"✓ Total courses extracted: {len(all_courses)}")
    print(f"{'=' * 80}")

    # Count by department
    dept_counts = {}
    for course in all_courses:
        dept = course['department']
        dept_counts[dept] = dept_counts.get(dept, 0) + 1

    print("\nBy department:")
    for dept, count in sorted(dept_counts.items()):
        print(f"  {dept}: {count} courses")

    # Save to file
    output_file = "data/courses.json"  # Replace the old file
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_courses, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Saved to {output_file}")

    # Show sample courses from each department
    print(f"\n{'=' * 80}")
    print("Sample courses from each department:")
    print(f"{'=' * 80}")

    by_dept = {}
    for course in all_courses:
        dept = course['department']
        if dept not in by_dept:
            by_dept[dept] = []
        by_dept[dept].append(course)

    for dept, courses in sorted(by_dept.items()):
        print(f"\n[{dept}] ({len(courses)} courses)")
        for course in courses[:3]:
            print(f"  • {course['course_id']}: {course['title']}")
            print(f"    {course['description'][:150]}...")

if __name__ == "__main__":
    main()
