#!/usr/bin/env python3
import os
os.environ["TAVILY_API_KEY"] = "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"

import sys
sys.path.insert(0, 'src')

from data_collection.vr_app_fetcher_improved import VRAppFetcherImproved

fetcher = VRAppFetcherImproved()
apps = fetcher.fetch_apps()

print(f'\nTotal: {len(apps)}')
print('\nFirst 10:')
for app in apps[:10]:
    print(f"  - {app.name} ({app.category})")
    print(f"    Description: {app.description[:80]}...")
    print(f"    Skills: {', '.join(app.skills_developed)}")
    print()

# Save to file
fetcher.save_apps(apps)
print(f"\n✅ Saved {len(apps)} high-quality VR apps to data/vr_apps.json")
