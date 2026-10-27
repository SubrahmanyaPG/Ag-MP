from typing import Dict, List, Any, Optional
from .prompts import SYSTEM_PROMPT, build_analysis_prompt
from .client import LLMClient


def generate_recommendations_and_titles(
    video_title: str,
    channel: str,
    sentiment_summary: Dict[str, Any],
    top_keywords: List[Dict[str, Any]],
    top_requests: List[Dict[str, Any]],
    topic_clusters: List[Dict[str, Any]],
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    High-level LLM analysis function.
    Takes strictly aggregated sentiment, keyword, topic, and request metrics
    (zero raw comments to keep token usage minimal), prompts Groq LLaMA,
    and returns content recommendations + 5 title suggestions.
    """
    user_prompt = build_analysis_prompt(
        video_title=video_title,
        channel=channel,
        sentiment_summary=sentiment_summary,
        top_keywords=top_keywords,
        top_requests=top_requests,
        topic_clusters=topic_clusters
    )

    client = LLMClient(api_key=api_key)
    return client.generate(system_prompt=SYSTEM_PROMPT, user_prompt=user_prompt)
