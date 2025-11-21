# Stage 4: Vector Store & Embeddings

## 目标

为技能创建向量嵌入，支持语义相似度搜索。

## 输入/输出

- **输入**: `data/skills.json` (来自 Stage 2)
- **输出**: ChromaDB 向量索引

## 前置条件

- Stage 2 完成
- 可选: OpenAI API Key (使用 OpenAI embeddings)

---

## 任务分解

### 4.1 Embedding 模型选择

```python
# src/vector_store/embeddings.py

from sentence_transformers import SentenceTransformer
from openai import OpenAI
import os
from typing import List
import numpy as np

class EmbeddingModel:
    """Embedding 模型抽象基类"""
    def encode(self, texts: List[str]) -> np.ndarray:
        raise NotImplementedError

class LocalEmbedding(EmbeddingModel):
    """本地 sentence-transformers 模型"""
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def encode(self, texts: List[str]) -> np.ndarray:
        return self.model.encode(texts, show_progress_bar=True)

class OpenAIEmbedding(EmbeddingModel):
    """OpenAI embedding API"""
    def __init__(self, model: str = "text-embedding-3-small"):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model

    def encode(self, texts: List[str]) -> np.ndarray:
        response = self.client.embeddings.create(
            model=self.model,
            input=texts
        )
        return np.array([e.embedding for e in response.data])

def get_embedding_model(use_openai: bool = False) -> EmbeddingModel:
    """获取 embedding 模型"""
    if use_openai:
        return OpenAIEmbedding()
    return LocalEmbedding()
```

### 4.2 ChromaDB 向量存储

```python
# src/vector_store/store.py

import chromadb
from chromadb.config import Settings
import json
from typing import List, Tuple

class SkillVectorStore:
    def __init__(self, persist_dir: str = "data/chroma"):
        self.client = chromadb.Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=persist_dir
        ))
        self.collection = self.client.get_or_create_collection(
            name="skills",
            metadata={"hnsw:space": "cosine"}
        )

    def add_skills(self, skills: List[dict], embeddings: List[List[float]]):
        """
        添加技能到向量存储

        Args:
            skills: 技能列表
            embeddings: 对应的 embedding 向量
        """
        ids = [s["name"] for s in skills]
        documents = [self._skill_to_document(s) for s in skills]
        metadatas = [{"category": s["category"], "aliases": ",".join(s.get("aliases", []))} for s in skills]

        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )

    def _skill_to_document(self, skill: dict) -> str:
        """将技能转换为用于 embedding 的文本"""
        aliases = skill.get("aliases", [])
        alias_str = f". Also known as: {', '.join(aliases)}" if aliases else ""
        return f"{skill['name']}{alias_str}. Category: {skill['category']}"

    def search(self, query: str, query_embedding: List[float], top_k: int = 10) -> List[Tuple[str, float]]:
        """
        搜索最相关的技能

        Args:
            query: 查询文本
            query_embedding: 查询的 embedding
            top_k: 返回数量

        Returns:
            List[(skill_name, similarity_score)]
        """
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["distances", "metadatas"]
        )

        skills = []
        for i, skill_id in enumerate(results["ids"][0]):
            # ChromaDB 返回距离，转换为相似度
            distance = results["distances"][0][i]
            similarity = 1 - distance  # cosine distance to similarity
            skills.append((skill_id, similarity))

        return skills

    def persist(self):
        """持久化存储"""
        self.client.persist()

    def clear(self):
        """清空集合"""
        self.client.delete_collection("skills")
        self.collection = self.client.create_collection(
            name="skills",
            metadata={"hnsw:space": "cosine"}
        )
```

### 4.3 索引构建管道

