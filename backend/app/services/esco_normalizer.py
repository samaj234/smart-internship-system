# app/services/esco_normalizer.py
import os
import csv
import numpy as np
from app.services.embedder import model as sbert_model, cosine_similarity

ESCO_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'dataset', 'esco_skills_en.csv')

_alias_to_esco = {}      # lowercased alias -> (preferredLabel, conceptUri)
_esco_labels = []        # list of preferredLabels, for embedding fallback
_esco_embeddings = None  # precomputed once


def _load_esco():
    global _esco_embeddings
    if _alias_to_esco:
        return

    with open(ESCO_PATH, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Skip occupations — we only want skills/competences/knowledge
            if row.get('conceptType') != 'KnowledgeSkillCompetence':
                continue

            label = row['preferredLabel'].strip()
            uri = row['conceptUri'].strip()
            if not label:
                continue

            _alias_to_esco[label.lower()] = (label, uri)
            _esco_labels.append(label)

            # altLabels AND hiddenLabels both feed the alias map
            for col in ('altLabels', 'hiddenLabels'):
                raw = row.get(col, '') or ''
                for alt in raw.split('\n'):
                    alt = alt.strip()
                    if alt:
                        _alias_to_esco[alt.lower()] = (label, uri)

    print(f"Loaded ESCO taxonomy: {len(_esco_labels)} skills, {len(_alias_to_esco)} labels+aliases")
    _esco_embeddings = sbert_model.encode(_esco_labels, batch_size=64, show_progress_bar=True)


def normalize_skill(raw_skill: str, fuzzy_threshold: float = 0.72) -> dict:
    """
    Maps a raw extracted skill string to its canonical ESCO label.
    1. Exact alias match (fast path, covers most cases)
    2. SBERT embedding similarity fallback for near-misses SkillNER
       phrased slightly differently than ESCO's vocabulary
    Returns {"label": str, "uri": str|None, "matched": bool}
    """
    _load_esco()
    key = raw_skill.lower().strip()

    if key in _alias_to_esco:
        label, uri = _alias_to_esco[key]
        return {"label": label, "uri": uri, "matched": True}

    # Fuzzy fallback via SBERT
    query_emb = sbert_model.encode(key)
    sims = [cosine_similarity(query_emb.tolist(), e.tolist()) for e in _esco_embeddings]
    best_idx = int(np.argmax(sims))
    if sims[best_idx] >= fuzzy_threshold:
        label = _esco_labels[best_idx]
        _, uri = _alias_to_esco[label.lower()]
        return {"label": label, "uri": uri, "matched": True}

    # No confident ESCO match — keep the raw term rather than dropping it
    return {"label": raw_skill.strip(), "uri": None, "matched": False}


def normalize_skills(raw_skills: list) -> list:
    """Normalize a list of raw skill strings, deduplicating by canonical label."""
    seen = {}
    for skill in raw_skills:
        result = normalize_skill(skill)
        seen[result["label"].lower()] = result["label"]
    return list(seen.values())