# Stage 6: Chatbot Integration

## 目标

重构现有的 `vr_recommender.py` 和 `flask_api.py`，集成 RAG 系统，保持 API 兼容性。

## 输入/输出

- **输入**: RAG 系统 (Stage 5)
- **输出**: 重构后的生产就绪 Chatbot

## 前置条件

- Stage 5 完成
- 现有 Flask API 可运行

---

## 任务分解

### 6.1 重构 HeinzVRLLMRecommender

```python
# vr_recommender.py (重构版)

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List
from datetime import datetime

from src.rag.service import RAGService

# 保留原有数据结构
@dataclass
class StudentQuery:
    query: str
    interests: List[str]
    background: str = ""


class HeinzVRLLMRecommender:
    """重构后: 使用 Knowledge Graph + RAG"""

    def __init__(self):
        self.rag_service = RAGService()

    def recommend_vr_apps(self, query: StudentQuery) -> List[Dict]:
        """
        生成 VR 应用推荐

        Args:
            query: StudentQuery 对象

        Returns:
            List[Dict]: 推荐应用列表
        """
        # 构建完整查询文本
        full_query = query.query
        if query.interests:
            full_query += f". Interests: {', '.join(query.interests)}"

        # 调用 RAG 服务
        result = self.rag_service.recommend(full_query, top_k=8)

        # 转换为原有格式
        apps = []
        max_score = max([app.score for app in result.apps], default=1)

        for app in result.apps:
            apps.append({
                "app_name": app.name,
                "likeliness_score": round(min(1.0, app.score / max_score), 2),
                "category": app.category,
                "reasoning": app.reasoning,
            })

        return apps

    def generate_recommendation(self, query: StudentQuery) -> Dict:
        """
        生成完整推荐结果

        Args:
            query: StudentQuery 对象

        Returns:
            Dict: 包含应用列表和元信息
        """
        print(f"\n🔍 Processing (RAG): {query.query}")

        try:
            vr_apps = self.recommend_vr_apps(query)
            return {
                "student_query": query.query,
                "vr_apps": vr_apps,
                "message": f"Here are {len(vr_apps)} VR apps aligned to your interests.",
                "generated_at": datetime.utcnow().isoformat() + "Z",
            }
        except Exception as e:
            print(f"❌ Error: {e}")
            return {
                "student_query": query.query,
                "vr_apps": [],
                "message": f"Error: {str(e)}",
                "generated_at": datetime.utcnow().isoformat() + "Z",
            }

    def close(self):
        """关闭连接"""
        self.rag_service.close()


# CLI for testing
def main():
    print("=" * 70)
    print("HEINZ RAG VR APP RECOMMENDER")
    print("=" * 70)

    rec = HeinzVRLLMRecommender()

    demos = [
        StudentQuery("I want to learn about cyber security", ["projects"], "MSISPM"),
        StudentQuery("machine learning for public policy", ["data analysis"], "MSPPM"),
        StudentQuery("data visualization", ["tableau"], "MISM"),
    ]

    for q in demos:
        out = rec.generate_recommendation(q)
        print(f"\nQuery: {out['student_query']}")
        print("Apps:")
        for a in out["vr_apps"][:5]:
            print(f"  • {a['app_name']} — {a['category']} ({int(a['likeliness_score']*100)}%)")
            print(f"    {a['reasoning']}")

    rec.close()


if __name__ == "__main__":
    main()
```

### 6.2 更新 Flask API

```python
# flask_api.py (关键修改部分)

# 初始化改为 RAG 版本
from vr_recommender import HeinzVRLLMRecommender, StudentQuery

print("\n🔄 Initializing RAG-based VR recommender...")
recommender = HeinzVRLLMRecommender()
print("✓ RAG VR Recommender ready!")

# extract_query_data 可简化，因为 RAG 自己会提取关键词
def extract_query_data(message: str) -> dict:
    """提取查询数据 (简化版)"""
    return {
        "interests": [],  # RAG 会自动处理
        "background": "CMU Heinz College student"
    }

# 其余保持不变...
```

### 6.3 Chat Session 管理

```python
# src/chat/session.py

import json
import os
from datetime import datetime
from typing import List, Dict

class ChatSession:
    """聊天会话管理"""

    def __init__(self, session_id: str, storage_dir: str = "chat_logs"):
        self.session_id = session_id
        self.storage_dir = storage_dir
        self.storage_path = f"{storage_dir}/{session_id}.json"
        self.history: List[Dict] = []

        os.makedirs(storage_dir, exist_ok=True)
        self._load()

    def _load(self):
        """加载历史记录"""
        if os.path.exists(self.storage_path):
            with open(self.storage_path) as f:
                self.history = json.load(f)

    def save(self):
        """保存历史记录"""
        with open(self.storage_path, "w") as f:
            json.dump(self.history, f, indent=2)

    def add_message(self, role: str, content: str):
        """添加消息"""
        self.history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self.save()

    def get_context(self, last_n: int = 5) -> str:
        """获取最近 n 条消息作为上下文"""
        recent = self.history[-last_n:] if len(self.history) > last_n else self.history
        return "\n".join([f"{m['role']}: {m['content']}" for m in recent])

    def should_trigger_recommendation(self, message: str) -> bool:
        """检测是否应触发推荐"""
        triggers = ["recommend", "suggest", "find", "vr app", "应用", "推荐", "learn", "study"]
        return any(t in message.lower() for t in triggers)
```

