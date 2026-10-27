from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import defaultdict
import math
import re
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from .preprocessor import clean_text

# Global cached analyzer
_analyzer = None

# Custom Hinglish & Modern YouTube Slang Lexicon Extensions
HINGLISH_LEXICON_UPDATES = {
    # Hinglish Positive
    'zabardast': 3.2,
    'badhiya': 2.6,
    'shandar': 2.9,
    'mast': 2.7,
    'lajawab': 3.0,
    'bohot accha': 2.8,
    'bhai maza': 2.5,
    'maza': 2.4,
    'banger': 3.2,
    'op': 2.8,
    'goat': 3.2,
    'fire': 2.7,
    'clutch': 2.5,
    'w': 2.0,
    # Hinglish Negative
    'bakwas': -3.2,
    'bekar': -2.8,
    'ghatiya': -3.4,
    'chutiya': -3.6,
    'samajh nahi': -2.2,
    'time waste': -2.8,
    'scam': -3.2,
    'fake': -2.8,
    'l': -2.0,
    'mid': -1.5,
    'cap': -1.8,
}

HINGLISH_KEYWORDS = re.compile(r'\b(?:bhai|yaar|kya|hai|nahi|accha|bohot|karo|batao|kahan|kab|sab|apna|kaise|hoga|aur|koi|bhi|wala|wali|yeh|woh|mast|bakwas|bekar|zabardast|badhiya)\b', re.I)
DEVANAGARI_PATTERN = re.compile(r'[\u0900-\u097F]')


def detect_language(text: str) -> str:
    """
    Detects language/dialect: 'hi' (Devanagari Hindi), 'hinglish', or 'en'.
    """
    if DEVANAGARI_PATTERN.search(text):
        return 'hi'
    if HINGLISH_KEYWORDS.search(text):
        return 'hinglish'
    return 'en'


def get_sentiment_analyzer() -> SentimentIntensityAnalyzer:
    """
    Returns a singleton SentimentIntensityAnalyzer instance with injected Hinglish & Internet lexicon.
    """
    global _analyzer
    if _analyzer is None:
        try:
            _analyzer = SentimentIntensityAnalyzer()
        except LookupError:
            nltk.download('vader_lexicon', quiet=True)
            _analyzer = SentimentIntensityAnalyzer()
        # Enrich lexicon with domain and Hinglish terminology
        _analyzer.lexicon.update(HINGLISH_LEXICON_UPDATES)
    return _analyzer


def analyze_sentiment(
    text: str,
    pos_threshold: float = 0.05,
    neg_threshold: float = -0.05
) -> Dict[str, Any]:
    """
    Analyzes sentiment of a comment using VADER with multilingual Hinglish support.
    """
    if not text or not text.strip():
        return {
            'compound': 0.0,
            'pos': 0.0,
            'neu': 1.0,
            'neg': 0.0,
            'label': 'neutral',
            'language': 'en'
        }

    lang = detect_language(text)

    # Lightly clean text while preserving emojis and punctuation
    cleaned = clean_text(text, keep_emojis=True)
    if not cleaned:
        return {
            'compound': 0.0,
            'pos': 0.0,
            'neu': 1.0,
            'neg': 0.0,
            'label': 'neutral',
            'language': lang
        }

    sia = get_sentiment_analyzer()
    scores = sia.polarity_scores(cleaned)
    compound = scores['compound']

    if compound >= pos_threshold:
        label = 'positive'
    elif compound <= neg_threshold:
        label = 'negative'
    else:
        label = 'neutral'

    return {
        'compound': round(compound, 4),
        'pos': round(scores['pos'], 4),
        'neu': round(scores['neu'], 4),
        'neg': round(scores['neg'], 4),
        'label': label,
        'language': lang
    }


def batch_analyze_sentiment(texts: List[str]) -> List[Dict[str, Any]]:
    return [analyze_sentiment(t) for t in texts]


def calculate_like_weighted_sentiment(comments: List[Dict[str, Any]]) -> float:
    """
    Calculates engagement-weighted compound polarity score:
    Comments with high likes (e.g. 500 likes) have mathematically higher influence
    than comments with 0 likes.
    """
    if not comments:
        return 0.0

    total_weight = 0.0
    weighted_sum = 0.0

    for c in comments:
        score = c.get('sentiment_score', 0.0)
        likes = c.get('like_count', 0)
        # Logarithmic dampening prevents viral outliers from drowning out all other comments
        weight = math.log1p(max(0, likes)) + 1.0
        weighted_sum += score * weight
        total_weight += weight

    return round(weighted_sum / total_weight, 4) if total_weight > 0 else 0.0


def generate_sentiment_timeline(comments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Aggregates sentiment by comment publication date (daily/weekly).
    Returns chronological points for Recharts line chart:
    [
      { 'date': '2026-10-21', 'avg_sentiment': 0.52, 'volume': 15, 'pos_pct': 73.3, 'neg_pct': 6.7 },
      ...
    ]
    """
    grouped = defaultdict(list)

    for c in comments:
        pub = c.get('published_at')
        if not pub:
            continue

        if isinstance(pub, str):
            date_key = pub[:10]
        elif isinstance(pub, datetime):
            date_key = pub.strftime('%Y-%m-%d')
        else:
            continue

        grouped[date_key].append(c)

    if not grouped:
        return []

    sorted_dates = sorted(grouped.keys())
    timeline_points = []

    for d in sorted_dates:
        items = grouped[d]
        vol = len(items)
        scores = [i.get('sentiment_score', 0.0) for i in items]
        pos_count = sum(1 for i in items if i.get('sentiment_label') == 'positive')
        neg_count = sum(1 for i in items if i.get('sentiment_label') == 'negative')

        timeline_points.append({
            'date': d,
            'avg_sentiment': round(sum(scores) / vol, 3),
            'volume': vol,
            'pos_pct': round((pos_count / vol) * 100, 1),
            'neg_pct': round((neg_count / vol) * 100, 1)
        })

    return timeline_points


def summarize_sentiment(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregates sentiment results into overall summary metrics.
    """
    total = len(results)
    if total == 0:
        return {
            'total': 0,
            'positive_count': 0,
            'neutral_count': 0,
            'negative_count': 0,
            'positive_percentage': 0.0,
            'neutral_percentage': 0.0,
            'negative_percentage': 0.0,
            'average_compound': 0.0,
        }

    pos_count = sum(1 for r in results if r['label'] == 'positive')
    neu_count = sum(1 for r in results if r['label'] == 'neutral')
    neg_count = sum(1 for r in results if r['label'] == 'negative')
    avg_compound = sum(r['compound'] for r in results) / total

    return {
        'total': total,
        'positive_count': pos_count,
        'neutral_count': neu_count,
        'negative_count': neg_count,
        'positive_percentage': round((pos_count / total) * 100, 2),
        'neutral_percentage': round((neu_count / total) * 100, 2),
        'negative_percentage': round((neg_count / total) * 100, 2),
        'average_compound': round(avg_compound, 4),
    }
