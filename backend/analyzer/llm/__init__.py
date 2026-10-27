"""
LLM Module for generating content recommendations and suggested video titles
from aggregated NLP sentiment, keyword, topic, and request data.
"""

from .prompts import build_analysis_prompt, SYSTEM_PROMPT
from .service import generate_recommendations_and_titles

__all__ = [
    'build_analysis_prompt',
    'SYSTEM_PROMPT',
    'generate_recommendations_and_titles',
]
