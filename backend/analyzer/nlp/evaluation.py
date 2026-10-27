from typing import Dict, List, Optional, Any
from sklearn.metrics import (
    precision_recall_fscore_support,
    accuracy_score,
    confusion_matrix,
    classification_report
)
from .benchmark_data import BENCHMARK_COMMENTS
from .spam_classifier import get_default_spam_classifier
from .sentiment import analyze_sentiment


def evaluate_spam_classifier(
    classifier=None,
    dataset: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Evaluates the SpamClassifier against a labeled dataset.
    Reports Precision, Recall, F1-Score, Accuracy, and Confusion Matrix.
    """
    if classifier is None:
        classifier = get_default_spam_classifier()

    data = dataset or BENCHMARK_COMMENTS
    y_true = [item['is_spam'] for item in data]
    texts = [item['text'] for item in data]

    predictions = [classifier.classify(t) for t in texts]
    y_pred = [1 if p['is_spam'] else 0 for p in predictions]

    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average='binary', pos_label=1, zero_division=0
    )
    accuracy = accuracy_score(y_true, y_pred)
    cm = confusion_matrix(y_true, y_pred)

    tn, fp, fn, tp = cm.ravel() if cm.shape == (2, 2) else (0, 0, 0, 0)

    detailed_report = classification_report(
        y_true, y_pred,
        target_names=['Legitimate (Ham)', 'Spam'],
        output_dict=True,
        zero_division=0
    )

    return {
        'total_samples': len(data),
        'spam_samples': sum(y_true),
        'ham_samples': len(y_true) - sum(y_true),
        'accuracy': round(accuracy, 4),
        'precision': round(precision, 4),
        'recall': round(recall, 4),
        'f1_score': round(f1, 4),
        'confusion_matrix': {
            'true_negatives': int(tn),
            'false_positives': int(fp),
            'false_negatives': int(fn),
            'true_positives': int(tp),
        },
        'detailed_report': detailed_report
    }


def evaluate_sentiment_classifier(
    dataset: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Evaluates the VADER sentiment classifier against ground truth labeled comments.
    Reports Precision, Recall, and F1-score across Positive, Neutral, and Negative classes.
    """
    data = dataset or BENCHMARK_COMMENTS
    y_true = [item['sentiment'].lower() for item in data]
    texts = [item['text'] for item in data]

    y_pred = [analyze_sentiment(t)['label'].lower() for t in texts]
    classes = ['positive', 'neutral', 'negative']

    accuracy = accuracy_score(y_true, y_pred)
    precision_macro, recall_macro, f1_macro, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=classes, average='macro', zero_division=0
    )
    precision_weighted, recall_weighted, f1_weighted, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=classes, average='weighted', zero_division=0
    )

    cm = confusion_matrix(y_true, y_pred, labels=classes)
    detailed_report = classification_report(
        y_true, y_pred, labels=classes, output_dict=True, zero_division=0
    )

    return {
        'total_samples': len(data),
        'accuracy': round(accuracy, 4),
        'macro_precision': round(precision_macro, 4),
        'macro_recall': round(recall_macro, 4),
        'macro_f1': round(f1_macro, 4),
        'weighted_f1': round(f1_weighted, 4),
        'confusion_matrix': {
            'classes': classes,
            'matrix': cm.tolist()
        },
        'per_class': {
            cls: {
                'precision': round(detailed_report[cls]['precision'], 4),
                'recall': round(detailed_report[cls]['recall'], 4),
                'f1_score': round(detailed_report[cls]['f1-score'], 4),
                'support': detailed_report[cls]['support']
            } for cls in classes if cls in detailed_report
        }
    }


def run_spam_ablation(dataset: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    Performs an ablation study comparing:
    1. Regex / Heuristics Only
    2. Logistic Regression (TF-IDF) Only
    3. Hybrid Architecture (Proposed Approach)
    Demonstrates that the hybrid approach provides superior recall and precision trade-off.
    """
    from .preprocessor import clean_text
    classifier = get_default_spam_classifier()
    data = dataset or BENCHMARK_COMMENTS
    y_true = [item['is_spam'] for item in data]
    texts = [item['text'] for item in data]

    # 1. Regex Only
    y_pred_regex = [1 if len(classifier.check_heuristics(t)) > 0 else 0 for t in texts]
    prec_r, rec_r, f1_r, _ = precision_recall_fscore_support(y_true, y_pred_regex, average='binary', zero_division=0)
    acc_r = accuracy_score(y_true, y_pred_regex)

    # 2. Machine Learning Only (TF-IDF + LR)
    y_pred_ml = []
    for t in texts:
        cleaned = clean_text(t)
        prob = float(classifier.pipeline.predict_proba([cleaned])[0][1])
        y_pred_ml.append(1 if prob >= 0.50 else 0)
    prec_m, rec_m, f1_m, _ = precision_recall_fscore_support(y_true, y_pred_ml, average='binary', zero_division=0)
    acc_m = accuracy_score(y_true, y_pred_ml)

    # 3. Hybrid (Proposed)
    y_pred_hybrid = [1 if classifier.classify(t)['is_spam'] else 0 for t in texts]
    prec_h, rec_h, f1_h, _ = precision_recall_fscore_support(y_true, y_pred_hybrid, average='binary', zero_division=0)
    acc_h = accuracy_score(y_true, y_pred_hybrid)

    return {
        'regex_only': {
            'accuracy': round(acc_r, 4),
            'precision': round(prec_r, 4),
            'recall': round(rec_r, 4),
            'f1_score': round(f1_r, 4),
        },
        'ml_only': {
            'accuracy': round(acc_m, 4),
            'precision': round(prec_m, 4),
            'recall': round(rec_m, 4),
            'f1_score': round(f1_m, 4),
        },
        'hybrid_proposed': {
            'accuracy': round(acc_h, 4),
            'precision': round(prec_h, 4),
            'recall': round(rec_h, 4),
            'f1_score': round(f1_h, 4),
        }
    }


def run_full_evaluation(dataset: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    Runs evaluation for spam classifier, sentiment classifier, and ablation analysis.
    """
    data = dataset or BENCHMARK_COMMENTS
    spam_eval = evaluate_spam_classifier(dataset=data)
    sentiment_eval = evaluate_sentiment_classifier(dataset=data)
    ablation = run_spam_ablation(dataset=data)

    return {
        'dataset_size': len(data),
        'spam_evaluation': spam_eval,
        'sentiment_evaluation': sentiment_eval,
        'ablation_study': ablation
    }
