"""
CMU Course Fetcher - Improved Version
Scrapes individual course detail pages for complete data
"""

import os
import json
import re
from typing import List, Dict

try:
    from firecrawl import FirecrawlApp
except ImportError:
    print("Warning: firecrawl not installed. Install with: pip install firecrawl-py")
    FirecrawlApp = None

from src.models import Course


class CMUCourseFetcherImproved:
    """Improved CMU course fetcher that scrapes detail pages from all departments"""

    def __init__(self):
        """Initialize the fetcher with Firecrawl API"""
        self.api_key = os.getenv("FIRECRAWL_API_KEY")
        if not self.api_key:
            raise ValueError("FIRECRAWL_API_KEY environment variable not set")

        if FirecrawlApp is None:
            raise ImportError("firecrawl-py not installed. Run: pip install firecrawl-py")

        self.client = FirecrawlApp(api_key=self.api_key)

        # CMU department course catalog URLs from main catalog
        # These URLs work and contain course codes
        self.department_catalogs = [
            ("School of Computer Science", "http://coursecatalog.web.cmu.edu/schools-colleges/schoolofcomputerscience/courses/"),
            ("College of Engineering", "http://coursecatalog.web.cmu.edu/schools-colleges/collegeofengineering/courses/"),
            ("Dietrich College", "http://coursecatalog.web.cmu.edu/schools-colleges/dietrichcollegeofhumanitiesandsocialsciences/courses/"),
            ("Mellon College of Science", "http://coursecatalog.web.cmu.edu/schools-colleges/melloncollegeofscience/courses/"),
            ("College of Fine Arts", "http://coursecatalog.web.cmu.edu/schools-colleges/collegeoffinearts/courses/"),
            ("Heinz College", "http://coursecatalog.web.cmu.edu/schools-colleges/heinzcollegeofinformationsystemsandpublicpolicy/"),
            ("Tepper School of Business", "http://coursecatalog.web.cmu.edu/schools-colleges/tepper/"),
        ]

        # Detail page URL patterns - ONLY departments with working detail pages
        # Format: {code} = course code without dash (e.g., 15112 for 15-112)
        # TESTED: Only CS (15-XXX) has working detail pages as of Fall 2025
        self.detail_url_patterns = {
            "15": "https://csd.cmu.edu/course/{}/f25",  # ✓ Works - CS has detail pages
        }

        # Departments that DON'T have detail pages (trying will waste API credits)
        self.no_detail_pages = {
            "94", "90", "95",  # Heinz College - no detail pages found
            "73",               # Tepper School - no detail pages found
            "66", "51",         # Dietrich College - no detail pages found
            "21", "38",         # Mellon College of Science - no detail pages found
            "36", "39", "24",   # College of Engineering - no detail pages found
            "62", "19",         # College of Fine Arts - no detail pages found
            "99",               # Interdisciplinary - no detail pages found
        }

        # Department prefix mappings for inferring departments from course codes
        self.department_mappings = {
            "15": "School of Computer Science",
            "94": "Heinz College",
            "90": "Heinz College",
            "95": "Heinz College",
            "73": "Tepper School of Business",
            "51": "Dietrich College",
            "21": "Mellon College of Science",
            "36": "College of Engineering",
            "19": "College of Fine Arts",
            "24": "College of Engineering",
            "67": "Heinz College",
            "99": "CMU",
            # SCS interdisciplinary codes
            "02": "School of Computer Science",
            "03": "School of Computer Science",
            "05": "School of Computer Science",
            "07": "School of Computer Science",
            "08": "School of Computer Science",
            "09": "School of Computer Science",
            "10": "School of Computer Science",
            "11": "School of Computer Science",
            "14": "School of Computer Science",
            "16": "School of Computer Science",
            "17": "School of Computer Science",
            "18": "School of Computer Science",
            # Engineering
            "39": "College of Engineering",
            # Dietrich
            "66": "Dietrich College",
            # Science
            "38": "Mellon College of Science",
            # Fine Arts
            "62": "College of Fine Arts",
        }

    def fetch_courses(self, max_courses: int = 100, use_extracted_codes: bool = True) -> List[Course]:
        """
        Fetch CMU courses from ALL departments

        Strategy:
        1. Load course codes from file (if use_extracted_codes=True) or extract from catalogs
        2. For departments with detail page support (currently only CS), scrape detail pages
        3. For other departments, extract basic info from catalog pages
        4. Parse structured data where available

        Args:
            max_courses: Maximum number of courses to fetch (set to 999999 for ALL)
            use_extracted_codes: If True, load course codes from all_cmu_courses.txt file

        Returns:
            List[Course]: List of Course objects
        """
        print(f"Fetching CMU courses (max: {max_courses if max_courses < 999999 else 'ALL'})...")

        # Step 1: Get course codes
        if use_extracted_codes:
            # Load from file to save API credits
            try:
                if os.path.exists("all_cmu_courses.txt"):
                    with open("all_cmu_courses.txt", 'r') as f:
                        all_course_codes = [line.strip() for line in f if line.strip()]
                    print(f"✓ Loaded {len(all_course_codes)} course codes from all_cmu_courses.txt")
                else:
                    print("⚠ all_cmu_courses.txt not found, extracting from catalogs...")
                    use_extracted_codes = False
            except Exception as e:
                print(f"⚠ Error loading file: {e}")
                use_extracted_codes = False

        if not use_extracted_codes:
            # Extract from department catalogs (uses API credits)
            print(f"Scanning {len(self.department_catalogs)} department catalogs...")
            print(f"Note: Only CS (15-XXX) has working detail pages.")
            print(f"      Other depts return basic info (no detail scraping).")

            all_course_codes = []
            for dept_name, url in self.department_catalogs:
                print(f"\n  [{dept_name}] Extracting from catalog page...")
                course_codes = self._extract_course_codes_from_catalog(url)
                if course_codes:
                    print(f"    Found {len(course_codes)} course codes")
                    all_course_codes.extend(course_codes)
                else:
                    print(f"    No course codes found")

            print(f"\n✓ Total course codes found: {len(all_course_codes)}")

            # Remove duplicates while preserving order
            seen = set()
            unique_course_codes = []
            for code in all_course_codes:
                if code not in seen:
                    seen.add(code)
                    unique_course_codes.append(code)

            all_course_codes = unique_course_codes

        # Limit number of courses if specified
        if max_courses < 999999:
            all_course_codes = all_course_codes[:max_courses]
            print(f"✓ Limited to {len(all_course_codes)} courses")

        # Step 2: Try to scrape detail pages where available
        # Only departments in detail_url_patterns have working detail pages
        courses = []
        failed_courses = []
        detail_success_count = 0
        basic_info_count = 0

        for i, code in enumerate(all_course_codes, 1):
            print(f"  [{i}/{len(all_course_codes)}] Processing {code}...", end=" ")

            course = self._scrape_course_detail(code)
            if course:
                courses.append(course)
                detail_success_count += 1
                print("✓ (detail)")
            else:
                # Fallback: create basic course from just the code
                course = self._create_basic_course(code)
                if course:
                    courses.append(course)
                    basic_info_count += 1
                    print("✓ (basic)")
                else:
                    print("⚠")
                    failed_courses.append(code)

        print(f"\n✓ Successfully processed {len(courses)} courses")
        print(f"  • {detail_success_count} with full details (departments with detail pages)")
        print(f"  • {basic_info_count} with basic info (depts without detail pages)")
        if failed_courses:
            print(f"⚠ Failed: {len(failed_courses)} courses")

        return courses

    def _extract_course_codes(self) -> List[str]:
        """
        Legacy method - kept for backward compatibility
        Now redirects to extracting from all department catalogs
        """
        print("Note: This method extracts from all CMU department catalogs")
        return self._extract_course_codes_from_all_departments()

    def _extract_course_codes_from_all_departments(self) -> List[str]:
        """Extract course codes from ALL department catalog pages"""
        all_course_codes = []
        for dept_name, url in self.department_catalogs:
            course_codes = self._extract_course_codes_from_catalog(url)
            all_course_codes.extend(course_codes)

        # Remove duplicates
        seen = set()
        unique_codes = []
        for code in all_course_codes:
            if code not in seen:
                seen.add(code)
                unique_codes.append(code)

        return unique_codes

    def _extract_course_codes_from_catalog(self, catalog_url: str) -> List[str]:
        """
        Extract course codes from a department catalog page

        Args:
            catalog_url: The department's course catalog URL

        Returns:
            List of course codes from this department
        """
        try:
            result = self.client.scrape(
                url=catalog_url,
                formats=["markdown"],
                wait_for=5
            )

            if not result or not result.markdown:
                print(f"    ⚠ No content received")
                return []

            markdown = result.markdown

            # Extract all course codes in format XX-XXX
            course_pattern = r'\b(\d{2}-\d{3})\b'
            matches = re.findall(course_pattern, markdown)

            # Remove duplicates while preserving order
            seen = set()
            unique_codes = []
            for code in matches:
                if code not in seen:
                    seen.add(code)
                    unique_codes.append(code)

            return unique_codes

        except Exception as e:
            print(f"    ❌ Error: {e}")
            return []

    def _scrape_course_detail(self, course_code: str) -> Course:
        """
        Scrape individual course detail page
        ONLY attempts to scrape if the department has working detail pages

        Args:
            course_code: Course code like "15-112" or "15104"

        Returns:
            Course: Parsed Course object or None if failed/no detail page available
        """
        # Get department prefix from course code
        prefix = course_code.split('-')[0]

        # Check if this department has detail pages
        if prefix not in self.detail_url_patterns:
            # Department doesn't have detail pages - don't waste API credits
            return None

        # Construct detail page URL based on department pattern
        code_no_dash = course_code.replace('-', '')
        url_pattern = self.detail_url_patterns.get(prefix)
        url = url_pattern.format(code_no_dash)

        try:
            result = self.client.scrape(
                url=url,
                formats=["markdown"],
                wait_for=5
            )

            if not result or not result.markdown:
                return None

            markdown = result.markdown

            # Check if it's a "Page Not Found" error
            if "Page Not Found" in markdown[:500]:  # Check first 500 chars
                return None

            # Parse the structured content
            course = self._parse_course_detail(markdown, course_code)

            # Additional check: if title is "Page Not Found", reject it
            if "Page Not Found" in course.title:
                return None

            return course

        except Exception as e:
            # Silently fail for individual courses
            return None

    def _parse_course_detail(self, markdown: str, course_code: str) -> Course:
        """
        Parse course detail page content

        Args:
            markdown: Course page markdown content
            course_code: Course code

        Returns:
            Course: Parsed Course object
        """
        lines = markdown.split('\n')

        # Extract title (usually the first h1 heading)
        title = ""
        for line in lines:
            if line.startswith('# '):
                # Extract title from markdown link format: [Title](URL)
                # First remove the '# ' prefix
                title = line[2:].strip()
                # Extract text from brackets
                title_match = re.search(r'\[(.*?)\]', title)
                if title_match:
                    title = title_match.group(1).strip()
                else:
                    # No brackets, just use the text
                    title = title
                break

        if not title:
            title = f"Course {course_code}"

        # Extract description
        description = ""
        in_description = False
        for line in lines:
            if '**Description**' in line or 'Description' in line:
                in_description = True
                continue

            if in_description:
                if line.startswith('**') and not line.startswith('**Description'):
                    # End of description
                    break
                if line.strip() and not line.startswith('#'):
                    description += line.strip() + " "

        description = description.strip()

        # Extract key topics
        topics = []
        in_topics = False
        for line in lines:
            if '**Key Topics**' in line or 'Topics' in line:
                in_topics = True
                continue

            if in_topics:
                if line.startswith('**') and 'Topics' not in line:
                    break
                # Parse bullet points or comma-separated values
                if line.strip():
                    # Remove markdown formatting
                    cleaned = re.sub(r'^[\*\-\d\.\s]*', '', line).strip()
                    if cleaned:
                        topics.append(cleaned)

        # Extract required background
        background = ""
        in_background = False
        for line in lines:
            if '**Required Background**' in line or '**Prerequisites**' in line:
                in_background = True
                continue

            if in_background:
                if line.startswith('**') and 'Background' not in line and 'Prerequisites' not in line:
                    break
                if line.strip() and not line.startswith('#'):
                    background += line.strip() + " "

        background = background.strip()

        # Extract course goals
        goals = []
        in_goals = False
        for line in lines:
            if '**Course Goals**' in line or '**Learning Outcomes**' in line:
                in_goals = True
                continue

            if in_goals:
                if line.startswith('**') and 'Goals' not in line and 'Outcomes' not in line:
                    break
                if line.strip():
                    cleaned = re.sub(r'^[\*\-\d\.\s]*', '', line).strip()
                    if cleaned:
                        goals.append(cleaned)

        # Determine department based on course code
        department = self._infer_department(course_code)

        # Extract units (usually in the course code section)
        units = 12  # Default units
        units_match = re.search(r'(\d+)\s*units?', markdown, re.IGNORECASE)
        if units_match:
            units = int(units_match.group(1))

        # Extract prerequisites
        prerequisites = []
        prereq_section = re.search(r'\*\*Prerequisites?\*\*:\s*(.+?)(?:\n\n|\*\*|$)', markdown, re.IGNORECASE | re.DOTALL)
        if prereq_section:
            prereq_text = prereq_text = prereq_section.group(1).strip()
            # Split by commas or 'and'
            prereqs = re.split(r',| and ', prereq_text)
            for prereq in prereqs:
                prereq = prereq.strip()
                if prereq and len(prereq) < 20:  # Reasonable prerequisite length
                    prerequisites.append(prereq)

        # Use topics as learning outcomes if no explicit goals
        learning_outcomes = goals if goals else topics

        return Course(
            course_id=course_code,
            title=title,
            department=department,
            description=description[:500],  # Limit length
            units=units,
            prerequisites=prerequisites[:5],  # Limit number
            learning_outcomes=learning_outcomes[:5]  # Limit number
        )

    def _infer_department(self, course_code: str) -> str:
        """Infer department from course code"""
        # CMU course code prefix indicates department
        prefix = course_code.split('-')[0]

        return self.department_mappings.get(prefix, 'CMU')

    def _create_basic_course(self, course_code: str) -> Course:
        """
        Create a basic Course object when detail page scraping fails
        Used for departments without working detail pages

        Args:
            course_code: Course code like "15-112"

        Returns:
            Course: Basic Course object with just code and inferred department
        """
        department = self._infer_department(course_code)

        return Course(
            course_id=course_code,
            title=f"Course {course_code}",
            department=department,
            description="Course description not available. This course was found in the CMU course catalog but detailed information could not be extracted.",
            units=12,
            prerequisites=[],
            learning_outcomes=[]
        )

    def save_courses(self, courses: List[Course], path: str = "data/courses.json"):
        """Save courses to JSON file"""
        import os
        os.makedirs(os.path.dirname(path), exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            json.dump([course.to_dict() for course in courses], f, indent=2, ensure_ascii=False)

        print(f"✓ Saved {len(courses)} courses to {path}")


if __name__ == "__main__":
    # Fetch ALL CMU courses from all departments
    import sys

    try:
        print("=" * 80)
        print("CMU Course Fetcher - All Departments Edition")
        print("=" * 80)
        print("\nThis will fetch ALL CMU courses for Fall 2025 from all departments:")
        print("  • School of Computer Science (15-XXX)")
        print("  • Heinz College (94-XXX, 90-XXX, 95-XXX)")
        print("  • Tepper School of Business (73-XXX)")
        print("  • Dietrich College (51-XXX)")
        print("  • Mellon College of Science (21-XXX)")
        print("  • College of Engineering (36-XXX, 24-XXX)")
        print("  • College of Fine Arts (19-XXX)")
        print("  • Information Systems (67-XXX)")
        print("  • Interdisciplinary (99-XXX)")
        print("\nThis may take several minutes...")
        print("=" * 80 + "\n")

        fetcher = CMUCourseFetcherImproved()

        # Use 999999 as a sentinel value meaning "ALL" courses
        courses = fetcher.fetch_courses(max_courses=999999)

        if courses:
            print(f"\n{'=' * 80}")
            print(f"Successfully fetched {len(courses)} CMU courses!")
            print(f"{'=' * 80}")

            # Show sample courses from different departments
            print("\nSample courses by department:")
            by_dept = {}
            for course in courses:
                dept = course.department
                if dept not in by_dept:
                    by_dept[dept] = []
                by_dept[dept].append(course)

            for dept, dept_courses in sorted(by_dept.items()):
                print(f"\n  [{dept}] ({len(dept_courses)} courses)")
                for course in dept_courses[:3]:
                    print(f"    • {course.course_id}: {course.title}")
                    if len(dept_courses) > 3:
                        print(f"      ... and {len(dept_courses) - 3} more")

            # Save to file
            fetcher.save_courses(courses)

            print(f"\n{'=' * 80}")
            print(f"✓ All {len(courses)} courses saved to data/courses.json")
            print(f"{'=' * 80}")
        else:
            print("⚠ No courses fetched")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
