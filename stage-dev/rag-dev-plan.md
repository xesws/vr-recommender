# Stage 1 Development Plan

## Deliverables

1. **Knowledge Graph**: 连接 CMU 课程目录、Meta Quest VR 应用和技能的知识图谱
   - 节点类型: Course, VRApp, Skill
   - 关系类型: Course-TEACHES->Skill, VRApp-DEVELOPS->Skill

2. **RAG System**: 基于知识图谱的实时检索系统
   - 支持自然语言查询
   - 返回相关 VR 应用推荐及理由
   - 支持实时更新

3. **重构现有 Chatbot**: 将现有的 `vr_recommender.py` 和 `flask_api.py` 改造为使用 Knowledge Graph

### 交付标准
- [ ] Knowledge Graph 包含 ≥100 门 CMU 课程节点
- [ ] Knowledge Graph 包含 ≥50 个 VR 应用节点
- [ ] Skill 节点 ≥200 个，且去重
- [ ] RAG 检索响应时间 < 2 秒
- [ ] 推荐准确率 ≥ 70%（人工评估）
- [ ] 现有 Flask API 端点保持兼容

---

## 现有代码重构计划

### 保留的组件

| 文件 | 组件 | 说明 |
|------|------|------|
| `flask_api.py` | `/chat`, `/health` 端点 | 保持 API 接口不变 |
| `flask_api.py` | `parse_user_intent()` | 保留意图识别逻辑 |
| `flask_api.py` | `is_supported_learning_query()` | 保留查询过滤 |
| `flask_api.py` | `format_vr_response()` | 保留响应格式化 |
| `vr_recommender.py` | `StudentQuery` dataclass | 保留输入数据结构 |

### 需要重构的组件

| 文件 | 组件 | 重构方向 |
|------|------|----------|
| `vr_recommender.py` | `vr_app_mappings` (硬编码) | → 从 Neo4j 动态查询 |
| `vr_recommender.py` | `_category_aliases()` | → 使用 Skill.aliases 字段 |
| `vr_recommender.py` | `_llm_map_to_categories()` | → 结合向量检索 + LLM |
| `vr_recommender.py` | `recommend_vr_apps()` | → 改用 Graph + Vector 检索 |
| `flask_api.py` | `extract_query_data()` | → 使用 skill-gen 模块提取 |

### 删除的组件

| 文件 | 组件 | 原因 |
|------|------|------|
| `analytics.py` | 整个文件 | MongoDB 分析被 KG 查询替代 |
| `analytics_demo.py` | 整个文件 | 不再需要 |
| `vr_recommender.py` | 所有硬编码 mappings | 数据来自 KG |

### 重构后的 HeinzVRLLMRecommender

```python
class HeinzVRLLMRecommender:
    """重构后: 使用 Knowledge Graph + Vector Search"""

    def __init__(self, neo4j_uri: str, neo4j_auth: tuple, ...):
        self.graph = Neo4jConnection(neo4j_uri, neo4j_auth)
        self.vector_store = ChromaDB(...)
        self.llm_client = OpenAI(base_url="https://openrouter.ai/api/v1", ...)

    def recommend_vr_apps(self, query: StudentQuery) -> List[Dict]:
        # 1. 提取关键词 → 向量检索相关 Skills
        keywords = extract_skills(query.query)
        related_skills = self.vector_store.search(keywords, top_k=10)

        # 2. 在 KG 中查询相关 VR 应用
        apps = self.graph.query("""
            MATCH (s:Skill)<-[:DEVELOPS]-(app:VRApp)
            WHERE s.name IN $skills
            RETURN app, count(s) as relevance
            ORDER BY relevance DESC
            LIMIT 8
        """, skills=related_skills)

        # 3. LLM 生成推荐理由
        return self._format_recommendations(apps, query)
```

---

## Information Module

负责获取和存储原始数据。

### CMU Course Catalog

