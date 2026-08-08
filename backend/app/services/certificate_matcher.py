# app/services/certificate_matcher.py
import re

# Curated — extend as you see real CVs come through
CERTIFICATE_PATTERNS = [
    r'\b(AWS|Azure|Google Cloud)\s+Certified[\w\s]*',
    r'\bPMP\b|\bProject Management Professional\b',
    r'\bCompTIA\s+\w+',
    r'\bCisco\s+(?:CCNA|CCNP|CCIE)\b',
    r'\bMicrosoft\s+Certified[\w\s]*',
    r'\bGoogle\s+(?:Data Analytics|IT Support|UX Design)\s+Certificate\b',
    r'\bScrum\s+Master\b|\bCSM\b|\bPSM\b',
    r'\bCFA\b|\bChartered Financial Analyst\b',
    r'\bACCA\b|\bCPA\b',
]

_compiled = [re.compile(p, re.IGNORECASE) for p in CERTIFICATE_PATTERNS]


def extract_certifications(text: str) -> list:
    if not text:
        return []
    found = set()
    for pattern in _compiled:
        for match in pattern.finditer(text):
            found.add(match.group(0).strip())
    return list(found)