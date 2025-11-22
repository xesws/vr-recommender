"""LLM-powered skill extraction using OpenRouter API"""

import json
import os
from typing import List, Dict
from openai import OpenAI


class SkillExtractor:
    """Extracts skills from text using OpenRouter LLM"""

    def __init__(self):
        """Initialize OpenRouter client with API key"""
        api_key = os.getenv(
            "OPENROUTER_API_KEY",
            "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"
        )
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        self.model = os.getenv("OPENROUTER_MODEL", "qwen/qwen3-next-80b-a3b-instruct")

    def extract_from_text(self, text: str, source_type: str = "course") -> List[Dict]:
        """
        Extract skills from text using LLM

        Args:
            text: Course description or app description
            source_type: "course" or "app"

        Returns:
            List[dict]: [{"name": "Python", "category": "technical", "weight": 0.9}, ...]
        """
        # Truncate very long text to avoid token limits
        if len(text) > 2000:
            text = text[:2000] + "..."

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

        try:
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
        except Exception as e:
            print(f"[ERROR] LLM extraction failed: {e}")
            return []

    def _parse_response(self, content: str) -> List[Dict]:
        """
        Parse JSON response from LLM

        Args:
            content: Raw response content

        Returns:
            List of skill dictionaries
        """
        try:
            # Clean and extract JSON
            content = content.strip()

            # Remove markdown code blocks if present
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.lower().startswith("json"):
                    content = content[4:]

            # Parse JSON
            data = json.loads(content)
            skills = data.get("skills", [])

            # Validate and clean skills
            valid_skills = []
            for skill in skills:
                if isinstance(skill, dict) and "name" in skill:
                    valid_skills.append({
                        "name": str(skill["name"]).strip(),
                        "category": skill.get("category", "technical"),
                        "weight": float(skill.get("weight", 0.5))
                    })

            return valid_skills
        except Exception as e:
            print(f"Error parsing LLM response: {e}")
            print(f"Content: {content}")
            return []
