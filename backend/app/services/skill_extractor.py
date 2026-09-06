import os
import csv
import spacy
from spacy.matcher import PhraseMatcher
from wordfreq import zipf_frequency

ESCO_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'dataset', 'esco_skills_en.csv')

_nlp = spacy.load("en_core_web_sm")
_matcher = PhraseMatcher(_nlp.vocab, attr="LOWER")  # case-insensitive matching
_pattern_to_canonical = {}  # matched text (lowercased) -> canonical ESCO label
_loaded = False

# zipf_frequency gives a log-scale estimate of how common a word is in
# everyday English (~7 = extremely common word like "the"; ~3 = rare).
# Above this threshold, a *single-word* ESCO term is common enough in
# ordinary usage that a bare phrase match against free text is more
# likely to be a coincidental English word than a genuine skill mention.
COMMON_WORD_ZIPF_THRESHOLD = 4.0

# Single-word terms that would otherwise be filtered by the frequency
# check above, but are common enough in tech/professional CVs and job
# postings that we want to keep matching them regardless.
SINGLE_WORD_ALLOWLIST = {
    'excel', 'sql', 'java', 'docker', 'photoshop', 'figma',
}

# Terms the frequency check alone doesn't catch (multi-word phrases,
# or single words that don't score as "common" but still cause false
# positives in practice) — grown from QA / user reports over time.
AMBIGUOUS_TERM_BLOCKLIST = {
    'dies', 'die', 'grammar', 'lead',
}


def _is_too_ambiguous(term: str) -> bool:
    key = term.lower()
    if key in AMBIGUOUS_TERM_BLOCKLIST:
        return True
    if key in SINGLE_WORD_ALLOWLIST:
        return False
    # Only single-token terms go through the frequency check — a
    # multi-word phrase like "lead police investigations" is specific
    # enough that ordinary-English-word overlap isn't a real risk.
    is_single_word = ' ' not in key
    if is_single_word and zipf_frequency(key, 'en') >= COMMON_WORD_ZIPF_THRESHOLD:
        return True
    return False


def _load_esco_patterns():
    """
    Builds spaCy match patterns directly from ESCO's preferredLabel,
    altLabels, and hiddenLabels columns. Every label/alias becomes a
    phrase pattern; matches are pre-mapped to their canonical label,
    so extraction and normalization happen in a single step.

    Terms flagged by `_is_too_ambiguous` (either a common English word
    with no tech-context override, or an explicitly blocklisted term)
    are excluded from matching entirely — see the module docstring
    comments above `AMBIGUOUS_TERM_BLOCKLIST` for why.
    """
    global _loaded
    if _loaded:
        return

    patterns = []
    skipped = []

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
                if _is_too_ambiguous(term):
                    skipped.append(term)
                    continue
                if key not in _pattern_to_canonical:  # keep first canonical mapping if duplicates
                    _pattern_to_canonical[key] = canonical
                    patterns.append(_nlp.make_doc(term))

    _matcher.add("ESCO_SKILL", patterns)
    _loaded = True
    print(f"Loaded {len(patterns)} ESCO skill patterns for extraction")
    print(f"Skipped {len(skipped)} ambiguous/common-word terms")


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