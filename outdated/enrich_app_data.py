import json
import os

DATA_DIR = "data_collection/data"
APPS_FILE = os.path.join(DATA_DIR, "vr_apps.json")
APP_SKILLS_FILE = os.path.join(DATA_DIR, "app_skills.json")
SKILLS_FILE = os.path.join(DATA_DIR, "skills.json")

def load_json(path):
    with open(path, 'r') as f:
        return json.load(f)

def save_json(data, path):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def main():
    print("=== Enriching App Data with Domain Skills ===")
    
    apps = load_json(APPS_FILE)
    app_skills = load_json(APP_SKILLS_FILE)
    skills_db = load_json(SKILLS_FILE)
    existing_skills = {s["name"] for s in skills_db}
    
    # Define enrichment map: keyword in Name/Desc -> List of new skills
    enrichment_map = {
        "GeoGebra": ["Mathematics", "Geometry", "Calculus", "Data Visualization"],
        "Molecules": ["Chemistry", "Molecular Biology", "Science"],
        "Chemistry": ["Chemistry", "Science", "Lab Safety"],
        "Body": ["Biology", "Anatomy", "Health Science", "Medicine"],
        "Anatomy": ["Biology", "Anatomy", "Medicine"],
        "Surgical": ["Medicine", "Surgery", "Health Science"],
        "Solar System": ["Astronomy", "Physics", "Space Science"],
        "Space": ["Astronomy", "Physics"],
        "Universe": ["Astronomy", "Physics"],
        "Cosmic": ["Astronomy"],
        "Virtual Desktop": ["Programming", "Computer Science", "Data Analysis", "Remote Work"],
        "Immersed": ["Programming", "Computer Science", "Data Analysis", "Remote Work"],
        "Workrooms": ["Collaboration", "Project Management", "Communication"],
        "InMind": ["Neuroscience", "Brain Science", "Psychology", "Artificial Intelligence"], # AI conceptual link
        "VRChat": ["Social Interaction", "Communication", "Community Building"],
        "Rec Room": ["Social Interaction", "Game Design", "Creativity"]
    }
    
    new_relations_count = 0
    new_skills_count = 0
    
    for app in apps:
        name = app.get("name", "")
        desc = app.get("description", "")
        
        # Find matching keywords
        matched_skills = set()
        for key, new_skills in enrichment_map.items():
            if key.lower() in name.lower() or key.lower() in desc.lower():
                matched_skills.update(new_skills)
        
        if not matched_skills:
            continue
            
        print(f"Enriching '{name}' with: {matched_skills}")
        
        # Update files
        for skill_name in matched_skills:
            # 1. Ensure skill exists in skills.json
            if skill_name not in existing_skills:
                skills_db.append({
                    "name": skill_name,
                    "category": "domain", # Assume domain for these high-level topics
                    "aliases": [],
                    "source_count": 1
                })
                existing_skills.add(skill_name)
                new_skills_count += 1
            
            # 2. Add relation to app_skills.json
            # Check if exists
            exists = any(r["source_id"] == app["app_id"] and r["skill_name"] == skill_name for r in app_skills)
            if not exists:
                app_skills.append({
                    "source_id": app["app_id"],
                    "source_type": "vr_app",
                    "skill_name": skill_name,
                    "weight": 0.85 # Good confidence for domain matches
                })
                new_relations_count += 1
                
                # Also update the app object itself for completeness (though graph builder uses app_skills.json)
                if skill_name not in app.get("skills_developed", []):
                    app["skills_developed"].append(skill_name)

    print(f"\nSummary:")
    print(f"  New Skills Added to DB: {new_skills_count}")
    print(f"  New App-Skill Relations: {new_relations_count}")
    
    if new_relations_count > 0:
        print("Saving updated files...")
        save_json(apps, APPS_FILE)
        save_json(app_skills, APP_SKILLS_FILE)
        save_json(skills_db, SKILLS_FILE)
        print("Done.")
    else:
        print("No changes needed.")

if __name__ == "__main__":
    main()
