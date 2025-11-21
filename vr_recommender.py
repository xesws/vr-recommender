"""
LLM‑Based VR App Recommender for Heinz College
------------------------------------------------
• Uses OpenRouter (chat.completions) to infer intent → map to canonical categories
• Maps categories to curated VR apps (no course list shown to users)
• Falls back gracefully if LLM fails (aliases + keywords)

Usage
-----
export OPENROUTER_API_KEY=sk-or-v1-...
python heinz_vr_recommender_llm.py

Integrate into your web app by importing HeinzVRLLMRecommender and calling
  generate_recommendation(StudentQuery(...))

Notes
-----
- No MongoDB required. (You can add logging later if you want.)
- Temperature=0 for deterministic category mapping.
"""

from __future__ import annotations

import os
import re
import json
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime

from openai import OpenAI


# ----------------------------- Data Model ----------------------------- #

@dataclass
class StudentQuery:
    query: str
    interests: List[str]
    background: str = ""


# --------------------------- Recommender ------------------------------ #

class HeinzVRLLMRecommender:
    """LLM-first recommender: LLM understands intent → map to categories → apps."""

    def __init__(
        self,
        model_name: str = "qwen/qwen3-next-80b-a3b-thinking",
        api_key: Optional[str] = None,
        base_url: str = "https://openrouter.ai/api/v1"
    ):
        self.model_name = model_name
        self.client = OpenAI(
            api_key=api_key or os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY"),
            base_url=base_url
        )
        if not self.client.api_key:
            raise RuntimeError("OPENROUTER_API_KEY not set. Export it before running.")

        # Curated VR apps per category (expand as needed)
        self.vr_app_mappings: Dict[str, Dict[str, List[str]]] = {
            # Programming & Software
            "programming": {
                "apps": ["CodeVR Workspace", "Immersed", "Virtual Desktop"],
                "keywords": [
                    "programming","coding","software","python","java","javascript",
                    "development","developer","code","software engineering","swe",
                ],
            },
            "data_science": {
                "apps": ["Virtualitics VR", "DataVR", "Spatial Analytics"],
                "keywords": [
                    "data science","data mining","big data","data analysis","pandas","numpy",
                    "data exploration","feature engineering","modeling",
                ],
            },
            "machine_learning": {
                "apps": ["Neural Explorer VR", "AI Visualization Studio"],
                "keywords": [
                    "machine learning","ml","artificial intelligence","ai","neural network",
                    "deep learning","tensorflow","pytorch","model training",
                ],
            },
            "data_analytics": {
                "apps": ["DataViz VR", "Tableau VR", "Analytics Space"],
                "keywords": [
                    "data analytics","analytics","business intelligence","bi","dashboards",
                    "metrics","kpi","reporting","analysis",
                ],
            },
            "data_visualization": {
                "apps": ["Tableau VR", "DataViz VR", "Spatial Analytics"],
                "keywords": ["data visualization","visualization","charts","graphs","tableau","viz"],
            },
            "statistics": {
                "apps": ["DataVR", "Analytics Space", "Spatial Analytics"],
                "keywords": ["statistics","statistical","regression","hypothesis","probability","stata","spss","r programming"],
            },
            # Policy & Social
            "public_policy": {
                "apps": ["PolicyVR", "Virtual Town Hall", "Spatial Meetings"],
                "keywords": ["public policy","policy analysis","government","policy making","policy evaluation","program evaluation"],
            },
            "economics": {
                "apps": ["DataVR", "Analytics Space", "PolicyVR"],
                "keywords": ["economics","econometrics","economic policy","microeconomics","macroeconomics"],
            },
            # Security & Risk
            "cybersecurity": {
                "apps": ["Cyber Range VR", "Security Training VR"],
                "keywords": [
                    "cybersecurity","cyber security","information security","infosec","security",
                    "hacking","penetration testing","threat","vulnerability","risk",
                ],
            },
            "risk_management": {
                "apps": ["Security Training VR", "Spatial Meetings"],
                "keywords": ["risk management","risk assessment","risk analysis","compliance","audit","governance"],
            },
            # Management & Leadership
            "project_management": {
                "apps": ["Horizon Workrooms", "Spatial", "Arthur VR"],
                "keywords": ["project management","agile","scrum","sprint","kanban","project planning","team management"],
            },
            "leadership": {
                "apps": ["Spatial Meetings", "Horizon Workrooms", "MeetinVR"],
                "keywords": ["leadership","management","organizational behavior","team building","strategic management"],
            },
            "communication": {
                "apps": ["Spatial Meetings", "Horizon Workrooms", "MeetinVR"],
                "keywords": ["communication","public speaking","presentation","collaboration","negotiation","interpersonal"],
            },
            # Design & Creative
            "design": {
                "apps": ["Gravity Sketch", "Tilt Brush", "ShapesXR"],
                "keywords": ["design","ux","ui","user experience","design thinking","prototyping","wireframe"],
            },
            # Finance & Business
            "finance": {
                "apps": ["Finance Simulator VR", "Trading Floor VR"],
                "keywords": ["finance","financial","fintech","accounting","investment","portfolio","trading","financial modeling"],
            },
            # Database & Systems
            "database": {
                "apps": ["CodeVR Workspace", "Immersed", "DataVR"],
                "keywords": ["database","sql","nosql","mongodb","postgresql","data modeling","relational database"],
            },
            "cloud_computing": {
                "apps": ["Virtual Desktop", "Immersed", "CodeVR Workspace"],
                "keywords": ["cloud","aws","azure","google cloud","cloud computing","devops","kubernetes","docker"],
            },
        }

    # ------------------------ Utilities ------------------------ #

    def _norm(self, text: str) -> str:
        t = (text or "").lower()
        t = re.sub(r"[^a-z0-9\s/+_-]+", " ", t)
        t = re.sub(r"\s+", " ", t).strip()
        return t

    def _category_aliases(self) -> Dict[str, str]:
        return {
            # security
            "cyber security": "cybersecurity",
            "information security": "cybersecurity",
            "infosec": "cybersecurity",
            "security": "cybersecurity",
            # programming / SWE
            "software engineering": "programming",
            "software engineer": "programming",
            "swe": "programming",
            "coding": "programming",
            # data
            "data analytics": "data_analytics",
            "analytics": "data_analytics",
            "bi": "data_analytics",
            "business intelligence": "data_analytics",
            "data viz": "data_visualization",
            "data visualization": "data_visualization",
            "viz": "data_visualization",
            "data science": "data_science",
            "ml": "machine_learning",
            "machine learning": "machine_learning",
            "ai": "machine_learning",
            # policy/econ
            "public policy": "public_policy",
            "policy": "public_policy",
            "econometrics": "economics",
            "economics": "economics",
            # mgmt
            "project management": "project_management",
            "pm": "project_management",
            "leadership": "leadership",
            "communication": "communication",
            # cloud/db
            "cloud": "cloud_computing",
            "aws": "cloud_computing",
            "kubernetes": "cloud_computing",
            "docker": "cloud_computing",
            "sql": "database",
            "database": "database",
        }

    # ------------------------ LLM Core ------------------------- #

    def _llm_map_to_categories(self, text: str, extra_hints: Optional[List[str]] = None) -> List[str]:
        """Ask the LLM to pick 1–3 categories from our canonical list.
        Returns canonical category strings; may return empty list if parsing fails."""
        categories = list(self.vr_app_mappings.keys())
        hints = ", ".join(extra_hints or [])

        system = (
            "You map student requests to canonical learning categories. "
            "Select ONLY from the provided categories. "
            "Return a JSON array of 1 to 3 strings (no prose)."
        )
        user = (
            f"Student request: {text}\n"
            f"Optional hints: {hints}\n"
            f"Allowed categories: {categories}\n"
            "Return JSON only, e.g., [\"cybersecurity\", \"risk_management\"]."
        )

        resp = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0,
            max_tokens=64,
        )
        raw = resp.choices[0].message.content.strip()
        # Be lenient in parsing: try JSON first, then python-literal-like
        try:
            data = json.loads(raw)
            if isinstance(data, list):
                return [c for c in data if isinstance(c, str)]
        except Exception:
            pass
        try:
            import ast
            data = ast.literal_eval(raw)
            if isinstance(data, list):
                return [str(c) for c in data]
        except Exception:
            pass
        # If model returned a single token string like "cybersecurity"
        raw_norm = self._norm(raw)
        if raw_norm in categories:
            return [raw_norm]
        return []

    # -------------------- Recommendation Logic ----------------- #

    def recommend_vr_apps(self, query: StudentQuery) -> List[Dict]:
        """Use LLM to map to categories, fall back to aliases/keywords, then map to apps."""
        print(f"  → Analyzing query (LLM): '{query.query}'")

        # 1) LLM category mapping
        llm_cats = self._llm_map_to_categories(query.query, extra_hints=query.interests)
        cat_scores: Dict[str, float] = {}
        for i, cat in enumerate(llm_cats[:3]):
            c = self._norm(cat)
            if c in self.vr_app_mappings:
                # Slight rank decay: first choice strongest
                cat_scores[c] = max(cat_scores.get(c, 0.0), 5.0 - i)
                print(f"  ✓ LLM category: {c} (+{5.0 - i:.1f})")

        # 2) Fallback: alias + keywords if LLM returns nothing
        if not cat_scores:
            print("  → LLM returned nothing; using aliases/keywords fallback…")
            search_text = self._norm(query.query + " " + " ".join(query.interests or []))
            # Aliases
            for alias, cat in self._category_aliases().items():
                if alias in search_text and cat in self.vr_app_mappings:
                    cat_scores[cat] = cat_scores.get(cat, 0.0) + 4.0
            # Direct category name
            for cat in self.vr_app_mappings.keys():
                cname = cat.replace("_", " ")
                if cname in search_text:
                    cat_scores[cat] = max(cat_scores.get(cat, 0.0), 3.5)
            # Keyword bag-of-words
            for cat, data in self.vr_app_mappings.items():
                score = 0.0
                for kw in data["keywords"]:
                    if self._norm(kw) in search_text:
                        score += 1.5
                if score > 0:
                    cat_scores[cat] = max(cat_scores.get(cat, 0.0), score)

        # 3) Last-resort defaults
        if not cat_scores:
            print("  → Still empty; applying sensible defaults…")
            cat_scores = {"project_management": 2.0, "communication": 2.0, "programming": 1.0}

        print(f"  → Final category scores: {cat_scores}")

        # Build app scores from categories
        app_scores: Dict[str, float] = {}
        for cat, score in cat_scores.items():
            if cat in self.vr_app_mappings:
                for app in self.vr_app_mappings[cat]["apps"]:
                    app_scores[app] = max(app_scores.get(app, 0.0), float(score))

        # Sort & shape
        sorted_apps = sorted(app_scores.items(), key=lambda x: x[1], reverse=True)
        recs: List[Dict] = []
        for app_name, score in sorted_apps[:8]:
            recs.append({
                "app_name": app_name,
                "likeliness_score": round(min(1.0, score / 5.0), 2),
                "category": self._get_app_category(app_name),
                "reasoning": "Mapped via LLM intent understanding",
            })
        print(f"  ✓ Returning {len(recs)} VR apps")
        return recs

    def _get_app_category(self, app_name: str) -> str:
        for category, data in self.vr_app_mappings.items():
            if app_name in data["apps"]:
                return category.replace("_", " ").title()
        return "General"

    def generate_recommendation(self, query: StudentQuery) -> Dict:
        print(f"\n🔍 Processing (LLM): {query.query}")
        try:
            vr_apps = self.recommend_vr_apps(query)
            return {
                "student_query": query.query,
                "vr_apps": vr_apps,
                "message": f"Here are {len(vr_apps)} VR apps aligned to your interests.",
                "generated_at": datetime.utcnow().isoformat() + "Z",
            }
        except Exception as e:
            return {
                "student_query": query.query,
                "vr_apps": [],
                "message": f"Error: {str(e)}",
                "generated_at": datetime.utcnow().isoformat() + "Z",
            }


# ------------------------------ CLI ---------------------------------- #

def main():
    print("=" * 70)
    print("HEINZ LLM VR APP RECOMMENDER")
    print("=" * 70)

    rec = HeinzVRLLMRecommender()

    demos = [
        StudentQuery("I want to learn about cyber security", ["projects"], "MSISPM"),
        StudentQuery("software engineering", ["coding"], "MISM"),
        StudentQuery("Data analytics", ["visualization"], "MSPPM"),
        StudentQuery("ML for public policy", ["causal inference"], "MSPPM"),
    ]

    for q in demos:
        out = rec.generate_recommendation(q)
        print("\nQuery:", out["student_query"])
        print("Apps:")
        for a in out["vr_apps"][:5]:
            print(f"  • {a['app_name']} — {a['category']} ({int(a['likeliness_score']*100)}%)")


if __name__ == "__main__":
    main()
