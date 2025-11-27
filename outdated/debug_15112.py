
from knowledge_graph.connection import Neo4jConnection

def check_15112():
    graph = Neo4jConnection()
    
    print("Checking 15-112...")
    
    # Check Node
    res = graph.query('MATCH (c:Course {course_id: "15-112"}) RETURN c')
    if not res:
        print("❌ Course 15-112 NOT found!")
    else:
        print(f"✅ Course 15-112 found: {res[0]['c']['title']}")

    # Check Relationships
    res = graph.query('MATCH (c:Course {course_id: "15-112"})-[r:RECOMMENDS]->(a:VRApp) RETURN count(a) as count')
    count = res[0]['count']
    print(f"📊 Recommendations count: {count}")
    
    if count > 0:
        res = graph.query('MATCH (c:Course {course_id: "15-112"})-[r:RECOMMENDS]->(a:VRApp) RETURN a.name, r.score LIMIT 5')
        for r in res:
            print(f"   - {r['a.name']} ({r['r.score']})")

    graph.close()

if __name__ == "__main__":
    check_15112()
