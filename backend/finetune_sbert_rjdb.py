"""
Fine-tune a sentence-transformers bi-encoder for resume <-> job-description
matching on RJDB (megagonlabs/rjdb), using the dataset's native hard-negative
structure: each row is (job_description, matched_resume, unmatched_resume),
where unmatched_resume is the matched_resume with skills deliberately removed.

Usage:
    python finetune_sbert_rjdb.py \
        --data_path rjdb_triples.jsonl \
        --base_model sentence-transformers/multi-qa-mpnet-base-dot-v1 \
        --output_dir ./sbert-rjdb-finetuned \
        --epochs 4

Expected input format (adjust `load_triples` if your loader differs):
    One JSON object per line, with keys: "job_description", "matched_resume",
    "unmatched_resume". If you already have RJDB loaded some other way
    (e.g. as a pandas DataFrame from your existing eval script), just skip
    load_triples() and pass a list of (job, pos, neg) string tuples into
    build_examples() directly.
"""

import argparse
import json
import random
from dataclasses import dataclass

import numpy as np
from sklearn.metrics import roc_auc_score, precision_recall_fscore_support
from sentence_transformers import (
    SentenceTransformer,
    InputExample,
    losses,
    util,
)
from torch.utils.data import DataLoader


# ── Data loading ──────────────────────────────────────────────────────────

def load_triples(path):
    """Load (job_description, matched_resume, unmatched_resume) triples.

    Adjust this to match however you currently load RJDB in your eval
    script — this assumes one JSON object per line with the three fields
    named below.
    """
    triples = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            triples.append((
                row["Job-Description"],
                row["Resume-matched"],
                row["Resume-unmatched"],
            ))
    return triples


def split_triples(triples, val_frac=0.1, test_frac=0.1, seed=42):
    """80/10/10 split. Split BEFORE building pairs so no job or resume
    text leaks across splits."""
    rng = random.Random(seed)
    shuffled = triples[:]
    rng.shuffle(shuffled)

    n = len(shuffled)
    n_val = int(n * val_frac)
    n_test = int(n * test_frac)

    val = shuffled[:n_val]
    test = shuffled[n_val:n_val + n_test]
    train = shuffled[n_val + n_test:]
    return train, val, test


# ── Building training examples ───────────────────────────────────────────

def build_train_examples(triples):
    """MultipleNegativesRankingLoss expects InputExample(texts=[anchor,
    positive, hard_negative]). It ALSO uses every other positive in the
    batch as an additional in-batch negative, so this gets both the
    dataset's deliberate hard negatives and free extra negatives."""
    examples = []
    for job, matched, unmatched in triples:
        examples.append(InputExample(texts=[job, matched, unmatched]))
    return examples


def build_eval_pairs(triples):
    """Flatten triples into labeled (job, resume, label) pairs for
    evaluation — mirrors the binary-pair format your original eval used."""
    jobs, resumes, labels = [], [], []
    for job, matched, unmatched in triples:
        jobs.append(job)
        resumes.append(matched)
        labels.append(1)

        jobs.append(job)
        resumes.append(unmatched)
        labels.append(0)
    return jobs, resumes, np.array(labels)


# ── Evaluation (mirrors your existing SBERT/TF-IDF/hybrid eval) ─────────

@dataclass
class EvalResult:
    precision: float
    recall: float
    f1: float
    auc_roc: float
    threshold: float


