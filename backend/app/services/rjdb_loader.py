import os
import json
import pandas as pd



RJDB_PATH = os.path.join(
    os.path.dirname(__file__), '..', '..', 'dataset', 'train.jsonl'
)


def load_rjdb_dataset(
    filepath: str = RJDB_PATH,
    max_records: int = None
) -> pd.DataFrame:
    """
    Loads the megagonlabs/rjdb dataset from JSONL format.
    Each line is a complete JSON record.
    """
    print(f"Loading RJDB dataset from {filepath}...")

    records = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    print(f"Raw records: {len(records)}")

    rows = []
    for record in records:
        job_text = record.get('Job-Description', '').strip()
        matched_resume = record.get('Resume-matched', '').strip()
        unmatched_resume = record.get('Resume-unmatched', '').strip()
        skills = record.get('Skills', [])
        filtered_info = record.get('Filtered-information', {})
        experiences = record.get('Experiences', [])

        if not job_text or not matched_resume or not unmatched_resume:
            continue

        # Positive pair
        rows.append({
            'job_text': job_text,
            'student_text': matched_resume,
            'label': 1,
            'required_skills': skills,
            'filtered_skills': filtered_info.get('Skills', []),
            'filtered_experience': filtered_info.get('Experience', ''),
            'experiences': experiences,
            'pair_type': 'matched'
        })

        # Negative pair
        rows.append({
            'job_text': job_text,
            'student_text': unmatched_resume,
            'label': 0,
            'required_skills': skills,
            'filtered_skills': filtered_info.get('Skills', []),
            'filtered_experience': filtered_info.get('Experience', ''),
            'experiences': experiences,
            'pair_type': 'unmatched'
        })

    df = pd.DataFrame(rows)

    if max_records:
        df = df.head(max_records)

    print(f"\nDataset shape: {df.shape}")
    print(f"\nLabel distribution:")
    print(df['label'].value_counts())
    print(f"Positive rate: {df['label'].mean():.2%}")

    print(f"\n--- Sample job text (first 300 chars) ---")
    print(df['job_text'].iloc[0][:300])
    print(f"\n--- Sample matched resume (first 300 chars) ---")
    print(df[df['label']==1]['student_text'].iloc[0][:300])
    print(f"\n--- Sample unmatched resume (first 300 chars) ---")
    print(df[df['label']==0]['student_text'].iloc[0][:300])
    print(f"\n--- Sample required skills ---")
    print(df['required_skills'].iloc[0])
    print(f"\n--- Sample filtered skills (what was removed) ---")
    print(df['filtered_skills'].iloc[0])

    return df

if __name__ == "__main__":
    print(f"Looking for file at: {os.path.abspath(RJDB_PATH)}")
    print(f"File exists: {os.path.exists(RJDB_PATH)}")
    df = load_rjdb_dataset()
    print(f"\nFinal dataset: {len(df)} pairs")
    print(f"Positive pairs: {df['label'].sum()}")
    print(f"Negative pairs: {(df['label']==0).sum()}")