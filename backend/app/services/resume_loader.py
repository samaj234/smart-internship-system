import os
import ast
import pandas as pd
import numpy as np

RESUME_PATH = os.path.join(
    os.path.dirname(__file__), '..', '..', 'dataset', 'resume_data.csv'
)


def parse_skill_list(skill_str: str) -> list:
    """
    Parses skill strings stored as Python list literals
    e.g. "['Python', 'SQL', 'Machine Learning']" → ['Python', 'SQL', 'Machine Learning']
    Returns empty list if parsing fails.
    """
    if not skill_str or pd.isna(skill_str):
        return []
    try:
        parsed = ast.literal_eval(skill_str)
        if isinstance(parsed, list):
            return [str(s).strip() for s in parsed if s]
        return []
    except (ValueError, SyntaxError):
        return []


def build_student_text(row) -> str:
    """
    Combines available student fields into a single
    representative text string for matching.

    Priority: career_objective (natural language) +
              skills (structured list) +
              major_field_of_studies (domain context)
    """
    parts = []

    if pd.notna(row.get('career_objective')) and row['career_objective']:
        parts.append(str(row['career_objective']).strip())

    skills = parse_skill_list(row.get('skills', ''))
    if skills:
        parts.append("Skills: " + ", ".join(skills))

    major = row.get('major_field_of_studies', '')
    if pd.notna(major) and major:
        try:
            major_parsed = ast.literal_eval(str(major))
            if isinstance(major_parsed, list) and major_parsed:
                parts.append("Field: " + ", ".join(str(m) for m in major_parsed))
        except (ValueError, SyntaxError):
            parts.append("Field: " + str(major))

    return " ".join(parts).strip()


def build_job_text(row) -> str:
    """
    Combines job fields into a single representative text
    string for matching.

    Priority: responsibilities (natural language description) +
              skills_required (structured requirements) +
              job_position_name (role context)
    """
    parts = []

    job_title_col = '﻿job_position_name'
    title = row.get(job_title_col, '')
    if pd.notna(title) and title:
        parts.append(str(title).strip())

    responsibilities = row.get('responsibilities.1', '')
    if pd.notna(responsibilities) and responsibilities:
        parts.append(str(responsibilities).strip()[:400])

    skills_req = row.get('skills_required', '')
    if pd.notna(skills_req) and skills_req:
        # skills_required uses newline-separated format
        skills_list = [s.strip() for s in str(skills_req).split('\n') if s.strip()]
        if skills_list:
            parts.append("Required: " + ", ".join(skills_list))

    return " ".join(parts).strip()


def load_resume_dataset(
    filepath: str = RESUME_PATH,
    threshold: float = 0.70
) -> pd.DataFrame:
    """
    Loads the resume matching dataset and prepares it for evaluation.

    threshold=0.70 gives near-balanced labels:
    - matched_score >= 0.70 → label=1 (good match)
    - matched_score <  0.70 → label=0 (poor match)

    Returns a clean DataFrame with:
    - student_text: combined student profile text
    - job_text: combined job description text
    - student_skills: parsed list of student skills
    - job_skills: parsed list of required skills
    - matched_score: original continuous score
    - label: binary label from threshold
    - certification_skills: parsed certifications
    """
    print(f"Loading resume dataset from {filepath}...")
    df = pd.read_csv(filepath, encoding='utf-8-sig')
    print(f"Raw shape: {df.shape}")

    # Drop rows missing critical fields
    df = df.dropna(subset=['matched_score'])
    df = df[df['matched_score'] > 0]

    print("Building student text...")
    df['student_text'] = df.apply(build_student_text, axis=1)

    print("Building job text...")
    df['job_text'] = df.apply(build_job_text, axis=1)

    # Drop rows where text building produced empty strings
    df = df[df['student_text'].str.len() > 20]
    df = df[df['job_text'].str.len() > 20]

    # Parse structured fields
    df['student_skills'] = df['skills'].apply(parse_skill_list)
    df['job_skills'] = df['skills_required'].apply(
        lambda x: [s.strip() for s in str(x).split('\n') if s.strip()]
        if pd.notna(x) else []
    )
    df['certification_skills'] = df['certification_skills'].apply(parse_skill_list)

    # Generate binary label from threshold
    df['label'] = (df['matched_score'] >= threshold).astype(int)

    print(f"\nCleaned shape: {df.shape}")
    print(f"\nLabel distribution at threshold={threshold}:")
    print(df['label'].value_counts())
    print(f"Positive rate: {df['label'].mean():.2%}")

    print(f"\nScore statistics:")
    print(f"  Min:    {df['matched_score'].min():.4f}")
    print(f"  Max:    {df['matched_score'].max():.4f}")
    print(f"  Mean:   {df['matched_score'].mean():.4f}")
    print(f"  Median: {df['matched_score'].median():.4f}")

    print("\n--- Sample student text ---")
    print(df['student_text'].iloc[0][:300])
    print("\n--- Sample job text ---")
    print(df['job_text'].iloc[0][:300])
    print("\n--- Sample student skills ---")
    print(df['student_skills'].iloc[0][:8])
    print("\n--- Sample job skills ---")
    print(df['job_skills'].iloc[0][:8])

    return df[[
        'student_text', 'job_text',
        'student_skills', 'job_skills',
        'certification_skills',
        'matched_score', 'label'
    ]]


if __name__ == "__main__":
    df = load_resume_dataset()
    print(f"\nFinal dataset ready: {len(df)} pairs")