**数据源**: Firecrawl API
**目标 URL**: `https://www.cmu.edu/hub/registrar/course-schedule/`

```python
# 函数签名
def fetch_cmu_courses(semester: str = "fall2024") -> List[Course]:
    """
    使用 Firecrawl API 爬取 CMU 课程目录

    Returns:
        List[Course]: 课程列表
    """
    pass

# 数据结构
@dataclass
class Course:
    course_id: str          # e.g., "95-865"
    title: str              # e.g., "Unstructured Data Analytics"
    department: str         # e.g., "Heinz College"
    description: str        # 课程描述
    units: int              # 学分
    prerequisites: List[str] # 先修课程
    learning_outcomes: List[str]  # 学习目标
```

**存储格式**: `data/courses.json`

### Meta Quest VR Apps

**数据源**: Tavily API
**查询策略**: 搜索教育类、培训类 VR 应用

```python
# 函数签名
def fetch_vr_apps(categories: List[str] = ["education", "training", "productivity"]) -> List[VRApp]:
    """
    使用 Tavily API 搜索 Meta Quest 应用信息

    Returns:
        List[VRApp]: VR 应用列表
    """
    pass

# 数据结构
@dataclass
class VRApp:
    app_id: str             # 应用唯一标识
    name: str               # e.g., "Spatial"
    category: str           # e.g., "Productivity"
    description: str        # 应用描述
    features: List[str]     # 功能特性
    skills_developed: List[str]  # 可培养的技能
    rating: float           # 用户评分
    price: str              # 价格
```

**存储格式**: `data/vr_apps.json`

### 更新策略
- 每周自动更新一次
- 增量更新，保留历史版本
- 脚本: `scripts/update_data.py --source [courses|apps|all]`

---

## skill-gen module

负责从课程描述和 VR 应用描述中提取技能关键词，作为连接两者的桥梁。

### 技术选型

**推荐方案**: LLM-based extraction (使用 GPT-4 或 Qwen)

**备选方案**:
- spaCy NER + 自定义技能词典
- TF-IDF 关键词提取
- KeyBERT

### 核心函数

```python
# 主函数
def extract_skills(text: str, source_type: str = "course") -> List[Skill]:
    """
    从文本中提取技能关键词

    Args:
        text: 课程描述或应用描述
        source_type: "course" 或 "app"

    Returns:
        List[Skill]: 提取的技能列表
    """
    pass

# 技能规范化
def normalize_skill(skill_name: str) -> str:
    """
    将技能名称标准化 (e.g., "ML" -> "Machine Learning")
    """
    pass

# 技能去重
def deduplicate_skills(skills: List[Skill]) -> List[Skill]:
    """
    合并相似技能 (e.g., "Python Programming" 和 "Python" -> "Python")
    """
    pass

# 数据结构
@dataclass
class Skill:
    name: str               # 标准化名称
    aliases: List[str]      # 别名列表
    category: str           # 技能类别: "technical", "soft", "domain"
    source_count: int       # 出现次数
```

### LLM Prompt 设计

```python
SKILL_EXTRACTION_PROMPT = """
从以下{source_type}描述中提取关键技能:

{text}

要求:
1. 提取技术技能 (如 Python, SQL, Machine Learning)
2. 提取软技能 (如 Communication, Leadership)
3. 提取领域知识 (如 Public Policy, Finance)
4. 返回 JSON 格式: {{"skills": ["skill1", "skill2", ...]}}
"""
```

### 技能分类体系

| 类别 | 示例 |
|------|------|
| Technical | Python, SQL, Data Visualization, VR Development |
| Soft Skills | Communication, Leadership, Teamwork, Creativity |
| Domain | Public Policy, Finance, Healthcare, Architecture |

---

## Knowledge Graph

使用 Neo4j 构建知识图谱。

### Schema 设计

#### 节点类型

