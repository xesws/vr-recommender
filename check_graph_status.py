from knowledge_graph.src.knowledge_graph.connection import Neo4jConnection
import os

def check_status():
    try:
        conn = Neo4jConnection()
        result = conn.query('MATCH (n) RETURN count(n) as count')
        print(f"Node count: {result[0]['count']}")
        result = conn.query('MATCH ()-[r]->() RETURN count(r) as count')
        print(f"Relationship count: {result[0]['count']}")
        conn.close()
    except Exception as e:
        print(f"Graph Error: {e}")

    print("\nData Files:")
    data_dir = "data_collection/data"
    if os.path.exists(data_dir):
        for f in os.listdir(data_dir):
            size = os.path.getsize(os.path.join(data_dir, f))
            print(f"  {f}: {size} bytes")
    else:
        print("  Data directory not found!")

if __name__ == "__main__":
    check_status()
