import re
import pandas as pd
import numpy as np
import os
from app.services.data_loader import load_recruitment_dataset

DATASET_PATH = os.path.join(
    os.path.dirname(__file__), '..', '..', 'dataset', 'recruitment_dataset.csv'
)
OUTPUT_PATH = os.path.join(
    os.path.dirname(__file__), '..', '..', 'dataset', 'labelled_dataset.csv'
)

# Known skills vocabulary — same list used by cv_parser.py
# expanded here to cover job description language too
SKILLS_VOCABULARY = [
    # Technology
    "python", "javascript", "react", "node.js", "flask", "django",
    "sql", "postgresql", "mysql", "mongodb", "html", "css",
    "machine learning", "data analysis", "tensorflow", "git",
    "docker", "aws", "linux", "typescript", "excel", "power bi",
    "java", "c++", "c#", "php", "ruby", "swift", "kotlin",
    "data science", "deep learning", "natural language processing",
    "computer vision", "neural network", "tableau", "spark",
    "hadoop", "kubernetes", "azure", "google cloud",

    # Business
    "project management", "strategic planning", "business analysis",
    "financial analysis", "budgeting", "risk management",
    "operations management", "supply chain", "procurement",
    "business development", "market research", "product management",
    "leadership", "team management", "negotiation",
    "stakeholder management", "consulting",

    # Marketing
    "digital marketing", "social media marketing", "content marketing",
    "seo", "sem", "email marketing", "brand management",
    "market analysis", "sales", "crm", "customer service",
    "public relations", "copywriting", "google analytics",

    # Finance
    "accounting", "auditing", "taxation", "financial reporting",
    "bookkeeping", "payroll", "financial modeling",
    "investment analysis", "banking", "cost accounting",
    "ifrs", "gaap", "variance analysis",

    # Engineering
    "civil engineering", "structural engineering",
    "mechanical engineering", "electrical engineering",
    "autocad", "solidworks", "matlab", "project planning",
    "quality control", "surveying", "construction management",

    # Healthcare
    "patient care", "clinical research", "nursing", "pharmacy",
    "public health", "epidemiology", "healthcare management",
    "first aid", "laboratory skills", "nutrition", "physiotherapy",

    # Soft skills
    "communication", "teamwork", "problem solving",
    "critical thinking", "time management", "adaptability",
    "attention to detail", "leadership", "creativity",
    "research", "data collection", "statistical analysis",

    # Health & Fitness specific (covers this dataset well)
    "injury prevention", "motivation", "health coaching",
    "strength training", "fitness", "personal training",
    "nutrition", "wellness", "rehabilitation",
    "exercise science", "anatomy", "physiology",

    # Additional health & fitness terms
"fitness coaching", "personal training", "exercise",
"wellness", "rehabilitation", "anatomy", "physiology",
"sports science", "biomechanics", "kinesiology",

# Additional business terms  
"market analysis", "financial modeling", "forecasting",
"data entry", "microsoft office", "presentation",
"report writing", "problem solving", "critical thinking",

# Additional tech terms
"software development", "web development", "mobile development",
"database management", "network administration", "cybersecurity",
"artificial intelligence", "cloud computing", "devops",
"agile", "scrum", "version control",

# Additional engineering terms
"cad", "3d modeling", "simulation", "testing",
"maintenance", "troubleshooting", "blueprint reading",

# Additional healthcare terms
"medical terminology", "electronic health records",
"infection control", "medication administration",
"health assessment", "disease prevention",

# Additional education terms
"curriculum development", "lesson planning", "teaching",
"student assessment", "classroom management", "tutoring",

# Additional law terms
"legal research", "contract drafting", "compliance",
"regulatory affairs", "due diligence", "legal writing",
]


def extract_skills_from_text(text: str) -> set:
    """
    Extracts skills from raw text by matching against the
    skills vocabulary. Case-insensitive substring matching.

    Returns a set of matched skill strings.
    """
    if not text or not isinstance(text, str):
        return set()

    text_lower = text.lower()
    found = set()
    for skill in SKILLS_VOCABULARY:
        if skill in text_lower:
            found.add(skill)
    return found


