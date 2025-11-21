# Stage 1: Data Collection Module

## 目标

从外部数据源获取 CMU 课程和 Meta Quest VR 应用信息。

## 输入/输出

- **输入**: Firecrawl API, Tavily API
- **输出**: `data/courses.json`, `data/vr_apps.json`

## 前置条件

- Firecrawl API Key
- Tavily API Key

---

## 任务分解

### 1.1 环境配置

```python
# .env 文件
FIRECRAWL_API_KEY=your-key
TAVILY_API_KEY=your-key
```

### 1.2 数据结构定义

```python
# src/models.py

from dataclasses import dataclass, asdict
from typing import List

@dataclass
class Course:
    course_id: str          # "95-865"
    title: str              # "Unstructured Data Analytics"
    department: str         # "Heinz College"
    description: str
    units: int
    prerequisites: List[str]
    learning_outcomes: List[str]

    def to_dict(self):
        return asdict(self)

@dataclass
class VRApp:
    app_id: str             # 唯一标识
    name: str               # "Spatial"
    category: str           # "Productivity"
    description: str
    features: List[str]
    skills_developed: List[str]
    rating: float
    price: str

    def to_dict(self):
        return asdict(self)
```

### 1.3 CMU 课程爬取

```python
# src/data_collection/course_fetcher.py

from firecrawl import FirecrawlApp
import json
import os

class CMUCourseFetcher:
    def __init__(self):
        self.client = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))
        self.base_url = "https://www.cmu.edu/hub/registrar/course-schedule/"

    def fetch_courses(self, semester: str = "fall2024") -> List[Course]:
        """
        爬取 CMU 课程目录

        Returns:
            List[Course]: 课程列表
        """
        # 爬取页面
        result = self.client.scrape_url(
            f"{self.base_url}",
            params={"formats": ["markdown"]}
        )

        # 解析课程数据
        courses = self._parse_courses(result)
        return courses

    def _parse_courses(self, raw_data: dict) -> List[Course]:
        """解析爬取的原始数据为 Course 对象"""
        courses = []
        # TODO: 根据实际页面结构实现解析逻辑
        # 可能需要使用 LLM 辅助提取结构化数据
        return courses

    def save_courses(self, courses: List[Course], path: str = "data/courses.json"):
        """保存课程数据到 JSON"""
        with open(path, "w", encoding="utf-8") as f:
            json.dump([c.to_dict() for c in courses], f, indent=2, ensure_ascii=False)
```

### 1.4 VR 应用搜索

```python
# src/data_collection/vr_app_fetcher.py

from tavily import TavilyClient
import os

class VRAppFetcher:
    def __init__(self):
        self.client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

    def fetch_apps(self, categories: List[str] = None) -> List[VRApp]:
        """
        搜索 Meta Quest VR 应用

        Args:
            categories: 应用类别 ["education", "training", "productivity"]

        Returns:
            List[VRApp]: 应用列表
        """
        categories = categories or ["education", "training", "productivity"]
        all_apps = []

        for category in categories:
            query = f"Meta Quest VR apps for {category} learning"
            results = self.client.search(
                query=query,
                search_depth="advanced",
                max_results=20
            )
            apps = self._parse_results(results, category)
            all_apps.extend(apps)

        # 去重
        return self._deduplicate(all_apps)

    def _parse_results(self, results: dict, category: str) -> List[VRApp]:
        """解析 Tavily 搜索结果"""
        apps = []
        for item in results.get("results", []):
            # TODO: 使用 LLM 从搜索结果中提取结构化应用信息
            pass
        return apps

    def _deduplicate(self, apps: List[VRApp]) -> List[VRApp]:
        """根据 app_id 或 name 去重"""
        seen = set()
        unique = []
        for app in apps:
            if app.name not in seen:
                seen.add(app.name)
                unique.append(app)
        return unique

    def save_apps(self, apps: List[VRApp], path: str = "data/vr_apps.json"):
        """保存应用数据到 JSON"""
        with open(path, "w", encoding="utf-8") as f:
            json.dump([a.to_dict() for a in apps], f, indent=2, ensure_ascii=False)
```

### 1.5 主脚本

```python
# scripts/fetch_data.py

import argparse
from src.data_collection.course_fetcher import CMUCourseFetcher
from src.data_collection.vr_app_fetcher import VRAppFetcher

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", choices=["courses", "apps", "all"], default="all")
    parser.add_argument("--output-dir", default="data")
    args = parser.parse_args()

    if args.source in ["courses", "all"]:
        print("Fetching CMU courses...")
        fetcher = CMUCourseFetcher()
        courses = fetcher.fetch_courses()
        fetcher.save_courses(courses, f"{args.output_dir}/courses.json")
        print(f"✓ Saved {len(courses)} courses")

    if args.source in ["apps", "all"]:
        print("Fetching VR apps...")
        fetcher = VRAppFetcher()
        apps = fetcher.fetch_apps()
        fetcher.save_apps(apps, f"{args.output_dir}/vr_apps.json")
        print(f"✓ Saved {len(apps)} apps")

if __name__ == "__main__":
    main()
```

---

## 文件结构

```
stage1/
├── src/
│   ├── models.py
│   └── data_collection/
│       ├── __init__.py
│       ├── course_fetcher.py
│       └── vr_app_fetcher.py
├── scripts/
│   └── fetch_data.py
├── data/
│   ├── courses.json
│   └── vr_apps.json
└── tests/
    └── test_data_collection.py
```

---

## 验收标准

- [ ] `courses.json` 包含 ≥50 门课程
- [ ] `vr_apps.json` 包含 ≥30 个应用
- [ ] 每个课程有完整的 `course_id`, `title`, `description`
- [ ] 每个应用有完整的 `name`, `category`, `description`
- [ ] 数据可被 Stage 2 正确读取和解析

---

## 依赖项

```txt
firecrawl-py
tavily-python
python-dotenv
```
