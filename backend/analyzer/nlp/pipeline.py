from typing import Dict, List, Any
from .preprocessor import clean_text
from .spam_classifier import get_default_spam_classifier, get_spam_explanation
from .sentiment import (
    analyze_sentiment, 
    summarize_sentiment, 
    generate_sentiment_timeline, 
    calculate_like_weighted_sentiment
)
from .topic_modeler import cluster_topics
from .request_extractor import extract_requests, extract_top_keywords
from .aspect_emotion import (
    classify_aspect, 
    classify_emotion, 
    check_needs_response, 
    draft_creator_reply,
    summarize_aspect_sentiment,
    summarize_emotions
)


def run_nlp_pipeline(comments_data: List[Dict[str, Any]], video_title: str = '') -> Dict[str, Any]:
    """
    Executes the end-to-end NLP analysis pipeline on a list of comment dictionaries.
    """
    if not comments_data:
        return {
            'total_comments': 0,
            'spam_count': 0,
            'ham_count': 0,
            'spam_ratio': 0.0,
            'annotated_comments': [],
            'sentiment_summary': summarize_sentiment([]),
            'sentiment_timeline': [],
            'aspect_sentiment': {},
            'emotion_breakdown': {},
            'weighted_compound': 0.0,
            'top_keywords': [],
            'top_requests': [],
            'topic_clusters': [],
            'needs_response_count': 0,
        }

    # Normalize input
    normalized_list = []
    for item in comments_data:
        if isinstance(item, str):
            normalized_list.append({'text': item, 'raw_item': item})
        elif isinstance(item, dict):
            normalized_list.append(item)
        else:
            normalized_list.append({'text': str(item), 'raw_item': item})

    spam_classifier = get_default_spam_classifier()
    annotated = []
    non_spam_texts = []
    all_sentiment_results = []
    non_spam_sentiment_results = []

    # 1. Spam Classification, Sentiment, Aspect, Emotion, and Reply Drafting
    for c in normalized_list:
        raw_text = c.get('text', '')
        author = c.get('author', '')
        cleaned = clean_text(raw_text)

        # Spam detection with explainability
        spam_result = spam_classifier.classify(raw_text)
        is_spam = spam_result['is_spam']
        spam_reason = get_spam_explanation(spam_result)

        # Sentiment analysis with Hinglish & Internet lexicon
        sentiment_result = analyze_sentiment(raw_text)
        all_sentiment_results.append(sentiment_result)

        # Aspect & Emotion classification
        aspect = classify_aspect(raw_text)
        emotion = classify_emotion(raw_text)
        needs_response = check_needs_response(raw_text, is_spam=is_spam)
        draft_reply = draft_creator_reply(raw_text, author=author, video_title=video_title) if needs_response else ''

        annotated_item = dict(c)
        annotated_item['cleaned_text'] = cleaned
        annotated_item['is_spam'] = is_spam
        annotated_item['spam_confidence'] = spam_result['confidence']
        annotated_item['spam_flags'] = spam_result['flags']
        annotated_item['spam_reason'] = spam_reason
        annotated_item['sentiment_label'] = sentiment_result['label']
        annotated_item['sentiment_score'] = sentiment_result['compound']
        annotated_item['language'] = sentiment_result.get('language', 'en')
        annotated_item['aspect'] = aspect
        annotated_item['emotion'] = emotion
        annotated_item['needs_response'] = needs_response
        annotated_item['draft_reply'] = draft_reply
        annotated_item['sentiment_breakdown'] = {
            'pos': sentiment_result['pos'],
            'neu': sentiment_result['neu'],
            'neg': sentiment_result['neg'],
        }
        annotated.append(annotated_item)

        if not is_spam:
            non_spam_texts.append(raw_text)
            non_spam_sentiment_results.append(sentiment_result)

    total_count = len(annotated)
    spam_count = sum(1 for a in annotated if a['is_spam'])
    ham_count = total_count - spam_count
    spam_ratio = round((spam_count / total_count), 4) if total_count > 0 else 0.0

    # 2. Sentiment Summary (based on genuine, non-spam comments)
    target_sentiments = non_spam_sentiment_results if non_spam_sentiment_results else all_sentiment_results
    sentiment_summary = summarize_sentiment(target_sentiments)
    sentiment_summary['total_raw'] = total_count
    sentiment_summary['spam_filtered'] = spam_count

    # 3. Sentiment Timeline & Engagement Weighting
    sentiment_timeline = generate_sentiment_timeline(annotated)
    weighted_compound = calculate_like_weighted_sentiment(annotated)

    # 4. Aspect Sentiment & Emotion Breakdown
    aspect_sentiment = summarize_aspect_sentiment(annotated)
    emotion_breakdown = summarize_emotions(annotated)

    # 5. Topic Modeling with Silhouette Score dynamic K selection
    topic_corpus = non_spam_texts if non_spam_texts else [c.get('text', '') for c in normalized_list]
    topic_clusters = cluster_topics(topic_corpus)

    # 6. Keyword & Request Extraction
    top_keywords = extract_top_keywords(topic_corpus, top_n=15)
    top_requests = extract_requests(topic_corpus, max_requests=10)

    needs_response_count = sum(1 for a in annotated if a.get('needs_response'))

    return {
        'total_comments': total_count,
        'spam_count': spam_count,
        'ham_count': ham_count,
        'spam_ratio': spam_ratio,
        'annotated_comments': annotated,
        'sentiment_summary': sentiment_summary,
        'sentiment_timeline': sentiment_timeline,
        'aspect_sentiment': aspect_sentiment,
        'emotion_breakdown': emotion_breakdown,
        'weighted_compound': weighted_compound,
        'top_keywords': top_keywords,
        'top_requests': top_requests,
        'topic_clusters': topic_clusters,
        'needs_response_count': needs_response_count,
    }