def jaccard_similarity(set_a: set, set_b: set) -> float:
    """
    Computes Jaccard similarity between two skill sets.
    Returns 0.0 if both sets are empty to avoid division by zero.

    J(A,B) = |A ∩ B| / |A ∪ B|
    """
    if not set_a and not set_b:
        return 0.0
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union)


def generate_skill_based_labels(
    df: pd.DataFrame,
    threshold: float = 0.15
) -> pd.DataFrame:
    """
    Generates ground truth labels based on skill overlap
    between student profile and job description.

    threshold=0.15 means at least 15% skill overlap is
    required to label a pair as a positive match (label=1).

    Why 0.15 specifically:
    - Too high (>0.3): most pairs become label=0, creating
      severe class imbalance
    - Too low (<0.1): almost everything becomes label=1,
      making discrimination impossible
    - 0.15 typically produces a balanced 40-60% split,
      confirmed by the distribution check below
    """
    print("Extracting skills from student profiles...")
    df['student_skills'] = df['student_text'].apply(extract_skills_from_text)

    print("Extracting skills from job descriptions...")
    df['job_skills'] = df['job_text'].apply(extract_skills_from_text)

    print("Computing Jaccard similarity scores...")
    df['jaccard_score'] = df.apply(
        lambda row: jaccard_similarity(row['student_skills'], row['job_skills']),
        axis=1
    )

    # Generate binary labels from Jaccard threshold
    df['jaccard_label'] = (df['jaccard_score'] >= threshold).astype(int)

    # Print distribution for transparency
    print(f"\nJaccard score statistics:")
    print(f"  Min:    {df['jaccard_score'].min():.4f}")
    print(f"  Max:    {df['jaccard_score'].max():.4f}")
    print(f"  Mean:   {df['jaccard_score'].mean():.4f}")
    print(f"  Median: {df['jaccard_score'].median():.4f}")

    print(f"\nLabel distribution at threshold={threshold}:")
    print(df['jaccard_label'].value_counts())
    print(f"Positive rate: {df['jaccard_label'].mean():.2%}")

    # Also print some examples so we can sanity-check the labels
    print("\n--- Sample POSITIVE matches (jaccard_label=1) ---")
    positives = df[df['jaccard_label'] == 1].head(3)
    for _, row in positives.iterrows():
        print(f"  Student skills: {list(row['student_skills'])[:5]}")
        print(f"  Job skills:     {list(row['job_skills'])[:5]}")
        print(f"  Jaccard score:  {row['jaccard_score']:.4f}")
        print()

    print("--- Sample NEGATIVE matches (jaccard_label=0) ---")
    negatives = df[df['jaccard_label'] == 0].head(3)
    for _, row in negatives.iterrows():
        print(f"  Student skills: {list(row['student_skills'])[:5]}")
        print(f"  Job skills:     {list(row['job_skills'])[:5]}")
        print(f"  Jaccard score:  {row['jaccard_score']:.4f}")
        print()

    return df


if __name__ == "__main__":
    print("Loading dataset...")
    df = load_recruitment_dataset(DATASET_PATH)

    df = generate_skill_based_labels(df, threshold=0.2)

    # Save labelled dataset
    df_save = df[['student_text', 'job_role', 'job_text',
                  'jaccard_score', 'jaccard_label']].copy()

    # Convert sets to lists for CSV serialization
    df['student_skills_list'] = df['student_skills'].apply(list)
    df['job_skills_list'] = df['job_skills'].apply(list)

    df_save.to_csv(OUTPUT_PATH, index=False)
    print(f"\nLabelled dataset saved to {OUTPUT_PATH}")
    print(f"Total pairs: {len(df_save)}")
    print(f"Positive pairs: {df_save['jaccard_label'].sum()}")
    print(f"Negative pairs: {(df_save['jaccard_label'] == 0).sum()}")