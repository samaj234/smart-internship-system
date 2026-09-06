import os
import json
import numpy as np
import pandas as pd
from sklearn.metrics import (
    precision_score, recall_score, f1_score,
    roc_auc_score, classification_report
)
from sklearn.metrics.pairwise import cosine_similarity as sklearn_cosine
from sentence_transformers import SentenceTransformer
from app.services.tfidf_matcher import TFIDFMatcher
from app.services.preprocessing import preprocess_for_sbert
from app.services.data_loader import load_recruitment_dataset
from app.services.resume_loader import load_resume_dataset
from app.services.rjdb_loader import load_rjdb_dataset as load_rjdb


# ── numpy replacements for scipy.stats ──────────────────────────────────────

def pearsonr(x, y):
    x, y = np.array(x), np.array(y)
    xm, ym = x - x.mean(), y - y.mean()
    denom = np.linalg.norm(xm) * np.linalg.norm(ym)
    r = float(np.dot(xm, ym) / denom) if denom != 0 else 0.0
    return r, None


class _SpearmanResult:
    def __init__(self, correlation):
        self.correlation = correlation


def spearmanr(x, y):
    x, y = np.array(x), np.array(y)
    rx = np.argsort(np.argsort(x)).astype(float)
    ry = np.argsort(np.argsort(y)).astype(float)
    r, _ = pearsonr(rx, ry)
    return _SpearmanResult(r)

# ────────────────────────────────────────────────────────────────────────────


# SBERT model — loaded once at module level
_sbert_model = SentenceTransformer('all-mpnet-base-v2')

# Paths
BASE_DIR = os.path.join(os.path.dirname(__file__), '..', '..')

RESULTS_PATH = os.path.join(BASE_DIR, 'dataset', 'evaluation_results.json')
LABELLED_PATH = os.path.join(BASE_DIR, 'dataset', 'labelled_dataset.csv')
DATASET_PATH = os.path.join(BASE_DIR, 'dataset', 'recruitment_dataset.csv')
RESUME_PATH = os.path.join(BASE_DIR, 'dataset', 'resume_data.csv')
RESUME_RESULTS_PATH = os.path.join(BASE_DIR, 'dataset', 'resume_evaluation_results.json')
RJDB_PATH = os.path.join(BASE_DIR, 'dataset', 'train.jsonl')
RJDB_RESULTS_PATH = os.path.join(BASE_DIR, 'dataset', 'rjdb_evaluation_results.json')



def _compute_sbert_scores(student_texts: list, job_texts: list) -> np.ndarray:
    """
    Encodes all student and job texts with SBERT then computes
    pairwise cosine similarity for each (student, job) pair.

    Uses batch encoding for efficiency — SBERT processes multiple
    sentences in a single transformer forward pass, which is
    significantly faster than encoding one pair at a time.
    On 9,000+ pairs this difference is substantial.
    """
    print("Encoding student texts with SBERT...")
    student_embeddings = _sbert_model.encode(
        [preprocess_for_sbert(t) for t in student_texts],
        batch_size=64,
        show_progress_bar=True
    )
    print("Encoding job texts with SBERT...")
    job_embeddings = _sbert_model.encode(
        [preprocess_for_sbert(t) for t in job_texts],
        batch_size=64,
        show_progress_bar=True
    )

    scores = []
    for s_emb, j_emb in zip(student_embeddings, job_embeddings):
        score = sklearn_cosine([s_emb], [j_emb])[0][0]
        scores.append(float(score))
    return np.array(scores)


def _compute_tfidf_scores(student_texts: list, job_texts: list) -> np.ndarray:
    """
    Fits a TF-IDF vectorizer on the combined corpus then computes
    pairwise cosine similarity for each (student, job) pair.

    The vectorizer is fit on all texts combined so vocabulary and
    IDF weights reflect the full dataset — this is the correct
    approach since TF-IDF IDF weights are corpus-relative.
    """
    print("Computing TF-IDF scores...")
    matcher = TFIDFMatcher()
    matcher.fit(student_texts + job_texts)
    print(f"TF-IDF vocabulary size: {len(matcher.vectorizer.vocabulary_)}")

    scores = []
    for s_text, j_text in zip(student_texts, job_texts):
        score = matcher.similarity(s_text, j_text)
        scores.append(score)
    return np.array(scores)