```python
# src/vector_store/indexer.py

import json
from .embeddings import get_embedding_model
from .store import SkillVectorStore

class VectorIndexer:
    def __init__(self, use_openai: bool = False, persist_dir: str = "data/chroma"):
        self.embedding_model = get_embedding_model(use_openai)
        self.store = SkillVectorStore(persist_dir)

    def build_index(self, skills_path: str):
        """
        为技能构建向量索引

        Args:
            skills_path: skills.json 路径
        """
        # 加载技能
        with open(skills_path) as f:
            skills = json.load(f)

        print(f"Building index for {len(skills)} skills...")

        # 生成文本
        texts = [self._skill_to_text(s) for s in skills]

        # 生成 embeddings
        embeddings = self.embedding_model.encode(texts)

        # 存入向量库
        self.store.clear()
        self.store.add_skills(skills, embeddings.tolist())
        self.store.persist()

        print(f"✓ Index built and persisted")

    def _skill_to_text(self, skill: dict) -> str:
        """将技能转换为 embedding 文本"""
        aliases = skill.get("aliases", [])
        alias_str = f". Also known as: {', '.join(aliases)}" if aliases else ""
        return f"{skill['name']}{alias_str}. Category: {skill['category']}"

    def search(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """
        搜索相关技能

        Args:
            query: 查询文本
            top_k: 返回数量

        Returns:
            List[(skill_name, similarity_score)]
        """
        # 生成查询 embedding
        query_embedding = self.embedding_model.encode([query])[0]

        # 搜索
        return self.store.search(query, query_embedding.tolist(), top_k)
```

### 4.4 主脚本

```python
# scripts/build_vector_index.py

import argparse
from src.vector_store.indexer import VectorIndexer

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skills", default="data/skills.json")
    parser.add_argument("--persist-dir", default="data/chroma")
    parser.add_argument("--use-openai", action="store_true")
    args = parser.parse_args()

    indexer = VectorIndexer(
        use_openai=args.use_openai,
        persist_dir=args.persist_dir
    )
    indexer.build_index(args.skills)

    # 测试搜索
    print("\n🔍 Test search: 'machine learning'")
    results = indexer.search("machine learning", top_k=5)
    for skill, score in results:
        print(f"   {skill}: {score:.3f}")

if __name__ == "__main__":
    main()
```

### 4.5 搜索服务

```python
# src/vector_store/search_service.py

from .indexer import VectorIndexer
from typing import List

class SkillSearchService:
    """技能搜索服务，供 RAG 系统调用"""

    def __init__(self, persist_dir: str = "data/chroma", use_openai: bool = False):
        self.indexer = VectorIndexer(use_openai, persist_dir)

    def find_related_skills(self, query: str, top_k: int = 10) -> List[str]:
        """
        查找与查询相关的技能

        Args:
            query: 用户查询
            top_k: 返回数量

        Returns:
            List[str]: 技能名称列表
        """
        results = self.indexer.search(query, top_k)
        return [skill for skill, score in results if score > 0.3]  # 过滤低相似度

    def find_skills_with_scores(self, query: str, top_k: int = 10) -> List[dict]:
        """
        查找相关技能及其分数

        Returns:
            List[dict]: [{"name": "Python", "score": 0.85}, ...]
        """
        results = self.indexer.search(query, top_k)
        return [{"name": skill, "score": score} for skill, score in results]
```

---

## 文件结构

```
stage4/
├── src/
│   └── vector_store/
│       ├── __init__.py
│       ├── embeddings.py
│       ├── store.py
│       ├── indexer.py
│       └── search_service.py
├── scripts/
│   └── build_vector_index.py
├── data/
│   └── chroma/           # ChromaDB 持久化目录
└── tests/
    └── test_vector_store.py
```

---

## 验收标准

- [ ] ChromaDB 成功存储所有技能 embeddings
- [ ] 搜索 "machine learning" 返回 ML 相关技能
- [ ] 搜索 "Python" 返回编程相关技能
- [ ] 搜索 "policy" 返回政策相关技能
- [ ] 相似度分数合理 (相关技能 > 0.5)
- [ ] 索引可持久化和重新加载

---

## 依赖项

```txt
chromadb
sentence-transformers
# 可选: openai (如使用 OpenAI embeddings)
```

---

## 测试用例

```python
# tests/test_vector_store.py

def test_skill_search():
    service = SkillSearchService()

    # 测试 1: ML 相关
    results = service.find_related_skills("deep learning neural networks")
    assert "Machine Learning" in results or "Deep Learning" in results

    # 测试 2: 编程相关
    results = service.find_related_skills("Python coding")
    assert "Python" in results

    # 测试 3: 政策相关
    results = service.find_related_skills("government policy analysis")
    assert "Public Policy" in results
```
