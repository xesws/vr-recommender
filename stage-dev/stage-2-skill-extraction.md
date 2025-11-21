# Stage 2: Skill Extraction Module

## 目标

从课程描述和 VR 应用描述中提取技能关键词，作为知识图谱的桥梁节点。

## 输入/输出

- **输入**: `data/courses.json`, `data/vr_apps.json` (来自 Stage 1)
- **输出**:
  - `data/skills.json` - 所有技能列表
  - `data/course_skills.json` - 课程-技能映射
  - `data/app_skills.json` - 应用-技能映射

## 前置条件

- Stage 1 完成
- OpenRouter API Key

---

## 任务分解

### 2.1 技能数据结构

```python
# src/models.py (扩展)

@dataclass
class Skill:
    name: str               # 标准化名称 "Machine Learning"
    aliases: List[str]      # ["ML", "机器学习"]
    category: str           # "technical" | "soft" | "domain"
    source_count: int       # 出现次数

@dataclass
class SkillMapping:
    source_id: str          # course_id 或 app_id
    source_type: str        # "course" | "app"
    skill_name: str         # 技能名称
    weight: float           # 重要程度 0.0-1.0
```

### 2.2 LLM 技能提取器

```python
# src/skill_extraction/extractor.py

from openai import OpenAI
import json
import os

class SkillExtractor:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1"
        )
        self.model = os.getenv("OPENROUTER_MODEL", "qwen/qwen3-30b-a3b")

    def extract_from_text(self, text: str, source_type: str = "course") -> List[dict]:
        """
        从文本中提取技能

        Args:
            text: 课程描述或应用描述
            source_type: "course" 或 "app"

        Returns:
            List[dict]: [{"name": "Python", "category": "technical", "weight": 0.8}, ...]
        """
        prompt = f"""从以下{source_type}描述中提取关键技能:

{text}

要求:
1. 提取技术技能 (如 Python, SQL, Machine Learning)
2. 提取软技能 (如 Communication, Leadership)
3. 提取领域知识 (如 Public Policy, Finance)
4. 为每个技能评估重要程度 (0.0-1.0)
5. 返回 JSON 格式

返回格式:
{{"skills": [
    {{"name": "Python", "category": "technical", "weight": 0.9}},
    {{"name": "Data Analysis", "category": "technical", "weight": 0.8}}
]}}"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一个技能提取专家。只返回 JSON，不要其他内容。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=512
        )

        return self._parse_response(response.choices[0].message.content)

    def _parse_response(self, content: str) -> List[dict]:
        """解析 LLM 返回的 JSON"""
        try:
            # 尝试提取 JSON
            content = content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            data = json.loads(content)
            return data.get("skills", [])
        except:
            return []
```

### 2.3 技能规范化

```python
# src/skill_extraction/normalizer.py

class SkillNormalizer:
    def __init__(self):
        # 预定义的别名映射
        self.alias_map = {
            "ml": "Machine Learning",
            "ai": "Artificial Intelligence",
            "dl": "Deep Learning",
            "nlp": "Natural Language Processing",
            "cv": "Computer Vision",
            "sql": "SQL",
            "python": "Python",
            "r": "R Programming",
            "js": "JavaScript",
            "swe": "Software Engineering",
            "pm": "Project Management",
            "ux": "User Experience",
            "ui": "User Interface",
            "bi": "Business Intelligence",
        }

    def normalize(self, skill_name: str) -> str:
        """将技能名称标准化"""
        lower = skill_name.lower().strip()

        # 检查别名
        if lower in self.alias_map:
            return self.alias_map[lower]

        # 标题化
        return skill_name.strip().title()

    def are_similar(self, skill1: str, skill2: str) -> bool:
        """判断两个技能是否相似"""
        s1 = self.normalize(skill1).lower()
        s2 = self.normalize(skill2).lower()

        # 完全匹配
        if s1 == s2:
            return True

        # 包含关系
        if s1 in s2 or s2 in s1:
            return True

        return False
```

### 2.4 技能去重与合并

```python
# src/skill_extraction/deduplicator.py

class SkillDeduplicator:
    def __init__(self, normalizer: SkillNormalizer):
        self.normalizer = normalizer

    def deduplicate(self, skills: List[dict]) -> List[Skill]:
        """
        合并相似技能

        Args:
            skills: [{"name": "ML", "category": "technical", "weight": 0.8}, ...]

        Returns:
            List[Skill]: 去重后的技能列表
        """
        merged = {}

        for skill in skills:
            name = self.normalizer.normalize(skill["name"])

            if name in merged:
                # 合并：保留最高 weight，累加 count
                merged[name]["source_count"] += 1
                merged[name]["weight"] = max(merged[name]["weight"], skill.get("weight", 0.5))
                # 添加别名
                if skill["name"] != name and skill["name"] not in merged[name]["aliases"]:
                    merged[name]["aliases"].append(skill["name"])
            else:
                merged[name] = {
                    "name": name,
                    "aliases": [skill["name"]] if skill["name"] != name else [],
                    "category": skill.get("category", "technical"),
                    "source_count": 1,
                    "weight": skill.get("weight", 0.5)
                }

        return [
            Skill(
                name=v["name"],
                aliases=v["aliases"],
                category=v["category"],
                source_count=v["source_count"]
            )
            for v in merged.values()
        ]
```

