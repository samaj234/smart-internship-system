import os
import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity as sklearn_cosine
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score

from app.services.rjdb_loader import load_rjdb_dataset
from app.services.tfidf_matcher import TFIDFMatcher
from app.services.preprocessing import preprocess_for_sbert, preprocess_for_tfidf
from app.services.embedder import model as sbert_model

RESULTS_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'dataset', 'rjdb_evaluation_results.json')


def run_rjdb_evaluation(max_records=None, force_rerun=False):
    if not force_rerun and os.path.exists(RESULTS_PATH):
        print("Loading cached rjdb evaluation results...")
        with open(RESULTS_PATH) as f:
            return json.load(f)

    df = load_rjdb_dataset(max_records=max_records)
    job_texts = df['job_text'].tolist()
    student_texts = df['student_text'].tolist()
    labels = df['label'].values

    print("Computing SBERT scores...")
    job_emb = sbert_model.encode(
        [preprocess_for_sbert(t) for t in job_texts], batch_size=32, show_progress_bar=True
    )
    student_emb = sbert_model.encode(
        [preprocess_for_sbert(t) for t in student_texts], batch_size=32, show_progress_bar=True
    )
    sbert_scores = np.array([
        sklearn_cosine([s], [j])[0][0] for s, j in zip(student_emb, job_emb)
    ])

    print("Computing TF-IDF scores...")
    matcher = TFIDFMatcher()
    matcher.fit(student_texts + job_texts)
    tfidf_scores = np.array([
        matcher.similarity(preprocess_for_tfidf(s), preprocess_for_tfidf(j))
        for s, j in zip(student_texts, job_texts)
    ])

    def compute_metrics(scores, labels, method):
        threshold = float(np.median(scores))
        preds = (scores >= threshold).astype(int)
        metrics = {
            "method": method,
            "precision": round(precision_score(labels, preds, zero_division=0), 4),
            "recall": round(recall_score(labels, preds, zero_division=0), 4),
            "f1_score": round(f1_score(labels, preds, zero_division=0), 4),
            "auc_roc": round(roc_auc_score(labels, scores), 4),
            "threshold": round(threshold, 4)
        }
        print(f"\n{method} Results:")
        for k, v in metrics.items():
            if k != "method":
                print(f"  {k}: {v}")
        return metrics

    sbert_metrics = compute_metrics(sbert_scores, labels, "SBERT")
    tfidf_metrics = compute_metrics(tfidf_scores, labels, "TF-IDF")

    print("\nSearching for optimal hybrid alpha...")
    best_alpha, best_auc, alpha_results = 0.5, 0.0, []
    for alpha in np.arange(0.0, 1.1, 0.1):
        alpha = round(float(alpha), 1)
        hybrid = alpha * sbert_scores + (1 - alpha) * tfidf_scores
        auc = roc_auc_score(labels, hybrid)
        alpha_results.append({"alpha": alpha, "auc": round(auc, 4)})
        print(f"  alpha={alpha:.1f} -> AUC={auc:.4f}")
        if auc > best_auc:
            best_auc, best_alpha = auc, alpha

    hybrid_scores = best_alpha * sbert_scores + (1 - best_alpha) * tfidf_scores
    hybrid_metrics = compute_metrics(hybrid_scores, labels, f"Hybrid (alpha={best_alpha})")

    results = {
        "dataset": "megagonlabs/rjdb (real matched/unmatched resume-job pairs)",
        "total_pairs": len(df),
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
    results = run_rjdb_evaluation(force_rerun=True)
    print("\n=== FINAL RJDB EVALUATION ===")
    print(f"SBERT  -> F1: {results['sbert']['f1_score']}, AUC: {results['sbert']['auc_roc']}")
    print(f"TF-IDF -> F1: {results['tfidf']['f1_score']}, AUC: {results['tfidf']['auc_roc']}")
    print(f"Hybrid -> F1: {results['hybrid']['f1_score']}, AUC: {results['hybrid']['auc_roc']}")
    print(f"Optimal alpha: {results['optimal_alpha']}")