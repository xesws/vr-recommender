#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# Set API keys
os.environ["FIRECRAWL_API_KEY"] = "fc-1213ec67816c4536b78d268eb1f04002"
os.environ["TAVILY_API_KEY"] = "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"

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Now import and test
from data_collection.vr_app_fetcher import VRAppFetcher

print("Testing VR App Fetcher...")
fetcher = VRAppFetcher()
apps = fetcher.fetch_apps(categories=["education", "training"])

print(f"\n✅ Successfully fetched {len(apps)} VR apps")

if apps:
    print("\nFirst 3 apps:")
    for app in apps[:3]:
        print(f"  • {app.name} ({app.category})")
        print(f"    Description: {app.description[:100]}...")

    # Save to file
    fetcher.save_apps(apps, "data/vr_apps.json")
    print(f"\n✅ Saved to data/vr_apps.json")
