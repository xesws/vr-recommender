import sys
import os

# Add paths
sys.path.append(os.path.join(os.getcwd(), "knowledge_graph/src"))
sys.path.append(os.path.join(os.getcwd(), "vector_store/src"))

from knowledge_graph.builder import KnowledgeGraphBuilder
from vector_store.indexer import VectorIndexer

def rebuild_all():
    print("=== FULL SYSTEM REBUILD ===")
    
    # 1. Rebuild Vector Index
    try:
        print("\n[Step 1] Rebuilding Vector Index...")
        indexer = VectorIndexer(persist_dir="vector_store/data/chroma")
        indexer.build_index("data_collection/data/skills.json", clear_existing=True)
    except Exception as e:
        print(f"Vector Index Build Failed: {e}")
        return

    # 2. Rebuild Knowledge Graph
    try:
        print("\n[Step 2] Rebuilding Knowledge Graph...")
        builder = KnowledgeGraphBuilder()
        builder.build(data_dir="data_collection/data", clear=True)
    except Exception as e:
        print(f"Graph Build Failed: {e}")
        return
        
    print("\n=== REBUILD COMPLETE ===")

if __name__ == "__main__":
    rebuild_all()

