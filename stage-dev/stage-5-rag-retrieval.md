# Stage 5: RAG Retrieval System

## 目标

整合向量搜索和知识图谱查询，实现完整的检索增强推荐系统。

## 输入/输出

- **输入**:
  - Neo4j 知识图谱 (Stage 3)
  - ChromaDB 向量索引 (Stage 4)
  - 用户查询文本
- **输出**: VR 应用推荐列表及理由

## 前置条件

- Stage 3 & 4 完成
- OpenRouter API Key (用于 LLM ranking)

---

## 任务分解

### 5.1 数据结构定义

```python
# src/rag/models.py

from dataclasses import dataclass
from typing import List

@dataclass
class VRAppMatch:
    app_id: str
    name: str
    category: str
    score: float
    matched_skills: List[str]
    reasoning: str

@dataclass
class RecommendationResult:
    apps: List[VRAppMatch]
    query_understanding: str
    matched_skills: List[str]
    total_matches: int
```

### 5.2 检索管道

```python
# src/rag/retriever.py

from typing import List
from src.vector_store.search_service import SkillSearchService
from src.knowledge_graph.connection import Neo4jConnection

class RAGRetriever:
    def __init__(self):
        self.skill_search = SkillSearchService()
        self.graph = Neo4jConnection()

    def retrieve(self, query: str, top_k: int = 8) -> List[dict]:
        """
        主检索函数

        Args:
            query: 用户查询
            top_k: 返回应用数量

        Returns:
            List[dict]: 推荐的 VR 应用
        """
        # 1. 向量搜索相关技能
        related_skills = self.skill_search.find_related_skills(query, top_k=15)

        if not related_skills:
            return []

        # 2. 在知识图谱中查询相关应用
        apps = self._query_apps_by_skills(related_skills, top_k)

        return apps

    def _query_apps_by_skills(self, skills: List[str], top_k: int) -> List[dict]:
        """基于技能在图谱中查询 VR 应用"""
        cypher = """
        MATCH (s:Skill)<-[d:DEVELOPS]-(a:VRApp)
        WHERE s.name IN $skills
        WITH a, collect(s.name) AS matched_skills, sum(d.weight) AS score
        RETURN a.app_id AS app_id,
               a.name AS name,
               a.category AS category,
               a.description AS description,
               matched_skills,
               score
        ORDER BY score DESC, size(matched_skills) DESC
        LIMIT $top_k
        """

        results = self.graph.query(cypher, {
            "skills": skills,
            "top_k": top_k
        })

        return results

    def close(self):
        self.graph.close()
```

### 5.3 LLM Ranking & 推理