### 2.5 批量处理管道

```python
# src/skill_extraction/pipeline.py

import json
from typing import List, Dict

class SkillExtractionPipeline:
    def __init__(self):
        self.extractor = SkillExtractor()
        self.normalizer = SkillNormalizer()
        self.deduplicator = SkillDeduplicator(self.normalizer)

    def process_courses(self, courses_path: str) -> tuple:
        """处理所有课程"""
        with open(courses_path) as f:
            courses = json.load(f)

        all_skills = []
        course_skills = []

        for course in courses:
            text = f"{course['title']}. {course['description']}"
            skills = self.extractor.extract_from_text(text, "course")

            for skill in skills:
                all_skills.append(skill)
                course_skills.append({
                    "source_id": course["course_id"],
                    "source_type": "course",
                    "skill_name": self.normalizer.normalize(skill["name"]),
                    "weight": skill.get("weight", 0.5)
                })

        return all_skills, course_skills

    def process_apps(self, apps_path: str) -> tuple:
        """处理所有应用"""
        with open(apps_path) as f:
            apps = json.load(f)

        all_skills = []
        app_skills = []

        for app in apps:
            text = f"{app['name']}. {app['description']}. Features: {', '.join(app.get('features', []))}"
            skills = self.extractor.extract_from_text(text, "app")

            for skill in skills:
                all_skills.append(skill)
                app_skills.append({
                    "source_id": app["app_id"],
                    "source_type": "app",
                    "skill_name": self.normalizer.normalize(skill["name"]),
                    "weight": skill.get("weight", 0.5)
                })

        return all_skills, app_skills

    def run(self, courses_path: str, apps_path: str, output_dir: str):
        """运行完整管道"""
        # 处理课程
        course_skills_raw, course_mappings = self.process_courses(courses_path)

        # 处理应用
        app_skills_raw, app_mappings = self.process_apps(apps_path)

        # 合并并去重所有技能
        all_skills_raw = course_skills_raw + app_skills_raw
        unique_skills = self.deduplicator.deduplicate(all_skills_raw)

        # 保存结果
        with open(f"{output_dir}/skills.json", "w") as f:
            json.dump([s.__dict__ for s in unique_skills], f, indent=2)

        with open(f"{output_dir}/course_skills.json", "w") as f:
            json.dump(course_mappings, f, indent=2)

        with open(f"{output_dir}/app_skills.json", "w") as f:
            json.dump(app_mappings, f, indent=2)

        return unique_skills, course_mappings, app_mappings
```

### 2.6 主脚本

```python
# scripts/extract_skills.py

import argparse
from src.skill_extraction.pipeline import SkillExtractionPipeline

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--courses", default="data/courses.json")
    parser.add_argument("--apps", default="data/vr_apps.json")
    parser.add_argument("--output-dir", default="data")
    args = parser.parse_args()

    pipeline = SkillExtractionPipeline()
    skills, course_map, app_map = pipeline.run(
        args.courses,
        args.apps,
        args.output_dir
    )

    print(f"✓ Extracted {len(skills)} unique skills")
    print(f"✓ Created {len(course_map)} course-skill mappings")
    print(f"✓ Created {len(app_map)} app-skill mappings")

if __name__ == "__main__":
    main()
```

---

## 文件结构

```
stage2/
├── src/
│   └── skill_extraction/
│       ├── __init__.py
│       ├── extractor.py
│       ├── normalizer.py
│       ├── deduplicator.py
│       └── pipeline.py
├── scripts/
│   └── extract_skills.py
├── data/
│   ├── skills.json
│   ├── course_skills.json
│   └── app_skills.json
└── tests/
    └── test_skill_extraction.py
```

---

## 验收标准

- [ ] `skills.json` 包含 ≥100 个去重技能
- [ ] 每个技能有 `name`, `aliases`, `category`
- [ ] 技能类别分布合理 (technical/soft/domain)
- [ ] `course_skills.json` 覆盖所有课程
- [ ] `app_skills.json` 覆盖所有应用
- [ ] 相似技能已正确合并 (如 "ML" 和 "Machine Learning")

---

## 依赖项

```txt
openai  # OpenRouter API
python-dotenv
```
