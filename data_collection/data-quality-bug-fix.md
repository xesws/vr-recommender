Data Quality Improvement Plan

    Current Issues Analysis

    VR Apps (37 apps - but low quality):
    - Current: "s VR Games on Meta Quest (education)" - article titles, 
    not app names
    - Root cause: Tavily returns search result snippets, not structured 
    app database
    - Problem: No filtering between articles/guides vs actual apps

    Courses (13 courses - poor extraction):
    - Current: "15-213: and 15-210" - parsing fragments, not titles
    - Root cause: Course list format spreads title across multiple lines
    - Problem: No access to individual course detail pages

    Ultra-Thinking: API Strategy Redesign

    Tavily API - Better VR App Strategy:

    1. Target Specific Sources: Search specific Meta Quest databases
      - "site:oculus.com Meta Quest apps"
      - "site:sidequestvr.com educational VR apps"
      - "site:vrchat.com VR apps list"
    2. App Store URL Scraping: Follow results to actual app pages
      - Find app store URLs in results
      - Use Firecrawl to scrape app store pages for structured data
      - Extract: name, description, rating, price, category, features
    3. Better Query Design:
      - "Meta Quest" education apps (quoted exact phrases)
      - "Meta Quest 3" training apps
      - "best VR apps for learning" site:oculus.com
    4. Multi-Stage Process:
      - Stage 1: Use Tavily to find app store URLs
      - Stage 2: Use Firecrawl to scrape detailed app pages

    Firecrawl API - Better Course Strategy:

    1. Course Detail Pages: Each course has a detail page
      - Example: https://csd.cmu.edu/course/15104/f25
      - Contains: full title, description, units, prerequisites, 
    learning outcomes
      - Pattern: /course/{course_number}/{semester}
    2. Action-Based Scraping: Use Firecrawl's action capability
      - Scrape main course list page
      - Extract course numbers
      - Follow links to detail pages
      - Or: Directly scrape known course detail pages
    3. Better URL Targeting:
      - coursecatalog.web.cmu.edu - full course catalog with details
      - Each course has comprehensive information
    4. Extract → Follow Pattern:
      - First pass: Extract all course IDs from list page
      - Second pass: Scrape detail pages for each course

    Implementation Plan

    1. Improve VR App Fetcher:
      - Rewrite search queries to target app stores
      - Extract app store URLs from results
      - Use Firecrawl to scrape app store pages
      - Parse structured app data
    2. Improve Course Fetcher:
      - Target course catalog with details
      - Or extract course IDs then scrape detail pages
      - Better parsing of course format
    3. Quality Metrics:
      - Courses: ≥50 with complete title/description
      - VR Apps: ≥30 with valid names/descriptions
      - Each entry has all required fields populated