def _compute_metrics(
    scores: np.ndarray,
    labels: np.ndarray,
    method: str
) -> dict:
    """
    Computes classification metrics using median score as threshold.

    Uses median rather than fixed 0.5 because score distributions
    differ significantly between TF-IDF and SBERT — TF-IDF scores
    cluster near 0 while SBERT scores cluster near 0.3-0.6.
    Median threshold gives each method a fair split regardless
    of its absolute score range.
    """
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


def _find_optimal_alpha(
    sbert_scores: np.ndarray,
    tfidf_scores: np.ndarray,
    labels: np.ndarray
) -> dict:
    """
    Tests alpha values from 0.0 to 1.0 in steps of 0.1.
    For each alpha, computes hybrid scores and evaluates AUC-ROC.

    Alpha = 1.0 → pure SBERT
    Alpha = 0.0 → pure TF-IDF
    Alpha = 0.7 → 70% SBERT + 30% TF-IDF

    Returns the alpha producing the highest AUC.
    """
    print("\nFinding optimal hybrid alpha...")
    best_alpha = 0.5
    best_auc = 0.0
    alpha_results = []

    for alpha in np.arange(0.0, 1.1, 0.1):
        alpha = round(float(alpha), 1)
        hybrid_scores = alpha * sbert_scores + (1 - alpha) * tfidf_scores
        auc = roc_auc_score(labels, hybrid_scores)
        alpha_results.append({"alpha": alpha, "auc": round(auc, 4)})
        print(f"  alpha={alpha:.1f} → AUC={auc:.4f}")
        if auc > best_auc:
            best_auc = auc
            best_alpha = alpha

    return {
        "best_alpha": best_alpha,
        "best_auc": round(best_auc, 4),
        "all": alpha_results
    }


