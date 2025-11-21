"""
CMU Course Fetcher
Fetches course data from CMU course catalog using Firecrawl
"""

import os
import json
import re
from typing import List, Dict
from dataclasses import asdict

try:
    from firecrawl import FirecrawlApp
except ImportError:
    print("Warning: firecrawl not installed. Install with: pip install firecrawl-py")
    FirecrawlApp = None

from src.models import Course


class CMUCourseFetcher:
    """Fetches CMU course data from the official course catalog"""

    def __init__(self):
        """Initialize the fetcher with Firecrawl API"""
        self.api_key = os.getenv("FIRECRAWL_API_KEY")
        if not self.api_key:
            raise ValueError("FIRECRAWL_API_KEY environment variable not set")

        if FirecrawlApp is None:
            raise ImportError("firecrawl-py not installed. Run: pip install firecrawl-py")

        self.client = FirecrawlApp(api_key=self.api_key)
        self.base_url = "https://www.cmu.edu/hub/registrar/course-schedule/"

    def fetch_courses(self, semester: str = "current") -> List[Course]:
        """
        Fetch CMU courses from the course catalog

        Args:
            semester: Semester to fetch courses for (e.g., "fall2024", "spring2024", "current")

        Returns:
            List[Course]: List of Course objects
        """
        print(f"Fetching CMU courses for {semester}...")

        try:
            # Scrape the course schedule page
            result = self.client.scrape_url(
                self.base_url,
                params={
                    "formats": ["markdown", "html"],
                    "wait_for": "networkidle"
                }
            )

            if not result or not result.get('content'):
                print("⚠ No content received from Firecrawl")
                return []

            # Parse the courses from the scraped content
            courses = self._parse_courses(result)

            print(f"✓ Fetched {len(courses)} courses")
            return courses

        except Exception as e:
            print(f"❌ Error fetching courses: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _parse_courses(self, result: Dict) -> List[Course]:
        """
        Parse courses from Firecrawl result

        Args:
            result: Firecrawl result containing scraped content

        Returns:
            List[Course]: Parsed course list
        """
        courses = []
        content = result.get('content', '')

        # Try multiple parsing strategies

        # Strategy 1: Parse markdown if available
        if 'markdown' in result:
            courses = self._parse_markdown_courses(result['markdown'])

        # Strategy 2: Parse HTML
        if 'html' in result and not courses:
            courses = self._parse_html_courses(result['html'])

        # Strategy 3: Parse from content text
        if not courses:
            courses = self._parse_text_courses(content)

        # Strategy 4: Try to extract from any structured data
        if not courses:
            courses = self._extract_structured_courses(content)

        return courses

    def _parse_markdown_courses(self, markdown: str) -> List[Course]:
        """Parse courses from markdown content"""
        courses = []
        lines = markdown.split('\n')
        current_course = None

        for line in lines:
            line = line.strip()

            # Course code pattern (e.g., 95-865, 73-374)
            course_code_match = re.match(r'^(\d{2}-\d{3})', line)
            if course_code_match:
                if current_course:
                    courses.append(current_course)

                current_course = {
                    'course_id': course_code_match.group(1),
                    'title': '',
                    'department': 'CMU',
                    'description': '',
                    'units': 0,
                    'prerequisites': [],
                    'learning_outcomes': []
                }
                continue

            # Title (usually the next line after course code)
            if current_course and not current_course['title'] and line and not line.startswith('Course'):
                current_course['title'] = line[:200]
                continue

            # Description (looking for descriptive text)
            if current_course and current_course['description'] == '' and len(line) > 50:
                current_course['description'] = line[:500]
                continue

        # Don't forget the last course
        if current_course:
            courses.append(current_course)

        # Convert to Course objects
        return [self._dict_to_course(c) for c in courses if c['course_id'] and c['title']]

    def _parse_html_courses(self, html: str) -> List[Course]:
        """Parse courses from HTML content"""
        courses = []

        # Look for course code patterns in HTML
        # Pattern like <strong>95-865</strong> or <span>95-865</span>
        course_pattern = r'<[^>]*>(\d{2}-\d{3})<[^>]*>'
        matches = re.finditer(course_pattern, html, re.IGNORECASE)

        for match in matches:
            # Extract context around the course code
            start = max(0, match.start() - 200)
            end = min(len(html), match.end() + 200)
            context = html[start:end]

            # Try to extract course info from context
            course = self._extract_course_from_context(context, match.group(1))
            if course:
                courses.append(course)

        return courses

    def _parse_text_courses(self, text: str) -> List[Course]:
        """Parse courses from plain text"""
        courses = []

        # Split into sections
        sections = text.split('\n\n')

        for section in sections:
            # Look for course codes
            course_code = re.search(r'\b\d{2}-\d{3}\b', section)
            if course_code:
                course = {
                    'course_id': course_code.group(),
                    'title': '',
                    'department': 'CMU',
                    'description': '',
                    'units': 0,
                    'prerequisites': [],
                    'learning_outcomes': []
                }

                # Try to extract title (usually on a separate line or in first sentence)
                title_match = re.search(r'\b\d{2}-\d{3}\s+(.+?)(?:\n|\.|$)', section)
                if title_match:
                    course['title'] = title_match.group(1).strip()[:200]

                # Description: take first substantial paragraph
                desc_match = re.search(r'\n\n(.+?)(?:\n\n|\.|$)', section, re.DOTALL)
                if desc_match:
                    course['description'] = desc_match.group(1).strip()[:500]

                courses.append(course)

        return [self._dict_to_course(c) for c in courses if c['course_id']]

    def _extract_structured_courses(self, content: str) -> List[Course]:
        """Extract courses using flexible pattern matching"""
        courses = []
        lines = content.split('\n')

        # Track potential course patterns
        for i, line in enumerate(lines):
            line = line.strip()

            # Check for course code
            code_match = re.search(r'(\d{2}-\d{3})', line)
            if code_match:
                course_id = code_match.group(1)

                # Look around this line for title and description
                context_lines = lines[max(0, i-2):i+5]

                course_dict = {
                    'course_id': course_id,
                    'title': '',
                    'department': 'CMU',
                    'description': '',
                    'units': 0,
                    'prerequisites': [],
                    'learning_outcomes': []
                }

                # Try to find title in next line
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line and not re.search(r'\d{2}-\d{3}', next_line):
                        course_dict['title'] = next_line[:200]

                # Try to find description in subsequent lines
                for j in range(i + 1, min(i + 5, len(lines))):
                    test_line = lines[j].strip()
                    if len(test_line) > 20 and not re.search(r'\d{2}-\d{3}', test_line):
                        course_dict['description'] = test_line[:500]
                        break

                courses.append(course_dict)

        return [self._dict_to_course(c) for c in courses if c['course_id'] and c['title']]

    def _extract_course_from_context(self, context: str, course_id: str) -> dict:
        """Extract course info from a context string"""
        # Simple extraction - can be enhanced
        return {
            'course_id': course_id,
            'title': '',
            'department': 'CMU',
            'description': context[:500],
            'units': 0,
            'prerequisites': [],
            'learning_outcomes': []
        }

    def _dict_to_course(self, course_dict: dict) -> Course:
        """Convert dict to Course object"""
        # Provide defaults for missing fields
        defaults = {
            'title': 'Unknown Course',
            'department': 'CMU',
            'description': '',
            'units': 0,
            'prerequisites': [],
            'learning_outcomes': []
        }

        # Fill in defaults
        for key, value in defaults.items():
            if not course_dict.get(key):
                course_dict[key] = value

        return Course(**course_dict)

    def save_courses(self, courses: List[Course], path: str = "data/courses.json"):
        """
        Save courses to JSON file

        Args:
            courses: List of Course objects
            path: Output file path
        """
        os.makedirs(os.path.dirname(path), exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            json.dump([asdict(course) for course in courses], f, indent=2, ensure_ascii=False)

        print(f"✓ Saved {len(courses)} courses to {path}")


if __name__ == "__main__":
    # Test the fetcher
    import sys

    try:
        fetcher = CMUCourseFetcher()
        courses = fetcher.fetch_courses()

        if courses:
            print(f"\nFirst course example:")
            print(f"  Course ID: {courses[0].course_id}")
            print(f"  Title: {courses[0].title}")
            print(f"  Description: {courses[0].description[:100]}...")

            # Save to file
            fetcher.save_courses(courses)
        else:
            print("⚠ No courses fetched - check API key and network connection")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
