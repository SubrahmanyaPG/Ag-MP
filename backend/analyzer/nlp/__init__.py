# backend/analyzer/nlp/__init__.py
"""
NLP Module for Automated Audience Sentiment and Feedback Analysis.
Contains text preprocessing, sentiment analysis, spam classification,
topic clustering, and request/feedback extraction.
"""

from .preprocessor import clean_text, tokenize_and_filter
from .sentiment import analyze_sentiment, batch_analyze_sentiment, summarize_sentiment
from .spam_classifier import SpamClassifier, get_default_spam_classifier
from .topic_modeler import cluster_topics
from .request_extractor import extract_requests, extract_top_keywords
from .pipeline import run_nlp_pipeline

__all__ = [
    'clean_text',
    'tokenize_and_filter',
    'analyze_sentiment',
    'batch_analyze_sentiment',
    'summarize_sentiment',
    'SpamClassifier',
    'get_default_spam_classifier',
    'cluster_topics',
    'extract_requests',
    'extract_top_keywords',
    'run_nlp_pipeline',
]
