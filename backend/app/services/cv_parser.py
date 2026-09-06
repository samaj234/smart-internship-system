import os
import re
from pdfminer.high_level import extract_text
from docx import Document
import spacy


from app.services.skill_extractor import extract_raw_skills
from app.services.certificate_matcher import extract_certifications

nlp = spacy.load("en_core_web_sm")

# How far into the document to look for contact info (name, email, phone).
# Résumés put this at the very top, so scoping the search here avoids
# accidentally matching date ranges, GPA fragments, or other employers'
# phone numbers that appear later in Experience/Education sections.
HEADER_WINDOW = 1000

SECTION_HEADERS = [
    'summary', 'objective', 'profile',
    'education', 'academic background',
    'experience', 'work experience', 'professional experience',
    'projects', 'technical skills', 'skills',
    'certifications', 'certificates',
    'leadership & activities', 'leadership and activities', 'activities',
    'references', 'awards', 'publications',
]

DEGREE_PATTERNS = [
    r"Bachelor(?:'?s)? (?:of|in) [A-Za-z&,/ ]+",
    r"B\.?Sc\.?\s*\(?[A-Za-z&,/ ]*\)?",
    r"B\.?A\.?\s*\(?[A-Za-z&,/ ]*\)?",
    r"B\.?Eng\.?\s*\(?[A-Za-z&,/ ]*\)?",
    r"Master(?:'?s)? (?:of|in) [A-Za-z&,/ ]+",
    r"M\.?Sc\.?\s*\(?[A-Za-z&,/ ]*\)?",
    r"M\.?B\.?A\.?",
    r"Ph\.?D\.?\s*\(?[A-Za-z&,/ ]*\)?",
    r"Diploma (?:in|of) [A-Za-z&,/ ]+",
    r"H\.?N\.?D\.?\s*\(?[A-Za-z&,/ ]*\)?",
]

INSTITUTION_KEYWORDS = [
    'university', 'college', 'institute', 'polytechnic',
    'school of', 'academy',
]


def extract_text_from_file(filepath):
    """Extract raw text from PDF or DOCX"""
    ext = os.path.splitext(filepath)[1].lower()

    if ext == ".pdf":
        return extract_text(filepath)
    elif ext == ".docx":
        doc = Document(filepath)
        return "\n".join([para.text for para in doc.paragraphs])
    else:
        raise ValueError("Unsupported file type. Use PDF or DOCX.")


def extract_skills(text):
    """Extract skills by matching directly against the ESCO taxonomy."""
    return extract_raw_skills(text)


def extract_certifications(text):
    """Extract recognized certifications (AWS, PMP, Scrum Master, etc.)"""
    from app.services.certificate_matcher import extract_certifications as _extract
    return _extract(text)


def _plausible_phone_candidates(segment):
    """Filters loose regex matches down to ones that actually look like
    phone numbers (7-15 digits total). This alone doesn't catch every
    false positive — a short date range can still slip through — which
    is why extract_phone() also scopes to the document header first."""
    pattern = r'(\+?\d[\d\s\-().]{7,}\d)'
    candidates = re.findall(pattern, segment)
    return [c for c in candidates if 7 <= sum(ch.isdigit() for ch in c) <= 15]


def extract_email(text):
    """Extract email, preferring the document header (contact info is
    always near the top) over a full-document search."""
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    header_matches = re.findall(pattern, text[:HEADER_WINDOW])
    if header_matches:
        return header_matches[0]
    full_matches = re.findall(pattern, text)
    return full_matches[0] if full_matches else None


def extract_phone(text):
    """Extract phone number, preferring the document header over a
    full-document search — see _plausible_phone_candidates for why the
    header-first search matters more than the digit-count filter alone."""
    header_matches = _plausible_phone_candidates(text[:HEADER_WINDOW])
    if header_matches:
        return header_matches[0].strip()
    full_matches = _plausible_phone_candidates(text)
    return full_matches[0].strip() if full_matches else None


def extract_name(text):
    """Extract name using spaCy NER"""
    doc = nlp(text[:500])  # check first 500 chars
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            return ent.text
    return None


def _split_sections(text):
    """Splits résumé text into named sections based on common headers
    (EDUCATION, EXPERIENCE, etc.), matched case-insensitively as a
    standalone line. Scoping GPA/degree/university extraction to just
    the education section — instead of the whole document — is what
    prevents an unrelated number or org name elsewhere in the CV from
    being picked up by mistake.

    Returns a dict of {section_name: body_text}; text before the first
    recognized header lands under 'header'.
    """
    header_pattern = re.compile(
        r'^\s*(' + '|'.join(re.escape(h) for h in SECTION_HEADERS) + r')\s*:?\s*$',
        re.IGNORECASE
    )

    sections = {}
    current = 'header'
    buffer = []

    for line in text.splitlines():
        stripped = line.strip()
        match = header_pattern.match(stripped)
        if match:
            sections[current] = '\n'.join(buffer)
            current = stripped.lower().rstrip(':').strip()
            buffer = []
        else:
            buffer.append(line)

    sections[current] = '\n'.join(buffer)
    return sections


def _get_education_text(sections):
    """Education content may land under slightly different header
    spellings — combine anything matching rather than relying on one
    exact key."""
    parts = [
        body for name, body in sections.items()
        if 'education' in name or 'academic' in name
    ]
    return '\n'.join(parts) if parts else sections.get('header', '')


def extract_gpa(education_text):
    """Matches common formats: 'GPA: 3.11/4.00', 'GPA 3.11 out of 4.0'."""
    pattern = re.compile(
        r'GPA[:\s]*([0-4](?:\.\d{1,2})?)\s*(?:/|out of)?\s*(?:[0-4](?:\.\d{1,2})?)?',
        re.IGNORECASE
    )
    match = pattern.search(education_text)
    if not match:
        return None
    try:
        return float(match.group(1))
    except (TypeError, ValueError):
        return None


def extract_degree(education_text):
    """Matches the first recognizable degree title in the education
    section (Bachelor's, Master's, HND, etc.)."""
    for pattern in DEGREE_PATTERNS:
        match = re.search(pattern, education_text, re.IGNORECASE)
        if match:
            return match.group(0).strip(' ,.-')
    return None


def extract_university(education_text):
    """Prefers a spaCy ORG entity found within the (already scoped)
    education section — much lower false-positive risk here than
    running NER on the whole document. Falls back to the first line
    containing an institution keyword if NER finds nothing."""
    if not education_text.strip():
        return None

    doc = nlp(education_text[:1000])
    for ent in doc.ents:
        if ent.label_ == 'ORG':
            return ent.text.strip()

    for line in education_text.splitlines():
        lower = line.lower()
        if any(keyword in lower for keyword in INSTITUTION_KEYWORDS):
            return line.strip()

    return None


def parse_cv(filepath):
    """Main function — parse CV and return structured data"""
    text = extract_text_from_file(filepath)
    sections = _split_sections(text)
    education_text = _get_education_text(sections)

    return {
        "raw_text": text,
        "name": extract_name(text),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "skills": extract_skills(text),
        "certifications": extract_certifications(text),
        "gpa": extract_gpa(education_text),
        "degree": extract_degree(education_text),
        "university": extract_university(education_text),
    }