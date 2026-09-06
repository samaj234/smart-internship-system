import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)
nltk.download('omw-1.4', quiet=True)
nltk.download('punkt', quiet=True)

_stop_words = set(stopwords.words('english'))
_lemmatizer = WordNetLemmatizer()


def preprocess_for_tfidf(text: str) -> str:
    """
    Full preprocessing pipeline for TF-IDF:
    - lowercase 
    - strip punctuation and digits
    - remove stopwords
    - lemmatize

    TF-IDF is a bag-of-words method — it has no concept of word
    order or context, so stopwords and inflected word forms add
    noise rather than signal. Removing them sharpens the vocabulary
    so TF-IDF focuses on meaningful, distinctive terms.
    """
    if not text or not isinstance(text, str):
        return ""

    text = text.lower()
    text = re.sub(r'[^a-z\s]', ' ', text)
    tokens = text.split()
    tokens = [
        _lemmatizer.lemmatize(tok)
        for tok in tokens
        if tok not in _stop_words and len(tok) > 2
    ]
    return " ".join(tokens)


def preprocess_for_sbert(text: str) -> str:
    """
    Minimal preprocessing for SBERT:
    - normalize whitespace
    - strip leading/trailing spaces
    - truncate to 512 characters (SBERT's practical input limit)

    SBERT is a transformer trained on natural language sentences.
    It uses word order, grammar, and context to build meaning —
    stopwords like 'not', 'but', 'without' are semantically important
    to it. Full preprocessing would actively hurt SBERT's performance
    by destroying the contextual cues it was trained to use.
    """
    if not text or not isinstance(text, str):
        return ""

    text = re.sub(r'\s+', ' ', text).strip()
    return text[:512]


def build_combined_text(skills: list, raw_text: str = "", role: str = "") -> str:
    """
    Builds a single representative text string from structured
    student/job fields, used as input to both matching methods.

    Skills are repeated twice to give them higher weight — both
    TF-IDF (via term frequency) and SBERT (via token presence)
    will treat repeated terms as more salient. This is a simple
    but effective way to bias the match toward skill overlap
    without needing a separate weighting mechanism.
    """
    parts = []
    if role:
        parts.append(role)
    if skills:
        skill_str = " ".join(skills)
        parts.append(skill_str)
        parts.append(skill_str)  # intentional repeat for emphasis
    if raw_text:
        parts.append(raw_text[:300])  # cap raw text to avoid diluting skills
    return " ".join(parts)

def build_sbert_text(skills: list, raw_text: str = "", role: str = "") -> str:
    """
    Builds natural-sentence input for SBERT, without the skill
    repetition used in build_combined_text() for TF-IDF weighting.
    SBERT works on sentence structure and context, not term
    frequency — repeating keywords doesn't help it and may dilute
    the semantic signal from real sentences. Use this for SBERT
    embeddings; keep build_combined_text() for TF-IDF.
    """
    parts = []
    if role:
        parts.append(role)
    if raw_text:
        parts.append(raw_text[:500])
    if skills:
        parts.append("Skills: " + ", ".join(skills))
    return " ".join(parts)