import json
import logging
import os
import re
from typing import Dict, List, Optional, Any
from django.conf import settings

logger = logging.getLogger(__name__)

# Preferred models available on Groq
CANDIDATE_MODELS = [
    'openai/gpt-oss-120b',
    'qwen/qwen3.8-27b',
    'openai/gpt-oss-20b',
    'allam-2-7b',
]


class LLMClient:
    """
    Client for invoking LLMs via Groq API with automatic model failover
    and structured JSON response extraction.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        if api_key is not None:
            self.groq_api_key = api_key.strip()
        else:
            self.groq_api_key = (
                getattr(settings, 'GROQ_API_KEY', '') or
                os.getenv('GROQ_API_KEY', '')
            ).strip()

        configured_model = (
            model or
            getattr(settings, 'GROQ_MODEL', '') or
            os.getenv('GROQ_MODEL', '')
        ).strip()

        # Build list of models to try
        self.models_to_try = []
        if configured_model:
            self.models_to_try.append(configured_model)
        for m in CANDIDATE_MODELS:
            if m not in self.models_to_try:
                self.models_to_try.append(m)

        self.model = self.models_to_try[0] if self.models_to_try else 'openai/gpt-oss-120b'

    def is_configured(self) -> bool:
        return bool(self.groq_api_key)

    def generate(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """
        Calls Groq API to generate structured content recommendations and titles.
        Tries candidate models in order if one is unavailable.
        """
        if not self.is_configured():
            logger.warning("GROQ_API_KEY is not configured. Falling back to heuristic insights.")
            return self._fallback_generation(user_prompt)

        try:
            from groq import Groq
            client = Groq(api_key=self.groq_api_key)
        except Exception as e:
            logger.error(f"Failed to initialize Groq client: {e}")
            return self._fallback_generation(user_prompt, error_note=str(e))

        last_error = None
        for candidate_model in self.models_to_try:
            try:
                logger.info(f"Invoking Groq model: {candidate_model}")
                # Try standard call without response_format to ensure compatibility with all open models
                chat_completion = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    model=candidate_model,
                    temperature=0.7,
                    max_tokens=1000
                )

                raw_content = chat_completion.choices[0].message.content
                if raw_content:
                    parsed = self._parse_json_response(raw_content)
                    parsed['model'] = candidate_model
                    parsed['provider'] = 'groq'
                    return parsed

            except Exception as e:
                logger.warning(f"Groq model {candidate_model} failed: {e}. Trying next candidate...")
                last_error = e

        logger.error(f"All candidate Groq models failed. Last error: {last_error}")
        return self._fallback_generation(user_prompt, error_note=str(last_error))

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """
        Parses JSON response safely, handling markdown code blocks and raw text.
        """
        if not content:
            return self._fallback_generation("")

        # 1. Direct JSON decode
        try:
            data = json.loads(content.strip())
            return self._format_parsed_data(data)
        except json.JSONDecodeError:
            pass

        # 2. Extract JSON code block: ```json { ... } ```
        json_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
        if json_block_match:
            try:
                data = json.loads(json_block_match.group(1))
                return self._format_parsed_data(data)
            except Exception:
                pass

        # 3. Extract any {...} object
        curly_match = re.search(r'(\{[\s\S]*\})', content)
        if curly_match:
            try:
                data = json.loads(curly_match.group(1))
                return self._format_parsed_data(data)
            except Exception:
                pass

        # 4. Fallback: Parse markdown bullet points if returned as plain text
        return {
            'recommendations': content.strip(),
            'suggested_titles': [
                "Audience Deep Dive: Top Insights & Strategies",
                "What Every Creator Should Know in 2026",
                "Addressing Viewer Feedback and Next Steps",
                "Masterclass: Community-Driven Content Creation",
                "The Ultimate Practical Guide Based on Audience Demand"
            ],
            'provider': 'groq',
            'model': self.model,
        }

    def _format_parsed_data(self, data: Dict) -> Dict[str, Any]:
        # Flexible key extraction for diverse model outputs
        recommendations = (
            data.get('recommendations') or
            data.get('contentRecommendations') or
            data.get('content_recommendations') or
            data.get('suggestions') or
            data.get('insights') or
            ''
        )
        titles = (
            data.get('suggested_titles') or
            data.get('suggestedTitles') or
            data.get('youtubeTitles') or
            data.get('youtube_titles') or
            data.get('titles') or
            []
        )

        if isinstance(recommendations, list):
            formatted_recs = []
            for r in recommendations:
                if isinstance(r, dict):
                    title = r.get('title') or r.get('type') or ''
                    desc = r.get('description') or r.get('summary') or str(r)
                    formatted_recs.append(f"- **{title}:** {desc}" if title else f"- {desc}")
                else:
                    formatted_recs.append(f"- {r}")
            recommendations = "\n".join(formatted_recs)

        clean_titles = []
        if isinstance(titles, list):
            for t in titles:
                if isinstance(t, dict):
                    clean_titles.append(str(t.get('title', str(t))))
                else:
                    clean_titles.append(str(t))
        elif isinstance(titles, str):
            clean_titles = [titles]

        return {
            'recommendations': str(recommendations).strip(),
            'suggested_titles': clean_titles[:5],
            'provider': 'groq',
            'model': self.model,
        }

    def _fallback_generation(self, prompt: str, error_note: Optional[str] = None) -> Dict[str, Any]:
        """
        Generates realistic template recommendations when Groq API key is missing or offline.
        """
        note = f"\n*(Note: Generated via fallback mode. {error_note or ''})*" if error_note else ""

        recs = (
            "### Audience Content Recommendations:\n\n"
            "- **Address Core Audience Inquiries:** Viewers frequently asked clarifying questions around implementation details and step-by-step setup.\n"
            "- **Create In-Depth Follow-up Content:** Focus the next video on high-demand topics identified in comments (e.g. advanced integrations, practical project demonstrations).\n"
            "- **Optimize Pacing & Presentation:** Ensure technical terms and code snippets are enlarged and clearly visible on mobile screens.\n"
            "- **Engage Top Commenters:** Pin a comment asking viewers what specific technology stack they want to see next."
            f"{note}"
        )

        titles = [
            "Complete Deep Dive: From Fundamentals to Production",
            "The Missing Guide: What Nobody Told You About This Topic",
            "5 Common Mistakes Every Developer Makes (And How to Fix Them)",
            "Step-by-Step Tutorial: Building Full-Stack Projects in 2026",
            "Everything You Need to Know Explained Simply in 15 Minutes"
        ]

        return {
            'recommendations': recs,
            'suggested_titles': titles,
            'provider': 'heuristic_fallback',
            'model': 'none',
        }