```cypher
// Course 节点
(:Course {
    course_id: STRING,      // PRIMARY KEY
    title: STRING,
    department: STRING,
    description: STRING,
    units: INTEGER
})

// VRApp 节点
(:VRApp {
    app_id: STRING,         // PRIMARY KEY
    name: STRING,
    category: STRING,
    description: STRING,
    rating: FLOAT
})

// Skill 节点
(:Skill {
    name: STRING,           // PRIMARY KEY
    category: STRING,       // technical/soft/domain
    aliases: LIST<STRING>
})
```

#### 关系类型

```cypher
// 课程教授技能
(:Course)-[:TEACHES {weight: FLOAT}]->(:Skill)

// VR应用培养技能
(:VRApp)-[:DEVELOPS {weight: FLOAT}]->(:Skill)

// 课程推荐VR应用 (通过共享技能计算)
(:Course)-[:RECOMMENDS {score: FLOAT, shared_skills: LIST<STRING>}]->(:VRApp)
```

### 核心函数

```python
# 初始化图谱
def init_knowledge_graph(neo4j_uri: str, auth: tuple) -> None:
    """创建约束和索引"""
    pass

# 导入数据
def populate_graph(
    courses: List[Course],
    apps: List[VRApp],
    skills: List[Skill]
) -> None:
    """将数据导入 Neo4j"""
    pass

# 创建关系
def create_relationships(course_skills: Dict, app_skills: Dict) -> None:
    """
    创建 TEACHES 和 DEVELOPS 关系
    weight 基于技能在描述中的重要程度 (TF-IDF 或 LLM 评分)
    """
    pass

# 计算推荐关系
def compute_recommendations() -> None:
    """
    基于共享技能计算 Course-RECOMMENDS->VRApp
    score = sum(skill_weights) / total_skills
    """
    pass
```

### 示例查询

```cypher
// 查找某课程相关的 VR 应用
MATCH (c:Course {course_id: "95-865"})-[:TEACHES]->(s:Skill)<-[:DEVELOPS]-(app:VRApp)
RETURN app.name, collect(s.name) as shared_skills, count(s) as relevance
ORDER BY relevance DESC
LIMIT 5

// 查找培养某技能的所有资源
MATCH (n)-[r]->(s:Skill {name: "Machine Learning"})
RETURN labels(n)[0] as type, n.title as name, r.weight as importance

// 获取推荐
MATCH (c:Course {course_id: "95-865"})-[r:RECOMMENDS]->(app:VRApp)
RETURN app.name, r.score, r.shared_skills
ORDER BY r.score DESC
```

### 索引策略

```cypher
CREATE CONSTRAINT course_id FOR (c:Course) REQUIRE c.course_id IS UNIQUE;
CREATE CONSTRAINT app_id FOR (a:VRApp) REQUIRE a.app_id IS UNIQUE;
CREATE CONSTRAINT skill_name FOR (s:Skill) REQUIRE s.name IS UNIQUE;

CREATE INDEX course_dept FOR (c:Course) ON (c.department);
CREATE INDEX app_category FOR (a:VRApp) ON (a.category);
CREATE INDEX skill_category FOR (s:Skill) ON (s.category);
```

---

## RAG system

基于知识图谱的检索增强生成系统。

### 技术选型

- **Embedding Model**: OpenAI `text-embedding-3-small` 或 `sentence-transformers`
- **Vector Store**: ChromaDB (本地) 或 Pinecone (云端)
- **LLM**: Qwen/GPT-4 (通过 OpenRouter)

### 系统架构

```
User Query
    ↓
[Keyword Extraction] ← Chat History
    ↓
[Vector Search] → Top-K Skills
    ↓
[Graph Query] → Related VR Apps
    ↓
[LLM Ranking & Explanation]
    ↓
Recommendation Response
```

### 核心函数

