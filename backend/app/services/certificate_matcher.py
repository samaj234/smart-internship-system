import re

# Regex patterns for certifications mentioned inline (outside a dedicated
# section), e.g. "PMP certified" buried in a summary paragraph.
CERTIFICATE_PATTERNS = [
    r'\b(AWS|Azure|Google Cloud)\s+Certified[\w\s]*',
    r'\bCompTIA\s+\w+',
    r'\bCisco\s+(?:CCNA|CCNP|CCIE)\b',
    r'\bMicrosoft\s+Certified[\w\s]*',
    r'\bScrum\s+Master\b|\bCSM\b|\bPSM\b',
    r'\bPMP\b|\bProject Management Professional\b',
    r'\bCFA\b|\bChartered Financial Analyst\b',
    r'\bACCA\b|\bCPA\b|\bCertified Public Accountant\b',
    r'\bFRM\b|\bFinancial Risk Manager\b',
    r'\bCMA\b|\bCertified Management Accountant\b',
    r'\bSHRM-CP\b|\bSHRM-SCP\b',
    r'\bPHR\b|\bSPHR\b',
]

_compiled = [re.compile(p, re.IGNORECASE) for p in CERTIFICATE_PATTERNS]

# Common CV section header names — used to detect where the
# certifications section ENDS.
_SECTION_HEADERS = [
    'education', 'experience', 'work experience', 'employment',
    'projects', 'technical skills', 'skills', 'leadership',
    'leadership & activities', 'activities', 'references',
    'summary', 'objective', 'awards', 'publications',
    'interests', 'languages', 'volunteer', 'volunteering',
]


def _extract_from_section(text: str) -> list:
    """
    Finds a 'Certifications' section header and extracts each
    subsequent line as a certification entry, stopping at the next
    recognized section header. This catches plain course/cert
    titles that don't match any keyword pattern (e.g. 'Microsoft
    Excel Fundamentals', 'Introduction to Financial Markets').
    """
    lines = [l.strip() for l in text.split('\n')]
    found = []
    in_section = False

    for line in lines:
        stripped = line.strip(' -•\t')
        lower = stripped.lower().rstrip(':')

        if not in_section:
            if lower == 'certifications' or lower == 'certification' or lower == 'certificates':
                in_section = True
            continue

        if not stripped:
            continue

        # Stop if we've hit another section header
        if lower in _SECTION_HEADERS:
            break

        # Guard against runaway matches — a real cert line is short
        if len(stripped) > 100:
            break

        found.append(stripped)

    return found


def extract_certifications(text: str) -> list:
    if not text:
        return []

    found = set()

    # Section-based extraction (primary — catches real CV cert lists)
    for cert in _extract_from_section(text):
        found.add(cert)

    # Pattern-based extraction (secondary — catches inline mentions
    # outside a dedicated section)
    for pattern in _compiled:
        for match in pattern.finditer(text):
            found.add(match.group(0).strip())

    return list(found)