def evaluate(model, jobs, resumes, labels, threshold=None, batch_size=64):
    job_emb = model.encode(jobs, batch_size=batch_size, convert_to_numpy=True,
                            show_progress_bar=True, normalize_embeddings=True)
    resume_emb = model.encode(resumes, batch_size=batch_size, convert_to_numpy=True,
                               show_progress_bar=True, normalize_embeddings=True)

    scores = np.sum(job_emb * resume_emb, axis=1)  # cosine sim, embeddings are normalized
    auc = roc_auc_score(labels, scores)

    if threshold is None:
        # Pick the threshold that maximizes F1 on THIS split only.
        # Call this once on val, then reuse that threshold on test.
        thresholds = np.linspace(scores.min(), scores.max(), 200)
        best_f1, best_t = -1, thresholds[0]
        for t in thresholds:
            preds = (scores >= t).astype(int)
            _, _, f1, _ = precision_recall_fscore_support(
                labels, preds, average="binary", zero_division=0
            )
            if f1 > best_f1:
                best_f1, best_t = f1, t
        threshold = best_t

    preds = (scores >= threshold).astype(int)
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, preds, average="binary", zero_division=0
    )

    return EvalResult(precision, recall, f1, auc, threshold)


# ── Main ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_path", required=True,
                         help="Path to RJDB triples (jsonl: job_description, matched_resume, unmatched_resume)")
    parser.add_argument("--base_model", default="sentence-transformers/all-mpnet-base-v2",
                         help="Starting checkpoint. Use all-MiniLM-L6-v2 for a faster first pass.")
    parser.add_argument("--output_dir", default="./sbert-rjdb-finetuned")
    parser.add_argument("--epochs", type=int, default=4)
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--warmup_ratio", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    random.seed(args.seed)
    np.random.seed(args.seed)

    print(f"Loading triples from {args.data_path} ...")
    triples = load_triples(args.data_path)
    print(f"Loaded {len(triples)} triples")

    train_triples, val_triples, test_triples = split_triples(triples)
    print(f"Split: train={len(train_triples)} val={len(val_triples)} test={len(test_triples)}")

    print(f"Loading base model: {args.base_model}")
    model = SentenceTransformer(args.base_model)

    # --- Baseline (pre-fine-tune) eval, for a clean before/after comparison ---
    val_jobs, val_resumes, val_labels = build_eval_pairs(val_triples)
    test_jobs, test_resumes, test_labels = build_eval_pairs(test_triples)

    print("\n=== BASELINE (before fine-tuning) ===")
    baseline_val = evaluate(model, val_jobs, val_resumes, val_labels)
    baseline_test = evaluate(model, test_jobs, test_resumes, test_labels,
                              threshold=baseline_val.threshold)
    print(f"val : {baseline_val}")
    print(f"test: {baseline_test}")

    # --- Fine-tune ---
    train_examples = build_train_examples(train_triples)
    train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=args.batch_size)
    train_loss = losses.MultipleNegativesRankingLoss(model)

    warmup_steps = int(len(train_dataloader) * args.epochs * args.warmup_ratio)

    print(f"\nFine-tuning for {args.epochs} epochs "
          f"({len(train_dataloader)} steps/epoch, {warmup_steps} warmup steps)...")

    model.fit(
        train_objectives=[(train_dataloader, train_loss)],
        epochs=args.epochs,
        warmup_steps=warmup_steps,
        output_path=args.output_dir,
        show_progress_bar=True,
        save_best_model=False,  # we evaluate/save manually below
    )

    # --- Post fine-tune eval ---
    print("\n=== AFTER FINE-TUNING ===")
    finetuned_val = evaluate(model, val_jobs, val_resumes, val_labels)
    finetuned_test = evaluate(model, test_jobs, test_resumes, test_labels,
                               threshold=finetuned_val.threshold)
    print(f"val : {finetuned_val}")
    print(f"test: {finetuned_test}")

    model.save(args.output_dir)
    print(f"\nSaved fine-tuned model to {args.output_dir}")

    summary = {
        "base_model": args.base_model,
        "n_train_triples": len(train_triples),
        "n_val_triples": len(val_triples),
        "n_test_triples": len(test_triples),
        "baseline": {
            "val": vars(baseline_val),
            "test": vars(baseline_test),
        },
        "finetuned": {
            "val": vars(finetuned_val),
            "test": vars(finetuned_test),
        },
    }
    with open(f"{args.output_dir}/eval_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Wrote comparison summary to {args.output_dir}/eval_summary.json")


if __name__ == "__main__":
    main()