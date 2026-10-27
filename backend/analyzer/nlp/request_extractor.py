import re
from collections import Counter
from typing import Dict, List, Any, Tuple
from .preprocessor import clean_text, tokenize_and_filter

# Request and feedback indicator patterns
REQUEST_PATTERNS = [
    # Explicit tutorial / video requests
    (re.compile(r'(?:could|can)\s+you\s+(?:please\s+)?(?:make|do|create|upload|cover|show|explain)\s+(.+?)(?:[?.!]|$)', re.I), 'video_request'),
    (re.compile(r'please\s+(?:make|do|create|cover|show|explain|upload)\s+(.+?)(?:[?.!]|$)', re.I), 'video_request'),
    (re.compile(r'(?:would|will)\s+love\s+to\s+see\s+(.+?)(?:[?.!]|$)', re.I), 'video_request'),
    (re.compile(r'next\s+(?:video|tutorial|time|part)\s+(?:should|could|please)\s+(.+?)(?:[?.!]|$)', re.I), 'next_episode_request'),
    (re.compile(r'(?:waiting\s+for|when\s+is)\s+(?:part\s*\d+|the\s+next\s+part)(.+?)(?:[?.!]|$)', re.I), 'next_part_request'),
    (re.compile(r'tutorial\s+(?:on|for|about)\s+(.+?)(?:[?.!]|$)', re.I), 'tutorial_request'),
    (re.compile(r'how\s+to\s+(?:use|integrate|deploy|connect|install|implement|run)\s+(.+?)(?:[?.!]|$)', re.I), 'how_to_question'),
    (re.compile(r'can\s+you\s+(?:share|provide|link)\s+(?:the\s+)?(?:github|repo|code|slides|notes|pdf)(.+?)(?:[?.!]|$)', re.I), 'resource_request'),
    # Constructive suggestions & technical feedback
    (re.compile(r'(?:i\s+suggest|suggestion:?|suggest\s+you)\s+(.+?)(?:[?.!]|$)', re.I), 'suggestion'),
    (re.compile(r'(?:audio|volume|sound)\s+is\s+(?:too\s+)?(?:low|loud|bad|terrible|quiet)(.+?)(?:[?.!]|$)', re.I), 'audio_feedback'),
    (re.compile(r'(?:font\s+size|terminal|text)\s+is\s+(?:too\s+)?(?:small|unreadable|tiny|hard\s+to\s+read)(.+?)(?:[?.!]|$)', re.I), 'visual_feedback'),
    (re.compile(r'(?:please\s+)?(?:zoom\s+in|increase\s+font|add\s+subtitles)(.+?)(?:[?.!]|$)', re.I), 'accessibility_feedback'),
]


def _clean_request_phrase(phrase: str) -> str:
    """
    Cleans extracted request fragment, trimming filler words and punctuation.
    """
    phrase = re.sub(r'^[,\s:;-]+', '', phrase)
    phrase = re.sub(r'[,\s:;-]+$', '', phrase)
    phrase = re.sub(r'\s+', ' ', phrase).strip()
    return phrase


def extract_requests(
    comments: List[str],
    max_requests: int = 10
) -> List[Dict[str, Any]]:
    """
    Extracts audience requests, content suggestions, and actionable feedback
    from a collection of comments.

    Returns:
        List of structured requests:
        [
            {
                'request': str,         # Normalized request description
                'category': str,        # 'video_request', 'resource_request', etc.
                'count': int,           # Frequency / popularity
                'sample_comment': str   # Real comment showcasing the request
            }, ...
        ]
    """
    extracted_items: List[Dict[str, Any]] = []
    seen_phrases: Counter = Counter()
    phrase_to_sample: Dict[str, Tuple[str, str]] = {}

    for comment in comments:
        cleaned_comment = clean_text(comment, keep_emojis=False)

        for pattern, category in REQUEST_PATTERNS:
            match = pattern.search(cleaned_comment)
            if match:
                captured = match.group(0).strip()
                # Extract the core requested subject if available
                subject = match.group(1).strip() if match.groups() else captured
                subject = _clean_request_phrase(subject)

                if len(subject) < 4 or len(subject) > 120:
                    continue

                # Canonical key (lowercased)
                canonical = re.sub(r'[^\w\s]', '', subject.lower()).strip()
                if not canonical:
                    continue

                seen_phrases[canonical] += 1
                if canonical not in phrase_to_sample:
                    phrase_to_sample[canonical] = (subject, category, comment.strip())
                break

    for canonical, count in seen_phrases.most_common(max_requests):
        display_phrase, category, sample_comment = phrase_to_sample[canonical]
        extracted_items.append({
            'request': display_phrase,
            'category': category,
            'count': count,
            'sample_comment': sample_comment
        })

    return extracted_items


def extract_top_keywords(
    comments: List[str],
    top_n: int = 15,
    include_bigrams: bool = True
) -> List[Dict[str, Any]]:
    """
    Extracts top unigram and bigram keywords across all comments,
    excluding English and YouTube-specific stopwords.
    """
    unigram_counter: Counter = Counter()
    bigram_counter: Counter = Counter()

    for comment in comments:
        tokens = tokenize_and_filter(comment, min_length=3, use_domain_stopwords=True)
        unigram_counter.update(tokens)

        if include_bigrams and len(tokens) >= 2:
            bigrams = [f"{tokens[i]} {tokens[i+1]}" for i in range(len(tokens) - 1)]
            bigram_counter.update(bigrams)

    # Combine unigrams and informative bigrams
    results: List[Dict[str, Any]] = []
    seen_terms = set()

    # Prioritize popular bigrams (they convey more context)
    for bigram, count in bigram_counter.most_common(top_n // 2):
        if count >= 2:
            results.append({'keyword': bigram, 'count': count, 'type': 'bigram'})
            seen_terms.update(bigram.split())

    # Fill remaining slots with top unigrams
    for unigram, count in unigram_counter.most_common(top_n * 2):
        if unigram not in seen_terms and count >= 2:
            results.append({'keyword': unigram, 'count': count, 'type': 'unigram'})
            seen_terms.add(unigram)
            if len(results) >= top_n:
                break

    # If too few keywords with count >= 2, include single-occurrence top words
    if len(results) < 5:
        for unigram, count in unigram_counter.most_common(top_n):
            if unigram not in seen_terms:
                results.append({'keyword': unigram, 'count': count, 'type': 'unigram'})
                seen_terms.add(unigram)
                if len(results) >= top_n:
                    break

    results.sort(key=lambda x: x['count'], reverse=True)
    return results[:top_n]
