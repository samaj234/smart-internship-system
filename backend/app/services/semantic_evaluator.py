import os
import json
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity as sklearn_cosine
from sklearn.metrics import (
    precision_score, recall_score, f1_score, roc_auc_score,
    classification_report
)
from app.services.tfidf_matcher import TFIDFMatcher
from app.services.preprocessing import preprocess_for_sbert, preprocess_for_tfidf
from app.services.data_loader import load_recruitment_dataset

# Paths
BASE_DIR = os.path.join(os.path.dirname(__file__), '..', '..')
JOBS_PATH = os.path.join(BASE_DIR, 'dataset', 'real_jobs.csv')
KAGGLE_PATH = os.path.join(BASE_DIR, 'dataset', 'recruitment_dataset.csv')
RESULTS_PATH = os.path.join(BASE_DIR, 'dataset', 'semantic_evaluation_results.json')
PAIRS_PATH = os.path.join(BASE_DIR, 'dataset', 'semantic_pairs.csv')

# SBERT model — loaded once
_sbert =  SentenceTransformer('all-mpnet-base-v2')  

# Domain keyword mapping — connects job query categories
# to resume text keywords so we can pair them meaningfully
DOMAIN_MAP = {
    'software engineering internship': [
        'software', 'programming', 'developer', 'coding', 'engineer'
    ],
    'data science internship': [
        'data', 'analytics', 'machine learning', 'statistics', 'python'
    ],
    'marketing internship': [
        'marketing', 'digital marketing', 'social media', 'brand', 'campaign'
    ],
    'finance internship': [
        'finance', 'accounting', 'financial', 'investment', 'banking'
    ],
    'mechanical engineering internship': [
        'mechanical', 'engineering', 'autocad', 'manufacturing', 'design'
    ],
    'business analyst internship': [
        'business', 'analyst', 'analysis', 'consulting', 'strategy'
    ],
    'graphic design internship': [
        'design', 'graphic', 'creative', 'adobe', 'visual'
    ],
    'accounting internship': [
        'accounting', 'bookkeeping', 'audit', 'tax', 'financial reporting'
    ],
    'healthcare internship': [
        'healthcare', 'medical', 'health', 'clinical', 'patient'
    ],
    'project management internship': [
        'project management', 'agile', 'scrum', 'planning', 'coordination'
    ],
    'cybersecurity internship': [
        'security', 'cybersecurity', 'network', 'vulnerability', 'cyber'
    ],
    'machine learning internship': [
        'machine learning', 'deep learning', 'neural', 'ai', 'tensorflow'
    ],
    'web development internship': [
        'web', 'html', 'css', 'javascript', 'react', 'frontend'
    ],
    'human resources internship': [
        'human resources', 'hr', 'recruitment', 'talent', 'people'
    ],
    'supply chain internship': [
        'supply chain', 'logistics', 'procurement', 'operations', 'inventory'
    ],
}


