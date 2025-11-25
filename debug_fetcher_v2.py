import os
import sys
from dotenv import load_dotenv

# Load env vars
load_dotenv()

# Fix path to import fetcher
sys.path.insert(0, os.path.abspath("vr-recommender"))
from data_collection.src.data_collection.course_fetcher_improved import CMUCourseFetcherImproved

def debug_fetch():
    print("🔍 Debugging Course Fetcher...")
    fetcher = CMUCourseFetcherImproved()
    
    dept = "School of Computer Science"
    url = "http://coursecatalog.web.cmu.edu/schools-colleges/schoolofcomputerscience/courses/"
    
    print(f"\n[1] Testing Catalog Extraction for: {dept}")
    print(f"    URL: {url}")
    
    try:
        # Directly call the extraction method
        codes = fetcher._extract_course_codes_from_catalog(url)
        print(f"\n👉 Result: Found {len(codes)} codes")
        if codes:
            print(f"   Examples: {codes[:5]}")
        else:
            print("   ❌ No codes found! Firecrawl might be returning empty content or regex mismatch.")
            
            # If empty, let's try to see a snippet of the raw content if possible (need to modify fetcher or verify manually)
            # actually I can just run a quick firecrawl scrape here to see raw output
            print("\n[2] Raw Scrape Diagnostic...")
            res = fetcher.client.scrape(url=url, formats=["markdown"])
            md = res.get('markdown', '')
            print(f"    Raw Markdown Length: {len(md)}")
            print(f"    Snippet (first 500 chars):\n    {md[:500]}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    debug_fetch()
