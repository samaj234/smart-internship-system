import re
from app.services.cv_parser import extract_text_from_file, extract_skills

DURATION_PATTERN = re.compile(
    r'(\d+)\s*[-\u2013]?\s*(month|months|week|weeks)', re.IGNORECASE
)

STIPEND_PATTERN = re.compile(
    r'((?:GHS|USD|NGN|\$|£|€|₦)\s?[\d,]+(?:\.\d{1,2})?(?:\s?/\s?month|\s?per\s?month)?)',
    re.IGNORECASE
)

LOCATION_PATTERN = re.compile(
    r'(?:location|based in|located in)\s*[:\-]?\s*(.+)', re.IGNORECASE
)


def extract_title(text):
    """Best-effort only: a job description's first non-empty line is
    almost always its heading/title. If that line looks too long to be
    a title (i.e. the document opens with a paragraph, not a heading),
    give up rather than return something wrong."""
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        return line if len(line) <= 100 else None
    return None


def extract_duration(text):
    match = DURATION_PATTERN.search(text)
    if not match:
        return None
    return f"{match.group(1)} {match.group(2).lower()}"


def extract_stipend(text):
    match = STIPEND_PATTERN.search(text)
    return match.group(1).strip() if match else None


def extract_location(text):
    match = LOCATION_PATTERN.search(text)
    if not match:
        return None
    # Keep it to one line/sentence — the pattern's capture group is
    # greedy and would otherwise swallow the rest of the document.
    candidate = match.group(1).strip().split('\n')[0].split('.')[0]
    return candidate[:100] or None


def extract_description(text, title):
    """Everything after the title line, since the title itself
    shouldn't be duplicated into the description body."""
    lines = text.splitlines()
    if title and lines and lines[0].strip() == title:
        lines = lines[1:]
    description = "\n".join(lines).strip()
    return description or text.strip()


def parse_job_description(filepath):
    """
    Parses an uploaded job description file (PDF/DOCX) into structured
    internship posting fields, for employers who'd rather upload a
    document than fill the form by hand.

    Deliberately does NOT attempt to parse a deadline — free-text date
    phrasing in a real-world document ("applications close end of
    March", "rolling basis", "31/03/2026") is too unreliable to trust
    on a live posting. The employer fills that field in manually.

    Every returned field is a best-effort guess; the employer reviews
    and edits before actually posting, same as CV-upload pre-fill.
    """
    text = extract_text_from_file(filepath)
    title = extract_title(text)

    return {
        "title": title,
        "description": extract_description(text, title),
        "required_skills": extract_skills(text),
        "location": extract_location(text),
        "duration": extract_duration(text),
        "stipend": extract_stipend(text),
    }