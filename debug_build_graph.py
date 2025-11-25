import sys
import os

# Add the 'knowledge_graph/src' directory to sys.path so that 'knowledge_graph' package can be found
current_dir = os.getcwd()
sys.path.append(os.path.join(current_dir, 'knowledge_graph', 'src'))

from knowledge_graph.builder import KnowledgeGraphBuilder

if __name__ == "__main__":
    try:
        builder = KnowledgeGraphBuilder()
        builder.build(data_dir="data_collection/data", clear=True)
    except Exception as e:
        print(f"Error: {e}")