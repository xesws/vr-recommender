
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath("vr-recommender"))

from skill_extraction.src.skill_extraction.normalizer import SkillNormalizer
from skill_extraction.src.skill_extraction.deduplicator import SkillDeduplicator

def test_deduplication_logic():
    print("🧪 Testing Skill Deduplication Logic...")
    
    normalizer = SkillNormalizer()
    deduplicator = SkillDeduplicator(normalizer)
    
    # Test cases: Synonyms that are NOT in the hardcoded alias_map
    # The current alias_map has "python" -> "Python", but what about:
    
    raw_skills = [
        {"name": "Python Scripting", "category": "technical", "weight": 1.0},
        {"name": "Writing Python Code", "category": "technical", "weight": 1.0},
        {"name": "Python Programming", "category": "technical", "weight": 1.0}, # Mapped in alias_map
        {"name": "Introductory Python", "category": "technical", "weight": 1.0},
        
        {"name": "Team Collaboration", "category": "soft", "weight": 1.0},
        {"name": "Working in Teams", "category": "soft", "weight": 1.0},
        
        {"name": "VR Development", "category": "technical", "weight": 1.0},
        {"name": "Virtual Reality Creation", "category": "technical", "weight": 1.0}
    ]
    
    print(f"\n[Input] Raw Skills ({len(raw_skills)}):")
    for s in raw_skills:
        print(f" - {s['name']}")
        
    unique_skills = deduplicator.deduplicate(raw_skills)
    
    print(f"\n[Output] Deduplicated Skills ({len(unique_skills)}):")
    for s in unique_skills:
        print(f" - {s.name} (Count: {s.source_count}, Aliases: {s.aliases})")
        
    # Analyze failure
    print("\n[Analysis]")
    python_variants = [s for s in unique_skills if "Python" in s.name]
    print(f"Python variants found: {len(python_variants)} (Expected 1 ideally, or at least fewer)")
    
    team_variants = [s for s in unique_skills if "Team" in s.name]
    print(f"Team variants found: {len(team_variants)}")

if __name__ == "__main__":
    test_deduplication_logic()
