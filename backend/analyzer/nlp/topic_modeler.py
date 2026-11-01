from typing import Dict, List, Any, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans, MiniBatchKMeans
from sklearn.metrics import silhouette_score
from .preprocessor import clean_text, tokenize_and_filter


def _find_optimal_k_by_silhouette(tfidf_matrix, n_docs: int, min_k: int = 2, max_k: int = 5) -> int:
    """
    Selects the optimal number of clusters K using Silhouette Score analysis.
    Evaluates cluster cohesion and separation, picking the K with the highest score.
    For large matrices (n_docs > 3000), evaluates on a representative subsample for speed.
    """
    effective_max_k = min(max_k, n_docs - 1)
    if effective_max_k < min_k:
        return min(min_k, n_docs)

    best_k = min_k
    best_score = -1.0
    sample_size = min(2000, n_docs) if n_docs > 3000 else None

    for candidate_k in range(min_k, effective_max_k + 1):
        try:
            if n_docs >= 15000:
                km = MiniBatchKMeans(n_clusters=candidate_k, batch_size=1024, random_state=42)
            else:
                km = KMeans(n_clusters=candidate_k, init='k-means++', max_iter=150, n_init=3, random_state=42)
            labels = km.fit_predict(tfidf_matrix)
            # Only compute silhouette if more than one distinct cluster was assigned
            if len(set(labels)) > 1:
                score = silhouette_score(tfidf_matrix, labels, sample_size=sample_size, random_state=42)
                if score > best_score:
                    best_score = score
                    best_k = candidate_k
        except Exception:
            continue

    return best_k


def _determine_num_clusters(n_comments: int, requested_k: Optional[int] = None, tfidf_matrix=None) -> int:
    """
    Dynamically determines an appropriate number of topic clusters (k)
    using silhouette score optimization if matrix is available, or data size heuristics.
    """
    if requested_k and requested_k > 0:
        return min(requested_k, max(1, n_comments - 1))

    if n_comments < 4:
        return 1
    elif n_comments < 8:
        return 2

    # If TF-IDF matrix is provided and we have sufficient comments, optimize with Silhouette score
    if tfidf_matrix is not None and n_comments >= 8:
        return _find_optimal_k_by_silhouette(tfidf_matrix, n_comments, min_k=2, max_k=5)

    if n_comments < 25:
        return 2
    elif n_comments < 60:
        return 3
    else:
        return 4


def cluster_topics(
    comments: List[str],
    num_clusters: Optional[int] = None,
    top_terms_per_cluster: int = 5,
    samples_per_cluster: int = 3
) -> List[Dict[str, Any]]:
    """
    Performs topic clustering on comments using TF-IDF and K-Means with Silhouette Score optimization.
    """
    if not comments:
        return []

    # Clean text for vectorization
    cleaned_comments = [
        " ".join(tokenize_and_filter(c)) for c in comments
    ]

    valid_indices = [i for i, text in enumerate(cleaned_comments) if text.strip()]
    if len(valid_indices) < 2:
        return [{
            'cluster_id': 0,
            'topic_name': 'General Discussion',
            'keywords': ['general', 'feedback'],
            'comment_count': len(comments),
            'percentage': 100.0,
            'sample_comments': comments[:samples_per_cluster]
        }]

    filtered_texts = [cleaned_comments[i] for i in valid_indices]
    filtered_raw = [comments[i] for i in valid_indices]
    n_docs = len(filtered_texts)

    # TF-IDF Vectorizer
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        max_df=0.85,
        min_df=1,
        max_features=2000,
        sublinear_tf=True
    )

    try:
        tfidf_matrix = vectorizer.fit_transform(filtered_texts)
    except ValueError:
        return []

    # Dynamically select optimal k using Silhouette Score
    k = _determine_num_clusters(n_docs, requested_k=num_clusters, tfidf_matrix=tfidf_matrix)
    if k <= 1:
        return [{
            'cluster_id': 0,
            'topic_name': 'General Discussion',
            'keywords': ['discussion', 'comments'],
            'comment_count': len(comments),
            'percentage': 100.0,
            'sample_comments': comments[:samples_per_cluster]
        }]

    # K-Means clustering: use MiniBatchKMeans for massive comment sets (>= 15,000)
    if n_docs >= 15000:
        kmeans = MiniBatchKMeans(
            n_clusters=k,
            batch_size=1024,
            max_iter=200,
            random_state=42
        )
    else:
        kmeans = KMeans(
            n_clusters=k,
            init='k-means++',
            max_iter=300,
            n_init=10,
            random_state=42
        )
    kmeans.fit(tfidf_matrix)

    labels = kmeans.labels_
    cluster_centers = kmeans.cluster_centers_
    terms = np.array(vectorizer.get_feature_names_out())

    clusters: List[Dict[str, Any]] = []

    for cluster_id in range(k):
        member_indices = np.where(labels == cluster_id)[0]
        count = len(member_indices)
        if count == 0:
            continue

        top_term_indices = cluster_centers[cluster_id].argsort()[::-1][:top_terms_per_cluster]
        top_terms = [str(terms[i]) for i in top_term_indices if cluster_centers[cluster_id][i] > 0]
        if not top_terms:
            top_terms = ['discussion']

        topic_name = " & ".join(top_terms[:2]).title()
        sample_texts = [filtered_raw[i] for i in member_indices[:samples_per_cluster]]

        clusters.append({
            'cluster_id': cluster_id,
            'topic_name': topic_name,
            'keywords': top_terms,
            'comment_count': int(count),
            'percentage': round((count / n_docs) * 100, 1),
            'sample_comments': sample_texts
        })

    clusters.sort(key=lambda x: x['comment_count'], reverse=True)
    return clusters
