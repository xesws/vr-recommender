"""LLM-based ranker for VR app recommendations.

Uses OpenRouter API to re-rank applications and generate explanations.
"""

import os
import json
from typing import List, Dict
from src.config_manager import ConfigManager

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class LLMRanker:
    """Rank and explain VR app recommendations using LLM."""

    def __init__(self):
        """Initialize the LLM ranker with OpenRouter configuration."""
        if OpenAI is None:
            raise ImportError("openai package required. Install with: pip install openai")

        self.config = ConfigManager()
        
        self.client = OpenAI(
            api_key=self.config.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        self.model = self.config.openrouter_model

    def rank_and_explain(self, query: str, apps: List[Dict]) -> List[Dict]:
        """
        Rank applications and generate reasoning for each.

        Args:
            query: User query string
            apps: List of candidate VR applications

        Returns:
            List of applications with reasoning added
        """
        if not apps:
            return []

        # Build prompt
        app_items = []
        for app in apps:
            info = f"- {app['name']} ({app['category']}): matches {', '.join(app['matched_skills'])}"
            if app.get("retrieval_source") == "semantic_bridge":
                info += f" [Note: {app.get('bridge_explanation', 'Indirect match')}]"
            app_items.append(info)
            
        app_list = "\n".join(app_items)

        prompt = f"""User Query: "{query}"

Candidate VR Apps:
{app_list}

Please generate a short reasoning for each app explaining why it fits the user's learning needs.
If an app has [Note: ...], incorporate that context into the reasoning (e.g., "Indirect match via...").

Return JSON format:
{{
    "rankings": [
        {{"name": "App Name", "reasoning": "Reasoning text in English"}},
        ...
    ]
}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert VR application recommender. Return JSON only. Output must be in English."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1024
            )

            return self._parse_rankings(response.choices[0].message.content, apps)
        except Exception as e:
            print(f"LLM ranking error: {e}")
            # Return apps with default reasoning
            for app in apps:
                app["reasoning"] = "Matches your learning interests"
            return apps

    def _parse_rankings(self, content: str, apps: List[Dict]) -> List[Dict]:
        """
        Parse LLM response and extract rankings.

        Args:
            content: LLM response text
            apps: Original apps list

        Returns:
            Apps with reasoning added
        """
        try:
            content = content.strip()
            if "```" in content:
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]

            data = json.loads(content)
            rankings = {r["name"]: r["reasoning"] for r in data.get("rankings", [])}
        except Exception as e:
            print(f"Parse error: {e}")
            rankings = {}

        # Add reasoning to each app
        for app in apps:
            app["reasoning"] = rankings.get(app["name"], "Matches your learning interests")

        return apps

    def understand_query(self, query: str) -> str:
        """
        Understand user query intent using LLM.

        Args:
            query: User query string

        Returns:
            One-sentence understanding of the query
        """
        prompt = f"""Analyze the following learning query and summarize what the user wants to learn in one sentence:

"{query}"

Return the summary directly, no other text. Output in English."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=100
            )

            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Query understanding error: {e}")
            return f"Learning interest: {query}"
