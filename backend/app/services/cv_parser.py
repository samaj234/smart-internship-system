import os
import json
from pdfminer.high_level import extract_text
from docx import Document
import spacy

nlp = spacy.load("en_core_web_sm")

# Common skills to look for
SKILLS_DB = [
    # Technology & IT
    "python", "javascript", "react", "node.js", "flask", "django",
    "sql", "postgresql", "mysql", "mongodb", "html", "css",
    "machine learning", "data analysis", "tensorflow", "git",
    "docker", "aws", "linux", "typescript", "excel", "power bi",

    # Business & Management
    "project management", "strategic planning", "business analysis",
    "financial analysis", "budgeting", "forecasting", "risk management",
    "operations management", "supply chain", "logistics", "procurement",
    "business development", "market research", "product management",
    "leadership", "team management", "decision making", "negotiation",
    "stakeholder management", "change management", "consulting",

    # Marketing & Sales
    "digital marketing", "social media marketing", "content marketing",
    "seo", "sem", "email marketing", "brand management", "advertising",
    "market analysis", "sales", "crm", "customer service",
    "public relations", "copywriting", "campaign management",
    "google analytics", "facebook ads", "influencer marketing",

    # Finance & Accounting
    "accounting", "auditing", "taxation", "financial reporting",
    "bookkeeping", "payroll", "quickbooks", "financial modeling",
    "investment analysis", "portfolio management", "banking",
    "cost accounting", "accounts payable", "accounts receivable",
    "ifrs", "gaap", "internal controls", "variance analysis",

    # Engineering
    "civil engineering", "structural engineering", "mechanical engineering",
    "electrical engineering", "autocad", "solidworks", "matlab",
    "project planning", "site management", "quality control",
    "surveying", "construction management", "environmental engineering",
    "chemical engineering", "industrial engineering", "manufacturing",

    # Healthcare & Medicine
    "patient care", "clinical research", "nursing", "pharmacy",
    "public health", "epidemiology", "medical coding", "healthcare management",
    "first aid", "laboratory skills", "health education", "nutrition",
    "physiotherapy", "counseling", "medical writing",

    # Education & Training
    "teaching", "curriculum development", "lesson planning",
    "training and development", "e-learning", "instructional design",
    "classroom management", "student assessment", "tutoring",
    "educational research", "mentoring", "coaching",

    # Law & Compliance
    "legal research", "contract drafting", "compliance",
    "regulatory affairs", "corporate law", "litigation",
    "intellectual property", "legal writing", "due diligence",
    "employment law", "mediation", "arbitration",

    # Human Resources
    "recruitment", "talent acquisition", "onboarding", "hr management",
    "performance management", "employee relations", "compensation",
    "benefits administration", "workforce planning", "hr policies",
    "organizational development", "training", "succession planning",

    # Creative & Design
    "graphic design", "ui/ux design", "adobe photoshop", "illustrator",
    "video editing", "photography", "animation", "branding",
    "interior design", "fashion design", "creative writing",
    "content creation", "storytelling", "art direction",

    # Communication & Languages
    "communication", "public speaking", "presentation skills",
    "report writing", "technical writing", "translation",
    "french", "spanish", "arabic", "chinese", "german",
    "english", "journalism", "editing", "proofreading",

    # Research & Analysis
    "research", "data collection", "statistical analysis",
    "qualitative research", "quantitative research", "spss",
    "survey design", "literature review", "report writing",
    "critical thinking", "problem solving",

    # Soft Skills
    "teamwork", "time management", "adaptability", "creativity",
    "attention to detail", "multitasking", "conflict resolution",
    "emotional intelligence", "work ethic", "initiative",
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
    """Match skills from text against skills database"""
    text_lower = text.lower()
    found_skills = [skill for skill in SKILLS_DB if skill in text_lower]
    return list(set(found_skills))


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
    }