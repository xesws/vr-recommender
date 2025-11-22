#!/usr/bin/env python3
"""
Test Heinz API for course details (no Firecrawl needed!)
"""
import requests
import json

# Test Heinz API
url = "https://api.heinz.cmu.edu/courses_api/course_detail/94-801/"

print("Testing Heinz API for course details...\n")
print(f"URL: {url}\n")

try:
    response = requests.get(url, timeout=10)

    if response.status_code == 200:
        data = response.json()
        print("✓ Got JSON response!")
        print(json.dumps(data, indent=2)[:1000])
    else:
        print(f"❌ Status code: {response.status_code}")
        print(f"Response: {response.text[:500]}")

except Exception as e:
    print(f"❌ Error: {e}")
