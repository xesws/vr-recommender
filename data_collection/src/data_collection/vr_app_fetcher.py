"""
VR App Fetcher
Searches for Meta Quest VR apps using Tavily API
"""

import os
import json
import re
from typing import List, Dict
from dataclasses import asdict

try:
    from tavily import TavilyClient
except ImportError:
    print("Warning: tavily not installed. Install with: pip install tavily-python")
    TavilyClient = None

from src.models import VRApp


class VRAppFetcher:
    """Fetches VR app data using Tavily search API"""

    def __init__(self):
        """Initialize the fetcher with Tavily API"""
        self.api_key = os.getenv("TAVILY_API_KEY")
        if not self.api_key:
            raise ValueError("TAVILY_API_KEY environment variable not set")

        if TavilyClient is None:
            raise ImportError("tavily-python not installed. Run: pip install tavily-python")

        self.client = TavilyClient(api_key=self.api_key)

    def fetch_apps(self, categories: List[str] = None) -> List[VRApp]:
        """
        Search for Meta Quest VR apps

        Args:
            categories: App categories to search ["education", "training", "productivity", "health", "fitness"]

        Returns:
            List[VRApp]: List of VR app objects
        """
        categories = categories or ["education", "training", "productivity"]
        print(f"Searching for VR apps in categories: {', '.join(categories)}")

        all_apps = []

        for category in categories:
            print(f"\n  Searching category: {category}...")
            apps = self._search_category(category)
            all_apps.extend(apps)
            print(f"  ✓ Found {len(apps)} apps")

        # Remove duplicates
        unique_apps = self._deduplicate(all_apps)
        print(f"\n✓ Total unique apps found: {len(unique_apps)}")

        return unique_apps

    def _search_category(self, category: str) -> List[VRApp]:
        """
        Search for apps in a specific category

        Args:
            category: Category to search

        Returns:
            List[VRApp]: Apps in the category
        """
        queries = [
            f"Meta Quest VR apps {category}",
            f"Oculus {category} VR applications",
            f"Quest VR {category} software",
            f"VR {category} training apps Meta Quest"
        ]

        all_results = []

        for query in queries:
            try:
                results = self.client.search(
                    query=query,
                    search_depth="advanced",
                    max_results=10,
                    include_answer=False,
                    include_raw_content=False
                )

                if results.get("results"):
                    all_results.extend(results["results"])

            except Exception as e:
                print(f"    ⚠ Error with query '{query}': {e}")

        # Parse results
        apps = self._parse_results(all_results, category)
        return apps

    def _parse_results(self, results: List[Dict], category: str) -> List[VRApp]:
        """
        Parse search results into VRApp objects

        Args:
            results: List of search result dictionaries
            category: The category being searched

        Returns:
            List[VRApp]: Parsed app list
        """
        apps = []

        for result in results:
            app = self._extract_app_info(result, category)
            if app and app.name and app.app_id:
                apps.append(app)

        return apps

    def _extract_app_info(self, result: Dict, category: str) -> VRApp:
        """
        Extract VR app info from a search result

        Args:
            result: Search result dictionary
            category: App category

        Returns:
            VRApp: Extracted app object
        """
        # Extract app name from title or content
        title = result.get('title', '')
        content = result.get('content', '')

        # Try multiple strategies to find app name
        app_name = self._extract_app_name(title, content)

        if not app_name:
            return None

        # Generate app_id
        app_id = self._generate_app_id(app_name)

        # Extract description
        description = self._extract_description(content, title)

        # Extract features
        features = self._extract_features(content)

        # Determine category (use provided category or infer)
        app_category = self._infer_category(content, title, category)

        # Estimate rating (since Tavily doesn't provide this)
        rating = self._estimate_rating(content)

        # Determine price
        price = self._extract_price(content)

        # Extract skills
        skills = self._extract_skills(content, features)

        return VRApp(
            app_id=app_id,
            name=app_name,
            category=app_category,
            description=description,
            features=features,
            skills_developed=skills,
            rating=rating,
            price=price
        )

    def _extract_app_name(self, title: str, content: str) -> str:
        """Extract VR app name from title or content"""
        # Strategy 1: Look for quoted app names
        quoted_match = re.search(r'"([^"]+)"', title)
        if quoted_match:
            return quoted_match.group(1).strip()

        # Strategy 2: Look for "App Name:" pattern
        app_name_match = re.search(r'app:?\s*["\']?([^"\'\n,.]+)["\']?', title, re.IGNORECASE)
        if app_name_match:
            return app_name_match.group(1).strip()

        # Strategy 3: Extract from title (before dash or colon)
        if ' - ' in title:
            return title.split(' - ')[0].strip()
        if ':' in title:
            parts = title.split(':')
            if len(parts) > 1 and len(parts[1].strip()) < 50:
                return parts[1].strip()

        # Strategy 4: Look for VR/VR-related keywords and get preceding word
        vr_patterns = [
            r'(.+?)\s+(?:VR|VR app|virtual reality)',
            r'(?:Meta Quest|Oculus)\s+(.+?)(?:\s|\n|$)',
            r'(?:VR|VR app)\s+(.+?)(?:\s|\n|$)'
        ]

        for pattern in vr_patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match and len(match.group(1)) > 2 and len(match.group(1)) < 50:
                return match.group(1).strip()

        # Strategy 5: Extract from content
        if content:
            content_match = re.search(r'"([^"]+)"', content)
            if content_match:
                name = content_match.group(1).strip()
                if len(name) < 50 and len(name) > 2:
                    return name

        return None

    def _generate_app_id(self, app_name: str) -> str:
        """Generate a unique app ID from app name"""
        # Remove special characters and convert to lowercase
        app_id = re.sub(r'[^a-zA-Z0-9]', '_', app_name.strip())
        # Remove multiple underscores
        app_id = re.sub(r'_+', '_', app_id)
        # Remove leading/trailing underscores
        app_id = app_id.strip('_')
        return app_id[:50]  # Limit length

    def _extract_description(self, content: str, title: str) -> str:
        """Extract description from content"""
        # Take first substantial paragraph
        if not content:
            return title[:500] if title else ""

        # Split into sentences and take first 1-2 meaningful ones
        sentences = re.split(r'[.!?]+', content)
        description = ""

        for sentence in sentences[:2]:
            sentence = sentence.strip()
            if len(sentence) > 20:
                description += sentence + ". "
            if len(description) > 200:
                break

        return description.strip()[:500]

    def _extract_features(self, content: str) -> List[str]:
        """Extract features from content"""
        features = []

        # Look for bullet points or feature lists
        lines = content.split('\n') if content else []

        for line in lines:
            line = line.strip()

            # Bullet points
            if line.startswith('•') or line.startswith('-') or line.startswith('*'):
                feature = re.sub(r'^[•\-\*]\s*', '', line).strip()
                if len(feature) > 5 and len(feature) < 100:
                    features.append(feature)

            # Numbered lists
            if re.match(r'^\d+\.', line):
                feature = re.sub(r'^\d+\.\s*', '', line).strip()
                if len(feature) > 5 and len(feature) < 100:
                    features.append(feature)

            # Key feature indicators
            if any(keyword in line.lower() for keyword in ['feature:', 'includes:', 'provides:']):
                feature = re.sub(r'.*?:\s*', '', line).strip()
                if len(feature) > 5:
                    features.append(feature)

        return features[:10]  # Limit to 10 features

    def _infer_category(self, content: str, title: str, default_category: str) -> str:
        """Infer category from content"""
        text = f"{title} {content}".lower()

        # Category keywords mapping
        category_map = {
            'education': ['education', 'learning', 'student', 'teacher', 'school', 'course'],
            'training': ['training', 'skill', 'practice', 'exercise', 'learning'],
            'productivity': ['productivity', 'work', 'business', 'office', 'collaboration', 'remote work'],
            'health': ['health', 'medical', 'therapy', 'wellness', 'exercise'],
            'fitness': ['fitness', 'workout', 'exercise', 'gym', 'training'],
            'entertainment': ['entertainment', 'game', 'fun', 'leisure', 'hobby'],
            'communication': ['communication', 'chat', 'video call', 'meeting', 'social']
        }

        # Check for category keywords
        for category, keywords in category_map.items():
            if any(keyword in text for keyword in keywords):
                return category

        # Default to provided category
        return default_category

    def _estimate_rating(self, content: str) -> float:
        """Estimate rating from content"""
        if not content:
            return 4.0  # Default rating

        text = content.lower()

        # Look for rating patterns
        rating_patterns = [
            r'rating[:\s]+(\d+\.?\d*)/5',
            r'rating[:\s]+(\d+\.?\d*)',
            r'(\d+\.?\d*)\s*stars?',
            r'(\d+\.?\d*)/5'
        ]

        for pattern in rating_patterns:
            match = re.search(pattern, text)
            if match:
                rating = float(match.group(1))
                # Normalize to 5-star scale
                if rating <= 1.0:
                    rating *= 5
                if 0 < rating <= 5:
                    return rating

        # No rating found - return default
        return 4.0

    def _extract_price(self, content: str) -> str:
        """Extract price information from content"""
        if not content:
            return "Unknown"

        text = content.lower()

        # Price patterns
        price_patterns = [
            r'\$?(\d+\.?\d*)\s*(?:usd|dollars?)',
            r'price[:\s]+\$?(\d+\.?\d*)',
            r'costs?\s+\$?(\d+\.?\d*)',
            r'\$(\d+\.?\d*)'
        ]

        for pattern in price_patterns:
            match = re.search(pattern, text)
            if match:
                price = float(match.group(1))
                if price == 0:
                    return "Free"
                elif price < 100:
                    return f"${price:.2f}"
                else:
                    return f"${price:.0f}"

        # Look for "free" keyword
        if 'free' in text:
            return "Free"

        # Look for "paid" or "premium"
        if 'premium' in text or 'paid' in text:
            return "Paid"

        return "Unknown"

    def _extract_skills(self, content: str, features: List[str]) -> List[str]:
        """Extract skills developed from content and features"""
        skills = []

        # Skills keywords
        skill_keywords = {
            'programming': ['programming', 'coding', 'software', 'development'],
            'data analysis': ['data', 'analytics', 'statistics', 'analysis'],
            'machine learning': ['machine learning', 'ml', 'ai', 'artificial intelligence'],
            'design': ['design', '3d modeling', 'creative', 'art'],
            'communication': ['communication', 'presentation', 'public speaking'],
            'collaboration': ['collaboration', 'team', 'cooperation', 'remote work'],
            'visualization': ['visualization', 'visual', 'charts', 'graphs'],
            'problem solving': ['problem solving', 'critical thinking', 'analysis'],
            'learning': ['learning', 'education', 'training', 'skill development']
        }

        text = f"{content} {' '.join(features)}".lower()

        # Find matching skills
        for skill, keywords in skill_keywords.items():
            if any(keyword in text for keyword in keywords):
                skills.append(skill)

        return skills[:8]  # Limit to 8 skills

    def _deduplicate(self, apps: List[VRApp]) -> List[VRApp]:
        """Remove duplicate apps by app_id or name"""
        seen = set()
        unique = []

        for app in apps:
            # Use app_id for deduplication if available, otherwise use name
            identifier = app.app_id if app.app_id else app.name

            if identifier not in seen:
                seen.add(identifier)
                unique.append(app)

        return unique

    def save_apps(self, apps: List[VRApp], path: str = "data/vr_apps.json"):
        """
        Save apps to JSON file

        Args:
            apps: List of VRApp objects
            path: Output file path
        """
        os.makedirs(os.path.dirname(path), exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            json.dump([asdict(app) for app in apps], f, indent=2, ensure_ascii=False)

        print(f"✓ Saved {len(apps)} apps to {path}")


if __name__ == "__main__":
    # Test the fetcher
    import sys

    try:
        fetcher = VRAppFetcher()
        apps = fetcher.fetch_apps()

        if apps:
            print(f"\nFirst app example:")
            print(f"  App ID: {apps[0].app_id}")
            print(f"  Name: {apps[0].name}")
            print(f"  Category: {apps[0].category}")
            print(f"  Description: {apps[0].description[:100]}...")

            # Save to file
            fetcher.save_apps(apps)
        else:
            print("⚠ No apps fetched - check API key and network connection")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