### 6.4 更新脚本

```python
# scripts/update_rag.py

import argparse
from src.data_collection.course_fetcher import CMUCourseFetcher
from src.data_collection.vr_app_fetcher import VRAppFetcher
from src.skill_extraction.pipeline import SkillExtractionPipeline
from src.knowledge_graph.builder import KnowledgeGraphBuilder
from src.vector_store.indexer import VectorIndexer

def main():
    parser = argparse.ArgumentParser(description="Update RAG system")
    parser.add_argument("--source", choices=["courses", "apps", "skills", "all"], default="all")
    parser.add_argument("--rebuild-graph", action="store_true")
    parser.add_argument("--rebuild-embeddings", action="store_true")
    parser.add_argument("--data-dir", default="data")
    args = parser.parse_args()

    # 1. 更新数据
    if args.source in ["courses", "all"]:
        print("\n📚 Fetching courses...")
        fetcher = CMUCourseFetcher()
        courses = fetcher.fetch_courses()
        fetcher.save_courses(courses, f"{args.data_dir}/courses.json")

    if args.source in ["apps", "all"]:
        print("\n🥽 Fetching VR apps...")
        fetcher = VRAppFetcher()
        apps = fetcher.fetch_apps()
        fetcher.save_apps(apps, f"{args.data_dir}/vr_apps.json")

    if args.source in ["skills", "all"]:
        print("\n🔧 Extracting skills...")
        pipeline = SkillExtractionPipeline()
        pipeline.run(
            f"{args.data_dir}/courses.json",
            f"{args.data_dir}/vr_apps.json",
            args.data_dir
        )

    # 2. 重建知识图谱
    if args.rebuild_graph:
        print("\n🕸️ Rebuilding knowledge graph...")
        builder = KnowledgeGraphBuilder()
        builder.build(args.data_dir, clear=True)

    # 3. 重建向量索引
    if args.rebuild_embeddings:
        print("\n📊 Rebuilding vector index...")
        indexer = VectorIndexer()
        indexer.build_index(f"{args.data_dir}/skills.json")

    print("\n✅ RAG system updated!")

if __name__ == "__main__":
    main()

# 使用示例:
# python scripts/update_rag.py --source all --rebuild-graph --rebuild-embeddings
```

---

## 删除的文件

完成集成后，删除以下不再需要的文件：

```bash
rm analytics.py
rm analytics_demo.py
```

---

## 文件结构 (最终)

```
vr-recommender/
├── vr_recommender.py      # 重构后
├── flask_api.py           # 更新后
├── src/
│   ├── models.py
│   ├── data_collection/
│   ├── skill_extraction/
│   ├── knowledge_graph/
│   ├── vector_store/
│   ├── rag/
│   └── chat/
│       └── session.py
├── scripts/
│   ├── fetch_data.py
│   ├── extract_skills.py
│   ├── build_graph.py
│   ├── build_vector_index.py
│   └── update_rag.py
├── data/
│   ├── courses.json
│   ├── vr_apps.json
│   ├── skills.json
│   ├── course_skills.json
│   ├── app_skills.json
│   └── chroma/
├── chat_logs/
├── tests/
└── requirements.txt
```

---

## 验收标准

- [ ] `flask_api.py` 启动无错误
- [ ] `/health` 返回 `{"status": "healthy", "recommender": "ready"}`
- [ ] `/chat` POST 请求返回有效推荐
- [ ] 推荐结果包含 `reasoning`
- [ ] API 响应格式与原版兼容
- [ ] `update_rag.py` 可成功更新系统
- [ ] 删除了 `analytics.py` 和 `analytics_demo.py`

---

## 测试命令

```bash
# 启动服务
python flask_api.py

# 测试推荐
curl -X POST http://localhost:5000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "I want to learn machine learning for public policy"}'

# 更新 RAG 系统
python scripts/update_rag.py --source all --rebuild-graph --rebuild-embeddings
```

---

## 依赖项 (完整)

```txt
# API
flask
flask-cors
gunicorn

# Data Collection
firecrawl-py
tavily-python

# LLM
openai

# Knowledge Graph
neo4j

# Vector Store
chromadb
sentence-transformers

# Utils
python-dotenv
pydantic
```
