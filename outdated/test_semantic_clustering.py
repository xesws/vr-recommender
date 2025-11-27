
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath("vr-recommender"))

from skill_extraction.src.skill_extraction.normalizer import SkillNormalizer
from skill_extraction.src.skill_extraction.semantic_deduplicator import SemanticDeduplicator

def test_semantic_logic():
    print("🧪 Testing SEMANTIC Skill Deduplication...")
    
    normalizer = SkillNormalizer()
    # Initialize with default threshold
    deduplicator = SemanticDeduplicator(normalizer, distance_threshold=0.4)
    
    raw_skills = [
        # Cluster 1: Python
        {"name": "Python Scripting", "category": "technical", "weight": 1.0},
        {"name": "Writing Python Code", "category": "technical", "weight": 1.0},
        {"name": "Python Programming", "category": "technical", "weight": 1.0},
        
        # Cluster 2: Teams (The difficult one for Regex)
        {"name": "Team Collaboration", "category": "soft", "weight": 1.0},
        {"name": "Working in Teams", "category": "soft", "weight": 1.0},
        {"name": "Collaborating with Teams", "category": "soft", "weight": 1.0},
        
        # Cluster 3: VR
        {"name": "VR Development", "category": "technical", "weight": 1.0},
        {"name": "Virtual Reality Creation", "category": "technical", "weight": 1.0},
        
        # Negative Test
        {"name": "Java", "category": "technical", "weight": 1.0}
    ]
    
    print(f"\n[Input] Raw Skills ({len(raw_skills)}):")
    for s in raw_skills:
        print(f" - {s['name']}")
        
    unique_skills = deduplicator.deduplicate(raw_skills)
    
    print(f"\n[Output] Deduplicated Skills ({len(unique_skills)}):")
    for s in unique_skills:
        print(f" - {s.name} (Count: {s.source_count})")
        print(f"   Aliases: {s.aliases}")

    # Validation
    print("\n[Validation]")
    team_skills = [s for s in unique_skills if "Team" in s.name or "Collab" in s.name]
    if len(team_skills) == 1:
        print(f"✅ SUCCESS: 'Team' skills merged into '{team_skills[0].name}'")
    else:
        print(f"❌ FAILURE: 'Team' skills NOT merged. Found: {[s.name for s in team_skills]}")
        
    python_skills = [s for s in unique_skills if "Python" in s.name]
    java_skills = [s for s in unique_skills if "Java" in s.name]
    
    if len(python_skills) == 1 and len(java_skills) == 1:
         if python_skills[0].name != java_skills[0].name:
             print(f"✅ SUCCESS: 'Python' and 'Java' kept separate.")
         else:
             print(f"❌ FAILURE: 'Python' and 'Java' merged into '{python_skills[0].name}'")
    else:
         print(f"❌ FAILURE: Unexpected count. Python: {len(python_skills)}, Java: {len(java_skills)}")

if __name__ == "__main__":
    test_semantic_logic()
