from knowledge_graph.src.knowledge_graph.connection import Neo4jConnection

def diagnose_15112():
    graph = Neo4jConnection()
    
    print("\nDiagnosing 15-112 Skills:")
    # Get skills taught by 15-112
    res = graph.query("""
        MATCH (c:Course {course_id: "15-112"})-[t:TEACHES]->(s:Skill)
        RETURN s.name
    """)
    
    course_skills = [r['s.name'] for r in res]
    print(f"Course Skills ({len(course_skills)}): {course_skills}")
    
    if not course_skills:
        print("No skills found for 15-112!")
        return

    print("\nChecking for VR Apps with these skills:")
    for skill in course_skills:
        res = graph.query("""
            MATCH (s:Skill {name: $skill})<-[d:DEVELOPS]-(a:VRApp)
            RETURN count(a) as count, collect(a.name) as apps
        """, {"skill": skill})
        
        count = res[0]['count']
        apps = res[0]['apps'][:3] # Show top 3
        print(f" - '{skill}': developed by {count} apps {apps if count > 0 else ''}")

    graph.close()

if __name__ == "__main__":
    diagnose_15112()
