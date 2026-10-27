"""
Prompts configuration for the LLM Content Recommendation & Title Generator.
Keep all prompt wording, templates, and persona definitions here so you can
iterate on tone and formatting without touching the core analysis pipeline.
"""

from typing import Dict, List, Any


SYSTEM_PROMPT = """You are an expert YouTube Content Strategist, Audience Research Analyst, and Creative Producer.
Your job is to analyze summarized audience feedback, sentiment metrics, and topic clusters for a YouTube video, then generate:
1. High-impact, actionable content recommendations for the creator's upcoming videos.
2. 5 high-CTR, engaging YouTube video title suggestions addressing unmet audience demand.

Rules:
- Base recommendations strictly on the aggregated audience sentiment, topics, and requests provided.
- Do not mention raw statistics unless relevant; focus on strategic takeaways.
- Always output clean JSON matching the requested schema.
"""


def build_analysis_prompt(
    video_title: str,
    channel: str,
    sentiment_summary: Dict[str, Any],
    top_keywords: List[Dict[str, Any]],
    top_requests: List[Dict[str, Any]],
    topic_clusters: List[Dict[str, Any]]
) -> str:
    """
    Constructs the user prompt containing aggregated data (NO raw comments)
    to strictly minimize token consumption while maximizing insight density.
    """
    # 1. Format Sentiment Metrics
    pos_pct = sentiment_summary.get('positive_percentage', 0.0)
    neu_pct = sentiment_summary.get('neutral_percentage', 0.0)
    neg_pct = sentiment_summary.get('negative_percentage', 0.0)
    avg_compound = sentiment_summary.get('average_compound', 0.0)
    total_comments = sentiment_summary.get('total', 0)
    spam_filtered = sentiment_summary.get('spam_filtered', 0)

    sentiment_text = (
        f"- Total Audience Comments Analyzed: {total_comments} (Spam Filtered: {spam_filtered})\n"
        f"- Sentiment Breakdown: {pos_pct}% Positive, {neu_pct}% Neutral, {neg_pct}% Negative\n"
        f"- Overall Sentiment Intensity (Compound Score): {avg_compound:+.2f} (Scale: -1.0 to +1.0)"
    )

    # 2. Format Topic Clusters
    topics_lines = []
    if topic_clusters:
        for c in topic_clusters:
            name = c.get('topic_name', 'Topic')
            pct = c.get('percentage', 0)
            kw = ", ".join(c.get('keywords', [])[:4])
            topics_lines.append(f"  * {name} ({pct}% of discussion): keywords [{kw}]")
    else:
        topics_lines.append("  * General audience reactions and discussion")
    topics_text = "\n".join(topics_lines)

    # 3. Format Top Keywords
    kw_items = [f"{k['keyword']} ({k['count']})" for k in top_keywords[:8]]
    keywords_text = ", ".join(kw_items) if kw_items else "None extracted"

    # 4. Format Audience Requests & Feedback
    req_lines = []
    if top_requests:
        for r in top_requests[:6]:
            cat = r.get('category', 'request')
            req_text = r.get('request', '')
            count = r.get('count', 1)
            req_lines.append(f"  * [{cat}] \"{req_text}\" (Mentioned {count} times)")
    else:
        req_lines.append("  * No specific tutorial/feature requests explicitly detected.")
    requests_text = "\n".join(req_lines)

    # Full prompt construction
    prompt = f"""VIDEO INFORMATION:
- Video Title: "{video_title}"
- Channel: "{channel or 'Unknown Channel'}"

AUDIENCE SENTIMENT SUMMARY:
{sentiment_text}

TOPIC CLUSTERS DISCOVERED:
{topics_text}

TOP AUDIENCE KEYWORDS:
{keywords_text}

EXTRACTED AUDIENCE REQUESTS & CONSTRUCTIVE FEEDBACK:
{requests_text}

TASK:
Based on the audience data above, generate:
1. Actionable Content Recommendations (3-5 bullet points covering: what resonated most with viewers, what constructive feedback or complaints should be addressed in future uploads, and strategic opportunities for follow-up content).
2. 5 Suggested Video Titles (high-CTR, authentic, and directly answering what viewers requested or showed enthusiasm for).

OUTPUT FORMAT:
Return ONLY a valid JSON object with the following structure:
{{
  "recommendations": "Markdown formatted string with bullet points detailing the strategic recommendations.",
  "suggested_titles": [
    "Title Suggestion 1",
    "Title Suggestion 2",
    "Title Suggestion 3",
    "Title Suggestion 4",
    "Title Suggestion 5"
  ]
}}
"""
    return prompt.strip()