```python
# src/rag/ranker.py

from openai import OpenAI
import os
import json
from typing import List

class LLMRanker:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1"
        )
        self.model = os.getenv("OPENROUTER_MODEL", "qwen/qwen3-30b-a3b")

    def rank_and_explain(self, query: str, apps: List[dict]) -> List[dict]:
        """
        使用 LLM 对应用进行排序并生成推荐理由

        Args:
            query: 用户查询
            apps: 候选应用列表

        Returns:
            带 reasoning 的应用列表
        """
        if not apps:
            return []

        # 构建 prompt
        app_list = "\n".join([
            f"- {app['name']} ({app['category']}): matches {', '.join(app['matched_skills'])}"
            for app in apps
        ])

        prompt = f"""用户查询: "{query}"

候选 VR 应用:
{app_list}

请为每个应用生成一句简短的推荐理由（说明为什么这个应用适合用户的学习需求）。

返回 JSON 格式:
{{
    "rankings": [
        {{"name": "App Name", "reasoning": "推荐理由"}},
        ...
    ]
}}"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一个 VR 学习应用推荐专家。只返回 JSON。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1024
        )

        return self._parse_rankings(response.choices[0].message.content, apps)

    def _parse_rankings(self, content: str, apps: List[dict]) -> List[dict]:
        """解析 LLM 返回的排序结果"""
        try:
            content = content.strip()
            if "```" in content:
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            data = json.loads(content)
            rankings = {r["name"]: r["reasoning"] for r in data.get("rankings", [])}
        except:
            rankings = {}

        # 为每个应用添加 reasoning
        for app in apps:
            app["reasoning"] = rankings.get(app["name"], "Matches your learning interests")

        return apps

    def understand_query(self, query: str) -> str:
        """理解用户查询意图"""
        prompt = f"""分析以下学习查询，用一句话总结用户想要学习什么:

"{query}"

直接返回总结，不要其他内容。"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=100
        )

        return response.choices[0].message.content.strip()
```

### 5.4 完整 RAG 服务

```python
# src/rag/service.py

from .retriever import RAGRetriever
from .ranker import LLMRanker
from .models import RecommendationResult, VRAppMatch
from typing import List

class RAGService:
    """RAG 推荐服务主入口"""

    def __init__(self):
        self.retriever = RAGRetriever()
        self.ranker = LLMRanker()

    def recommend(self, query: str, top_k: int = 8) -> RecommendationResult:
        """
        生成 VR 应用推荐

        Args:
            query: 用户查询
            top_k: 返回数量

        Returns:
            RecommendationResult
        """
        # 1. 理解查询
        query_understanding = self.ranker.understand_query(query)

        # 2. 检索候选应用
        candidates = self.retriever.retrieve(query, top_k=top_k * 2)  # 多检索一些用于排序

        if not candidates:
            return RecommendationResult(
                apps=[],
                query_understanding=query_understanding,
                matched_skills=[],
                total_matches=0
            )

        # 3. LLM 排序并生成理由
        ranked_apps = self.ranker.rank_and_explain(query, candidates)

        # 4. 构建结果
        all_skills = set()
        app_matches = []

        for app in ranked_apps[:top_k]:
            all_skills.update(app["matched_skills"])
            app_matches.append(VRAppMatch(
                app_id=app["app_id"],
                name=app["name"],
                category=app["category"],
                score=app["score"],
                matched_skills=app["matched_skills"],
                reasoning=app["reasoning"]
            ))

        return RecommendationResult(
            apps=app_matches,
            query_understanding=query_understanding,
            matched_skills=list(all_skills),
            total_matches=len(candidates)
        )

    def close(self):
        self.retriever.close()
```

### 5.5 主脚本

```python
# scripts/test_rag.py

from src.rag.service import RAGService

def main():
    service = RAGService()

    queries = [
        "I want to learn machine learning for public policy",
        "cybersecurity and risk management",
        "data visualization and analytics",
        "Python programming for beginners"
    ]

    for query in queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print('='*60)

        result = service.recommend(query)

        print(f"\n📝 Understanding: {result.query_understanding}")
        print(f"🔗 Matched Skills: {', '.join(result.matched_skills[:5])}")
        print(f"\n🥽 Recommended VR Apps:")

        for i, app in enumerate(result.apps, 1):
            print(f"\n{i}. {app.name} ({app.category})")
            print(f"   Score: {app.score:.2f}")
            print(f"   Skills: {', '.join(app.matched_skills)}")
            print(f"   Why: {app.reasoning}")

    service.close()

if __name__ == "__main__":
    main()
```

---

## 检索流程图

```
User Query: "machine learning for policy"
                    ↓
    ┌───────────────────────────────┐
    │   Vector Search (ChromaDB)    │
    │   → Machine Learning          │
    │   → Public Policy             │
    │   → Data Science              │
    └───────────────────────────────┘
                    ↓
    ┌───────────────────────────────┐
    │   Graph Query (Neo4j)         │
    │   MATCH (s:Skill)<-[:DEVELOPS]│
    │         -(a:VRApp)            │
    │   WHERE s.name IN [skills]    │
    └───────────────────────────────┘
                    ↓
    ┌───────────────────────────────┐
    │   LLM Ranking (OpenRouter)    │
    │   → Generate reasoning        │
    │   → Re-rank by relevance      │
    └───────────────────────────────┘
                    ↓
    RecommendationResult
```

---

## 文件结构

```
stage5/
├── src/
│   └── rag/
│       ├── __init__.py
│       ├── models.py
│       ├── retriever.py
│       ├── ranker.py
│       └── service.py
├── scripts/
│   └── test_rag.py
└── tests/
    └── test_rag_service.py
```

---

## 验收标准

- [ ] `RAGService.recommend()` 返回有效推荐
- [ ] 查询 "machine learning" 返回 ML 相关应用
- [ ] 每个应用有合理的 `reasoning`
- [ ] `matched_skills` 与查询相关
- [ ] 检索延迟 < 2 秒
- [ ] 无应用时返回空结果而非错误

---

## 依赖项

```txt
openai  # OpenRouter
chromadb
neo4j
```
