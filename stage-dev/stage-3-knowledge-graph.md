# Stage 3: Knowledge Graph Construction

## 目标

使用 Neo4j 构建知识图谱，包含课程、VR 应用、技能三类节点及其关系。

## 输入/输出

- **输入**: Stage 1 & 2 的所有 JSON 文件
- **输出**: 填充完成的 Neo4j 数据库

## 前置条件

- Stage 1 & 2 完成
- Neo4j 数据库运行中

---

## 任务分解

### 3.1 Neo4j 连接管理

```python
# src/knowledge_graph/connection.py

from neo4j import GraphDatabase
import os

class Neo4jConnection:
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "password")
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))

    def close(self):
        self.driver.close()

    def query(self, cypher: str, params: dict = None):
        with self.driver.session() as session:
            result = session.run(cypher, params or {})
            return [record.data() for record in result]

    def execute(self, cypher: str, params: dict = None):
        with self.driver.session() as session:
            session.run(cypher, params or {})
```

### 3.2 Schema 初始化

```python
# src/knowledge_graph/schema.py

class KnowledgeGraphSchema:
    def __init__(self, connection: Neo4jConnection):
        self.conn = connection

    def init_constraints(self):
        """创建唯一性约束"""
        constraints = [
            "CREATE CONSTRAINT course_id IF NOT EXISTS FOR (c:Course) REQUIRE c.course_id IS UNIQUE",
            "CREATE CONSTRAINT app_id IF NOT EXISTS FOR (a:VRApp) REQUIRE a.app_id IS UNIQUE",
            "CREATE CONSTRAINT skill_name IF NOT EXISTS FOR (s:Skill) REQUIRE s.name IS UNIQUE",
        ]
        for c in constraints:
            self.conn.execute(c)
        print("✓ Constraints created")

    def init_indexes(self):
        """创建索引"""
        indexes = [
            "CREATE INDEX course_dept IF NOT EXISTS FOR (c:Course) ON (c.department)",
            "CREATE INDEX app_category IF NOT EXISTS FOR (a:VRApp) ON (a.category)",
            "CREATE INDEX skill_category IF NOT EXISTS FOR (s:Skill) ON (s.category)",
        ]
        for i in indexes:
            self.conn.execute(i)
        print("✓ Indexes created")

    def clear_database(self):
        """清空数据库 (谨慎使用)"""
        self.conn.execute("MATCH (n) DETACH DELETE n")
        print("✓ Database cleared")
```

### 3.3 节点创建

```python
# src/knowledge_graph/nodes.py

import json
from typing import List

class NodeCreator:
    def __init__(self, connection: Neo4jConnection):
        self.conn = connection

    def create_courses(self, courses_path: str):
        """创建 Course 节点"""
        with open(courses_path) as f:
            courses = json.load(f)

        cypher = """
        UNWIND $courses AS course
        MERGE (c:Course {course_id: course.course_id})
        SET c.title = course.title,
            c.department = course.department,
            c.description = course.description,
            c.units = course.units
        """
        self.conn.execute(cypher, {"courses": courses})
        print(f"✓ Created {len(courses)} Course nodes")

    def create_apps(self, apps_path: str):
        """创建 VRApp 节点"""
        with open(apps_path) as f:
            apps = json.load(f)

        cypher = """
        UNWIND $apps AS app
        MERGE (a:VRApp {app_id: app.app_id})
        SET a.name = app.name,
            a.category = app.category,
            a.description = app.description,
            a.rating = app.rating,
            a.price = app.price
        """
        self.conn.execute(cypher, {"apps": apps})
        print(f"✓ Created {len(apps)} VRApp nodes")

    def create_skills(self, skills_path: str):
        """创建 Skill 节点"""
        with open(skills_path) as f:
            skills = json.load(f)

        cypher = """
        UNWIND $skills AS skill
        MERGE (s:Skill {name: skill.name})
        SET s.category = skill.category,
            s.aliases = skill.aliases,
            s.source_count = skill.source_count
        """
        self.conn.execute(cypher, {"skills": skills})
        print(f"✓ Created {len(skills)} Skill nodes")
```

### 3.4 关系创建

```python
# src/knowledge_graph/relationships.py

import json

class RelationshipCreator:
    def __init__(self, connection: Neo4jConnection):
        self.conn = connection

    def create_course_skill_relations(self, course_skills_path: str):
        """创建 Course-TEACHES->Skill 关系"""
        with open(course_skills_path) as f:
            mappings = json.load(f)

        cypher = """
        UNWIND $mappings AS m
        MATCH (c:Course {course_id: m.source_id})
        MATCH (s:Skill {name: m.skill_name})
        MERGE (c)-[r:TEACHES]->(s)
        SET r.weight = m.weight
        """
        self.conn.execute(cypher, {"mappings": mappings})
        print(f"✓ Created {len(mappings)} TEACHES relationships")

    def create_app_skill_relations(self, app_skills_path: str):
        """创建 VRApp-DEVELOPS->Skill 关系"""
        with open(app_skills_path) as f:
            mappings = json.load(f)

        cypher = """
        UNWIND $mappings AS m
        MATCH (a:VRApp {app_id: m.source_id})
        MATCH (s:Skill {name: m.skill_name})
        MERGE (a)-[r:DEVELOPS]->(s)
        SET r.weight = m.weight
        """
        self.conn.execute(cypher, {"mappings": mappings})
        print(f"✓ Created {len(mappings)} DEVELOPS relationships")

    def compute_recommendations(self):
        """
        计算 Course-RECOMMENDS->VRApp 关系
        基于共享技能数量和权重
        """
        cypher = """
        MATCH (c:Course)-[t:TEACHES]->(s:Skill)<-[d:DEVELOPS]-(a:VRApp)
        WITH c, a, collect(s.name) AS shared_skills,
             sum(t.weight * d.weight) AS score
        WHERE size(shared_skills) >= 1
        MERGE (c)-[r:RECOMMENDS]->(a)
        SET r.score = score,
            r.shared_skills = shared_skills,
            r.skill_count = size(shared_skills)
        """
        self.conn.execute(cypher)

        # 统计创建的关系数
        result = self.conn.query("MATCH ()-[r:RECOMMENDS]->() RETURN count(r) as count")
        count = result[0]["count"] if result else 0
        print(f"✓ Computed {count} RECOMMENDS relationships")
```

