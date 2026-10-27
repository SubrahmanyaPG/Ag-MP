import re
import html
from typing import List, Optional
import nltk
from nltk.corpus import stopwords

# Ensure stopwords are available
try:
    _STOPWORDS = set(stopwords.words('english'))
except LookupError:
    nltk.download('stopwords', quiet=True)
    _STOPWORDS = set(stopwords.words('english'))

# Custom domain stopwords often present in YouTube comments that add no topical meaning
DOMAIN_STOPWORDS = {
    'video', 'videos', 'channel', 'youtube', 'yt', 'watch', 'watching',
    'watched', 'like', 'likes', 'liked', 'subscribe', 'subscribed',
    'view', 'views', 'comment', 'comments', 'bro', 'dude', 'guy', 'guys',
    'sir', 'hello', 'hi', 'hey', 'please', 'pls', 'thank', 'thanks', 'thx',
    'also', 'really', 'much', 'get', 'got', 'even', 'one', 'would', 'make',
    'making', 'made', 'know', 'see', 'look', 'time', 'first'
}

CUSTOM_STOPWORDS = _STOPWORDS.union(DOMAIN_STOPWORDS)

# Regex patterns
URL_PATTERN = re.compile(
    r'(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|'
    r'www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|'
    r'https?:\/\/[^\s]+|'
    r'(?:t|wa)\.me\/[^\s]+|'
    r'bit\.ly\/[^\s]+)',
    re.IGNORECASE
)

MENTION_PATTERN = re.compile(r'@[\w.-]+')
TIMESTAMP_PATTERN = re.compile(r'\b\d{1,2}:\d{2}(?::\d{2})?\b')
REPEATED_PUNCT_PATTERN = re.compile(r'([!?.,])\1+')
REPEATED_CHAR_PATTERN = re.compile(r'(.)\1{3,}')
WHITESPACE_PATTERN = re.compile(r'\s+')


def clean_text(text: str, keep_emojis: bool = True) -> str:
    """
    Cleans raw comment text while preserving semantic cues for sentiment analysis.
    - Decodes HTML entities (&amp; -> &)
    - Removes URLs and hyperlinks
    - Removes YouTube timestamps (e.g. 03:45)
    - Normalizes user mentions (@username)
    - Normalizes excessive repeated punctuation (e.g. '!!!!!' -> '!')
    - Normalizes excessive character repetition (e.g. 'coooool' -> 'cool')
    - Collapses multiple whitespace characters into a single space
    """
    if not text or not isinstance(text, str):
        return ""

    # 1. Unescape HTML entities
    cleaned = html.unescape(text)

    # 2. Remove URLs
    cleaned = URL_PATTERN.sub('', cleaned)

    # 3. Remove user mentions
    cleaned = MENTION_PATTERN.sub('', cleaned)

    # 4. Remove timestamps
    cleaned = TIMESTAMP_PATTERN.sub('', cleaned)

    # 5. Normalize repeated characters (e.g. 'sooooo good' -> 'soo good')
    cleaned = REPEATED_CHAR_PATTERN.sub(r'\1\1', cleaned)

    # 6. Normalize repeated punctuation (e.g. 'amazing!!!!' -> 'amazing!')
    cleaned = REPEATED_PUNCT_PATTERN.sub(r'\1', cleaned)

    # 7. Optionally strip non-ASCII / emojis if keep_emojis is False
    if not keep_emojis:
        cleaned = re.sub(r'[^\x00-\x7F]+', ' ', cleaned)

    # 8. Collapse whitespace and strip
    cleaned = WHITESPACE_PATTERN.sub(' ', cleaned).strip()

    return cleaned


def tokenize_and_filter(
    text: str,
    min_length: int = 2,
    use_domain_stopwords: bool = True
) -> List[str]:
    """
    Tokenizes text and removes punctuation, numbers, and stopwords.
    Ideal for TF-IDF feature extraction, keyword analysis, and topic modeling.
    """
    cleaned = clean_text(text, keep_emojis=False).lower()
    
    # Extract purely alphabetical words
    words = re.findall(r'\b[a-zA-Z]+\b', cleaned)
    
    stop_set = CUSTOM_STOPWORDS if use_domain_stopwords else _STOPWORDS

    tokens = [
        w for w in words
        if len(w) >= min_length and w not in stop_set
    ]

    return tokens
