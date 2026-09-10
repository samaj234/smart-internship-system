import os
import csv
import spacy
from spacy.matcher import PhraseMatcher

from app.services.skill_synonyms import SKILL_SYNONYMS

ESCO_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'dataset', 'esco_skills_en.csv')

_nlp = spacy.load("en_core_web_sm")
_matcher = PhraseMatcher(_nlp.vocab, attr="LOWER")  # case-insensitive matching
_pattern_to_canonical = {}  # matched text (lowercased) -> canonical label
_loaded = False


def _load_esco_patterns():
    """
    Builds spaCy match patterns from two sources:

    1. ESCO's preferredLabel/altLabels/hiddenLabels — the original
       source. ESCO is broad and conceptual; it generally does NOT
       include specific software product names ("Microsoft Excel"),
       everyday soft-skill phrasings ("Teamwork", "Report Writing"),
       or niche/proprietary terms. Those are structurally impossible
       to extract from ESCO alone, no matter how clearly a CV states
       them.

    2. skill_synonyms.py's canonical skill names — added specifically
       to close that gap. That file already curates exactly the terms
       ESCO is missing (Microsoft Excel, Communication, Teamwork,
       Data Entry, etc.), but until now it was only used to compare
       two already-extracted skill strings, never to extract from raw
       text in the first place.

    Deliberately uses ONLY the synonym dict's canonical key names, not
    its full alias lists. Many aliases are short, ambiguous tokens
    ("cv" for computer vision, "ai" for artificial intelligence, "js",
    "go", "ps") that would cause false-positive extractions if matched
    against raw free text — e.g. "cv" would match constantly, since
    every résumé says "CV" to mean the document itself, not Computer
    Vision. Canonical names were deliberately written to be more
    complete/specific ("microsoft excel", not "excel") and carry much
    lower false-positive risk as extraction patterns. Short aliases
    remain fully available for post-extraction comparison via
    skills_match() — this restriction only applies to what's used for
    pulling terms out of raw text.

    ESCO matches take priority when both sources define the same
    literal string, so this only fills genuine gaps rather than
    overriding ESCO's own labeling.
    """
    global _loaded
    if _loaded:
        return

    patterns = []

    # --- Source 1: ESCO taxonomy ---
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

    esco_pattern_count = len(patterns)

    # --- Source 2: curated synonym-dictionary canonical names ---
    for canonical in SKILL_SYNONYMS:
        key = canonical.lower().strip()
        if key not in _pattern_to_canonical:  # ESCO's own labeling wins on overlap
            _pattern_to_canonical[key] = canonical
            patterns.append(_nlp.make_doc(canonical))

    _matcher.add("SKILL", patterns)
    _loaded = True
    print(f"Loaded {esco_pattern_count} ESCO skill patterns and "
          f"{len(patterns) - esco_pattern_count} synonym-dictionary patterns "
          f"for extraction ({len(patterns)} total)")


def extract_raw_skills(text: str) -> list:
    """
    Extracts skill mentions from text by matching against the ESCO
    taxonomy AND the curated skill-synonym dictionary's canonical
    names. Returns canonical labels — ESCO's preferredLabel for ESCO
    matches, or the synonym dictionary's canonical name for anything
    ESCO doesn't cover.
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