### 3.5 图谱构建管道

```python
# src/knowledge_graph/builder.py

class KnowledgeGraphBuilder:
    def __init__(self):
        self.conn = Neo4jConnection()
        self.schema = KnowledgeGraphSchema(self.conn)
        self.nodes = NodeCreator(self.conn)
        self.relations = RelationshipCreator(self.conn)

    def build(self, data_dir: str = "data", clear: bool = False):
        """构建完整知识图谱"""
        print("\n" + "="*50)
        print("Building Knowledge Graph")
        print("="*50 + "\n")

        if clear:
            self.schema.clear_database()

        # 1. 初始化 schema
        self.schema.init_constraints()
        self.schema.init_indexes()

        # 2. 创建节点
        self.nodes.create_courses(f"{data_dir}/courses.json")
        self.nodes.create_apps(f"{data_dir}/vr_apps.json")
        self.nodes.create_skills(f"{data_dir}/skills.json")

        # 3. 创建关系
        self.relations.create_course_skill_relations(f"{data_dir}/course_skills.json")
        self.relations.create_app_skill_relations(f"{data_dir}/app_skills.json")
        self.relations.compute_recommendations()

        # 4. 打印统计
        self._print_stats()

        self.conn.close()

    def _print_stats(self):
        """打印图谱统计"""
        stats = self.conn.query("""
        MATCH (c:Course) WITH count(c) as courses
        MATCH (a:VRApp) WITH courses, count(a) as apps
        MATCH (s:Skill) WITH courses, apps, count(s) as skills
        MATCH ()-[r:TEACHES]->() WITH courses, apps, skills, count(r) as teaches
        MATCH ()-[r:DEVELOPS]->() WITH courses, apps, skills, teaches, count(r) as develops
        MATCH ()-[r:RECOMMENDS]->()
        RETURN courses, apps, skills, teaches, develops, count(r) as recommends
        """)

        if stats:
            s = stats[0]
            print("\n📊 Knowledge Graph Statistics:")
            print(f"   Courses: {s['courses']}")
            print(f"   VR Apps: {s['apps']}")
            print(f"   Skills: {s['skills']}")
            print(f"   TEACHES: {s['teaches']}")
            print(f"   DEVELOPS: {s['develops']}")
            print(f"   RECOMMENDS: {s['recommends']}")
```

### 3.6 主脚本

```python
# scripts/build_graph.py

import argparse
from src.knowledge_graph.builder import KnowledgeGraphBuilder

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--clear", action="store_true", help="Clear existing data")
    args = parser.parse_args()

    builder = KnowledgeGraphBuilder()
    builder.build(args.data_dir, args.clear)

if __name__ == "__main__":
    main()
```

---

## 示例查询

```cypher
-- 查找某课程推荐的 VR 应用
MATCH (c:Course {course_id: "95-865"})-[r:RECOMMENDS]->(a:VRApp)
RETURN a.name, r.score, r.shared_skills
ORDER BY r.score DESC
LIMIT 5

-- 查找培养 Machine Learning 技能的所有资源
MATCH (n)-[r]->(s:Skill {name: "Machine Learning"})
RETURN labels(n)[0] as type,
       COALESCE(n.title, n.name) as name,
       r.weight as importance
ORDER BY r.weight DESC

-- 查找与某应用相关的课程
MATCH (c:Course)-[:TEACHES]->(s:Skill)<-[:DEVELOPS]-(a:VRApp {name: "Spatial"})
RETURN c.title, collect(s.name) as shared_skills
ORDER BY size(shared_skills) DESC
```

---

## 文件结构

```
stage3/
├── src/
│   └── knowledge_graph/
│       ├── __init__.py
│       ├── connection.py
│       ├── schema.py
│       ├── nodes.py
│       ├── relationships.py
│       └── builder.py
├── scripts/
│   └── build_graph.py
└── tests/
    └── test_knowledge_graph.py
```

---

## 验收标准

- [ ] Neo4j 数据库包含所有 Course、VRApp、Skill 节点
- [ ] TEACHES 关系连接 Course 和 Skill
- [ ] DEVELOPS 关系连接 VRApp 和 Skill
- [ ] RECOMMENDS 关系连接 Course 和 VRApp
- [ ] 所有示例查询返回合理结果
- [ ] 图谱可在 Neo4j Browser 中可视化浏览

---

## 依赖项

```txt
neo4j
python-dotenv
```

## 环境配置

```bash
# .env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password
```