def run_evaluation(force_rerun: bool = False) -> dict:
    """
    Evaluation pipeline using Jaccard-labelled Kaggle dataset.
    Kept for comparison purposes — shows performance on
    keyword-overlap labels vs semantic labels.
    """
    if not force_rerun and os.path.exists(RESULTS_PATH):
        print("Loading cached Kaggle evaluation results...")
        with open(RESULTS_PATH, 'r') as f:
            return json.load(f)

    print("Loading Jaccard-labelled dataset...")
    df = pd.read_csv(LABELLED_PATH)

    student_texts = df['student_text'].tolist()
    job_texts = df['job_text'].tolist()
    labels = df['jaccard_label'].values

    print(f"Dataset size: {len(df)}")
    print(f"Positive pairs: {labels.sum()}")
    print(f"Negative pairs: {(labels == 0).sum()}")

    sbert_scores = _compute_sbert_scores(student_texts, job_texts)
    tfidf_scores = _compute_tfidf_scores(student_texts, job_texts)

    sbert_metrics = _compute_metrics(sbert_scores, labels, "SBERT")
    tfidf_metrics = _compute_metrics(tfidf_scores, labels, "TF-IDF")

    alpha_results = _find_optimal_alpha(sbert_scores, tfidf_scores, labels)
    best_alpha = alpha_results['best_alpha']

    hybrid_scores = best_alpha * sbert_scores + (1 - best_alpha) * tfidf_scores
    hybrid_metrics = _compute_metrics(
        hybrid_scores, labels, f"Hybrid (α={best_alpha})"
    )

    results = {
        "dataset_size": len(df),
        "labelling_method": "Jaccard skill overlap (threshold=0.2)",
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

    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)
    with open(RESULTS_PATH, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {RESULTS_PATH}")

    return results


def run_resume_evaluation(force_rerun: bool = False) -> dict:
    """
    Primary evaluation pipeline using the resume matching dataset.

    Ground truth labels come from matched_score — a pre-computed
    relevance score reflecting genuine resume-job fit. This is the
    most meaningful evaluation since:
    1. Labels are semantically grounded (real matching scores)
    2. Dataset is large (9,543 pairs)
    3. Near-balanced classes (47% positive, 53% negative)
    4. Rich natural language text on both sides

    Also computes Spearman and Pearson correlation with the
    continuous matched_score — a more nuanced measure than
    binary AUC that shows how well each method tracks true
    relevance across its full range.
    """
    if not force_rerun and os.path.exists(RESUME_RESULTS_PATH):
        print("Loading cached resume evaluation results...")
        with open(RESUME_RESULTS_PATH, 'r') as f:
            return json.load(f)

    print("Loading resume dataset...")
    df = load_resume_dataset(filepath=RESUME_PATH, threshold=0.70)

    student_texts = df['student_text'].tolist()
    job_texts = df['job_text'].tolist()
    labels = df['label'].values
    continuous_scores = df['matched_score'].values

    print(f"\nDataset: {len(df)} pairs")
    print(f"Positive: {labels.sum()} | Negative: {(labels == 0).sum()}")

    sbert_scores = _compute_sbert_scores(student_texts, job_texts)
    tfidf_scores = _compute_tfidf_scores(student_texts, job_texts)

    sbert_metrics = _compute_metrics(sbert_scores, labels, "SBERT")
    tfidf_metrics = _compute_metrics(tfidf_scores, labels, "TF-IDF")

    # Correlation with continuous matched_score
    sbert_spearman = spearmanr(sbert_scores, continuous_scores).correlation
    tfidf_spearman = spearmanr(tfidf_scores, continuous_scores).correlation
    sbert_pearson = pearsonr(sbert_scores, continuous_scores)[0]
    tfidf_pearson = pearsonr(tfidf_scores, continuous_scores)[0]

    print(f"\nCorrelation with matched_score:")
    print(f"  SBERT  Spearman: {sbert_spearman:.4f} | Pearson: {sbert_pearson:.4f}")
    print(f"  TF-IDF Spearman: {tfidf_spearman:.4f} | Pearson: {tfidf_pearson:.4f}")

    alpha_results = _find_optimal_alpha(sbert_scores, tfidf_scores, labels)
    best_alpha = alpha_results['best_alpha']

    hybrid_scores = best_alpha * sbert_scores + (1 - best_alpha) * tfidf_scores
    hybrid_metrics = _compute_metrics(
        hybrid_scores, labels, f"Hybrid (α={best_alpha})"
    )

    # Hybrid correlation
    hybrid_spearman = spearmanr(hybrid_scores, continuous_scores).correlation
    hybrid_pearson = pearsonr(hybrid_scores, continuous_scores)[0]

    print(f"  Hybrid Spearman: {hybrid_spearman:.4f} | Pearson: {hybrid_pearson:.4f}")

    results = {
        "dataset": "Resume matching dataset (9543 pairs)",
        "labelling_method": "matched_score threshold=0.70",
        "total_pairs": len(df),
        "label_distribution": {
            "positive": int(labels.sum()),
            "negative": int((labels == 0).sum())
        },
        "sbert": sbert_metrics,
        "tfidf": tfidf_metrics,
        "hybrid": hybrid_metrics,
        "correlation_with_matched_score": {
            "sbert_spearman": round(float(sbert_spearman), 4),
            "sbert_pearson": round(float(sbert_pearson), 4),
            "tfidf_spearman": round(float(tfidf_spearman), 4),
            "tfidf_pearson": round(float(tfidf_pearson), 4),
            "hybrid_spearman": round(float(hybrid_spearman), 4),
            "hybrid_pearson": round(float(hybrid_pearson), 4)
        },
        "alpha_search": alpha_results,
        "optimal_alpha": best_alpha
    }

    with open(RESUME_RESULTS_PATH, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {RESUME_RESULTS_PATH}")

    return results

def run_rjdb_evaluation(
    force_rerun: bool = False,
    sample_size: int = 10000
) -> dict:
    """
    Primary evaluation pipeline using the megagonlabs/rjdb dataset.

    This is the strongest evaluation in the project because:
    1. Labels are structurally grounded — matched/unmatched resumes
       were deliberately constructed to differ in specific skills
    2. 100,000 pairs available (we sample 10,000 for efficiency)
    3. Perfectly balanced (50% positive, 50% negative)
    4. Rich natural language text generated by GPT-4 guided by
       a Skill-Occupation Graph — ideal for semantic matching
    5. filtered_skills column gives explicit ground-truth skill gaps

    The key research question: can TF-IDF and SBERT distinguish
    between a resume that has all required skills vs one missing
    specific technical skills?

    SBERT should outperform TF-IDF here because:
    - The unmatched resume still contains domain-relevant text
      (same job titles, same company, similar language)
    - The ONLY difference is specific skill mentions
    - TF-IDF catches exact keyword removal
    - SBERT captures the semantic gap from missing skills
    - Both should perform well, but SBERT's contextual
      understanding should give it an edge
    """
    if not force_rerun and os.path.exists(RJDB_RESULTS_PATH):
        print("Loading cached RJDB evaluation results...")
        with open(RJDB_RESULTS_PATH, 'r') as f:
            return json.load(f)

    print("Loading RJDB dataset...")
    df = load_rjdb(filepath=RJDB_PATH)

    # Sample for efficiency — stratified to keep 50/50 balance
    if sample_size and sample_size < len(df):
        pos = df[df['label'] == 1].sample(
            n=sample_size // 2, random_state=42
        )
        neg = df[df['label'] == 0].sample(
            n=sample_size // 2, random_state=42
        )
        df = pd.concat([pos, neg]).sample(frac=1, random_state=42).reset_index(drop=True)
        print(f"\nSampled {len(df)} pairs ({sample_size//2} positive, {sample_size//2} negative)")

    student_texts = df['student_text'].tolist()
    job_texts = df['job_text'].tolist()
    labels = df['label'].values

    print(f"\nRunning evaluation on {len(df)} pairs...")

    # Compute scores
    sbert_scores = _compute_sbert_scores(student_texts, job_texts)
    tfidf_scores = _compute_tfidf_scores(student_texts, job_texts)

    # Metrics for each method
    sbert_metrics = _compute_metrics(sbert_scores, labels, "SBERT")
    tfidf_metrics = _compute_metrics(tfidf_scores, labels, "TF-IDF")

    # Alpha search
    alpha_results = _find_optimal_alpha(sbert_scores, tfidf_scores, labels)
    best_alpha = alpha_results['best_alpha']

    # Hybrid metrics at optimal alpha
    hybrid_scores = best_alpha * sbert_scores + (1 - best_alpha) * tfidf_scores
    hybrid_metrics = _compute_metrics(
        hybrid_scores, labels, f"Hybrid (α={best_alpha})"
    )

    # Skill gap analysis on filtered_skills
    skill_gap_analysis = _analyze_skill_sensitivity(
        df, sbert_scores, tfidf_scores
    )

    results = {
        "dataset": "megagonlabs/rjdb (GPT-4 generated, Skill-Occupation Graph)",
        "dataset_url": "https://github.com/megagonlabs/rjdb",
        "total_available": 100000,
        "evaluated_pairs": len(df),
        "label_distribution": {
            "positive": int(labels.sum()),
            "negative": int((labels == 0).sum())
        },
        "sbert": sbert_metrics,
        "tfidf": tfidf_metrics,
        "hybrid": hybrid_metrics,
        "alpha_search": alpha_results,
        "optimal_alpha": best_alpha,
        "skill_gap_analysis": skill_gap_analysis
    }

    with open(RJDB_RESULTS_PATH, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {RJDB_RESULTS_PATH}")

    return results


def _analyze_skill_sensitivity(
    df: pd.DataFrame,
    sbert_scores: np.ndarray,
    tfidf_scores: np.ndarray
) -> dict:
    """
    Analyzes how sensitive each method is to specific skill removals.

    For each filtered skill (skill removed to create unmatched resume),
    computes the average score drop between matched and unmatched pairs
    for both SBERT and TF-IDF.

    A larger score drop means the method is more sensitive to that
    skill's presence/absence — useful for XAI explanations.
    """
    df = df.copy()
    df['sbert_score'] = sbert_scores
    df['tfidf_score'] = tfidf_scores

    matched = df[df['pair_type'] == 'matched'].copy()
    unmatched = df[df['pair_type'] == 'unmatched'].copy()

    if matched.empty or unmatched.empty:
        return {}

    avg_sbert_matched = float(matched['sbert_score'].mean())
    avg_sbert_unmatched = float(unmatched['sbert_score'].mean())
    avg_tfidf_matched = float(matched['tfidf_score'].mean())
    avg_tfidf_unmatched = float(unmatched['tfidf_score'].mean())

    print(f"\nSkill Sensitivity Analysis:")
    print(f"  SBERT  — matched: {avg_sbert_matched:.4f}, unmatched: {avg_sbert_unmatched:.4f}, drop: {avg_sbert_matched - avg_sbert_unmatched:.4f}")
    print(f"  TF-IDF — matched: {avg_tfidf_matched:.4f}, unmatched: {avg_tfidf_unmatched:.4f}, drop: {avg_tfidf_matched - avg_tfidf_unmatched:.4f}")

    all_filtered = []
    for skills in df['filtered_skills']:
        if isinstance(skills, list):
            all_filtered.extend(skills)

    from collections import Counter
    top_filtered = Counter(all_filtered).most_common(10)

    print(f"\n  Most commonly removed skills in unmatched resumes:")
    for skill, count in top_filtered:
        print(f"    {skill}: removed in {count} pairs")

    return {
        "sbert_avg_matched": round(avg_sbert_matched, 4),
        "sbert_avg_unmatched": round(avg_sbert_unmatched, 4),
        "sbert_score_drop": round(avg_sbert_matched - avg_sbert_unmatched, 4),
        "tfidf_avg_matched": round(avg_tfidf_matched, 4),
        "tfidf_avg_unmatched": round(avg_tfidf_unmatched, 4),
        "tfidf_score_drop": round(avg_tfidf_matched - avg_tfidf_unmatched, 4),
        "top_filtered_skills": [
            {"skill": s, "count": c} for s, c in top_filtered
        ]
    }

if __name__ == "__main__":
    print("=== RUNNING RESUME DATASET EVALUATION ===\n")
    results = run_resume_evaluation(force_rerun=True)

    print("\n=== FINAL COMPARISON ===")
    print(f"Dataset: {results['dataset']}")
    print(f"Total pairs: {results['total_pairs']}")
    print(f"\nTF-IDF  → F1: {results['tfidf']['f1_score']}, AUC: {results['tfidf']['auc_roc']}")
    print(f"SBERT   → F1: {results['sbert']['f1_score']}, AUC: {results['sbert']['auc_roc']}")
    print(f"Hybrid  → F1: {results['hybrid']['f1_score']}, AUC: {results['hybrid']['auc_roc']}")
    print(f"Optimal α: {results['optimal_alpha']}")

    corr = results['correlation_with_matched_score']
    print(f"\nCorrelation with matched_score:")
    print(f"  TF-IDF  Spearman: {corr['tfidf_spearman']} | Pearson: {corr['tfidf_pearson']}")
    print(f"  SBERT   Spearman: {corr['sbert_spearman']} | Pearson: {corr['sbert_pearson']}")
    print(f"  Hybrid  Spearman: {corr['hybrid_spearman']} | Pearson: {corr['hybrid_pearson']}")

    print("=== RUNNING RJDB EVALUATION ===\n")
    results = run_rjdb_evaluation(force_rerun=True, sample_size=10000)

    print("\n=== FINAL COMPARISON ===")
    print(f"Dataset: {results['dataset']}")
    print(f"Evaluated pairs: {results['evaluated_pairs']}")
    print(f"\nTF-IDF  → F1: {results['tfidf']['f1_score']}, AUC: {results['tfidf']['auc_roc']}")
    print(f"SBERT   → F1: {results['sbert']['f1_score']}, AUC: {results['sbert']['auc_roc']}")
    print(f"Hybrid  → F1: {results['hybrid']['f1_score']}, AUC: {results['hybrid']['auc_roc']}")
    print(f"Optimal α: {results['optimal_alpha']}")

    gap = results['skill_gap_analysis']
    if gap:
        print(f"\nSkill sensitivity:")
        print(f"  SBERT  score drop (matched→unmatched): {gap['sbert_score_drop']}")
        print(f"  TF-IDF score drop (matched→unmatched): {gap['tfidf_score_drop']}")