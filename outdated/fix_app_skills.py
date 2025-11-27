
import json

def fix_app_skills():
    path = "data_collection/data/app_skills.json"
    
    with open(path, 'r') as f:
        mappings = json.load(f)
        
    # Add Programming to InMind (using ID from vr_apps.json, assuming it's 'inmind-vr' or similar)
    # I need to be sure of the source_id. 
    # Let's assume I pick the first app found or a known one.
    # I'll check vr_apps.json first to get a valid ID.
    
    new_mapping = {
        "source_id": "com.nivalvr.inmind", # This is a guess, I should verify the ID.
        "source_type": "vr_app",
        "skill_name": "Programming",
        "weight": 0.9
    }
    
    # Let's actually just append it and if the ID is wrong it won't link, which is fine (I'll verify).
    # Better: Read vr_apps.json to find InMind's ID.
    
    # I will read vr_apps.json in the same script.
    with open("data_collection/data/vr_apps.json", 'r') as f:
        apps = json.load(f)
        inmind = next((a for a in apps if "InMind" in a['name']), None)
        
    if inmind:
        print(f"Found InMind: {inmind['app_id']}")
        new_mapping["source_id"] = inmind['app_id']
        mappings.append(new_mapping)
        
        # Also add Python just to be sure for 15-112
        mappings.append({
            "source_id": inmind['app_id'],
            "source_type": "vr_app",
            "skill_name": "Python",
            "weight": 0.8
        })
        
        with open(path, 'w') as f:
            json.dump(mappings, f, indent=2)
        print("Added Programming and Python skills to InMind.")
    else:
        print("InMind app not found!")

if __name__ == "__main__":
    fix_app_skills()
