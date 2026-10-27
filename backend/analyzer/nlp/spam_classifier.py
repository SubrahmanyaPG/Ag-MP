import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from .preprocessor import clean_text
from .benchmark_data import BENCHMARK_COMMENTS

# Model persistence path
DEFAULT_MODEL_DIR = Path(__file__).resolve().parent / 'saved_models'
DEFAULT_MODEL_PATH = DEFAULT_MODEL_DIR / 'spam_classifier.joblib'

# Domain-specific spam heuristic patterns for YouTube comments
SPAM_HEURISTIC_PATTERNS = [
    # Crypto / WhatsApp / Telegram recovery & trading scams
    (re.compile(r'(?:whatsapp|whats\s*app|tele\s*gram|t\.me\/|wa\.me\/)', re.I), 'messaging_app_solicitation'),
    (re.compile(r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', re.I), 'phone_number_detected'),
    (re.compile(r'(?:invest|investing|trader|trading|profit|roi|crypto|btc|bitcoin|usdt|forex)\b.*\b(?:guaranteed|mrs\.|mr\.|weekly|daily|signals|pumps)', re.I), 'crypto_investment_scam'),
    (re.compile(r'(?:recover|stolen|lost)\s+(?:funds|btc|crypto|bitcoin|money)', re.I), 'fund_recovery_scam'),
    # Bot promotions & Sub4Sub
    (re.compile(r'\b(?:sub4sub|sub\s+to\s+my\s+channel|check\s+(?:out\s+)?my\s+channel|subscribe\s+to\s+me)\b', re.I), 'channel_promo_bot'),
    (re.compile(r'\b(?:free\s+(?:v-?bucks|robux|iphone|gift\s*card)|winner\s+announced|claim\s+your\s+prize)\b', re.I), 'fake_giveaway'),
    # Suspicious shortlinks & phishing
    (re.compile(r'(?:bit\.ly|tinyurl\.com|t\.co|goo\.gl|\.xyz|\.biz|\.top|\.click)\b', re.I), 'suspicious_link'),
    (re.compile(r'\b(?:hot\s+girls|lonely\s+singles|adult\s+video|cam\s+shows|leaked\s+tape)\b', re.I), 'adult_spam'),
]


class SpamClassifier:
    """
    Hybrid YouTube comment spam classifier combining:
    1. TF-IDF + Logistic Regression trained on YouTube spam datasets.
    2. High-precision heuristic pattern matcher for zero-day social media scam evasion.
    """

    def __init__(self, model_path: Optional[Path] = None):
        self.model_path = model_path or DEFAULT_MODEL_PATH
        self.pipeline: Optional[Pipeline] = None
        self._load_or_train()

    def _build_pipeline(self) -> Pipeline:
        return Pipeline([
            ('tfidf', TfidfVectorizer(
                ngram_range=(1, 2),
                max_features=5000,
                sublinear_tf=True,
                stop_words='english',
                lowercase=True
            )),
            ('clf', LogisticRegression(
                C=1.5,
                class_weight='balanced',
                max_iter=1000,
                random_state=42
            ))
        ])

    def _load_or_train(self):
        """
        Loads saved model if available; otherwise trains on benchmark data and saves.
        """
        if self.model_path.exists():
            try:
                self.pipeline = joblib.load(self.model_path)
                return
            except Exception:
                pass

        # Train on built-in benchmark dataset
        self.train_on_benchmark()

    def train(self, texts: List[str], labels: List[int]):
        """
        Trains or re-trains the model on given texts and binary labels (1=spam, 0=ham).
        """
        cleaned_texts = [clean_text(t) for t in texts]
        self.pipeline = self._build_pipeline()
        self.pipeline.fit(cleaned_texts, labels)

        # Save to disk
        DEFAULT_MODEL_DIR.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.pipeline, self.model_path)

    def train_on_benchmark(self):
        """
        Trains on the embedded benchmark comments dataset.
        """
        texts = [c['text'] for c in BENCHMARK_COMMENTS]
        labels = [c['is_spam'] for c in BENCHMARK_COMMENTS]
        self.train(texts, labels)

    def check_heuristics(self, raw_text: str) -> List[str]:
        """
        Checks for explicit YouTube spam patterns.
        """
        flags = []
        for pattern, flag_name in SPAM_HEURISTIC_PATTERNS:
            if pattern.search(raw_text):
                flags.append(flag_name)
        return flags

    def classify(self, text: str) -> Dict[str, Any]:
        """
        Classifies a single comment as spam or ham.

        Returns:
            {
                'is_spam': bool,
                'confidence': float,  # Probability of spam (0.0 to 1.0)
                'flags': List[str],    # Triggered heuristics or 'ml_model'
                'decision_method': str # 'heuristic' or 'machine_learning'
            }
        """
        if not text or not text.strip():
            return {
                'is_spam': False,
                'confidence': 0.0,
                'flags': [],
                'decision_method': 'empty'
            }

        # 1. First check heuristics
        heuristic_flags = self.check_heuristics(text)
        if len(heuristic_flags) >= 1:
            # If explicit spam signals like WhatsApp numbers, adult links, or crypto trading scams are found
            confidence = min(0.99, 0.75 + 0.12 * len(heuristic_flags))
            return {
                'is_spam': True,
                'confidence': round(confidence, 4),
                'flags': heuristic_flags,
                'decision_method': 'heuristic'
            }

        # 2. Machine Learning pipeline prediction
        cleaned = clean_text(text)
        if self.pipeline is None:
            self._load_or_train()

        probas = self.pipeline.predict_proba([cleaned])[0]
        spam_prob = float(probas[1])

        # Classification threshold
        is_spam = spam_prob >= 0.50

        flags = ['ml_model_spam'] if is_spam else []

        return {
            'is_spam': is_spam,
            'confidence': round(spam_prob, 4),
            'flags': flags,
            'decision_method': 'machine_learning'
        }

    def batch_classify(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Batch classification of comments.
        """
        return [self.classify(t) for t in texts]


def get_spam_explanation(classification_result: Dict[str, Any]) -> str:
    """
    Returns a human-readable explanation of why a comment was categorized as spam.
    Provides transparency and explainable AI for moderators and evaluators.
    """
    if not classification_result.get('is_spam'):
        return 'Clean'

    flags = classification_result.get('flags', [])
    method = classification_result.get('decision_method', '')

    reason_map = {
        'messaging_app_solicitation': 'WhatsApp/Telegram Solicitation',
        'phone_number_detected': 'Unsolicited Phone Number Dropped',
        'crypto_investment_scam': 'Crypto / Forex Trading Scam',
        'fund_recovery_scam': 'Fake Crypto Recovery Scam',
        'channel_promo_bot': 'Sub4Sub / Self-Promotion Bot',
        'fake_giveaway': 'Deceptive Giveaway / Prize Bait',
        'suspicious_link': 'Suspicious Shortlink / Phishing',
        'adult_spam': 'Explicit Link / Adult Spam',
        'ml_model_spam': f"High ML Spam Probability ({int(classification_result.get('confidence', 0.5) * 100)}%)"
    }

    explanations = [reason_map.get(f, f.replace('_', ' ').title()) for f in flags]
    return "; ".join(explanations) if explanations else f"Flagged by {method}"


# Cached global classifier
_spam_classifier: Optional[SpamClassifier] = None


def get_default_spam_classifier() -> SpamClassifier:
    """
    Returns singleton instance of SpamClassifier.
    """
    global _spam_classifier
    if _spam_classifier is None:
        _spam_classifier = SpamClassifier()
    return _spam_classifier