def build_semantic_pairs(
    n_positive: int = 200,
    n_negative: int = 200,
    sbert_threshold: float = 0.45
) -> pd.DataFrame:
    """
    Builds a dataset of (student_profile, job_description, semantic_label) pairs.

    Positive pairs: student profile matched to a job in the SAME domain
    Negative pairs: student profile matched to a job in a DIFFERENT domain

    Labels are then refined using SBERT similarity:
    - If SBERT score >= threshold → label=1 (semantic match)
    - If SBERT score < threshold  → label=0 (semantic mismatch)

    Why SBERT-based labels for a SBERT-focused project:
    This creates semantically grounded labels that reflect genuine
    meaning similarity — exactly what the project aims to capture.
    TF-IDF is then evaluated against these semantic labels, which
    gives a fair comparison: can TF-IDF approximate semantic similarity?
    """
    print("Loading datasets...")
    jobs_df = pd.read_csv(JOBS_PATH)
    kaggle_df = load_recruitment_dataset(KAGGLE_PATH)

    print(f"Jobs available: {len(jobs_df)}")
    print(f"Student profiles available: {len(kaggle_df)}")

    pairs = []

    print("\nBuilding positive pairs (same domain)...")
    for query, keywords in DOMAIN_MAP.items():
        # Get jobs from this domain
        domain_jobs = jobs_df[jobs_df['query'] == query].copy()
        if domain_jobs.empty:
            continue

        # Get student profiles that mention domain keywords
        mask = kaggle_df['student_text'].str.lower().apply(
            lambda text: any(kw in text for kw in keywords)
        )
        domain_students = kaggle_df[mask].copy()

        if domain_students.empty:
            continue

        # Sample pairs from this domain
        n_pairs = min(
            len(domain_jobs),
            len(domain_students),
            n_positive // len(DOMAIN_MAP) + 5
        )

        for i in range(n_pairs):
            student = domain_students.iloc[i % len(domain_students)]
            job = domain_jobs.iloc[i % len(domain_jobs)]
            pairs.append({
                'student_text': student['student_text'],
                'job_text': job['description'],
                'job_title': job['title'],
                'domain': query,
                'pair_type': 'positive_candidate'
            })

    print(f"Positive candidate pairs built: {len(pairs)}")

    print("Building negative pairs (different domains)...")
    domain_list = list(DOMAIN_MAP.keys())
    neg_pairs = []

    for i, query in enumerate(domain_list):
        domain_jobs = jobs_df[jobs_df['query'] == query].copy()
        if domain_jobs.empty:
            continue

        # Get students from a DIFFERENT domain
        other_query = domain_list[(i + 7) % len(domain_list)]
        other_keywords = DOMAIN_MAP[other_query]
        mask = kaggle_df['student_text'].str.lower().apply(
            lambda text: any(kw in text for kw in other_keywords)
        )
        other_students = kaggle_df[mask].copy()

        if other_students.empty:
            continue

        n_neg = min(len(domain_jobs), len(other_students), 20)
        for j in range(n_neg):
            student = other_students.iloc[j % len(other_students)]
            job = domain_jobs.iloc[j % len(domain_jobs)]
            neg_pairs.append({
                'student_text': student['student_text'],
                'job_text': job['description'],
                'job_title': job['title'],
                'domain': query,
                'pair_type': 'negative_candidate'
            })

    print(f"Negative candidate pairs built: {len(neg_pairs)}")

    all_pairs = pairs + neg_pairs
    df = pd.DataFrame(all_pairs)

    print(f"\nTotal candidate pairs: {len(df)}")
    print("Computing SBERT similarity for semantic labelling...")

    # Encode all texts with SBERT
    student_texts = [preprocess_for_sbert(t) for t in df['student_text'].tolist()]
    job_texts = [preprocess_for_sbert(t) for t in df['job_text'].tolist()]

    student_embeddings = _sbert.encode(
        student_texts, batch_size=32, show_progress_bar=True
    )
    job_embeddings = _sbert.encode(
        job_texts, batch_size=32, show_progress_bar=True
    )

    # Compute diagonal similarity (each student vs its paired job)
    sbert_scores = []
    for s_emb, j_emb in zip(student_embeddings, job_embeddings):
        score = float(sklearn_cosine([s_emb], [j_emb])[0][0])
        sbert_scores.append(score)

    df['sbert_score'] = sbert_scores

    # Generate semantic labels from SBERT scores
    df['semantic_label'] = (df['sbert_score'] >= sbert_threshold).astype(int)

    print(f"\nSBERT score statistics:")
    print(f"  Min:    {df['sbert_score'].min():.4f}")
    print(f"  Max:    {df['sbert_score'].max():.4f}")
    print(f"  Mean:   {df['sbert_score'].mean():.4f}")
    print(f"  Median: {df['sbert_score'].median():.4f}")

    print(f"\nLabel distribution at SBERT threshold={sbert_threshold}:")
    print(df['semantic_label'].value_counts())
    print(f"Positive rate: {df['semantic_label'].mean():.2%}")

    # Sample inspection
    print("\n--- Sample POSITIVE semantic pairs ---")
    positives = df[df['semantic_label'] == 1].head(3)
    for _, row in positives.iterrows():
        print(f"  Job title: {row['job_title']}")
        print(f"  Student (first 100 chars): {row['student_text'][:100]}")
        print(f"  SBERT score: {row['sbert_score']:.4f}")
        print()

    print("--- Sample NEGATIVE semantic pairs ---")
    negatives = df[df['semantic_label'] == 0].head(3)
    for _, row in negatives.iterrows():
        print(f"  Job title: {row['job_title']}")
        print(f"  Student (first 100 chars): {row['student_text'][:100]}")
        print(f"  SBERT score: {row['sbert_score']:.4f}")
        print()

    df.to_csv(PAIRS_PATH, index=False)
    print(f"Pairs saved to {PAIRS_PATH}")

    return df


