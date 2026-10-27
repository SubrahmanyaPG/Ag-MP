import re
from typing import Dict, List, Any, Optional

# Keywords and patterns for aspect classification
ASPECT_PATTERNS = {
    'audio': re.compile(r'\b(?:audio|sound|voice|mic|microphone|volume|bgm|music|loud|quiet|hear|noise|buzzing|echo)\b', re.I),
    'visuals': re.compile(r'\b(?:video|visual|visuals|screen|font|thumbnail|4k|1080p|resolution|camera|quality|editing|graphics|animation|zoom|blur)\b', re.I),
    'content': re.compile(r'\b(?:content|concept|explanation|explain|example|code|github|topic|theory|formula|math|tutorial|logic|detail|depth|clear|understand)\b', re.I),
    'pacing': re.compile(r'\b(?:pace|pacing|speed|fast|slow|short|length|long|minute|duration|boring|engaging|energy|drag|stretched)\b', re.I),
}

# Emotion lexicons
EMOTION_PATTERNS = {
    'joy': re.compile(r'\b(?:love|amazing|awesome|great|superb|best|brilliant|masterclass|fire|banger|mast|zabardast|badhiya|shandar|op|w|goat|thank|thanks|grateful|appreciate|happy)\b|❤️|🔥|👏|🙌|😍|🎉', re.I),
    'inquiry': re.compile(r'\b(?:why|how|what|when|where|who|could|can|would|should|question|doubt|part\s*2|tutorial|source\s*code|repo|link|github|help|batao|kahan|kab)\b|\?', re.I),
    'frustration': re.compile(r'\b(?:hate|terrible|horrible|worst|bad|awful|disappointed|waste|useless|confusing|unclear|bug|error|broken|fail|failed|scam|bakwas|bekar|ghatiya)\b|😡|😠|👎|🤮|💩', re.I),
    'surprise': re.compile(r'\b(?:wow|unbelievable|shocked|shocking|crazy|insane|mind\s*blown|unexpected|omg|gosh)\b|😱|😲|🤯|😮', re.I),
}

# Detection for comments needing a creator response
QUESTION_PATTERNS = [
    re.compile(r'\b(?:how\s+(?:to|do|can|did)|where\s+(?:is|can|to)|what\s+(?:is|about)|why\s+(?:is|did|does)|can\s+you|could\s+you|is\s+there|any\s+(?:way|chance|update))\b', re.I),
    re.compile(r'\b(?:please\s+explain|need\s+help|having\s+(?:an?\s+)?(?:issue|error|bug|problem)|stuck\s+at)\b', re.I),
    re.compile(r'\b(?:part\s*\d+|github\s+link|source\s+code|repo\s+link|pdf\s+notes)\b', re.I),
    re.compile(r'\?+', re.I),
]


def classify_aspect(text: str) -> str:
    """
    Classifies comment into a feedback aspect:
    'content', 'audio', 'visuals', 'pacing', or 'general'.
    """
    for aspect, pattern in ASPECT_PATTERNS.items():
        if pattern.search(text):
            return aspect
    return 'general'


def classify_emotion(text: str) -> str:
    """
    Classifies primary emotional tone of the comment:
    'joy', 'inquiry', 'frustration', 'surprise', or 'neutral'.
    """
    for emotion, pattern in EMOTION_PATTERNS.items():
        if pattern.search(text):
            return emotion
    return 'neutral'


def check_needs_response(text: str, is_spam: bool = False) -> bool:
    """
    Determines whether a comment is a genuine question or tutorial request
    that would benefit from a creator reply.
    """
    if is_spam:
        return False
    
    text_clean = text.strip()
    if len(text_clean) < 8:
        return False

    for pattern in QUESTION_PATTERNS:
        if pattern.search(text_clean):
            return True
    return False


def draft_creator_reply(comment_text: str, author: str = '', video_title: str = '') -> str:
    """
    Generates a polite, context-aware creator reply draft for viewer questions or feedback.
    """
    salutation = f"Hey @{author}, " if author and author.lower() != 'anonymous' else "Hey! "
    text_lower = comment_text.lower()

    if 'part 2' in text_lower or 'next part' in text_lower or 'next video' in text_lower:
        return f"{salutation}Thanks for watching! Part 2 is currently in production and will be dropping very soon. Make sure notifications are turned on so you don't miss it!"
    
    if any(k in text_lower for k in ['github', 'repo', 'code', 'source code', 'link', 'notes']):
        return f"{salutation}Glad you found the video helpful! You can find the full GitHub repository and resource links pinned in the video description below. Let me know if you run into any setup issues!"
    
    if any(k in text_lower for k in ['error', 'bug', 'issue', 'not working', 'stuck', 'help']):
        return f"{salutation}Thanks for reaching out! Could you share the exact error traceback or the step where it failed? Happy to help you troubleshoot it!"
    
    if 'audio' in text_lower or 'sound' in text_lower or 'volume' in text_lower:
        return f"{salutation}Thanks so much for the audio feedback! I've noted down the volume levels and will adjust the sound mastering for the upcoming episodes."
    
    if '?' in comment_text or 'how' in text_lower or 'why' in text_lower:
        return f"{salutation}Great question! I'm planning to cover this exact edge-case in an upcoming deep-dive follow-up video. Appreciate you bringing it up!"
    
    return f"{salutation}Thank you so much for the feedback and for supporting the channel! Really means a lot."


def summarize_aspect_sentiment(comments: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Computes sentiment distribution and comment counts across each aspect.
    """
    aspects = {'content': [], 'audio': [], 'visuals': [], 'pacing': []}
    
    for c in comments:
        asp = c.get('aspect', 'general')
        if asp in aspects:
            aspects[asp].append(c.get('sentiment_score', 0.0))

    summary = {}
    for asp, scores in aspects.items():
        count = len(scores)
        avg_score = round(sum(scores) / count, 3) if count > 0 else 0.0
        summary[asp] = {
            'count': count,
            'average_score': avg_score,
            'sentiment': 'positive' if avg_score >= 0.05 else 'negative' if avg_score <= -0.05 else 'neutral'
        }
    return summary


def summarize_emotions(comments: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Computes breakdown percentages across emotions.
    """
    total = len(comments)
    if total == 0:
        return {'joy': 0, 'inquiry': 0, 'frustration': 0, 'surprise': 0, 'neutral': 0}

    counts = {'joy': 0, 'inquiry': 0, 'frustration': 0, 'surprise': 0, 'neutral': 0}
    for c in comments:
        emo = c.get('emotion', 'neutral')
        if emo in counts:
            counts[emo] += 1
        else:
            counts['neutral'] += 1

    return {
        k: {
            'count': v,
            'percentage': round((v / total) * 100, 1)
        }
        for k, v in counts.items()
    }
