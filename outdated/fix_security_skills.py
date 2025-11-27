import json
import os
import re
from typing import List, Dict

DATA_DIR = "data_collection/data"
COURSES_FILE = os.path.join(DATA_DIR, "courses.json")
SKILLS_FILE = os.path.join(DATA_DIR, "skills.json")
COURSE_SKILLS_FILE = os.path.join(DATA_DIR, "course_skills.json")

SECURITY_KEYWORDS = [
    "Cyber Security", "Information Security", "Network Security", 
    "Software Security", "Cryptography", "Privacy Engineering", 
    "Vulnerability Analysis", "Secure Coding", "Ethical Hacking",
    "Risk Management", "Security Protocols"
]

def load_json(path):
    with open(path, 'r') as f:
        return json.load(f)

def save_json(data, path):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def quick_extract_security_skills(text: str) -> List[str]:
    found = []
    text_lower = text.lower()
    
    # Heuristic matching
    for kw in SECURITY_KEYWORDS:
        # Simple partial match
        if kw.lower() in text_lower:
            found.append(kw)
            
    # Specific rule for "Security and Privacy" -> Cyber Security
    if "security and privacy" in text_lower:
        found.append("Cyber Security")
        
    return list(set(found))

def main():
    print("=== Incremental Security Skill Fix ===")
    
    courses = load_json(COURSES_FILE)
    skills = load_json(SKILLS_FILE)
    course_skills = load_json(COURSE_SKILLS_FILE)
    
    existing_skill_names = {s['name'] for s in skills}
    new_skills_added = 0
    new_relations_added = 0
    
    for course in courses:
        # Check if course is relevant
        full_text = (course.get('title', '') + " " + course.get('description', '')).lower()
        if "security" not in full_text:
            continue
            
        print(f"Processing: {course['title']}")
        
        extracted = quick_extract_security_skills(full_text)
        if not extracted:
            continue
            
        print(f"  -> Found: {extracted}")
        
        for skill_name in extracted:
            # 1. Add to skills.json if new
            if skill_name not in existing_skill_names:
                new_skill = {
                    "name": skill_name,
                    "category": "technical",
                    "aliases": [],
                    "source_count": 1
                }
                skills.append(new_skill)
                existing_skill_names.add(skill_name)
                new_skills_added += 1
            
            # 2. Add to course_skills.json
            # Check if relation exists
            exists = any(
                r['source_id'] == course['course_id'] and r['skill_name'] == skill_name 
                for r in course_skills
            )
            
            if not exists:
                course_skills.append({
                    "source_id": course['course_id'],
                    "source_type": "course",
                    "skill_name": skill_name,
                    "weight": 0.95  # High confidence
                })
                new_relations_added += 1

    print(f"\nSummary:")
    print(f"  New Skills Created: {new_skills_added}")
    print(f"  New Relations Created: {new_relations_added}")
    
    if new_skills_added > 0 or new_relations_added > 0:
        print("Saving files...")
        save_json(skills, SKILLS_FILE)
        save_json(course_skills, COURSE_SKILLS_FILE)
        print("Done.")
    else:
        print("No changes needed.")

if __name__ == "__main__":
    main()
