import os
import csv
import spacy
from spacy.matcher import PhraseMatcher

ESCO_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'dataset', 'esco_skills_en.csv')

_nlp = spacy.load("en_core_web_sm")
_matcher = PhraseMatcher(_nlp.vocab, attr="LOWER")  # case-insensitive matching
_pattern_to_canonical = {}  # matched text (lowercased) -> canonical ESCO label
_loaded = False


def _load_esco_patterns():
    """
    Builds spaCy match patterns directly from ESCO's preferredLabel,
    altLabels, and hiddenLabels columns. Every label/alias becomes a
    phrase pattern; matches are pre-mapped to their canonical label,
    so extraction and normalization happen in a single step.
    """
    global _loaded
    if _loaded:
        return

    patterns = []
    with open(ESCO_PATH, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('conceptType') != 'KnowledgeSkillCompetence':
                continue

            canonical = row['preferredLabel'].strip()
            if not canonical:
                continue

            all_terms = [canonical]
            for col in ('altLabels', 'hiddenLabels'):
                raw = row.get(col, '') or ''
                all_terms.extend(t.strip() for t in raw.split('\n') if t.strip())

            for term in all_terms:
                key = term.lower()
                if key not in _pattern_to_canonical:  # keep first canonical mapping if duplicates
                    _pattern_to_canonical[key] = canonical
                    patterns.append(_nlp.make_doc(term))

    _matcher.add("ESCO_SKILL", patterns)
    _loaded = True
    print(f"Loaded {len(patterns)} ESCO skill patterns for extraction")


def extract_raw_skills(text: str) -> list:
    """
    Extracts skill mentions from text by matching against the full
    ESCO vocabulary directly. Returns canonical ESCO labels — no
    separate normalization step needed since matches are already
    keyed to their preferredLabel.
    """
    _load_esco_patterns()

    if not text or not text.strip():
        return []

    doc = _nlp(text[:20000])  # cap length for performance on long CVs
    matches = _matcher(doc)

    found = set()
    for match_id, start, end in matches:
        span_text = doc[start:end].text.lower()
        canonical = _pattern_to_canonical.get(span_text)
        if canonical:
            found.add(canonical)

    return list(found)