import os
from pdfminer.high_level import extract_text
from docx import Document
import spacy


from app.services.skill_extractor import extract_raw_skills
from app.services.certificate_matcher import extract_certifications

nlp = spacy.load("en_core_web_sm")


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


def extract_email(text):
    """Extract email using spaCy and basic search"""
    import re
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    matches = re.findall(pattern, text)
    return matches[0] if matches else None


def extract_phone(text):
    """Extract phone number"""
    import re
    pattern = r'(\+?\d[\d\s\-().]{7,}\d)'
    matches = re.findall(pattern, text)
    return matches[0].strip() if matches else None


def extract_name(text):
    """Extract name using spaCy NER"""
    doc = nlp(text[:500])  # check first 500 chars
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            return ent.text
    return None


def parse_cv(filepath):
    """Main function — parse CV and return structured data"""
    text = extract_text_from_file(filepath)

    return {
        "raw_text": text,
        "name": extract_name(text),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "skills": extract_skills(text),
        "certifications": extract_certifications(text),
    }