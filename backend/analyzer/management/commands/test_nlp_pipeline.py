import json
import sys
from pathlib import Path
from django.core.management.base import BaseCommand
from analyzer.models import Comment, Video
from analyzer.nlp.preprocessor import clean_text, tokenize_and_filter
from analyzer.nlp.sentiment import analyze_sentiment, summarize_sentiment
from analyzer.nlp.spam_classifier import get_default_spam_classifier
from analyzer.nlp.topic_modeler import cluster_topics
from analyzer.nlp.request_extractor import extract_requests, extract_top_keywords
from analyzer.nlp.pipeline import run_nlp_pipeline
from analyzer.nlp.evaluation import run_full_evaluation


def safe_text(s: str) -> str:
    """Sanitizes text for printing on Windows consoles with limited encodings."""
    if not s:
        return ""
    encoding = getattr(sys.stdout, 'encoding', 'utf-8') or 'utf-8'
    return s.encode(encoding, errors='replace').decode(encoding)


class Command(BaseCommand):
    help = 'Runs Phase 2 NLP pipeline verification, component sanity-checks, and classification evaluation.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--evaluate',
            action='store_true',
            help='Run precision, recall, and F1 evaluation on the benchmark dataset.'
        )
        parser.add_argument(
            '--video-id',
            type=str,
            default=None,
            help='Run pipeline on comments stored in DB for a specific YouTube video ID.'
        )
        parser.add_argument(
            '--dataset-file',
            type=str,
            default=None,
            help='Path to a custom JSON or CSV file with labeled comments for evaluation.'
        )
        parser.add_argument(
            '--update-db',
            action='store_true',
            help='Update is_spam, sentiment_label, and sentiment_score in the database for stored comments.'
        )

    def write_safe(self, msg, style_func=None):
        cleaned = safe_text(str(msg))
        if style_func:
            self.stdout.write(style_func(cleaned))
        else:
            self.stdout.write(cleaned)

    def handle(self, *args, **options):
        self.write_safe("=" * 70, self.style.MIGRATE_HEADING)
        self.write_safe(" Phase 2: NLP Pipeline Verification & Evaluation Suite ", self.style.MIGRATE_HEADING)
        self.write_safe("=" * 70, self.style.MIGRATE_HEADING)

        # -------------------------------------------------------------
        # 1. EVALUATION (Precision / Recall / F1)
        # -------------------------------------------------------------
        self.write_safe("\n[1/5] Evaluating Spam & Sentiment Classifiers...", self.style.NOTICE)

        custom_data = None
        if options.get('dataset_file'):
            file_path = Path(options['dataset_file'])
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    custom_data = json.load(f)
                self.write_safe(f"Loaded custom dataset from {file_path} ({len(custom_data)} samples)")
            else:
                self.stderr.write(f"Dataset file not found: {file_path}")

        eval_results = run_full_evaluation(dataset=custom_data)
        spam_ev = eval_results['spam_evaluation']
        sent_ev = eval_results['sentiment_evaluation']

        self.write_safe(f"\n--- SPAM CLASSIFIER EVALUATION ({spam_ev['total_samples']} samples) ---", self.style.SUCCESS)
        self.write_safe(f"  Accuracy  : {spam_ev['accuracy'] * 100:.2f}%")
        self.write_safe(f"  Precision : {spam_ev['precision'] * 100:.2f}%  (Spam)")
        self.write_safe(f"  Recall    : {spam_ev['recall'] * 100:.2f}%  (Spam)")
        self.write_safe(f"  F1-Score  : {spam_ev['f1_score'] * 100:.2f}%  (Spam)")
        cm = spam_ev['confusion_matrix']
        self.write_safe(f"  Confusion Matrix: TP={cm['true_positives']}, FP={cm['false_positives']}, TN={cm['true_negatives']}, FN={cm['false_negatives']}")

        # Ablation study display
        ablation = eval_results.get('ablation_study', {})
        if ablation:
            self.write_safe("\n--- ABLATION STUDY: REGEX vs ML (TF-IDF+LR) vs HYBRID ---", self.style.SUCCESS)
            self.write_safe(f"  1. Regex Only       : Accuracy={ablation['regex_only']['accuracy']*100:.1f}%, Precision={ablation['regex_only']['precision']*100:.1f}%, Recall={ablation['regex_only']['recall']*100:.1f}%, F1={ablation['regex_only']['f1_score']*100:.1f}%")
            self.write_safe(f"  2. ML Only (TF-IDF) : Accuracy={ablation['ml_only']['accuracy']*100:.1f}%, Precision={ablation['ml_only']['precision']*100:.1f}%, Recall={ablation['ml_only']['recall']*100:.1f}%, F1={ablation['ml_only']['f1_score']*100:.1f}%")
            self.write_safe(f"  3. Hybrid (Proposed): Accuracy={ablation['hybrid_proposed']['accuracy']*100:.1f}%, Precision={ablation['hybrid_proposed']['precision']*100:.1f}%, Recall={ablation['hybrid_proposed']['recall']*100:.1f}%, F1={ablation['hybrid_proposed']['f1_score']*100:.1f}%")

        self.write_safe(f"\n--- VADER SENTIMENT CLASSIFIER EVALUATION ---", self.style.SUCCESS)
        self.write_safe(f"  Overall Accuracy : {sent_ev['accuracy'] * 100:.2f}%")
        self.write_safe(f"  Macro F1-Score   : {sent_ev['macro_f1'] * 100:.2f}%")
        self.write_safe(f"  Weighted F1      : {sent_ev['weighted_f1'] * 100:.2f}%")
        self.write_safe("  Per-Class Metrics:")
        for cls, metrics in sent_ev['per_class'].items():
            self.write_safe(
                f"    - {cls.capitalize():<8}: Precision={metrics['precision']*100:.1f}%, "
                f"Recall={metrics['recall']*100:.1f}%, F1={metrics['f1_score']*100:.1f}% "
                f"(Support: {metrics['support']})"
            )

        # -------------------------------------------------------------
        # 2. COMPONENT SANITY-CHECKS
        # -------------------------------------------------------------
        self.write_safe("\n[2/5] Testing Standalone Preprocessor & Cleaner...", self.style.NOTICE)
        sample_dirty = "Awesome video at 04:12!!!!! &amp; Check my channel http://spam.xyz @creator"
        sample_clean = clean_text(sample_dirty)
        sample_tokens = tokenize_and_filter(sample_dirty)
        self.write_safe(f"  Raw     : {sample_dirty}")
        self.write_safe(f"  Cleaned : {sample_clean}")
        self.write_safe(f"  Tokens  : {sample_tokens}")

        self.write_safe("\n[3/5] Testing Standalone Spam Classifier...", self.style.NOTICE)
        spam_cases = [
            "Contact Mrs. Brenda on WhatsApp: +1-202-555-0184 to recover crypto funds!",
            "This was the best tutorial on dynamic programming I have ever seen. Thank you!",
            "Sub to my channel for free robux and v-bucks giveaway!!!",
            "The explanation of backpropagation was so clear.",
        ]
        clf = get_default_spam_classifier()
        for text in spam_cases:
            res = clf.classify(text)
            status_style = self.style.ERROR if res['is_spam'] else self.style.SUCCESS
            status_text = "SPAM" if res['is_spam'] else "HAM "
            self.write_safe(
                f"  [{status_style(status_text)}] (Conf: {res['confidence']:.2f}, Method: {res['decision_method']}): \"{text[:65]}...\""
            )

        self.write_safe("\n[4/5] Testing Standalone Sentiment Classifier (VADER)...", self.style.NOTICE)
        sentiment_cases = [
            "Absolutely loved this lecture! You made everything so clear and engaging. 10/10!",
            "What version of Python is being used at timestamp 03:15?",
            "The audio was terrible, constant buzzing noise and background music was too loud.",
        ]
        for text in sentiment_cases:
            res = analyze_sentiment(text)
            self.write_safe(
                f"  [{res['label'].upper():<8}] (Compound: {res['compound']:+.3f}): \"{text}\""
            )

        # -------------------------------------------------------------
        # 3. TOPIC CLUSTERING & REQUEST EXTRACTION TEST
        # -------------------------------------------------------------
        self.write_safe("\n[5/5] Testing Topic Clustering & Request Extraction on Corpus...", self.style.NOTICE)

        # Check if comments exist in PostgreSQL
        video_id = options.get('video_id')
        comments_qs = Comment.objects.all()
        if video_id:
            comments_qs = comments_qs.filter(video__youtube_video_id=video_id)

        db_count = comments_qs.count()
        if db_count > 0:
            self.write_safe(f"  Using {db_count} comments stored in PostgreSQL database...")
            comments_data = list(comments_qs.values('id', 'text', 'author'))
        else:
            self.write_safe("  (No stored comments in DB yet; using benchmark sample comments for demonstration)")
            from analyzer.nlp.benchmark_data import BENCHMARK_COMMENTS
            comments_data = [{'text': c['text']} for c in BENCHMARK_COMMENTS]

        # Run end-to-end NLP pipeline
        results = run_nlp_pipeline(comments_data)

        # Print Topic Clusters
        self.write_safe(f"\n--- DISCOVERED TOPIC CLUSTERS ({len(results['topic_clusters'])} clusters) ---", self.style.SUCCESS)
        for cluster in results['topic_clusters']:
            self.write_safe(
                f"  Cluster #{cluster['cluster_id'] + 1}: {cluster['topic_name']} "
                f"({cluster['comment_count']} comments, {cluster['percentage']}%)"
            )
            self.write_safe(f"    Keywords : {', '.join(cluster['keywords'])}")
            if cluster['sample_comments']:
                sample = cluster['sample_comments'][0].replace('\n', ' ')
                self.write_safe(f"    Sample   : \"{sample[:75]}...\"")

        # Print Extracted Requests
        self.write_safe(f"\n--- EXTRACTED AUDIENCE REQUESTS & FEEDBACK ---", self.style.SUCCESS)
        if results['top_requests']:
            for i, req in enumerate(results['top_requests'][:5], 1):
                self.write_safe(f"  {i}. [{req['category']}] \"{req['request']}\" (Mentions: {req['count']})")
                sample = req['sample_comment'].replace('\n', ' ')
                self.write_safe(f"     Example: \"{sample[:80]}...\"")
        else:
            self.write_safe("  No specific request patterns found in sample.")

        # Print Top Keywords
        self.write_safe(f"\n--- TOP EXTRACTED KEYWORDS ---", self.style.SUCCESS)
        top_kw_str = ", ".join([f"{kw['keyword']} ({kw['count']})" for kw in results['top_keywords'][:10]])
        self.write_safe(f"  {top_kw_str}")

        # Print Sentiment Summary
        ss = results['sentiment_summary']
        self.write_safe(f"\n--- SENTIMENT BREAKDOWN (Spam-Filtered) ---", self.style.SUCCESS)
        self.write_safe(
            f"  Positive : {ss['positive_count']} ({ss['positive_percentage']}%)\n"
            f"  Neutral  : {ss['neutral_count']} ({ss['neutral_percentage']}%)\n"
            f"  Negative : {ss['negative_count']} ({ss['negative_percentage']}%)\n"
            f"  Avg Compound Score : {ss['average_compound']}"
        )

        # Update DB if flag requested
        if options.get('update_db') and db_count > 0:
            self.write_safe("\nUpdating comments in PostgreSQL...", self.style.NOTICE)
            for annotated in results['annotated_comments']:
                if 'id' in annotated:
                    Comment.objects.filter(id=annotated['id']).update(
                        is_spam=annotated['is_spam'],
                        sentiment_label=annotated['sentiment_label'],
                        sentiment_score=annotated['sentiment_score']
                    )
            self.write_safe("Database records updated successfully.", self.style.SUCCESS)

        self.write_safe("\n" + "=" * 70, self.style.MIGRATE_HEADING)
        self.write_safe(" Phase 2 NLP Pipeline Verification Finished Successfully! ", self.style.SUCCESS)
        self.write_safe("=" * 70 + "\n", self.style.MIGRATE_HEADING)
