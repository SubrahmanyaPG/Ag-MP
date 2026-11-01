import re
import json
import logging
from typing import Dict, List, Any, Optional
from .prompts import SYSTEM_PROMPT, build_analysis_prompt
from .client import LLMClient

logger = logging.getLogger(__name__)


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


def generate_comparison_insights(comparison_stats: Dict[str, Any], api_key: Optional[str] = None) -> List[str]:
    """
    Generates 3 executive bullet points comparing audience reception between two videos.
    Passes strictly aggregated metrics (never raw comments) to Groq.
    """
    v_a = comparison_stats.get('video_a', {})
    v_b = comparison_stats.get('video_b', {})
    deltas = comparison_stats.get('deltas', {})
    shared_kw = comparison_stats.get('shared_keywords', [])
    jaccard = comparison_stats.get('jaccard_similarity', 0.0)

    system_prompt = (
        "You are an expert YouTube audience analytics consultant. "
        "Analyze the comparative feedback metrics of two videos and provide exactly 3 concise, high-value executive takeaway bullet points. "
        "Do not repeat raw numbers verbatim; interpret what they mean for creator retention, content pacing, and audience enthusiasm. "
        "Return your response strictly as a JSON array of 3 strings: [\"takeaway 1\", \"takeaway 2\", \"takeaway 3\"]."
    )

    user_prompt = f"""
Video A:
- Title: "{v_a.get('video', {}).get('title', 'Video A')}"
- Comments: {v_a.get('comments_analyzed')} | Spam Rate: {v_a.get('spam_rate')}%
- Sentiment: {v_a.get('positive_percentage')}% Pos, {v_a.get('neutral_percentage')}% Neu, {v_a.get('negative_percentage')}% Neg
- Avg Polarity: {v_a.get('average_compound')} | Like-Weighted: {v_a.get('weighted_compound')}
- Top Keywords: {', '.join(v_a.get('top_keywords', []))}

Video B:
- Title: "{v_b.get('video', {}).get('title', 'Video B')}"
- Comments: {v_b.get('comments_analyzed')} | Spam Rate: {v_b.get('spam_rate')}%
- Sentiment: {v_b.get('positive_percentage')}% Pos, {v_b.get('neutral_percentage')}% Neu, {v_b.get('negative_percentage')}% Neg
- Avg Polarity: {v_b.get('average_compound')} | Like-Weighted: {v_b.get('weighted_compound')}
- Top Keywords: {', '.join(v_b.get('top_keywords', []))}

Deltas (A minus B):
- Sentiment Positivity Delta: {deltas.get('positive_percentage')}%
- Like-Weighted Sentiment Delta: {deltas.get('weighted_compound')}
- Keyword Overlap Jaccard Score: {jaccard}
- Shared Keywords: {', '.join(shared_kw) if shared_kw else 'None'}
"""
    client = LLMClient(api_key=api_key)
    if not client.is_configured():
        return _heuristic_comparison_takeaways(comparison_stats)

    try:
        from groq import Groq
        groq_client = Groq(api_key=client.groq_api_key)
        for cand in client.models_to_try:
            try:
                res = groq_client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    model=cand,
                    temperature=0.6,
                    max_tokens=400
                )
                text = res.choices[0].message.content.strip()
                match = re.search(r'\[.*\]', text, re.DOTALL)
                if match:
                    parsed = json.loads(match.group(0))
                    if isinstance(parsed, list) and len(parsed) >= 2:
                        return [str(x).strip() for x in parsed[:3]]
                lines = [l.strip().lstrip('•-123. ') for l in text.split('\n') if l.strip() and not l.startswith('```')]
                if len(lines) >= 2:
                    return lines[:3]
            except Exception:
                continue
    except Exception:
        pass

    return _heuristic_comparison_takeaways(comparison_stats)


def _heuristic_comparison_takeaways(stats: Dict[str, Any]) -> List[str]:
    v_a = stats.get('video_a', {})
    v_b = stats.get('video_b', {})
    deltas = stats.get('deltas', {})
    jaccard = stats.get('jaccard_similarity', 0.0)

    title_a = v_a.get('video', {}).get('title', 'Video A')
    title_b = v_b.get('video', {}).get('title', 'Video B')
    pos_delta = deltas.get('positive_percentage', 0.0)
    w_delta = deltas.get('weighted_compound', 0.0)

    takeaways = []
    if pos_delta > 0:
        takeaways.append(
            f"'{title_a}' achieved {pos_delta:.1f}% higher audience positivity compared to '{title_b}', reflecting stronger thematic resonance with viewers."
        )
    elif pos_delta < 0:
        takeaways.append(
            f"'{title_b}' held a {abs(pos_delta):.1f}% positive sentiment advantage over '{title_a}', showing fewer critical or frustrated viewer reactions."
        )
    else:
        takeaways.append(
            "Both videos maintained nearly identical baseline positivity ratings across their comment sections."
        )

    if w_delta > 0:
        takeaways.append(
            f"Engagement-weighted polarity favors '{title_a}' (+{w_delta:.2f}), indicating that top-liked audience comments were significantly more enthusiastic."
        )
    else:
        takeaways.append(
            f"Highly liked audience comments gave '{title_b}' stronger engagement endorsement (+{abs(w_delta):.2f}) relative to '{title_a}'."
        )

    takeaways.append(
        f"Topic overlap stands at a Jaccard index of {jaccard:.2f}, indicating " +
        ("broad thematic alignment with a shared audience core." if jaccard > 0.25 else "distinct viewer bases focusing on different aspects.")
    )
    return takeaways