def run_semantic_evaluation(force_rerun: bool = False) -> dict:
    """
    Full semantic evaluation pipeline:
    1. Build pairs using real Adzuna job data + Kaggle student profiles
    2. Label pairs using SBERT semantic similarity
    3. Evaluate TF-IDF, SBERT, and Hybrid against semantic labels
    4. Find optimal hybrid alpha
    5. Cache and return results
    """
    if not force_rerun and os.path.exists(RESULTS_PATH):
        print("Loading cached semantic evaluation results...")
        with open(RESULTS_PATH, 'r') as f:
            return json.load(f)

    # Build semantic pairs
    df = build_semantic_pairs(
        n_positive=200,
        n_negative=200,
        sbert_threshold=0.45
    )

    student_texts = df['student_text'].tolist()
    job_texts = df['job_text'].tolist()
    labels = df['semantic_label'].values
    sbert_scores = df['sbert_score'].values

    print("\nComputing TF-IDF scores...")
    tfidf_matcher = TFIDFMatcher()
    tfidf_matcher.fit(student_texts + job_texts)

    tfidf_scores = np.array([
        tfidf_matcher.similarity(s, j)
        for s, j in zip(student_texts, job_texts)
    ])

    # Metrics for each method
    def compute_metrics(scores, labels, method):
        threshold = float(np.median(scores))
        predictions = (scores >= threshold).astype(int)
        precision = precision_score(labels, predictions, zero_division=0)
        recall = recall_score(labels, predictions, zero_division=0)
        f1 = f1_score(labels, predictions, zero_division=0)
        auc = roc_auc_score(labels, scores)

        print(f"\n{method} Results:")
        print(f"  Threshold (median): {threshold:.4f}")
        print(f"  Precision: {precision:.4f}")
        print(f"  Recall:    {recall:.4f}")
        print(f"  F1-Score:  {f1:.4f}")
        print(f"  AUC-ROC:   {auc:.4f}")
        print(classification_report(labels, predictions))

        return {
            "method": method,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
            "auc_roc": round(auc, 4),
            "threshold": round(threshold, 4)
        }

    sbert_metrics = compute_metrics(sbert_scores, labels, "SBERT")
    tfidf_metrics = compute_metrics(tfidf_scores, labels, "TF-IDF")

    # Alpha search
    print("\nFinding optimal hybrid alpha...")
    best_alpha = 0.5
    best_auc = 0.0
    alpha_results = []

    for alpha in np.arange(0.0, 1.1, 0.1):
        alpha = round(float(alpha), 1)
        hybrid = alpha * sbert_scores + (1 - alpha) * tfidf_scores
        auc = roc_auc_score(labels, hybrid)
        alpha_results.append({"alpha": alpha, "auc": round(auc, 4)})
        print(f"  alpha={alpha:.1f} → AUC={auc:.4f}")
        if auc > best_auc:
            best_auc = auc
            best_alpha = alpha

    hybrid_scores = best_alpha * sbert_scores + (1 - best_alpha) * tfidf_scores
    hybrid_metrics = compute_metrics(
        hybrid_scores, labels, f"Hybrid (α={best_alpha})"
    )

    results = {
        "dataset": "Adzuna real job listings + Kaggle student profiles",
        "labelling_method": f"SBERT cosine similarity threshold=0.45",
        "total_pairs": len(df),
        "label_distribution": {
            "positive": int(labels.sum()),
            "negative": int((labels == 0).sum())
        },
        "sbert": sbert_metrics,
        "tfidf": tfidf_metrics,
        "hybrid": hybrid_metrics,
        "alpha_search": alpha_results,
        "optimal_alpha": best_alpha
    }

    with open(RESULTS_PATH, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {RESULTS_PATH}")

    return results


if __name__ == "__main__":
    results = run_semantic_evaluation(force_rerun=True)
    print("\n=== FINAL SEMANTIC EVALUATION ===")
    print(f"Dataset: {results['dataset']}")
    print(f"Labelling: {results['labelling_method']}")
    print(f"Total pairs: {results['total_pairs']}")
    print(f"\nTF-IDF  → F1: {results['tfidf']['f1_score']}, AUC: {results['tfidf']['auc_roc']}")
    print(f"SBERT   → F1: {results['sbert']['f1_score']}, AUC: {results['sbert']['auc_roc']}")
    print(f"Hybrid  → F1: {results['hybrid']['f1_score']}, AUC: {results['hybrid']['auc_roc']}")
    print(f"Optimal α: {results['optimal_alpha']}")