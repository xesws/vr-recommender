"""
VR App Fetcher - Improved Version
Uses Tavily's direct answers to extract curated VR app names
"""
import os
import json
import re
from typing import List, Dict

try:
    from tavily import TavilyClient
except ImportError:
    print("Warning: tavily not installed. Install with: pip install tavily-python")
    TavilyClient = None

from models import VRApp


class VRAppFetcherImproved:
    """Improved VR app fetcher using direct app name extraction"""

    def __init__(self, api_key: str = None):
        """Initialize the fetcher with Tavily API"""
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        if not self.api_key:
            # raise ValueError("TAVILY_API_KEY environment variable not set")
            # Warn instead of crash to allow curated apps
            print("Warning: TAVILY_API_KEY not set. Only curated apps will be available.")
            self.client = None
        else:
            if TavilyClient is None:
                raise ImportError("tavily-python not installed. Run: pip install tavily-python")
            self.client = TavilyClient(api_key=self.api_key)

        # Curated VR apps database with high-quality data
        self.curated_apps = self._build_curated_database()

    def fetch_apps(self, categories: List[str] = None) -> List[VRApp]:
        """
        Fetch VR apps using improved strategy

        Strategy:
        1. Start with curated database
        2. Use Tavily to discover new apps
        3. Extract app names from search results
        4. Build comprehensive app list

        Args:
            categories: App categories to search

        Returns:
            List[VRApp]: List of VR app objects
        """
        categories = categories or ["education", "training", "productivity"]
        print(f"Fetching VR apps for categories: {', '.join(categories)}")

        # Start with curated apps matching categories
        apps = []
        for category in categories:
            matching_apps = [app for app in self.curated_apps if app.category == category]
            apps.extend(matching_apps)
            print(f"  {category}: {len(matching_apps)} curated apps")

        # Use Tavily to find additional apps
        additional_apps = self._search_additional_apps(categories)
        print(f"  Found {len(additional_apps)} additional apps via search")

        # Combine and deduplicate
        all_apps = apps + additional_apps
        unique_apps = self._deduplicate(all_apps)

        print(f"\n✓ Total unique apps: {len(unique_apps)}")
        return unique_apps

    def _search_additional_apps(self, categories: List[str]) -> List[VRApp]:
        """Use Tavily to search for additional apps"""
        apps = []

        for category in categories:
            # Search for app lists and reviews
            queries = [
                f'best VR {category} apps Meta Quest',
                f'top {category} apps for learning in VR',
                f'Meta Quest {category} applications list',
            ]

            for query in queries:
                try:
                    results = self.client.search(
                        query=query,
                        search_depth="advanced",
                        max_results=3,
                        include_answer=True
                    )

                    # Extract app names from direct answer
                    if results.get("answer"):
                        app_names = self._extract_app_names(results["answer"])
                        for name in app_names:
                            if len(name) > 2 and len(name) < 50:
                                app = self._build_app_from_name(name, category)
                                if app:
                                    apps.append(app)

                    # Also check results for app names
                    for result in results.get("results", []):
                        title = result.get("title", "")
                        app_names = self._extract_app_names(title)
                        for name in app_names:
                            if len(name) > 2 and len(name) < 50:
                                app = self._build_app_from_name(name, category)
                                if app:
                                    apps.append(app)

                except Exception as e:
                    print(f"    ⚠ Error with query '{query}': {e}")

        return apps

    def _extract_app_names(self, text: str) -> List[str]:
        """Extract potential VR app names from text"""
        if not text:
            return []

        app_names = []

        # Pattern 1: Names in quotes
        quoted = re.findall(r'"([^"]+)"', text)
        app_names.extend(quoted)

        # Pattern 2: Look for capitalized words that might be app names
        # Specifically after words like "apps include", "such as", etc.
        patterns = [
            r'(?:including|include|such as|like|examples?):\s*([A-Z][A-Za-z0-9\s]+?)(?:\.|,|\n)',
            r'(?:best|top|leading)\s+([A-Z][A-Za-z0-9\s]+?)(?:\s+(?:app|VR|Quest))',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            app_names.extend(matches)

        # Clean up names
        cleaned = []
        for name in app_names:
            name = re.sub(r'\s+', ' ', name.strip())
            # Filter out non-app-like entries
            if len(name) > 2 and not re.match(r'^(and|or|the|best|top|list|apps|VR|Quest)$', name.lower()):
                cleaned.append(name)

        # Remove duplicates while preserving order
        seen = set()
        unique = []
        for name in cleaned:
            if name.lower() not in seen:
                seen.add(name.lower())
                unique.append(name)

        return unique[:10]  # Limit per search

    def _build_app_from_name(self, name: str, category: str) -> VRApp:
        """Build a VRApp object from a name with inferred data"""
        # Infer category from name and keywords
        inferred_category = self._infer_category_from_name(name)

        # Generate app_id
        app_id = self._generate_app_id(name)

        # Build features and skills based on category
        features, skills = self._infer_features_and_skills(name, category)

        return VRApp(
            app_id=app_id,
            name=name,
            category=inferred_category,
            description=f"VR application focused on {category}. Enhances learning and skill development through immersive virtual reality experiences.",
            features=features,
            skills_developed=skills,
            rating=4.0,  # Default rating
            price="Unknown"
        )

    def _infer_category_from_name(self, name: str) -> str:
        """Infer category from app name"""
        name_lower = name.lower()

        if any(word in name_lower for word in ['education', 'learn', 'study', 'school']):
            return 'education'
        if any(word in name_lower for word in ['train', 'practice', 'skill']):
            return 'training'
        if any(word in name_lower for word in ['work', 'productivity', 'office', 'desktop', 'virtual']):
            return 'productivity'
        if any(word in name_lower for word in ['health', 'medical', 'anatomy', 'therapy']):
            return 'health'
        if any(word in name_lower for word in ['fitness', 'workout', 'exercise']):
            return 'fitness'
        if any(word in name_lower for word in ['game', 'play', 'fun']):
            return 'entertainment'

        return 'productivity'  # Default

    def _generate_app_id(self, name: str) -> str:
        """Generate app ID from name"""
        app_id = re.sub(r'[^a-zA-Z0-9]', '_', name.strip())
        app_id = re.sub(r'_+', '_', app_id)
        return app_id.strip('_')[:50]

    def _infer_features_and_skills(self, name: str, category: str) -> tuple:
        """Infer features and skills from app name and category"""
        name_lower = name.lower()
        features = []
        skills = []

        # Category-based inference
        if category == 'education':
            features = ['Interactive learning', '3D visualizations', 'Knowledge assessment']
            skills = ['Learning', 'Knowledge retention', 'Visual understanding']

        elif category == 'training':
            features = ['Skill practice', 'Realistic simulations', 'Progress tracking']
            skills = ['Practical skills', 'Problem solving', 'Technique mastery']

        elif category == 'productivity':
            features = ['Multi-screen setup', 'Remote collaboration', 'Workspace customization']
            skills = ['Productivity', 'Remote work', 'Collaboration']

        elif category == 'health':
            features = ['Medical visualization', 'Interactive models', 'Educational content']
            skills = ['Medical knowledge', 'Anatomy understanding', 'Healthcare training']

        elif category == 'fitness':
            features = ['Workout tracking', 'Guided exercises', 'Physical activity']
            skills = ['Physical fitness', 'Exercise techniques', 'Health maintenance']

        else:
            features = ['Immersive experience', 'Interactive interface']
            skills = ['General skills', 'Entertainment', 'Engagement']

        return features[:5], skills[:5]

    def _build_curated_database(self) -> List[VRApp]:
        """Build a curated database of known VR apps"""
        apps = []

        # Education Apps
        education_apps = [
            "InMind", "VR Museum: Art Through Time", "Origami Dojo",
            "VEDAVI VR Human Anatomy", "3D Organon VR Anatomy",
            "Mission ISS", "Babel VR", "Unimersiv",
            "MEL Science VR", "Chemistry Lab", "宇宙VR (Space VR)",
            "Newton's Cradle", "Solar System VR", "GeoGebra AR",
            "Molecules by Theodore Gray", "The Body VR", "Google Expeditions",
            "Discovery VR", "Titans of Space", "Apollo 11",
            "Cosmic Watch", "Skygaze", "Universe Sandbox",
        ]

        for name in education_apps:
            app_id = self._generate_app_id(name)
            apps.append(VRApp(
                app_id=app_id,
                name=name,
                category="education",
                description=f"Educational VR application that enhances learning through immersive experiences. Perfect for students and educators.",
                features=['Interactive learning', 'Educational content', '3D visualizations'],
                skills_developed=['Learning', 'Knowledge retention', 'Visual understanding'],
                rating=4.2,
                price="$0-19.99"
            ))

        # Productivity Apps
        productivity_apps = [
            "Virtual Desktop", "Immersed", "Horizon Workrooms",
            "Spatial", "Arthur VR", "MeetinVR",
            "Glue", "Spatial Rooms", "VRChat",
            "Rec Room", "Bigscreen", "Mozilla Hubs",
            "AltspaceVR", "VRWorkout", "Supernatural",
            "FitXR", "BoxVR", "Beat Saber",
            "Robo Recall", "Boneworks", "Half-Life: Alyx",
            "The Walking Dead: Saints & Sinners", "Population: One",
        ]

        for name in productivity_apps:
            app_id = self._generate_app_id(name)
            apps.append(VRApp(
                app_id=app_id,
                name=name,
                category="productivity",
                description=f"Productivity-focused VR application for enhanced workflow and collaboration.",
                features=['Workflow enhancement', 'Productivity tools', 'Interface optimization'],
                skills_developed=['Productivity', 'Remote work', 'Collaboration'],
                rating=4.3,
                price="$0-29.99"
            ))

        # Training Apps
        training_apps = [
            "Metaenga", "Vrainers", "SafeFire VR",
            "STRIVR", "Voxels", "Immersive Training",
            "Engage VR", "VirBELA", "Campus",
            "MediTeach VR", "SimX VR", "OrthoVR",
            "Dentali VR", "VR Surgical Training", "Surgical Theater",
            "Level Ex", "FundamentalVR", "Touch Surgery",
            "AppliedVR", "Psious", "Luminopia",
            "Caribu", "Futuclass Education", "VictoryXR",
        ]

        for name in training_apps:
            app_id = self._generate_app_id(name)
            apps.append(VRApp(
                app_id=app_id,
                name=name,
                category="training",
                description=f"Training and skill development VR application with realistic simulations.",
                features=['Skill training', 'Realistic simulations', 'Progress tracking'],
                skills_developed=['Practical skills', 'Professional development', 'Technical training'],
                rating=4.1,
                price="$10-49.99"
            ))

        return apps

    def _deduplicate(self, apps: List[VRApp]) -> List[VRApp]:
        """Remove duplicate apps by app_id"""
        seen = set()
        unique = []

        for app in apps:
            if app.app_id not in seen:
                seen.add(app.app_id)
                unique.append(app)

        return unique

    def save_apps(self, apps: List[VRApp], path: str = "data/vr_apps.json"):
        """Save apps to JSON file"""
        import os
        os.makedirs(os.path.dirname(path), exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            json.dump([app.to_dict() for app in apps], f, indent=2, ensure_ascii=False)

        print(f"✓ Saved {len(apps)} apps to {path}")


if __name__ == "__main__":
    # Test the improved fetcher
    import sys

    try:
        fetcher = VRAppFetcherImproved()
        apps = fetcher.fetch_apps()

        print(f"\n✅ Successfully fetched {len(apps)} VR apps")

        if apps:
            print("\nSample apps:")
            for app in apps[:5]:
                print(f"  • {app.name} ({app.category})")
                print(f"    {app.description[:80]}...")

            # Save to file
            fetcher.save_apps(apps)
        else:
            print("⚠ No apps fetched")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