```python
# 主检索函数
def retrieve_recommendations(
    query: str,
    chat_history: List[Dict] = None,
    top_k: int = 5
) -> RecommendationResult:
    """
    主检索入口

    Args:
        query: 用户查询
        chat_history: 对话历史
        top_k: 返回数量

    Returns:
        RecommendationResult: 推荐结果
    """
    pass

# 关键词提取
def extract_query_keywords(
    query: str,
    chat_history: List[Dict] = None
) -> List[str]:
    """
    从查询和对话历史中提取关键词
    触发词: "recommend", "suggest", "find apps", "VR for..."
    """
    pass

# 向量检索
def vector_search(
    keywords: List[str],
    top_k: int = 10
) -> List[Tuple[str, float]]:
    """
    在 Skill embeddings 中检索最相关的技能

    Returns:
        List[(skill_name, similarity_score)]
    """
    pass

# 图谱查询
def graph_query(
    skills: List[str],
    top_k: int = 5
) -> List[VRAppMatch]:
    """
    基于技能在图谱中查询相关 VR 应用
    """
    pass

# 结果数据结构
@dataclass
class VRAppMatch:
    app: VRApp
    score: float
    matched_skills: List[str]
    reasoning: str

@dataclass
class RecommendationResult:
    apps: List[VRAppMatch]
    query_understanding: str
    total_matches: int
```

### real-time update module

```python
# update_rag.py CLI 接口

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", choices=["courses", "apps", "skills", "all"])
    parser.add_argument("--rebuild-graph", action="store_true")
    parser.add_argument("--rebuild-embeddings", action="store_true")
    args = parser.parse_args()

    if args.source in ["courses", "all"]:
        courses = fetch_cmu_courses()
        update_course_nodes(courses)

    if args.source in ["apps", "all"]:
        apps = fetch_vr_apps()
        update_app_nodes(apps)

    if args.source in ["skills", "all"]:
        regenerate_skills()

    if args.rebuild_graph:
        compute_recommendations()

    if args.rebuild_embeddings:
        rebuild_vector_index()

# 使用示例
# python update_rag.py --source all --rebuild-graph --rebuild-embeddings
```

### retrieval module

```python
# 对话管理
class ChatSession:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.history: List[Dict] = []
        self.storage_path = f"chat_logs/{session_id}.json"

    def add_message(self, role: str, content: str):
        self.history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self.save()

    def should_trigger_recommendation(self, message: str) -> bool:
        """
        检测是否触发推荐
        触发词: "recommend", "suggest", "find", "VR app", "应用"
        """
        triggers = ["recommend", "suggest", "find", "vr app", "应用", "推荐"]
        return any(t in message.lower() for t in triggers)

    def get_context_keywords(self) -> List[str]:
        """从对话历史提取上下文关键词"""
        pass
```

### Embedding 策略

```python
# 为每个 Skill 生成 embedding
def build_skill_embeddings(skills: List[Skill]) -> None:
    """
    生成技能 embeddings 并存入向量数据库

    每个技能的文本 = name + aliases + category
    """
    texts = []
    for skill in skills:
        text = f"{skill.name}. Aliases: {', '.join(skill.aliases)}. Category: {skill.category}"
        texts.append(text)

    embeddings = embedding_model.encode(texts)
    vector_store.add(ids=[s.name for s in skills], embeddings=embeddings)
```

---

## 依赖项

```txt
# API Clients
firecrawl-py
tavily-python
openai  # 用于 OpenRouter API (通过设置 base_url)

# Knowledge Graph
neo4j
py2neo

# Vector Store & Embeddings
chromadb
sentence-transformers

# Utils
pydantic
python-dotenv
```

---

## 文件结构

```
stage1/
├── data/
│   ├── courses.json
│   ├── vr_apps.json
│   └── skills.json
├── chat_logs/
│   └── {session_id}.json
├── scripts/
│   ├── update_data.py
│   └── update_rag.py
├── src/
│   ├── information_module.py
│   ├── skill_gen.py
│   ├── knowledge_graph.py
│   └── rag_system.py
└── tests/
    └── test_retrieval.py
```
