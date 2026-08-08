import pandas as pd
import os


def load_recruitment_dataset(filepath: str) -> pd.DataFrame:
    """
    Loads and cleans the recruitment dataset.
    Drops demographic columns irrelevant to matching,
    removes nulls, and standardizes column names.
    """
    df = pd.read_csv(filepath)

    print("Raw columns:", df.columns.tolist())
    print("Shape:", df.shape)
    print("\nFirst row sample:")
    print(df.iloc[0])
    print("\nLabel distribution:")
    print(df['Best Match'].value_counts())
    print("\nNull counts:")
    print(df.isnull().sum())

    # Drop demographic columns — irrelevant to matching task
    cols_to_drop = ['Job Applicant Name', 'Age', 'Gender', 'Race', 'Ethnicity']
    df = df.drop(columns=[c for c in cols_to_drop if c in df.columns])

    # Standardize column names
    df = df.rename(columns={
        'Resume': 'student_text',
        'Job Roles': 'job_role',
        'Job Description': 'job_text',
        'Best Match': 'label'
    })

    # Drop rows with missing text or label
    df = df.dropna(subset=['student_text', 'job_text', 'label'])

    # Ensure label is integer
    df['label'] = df['label'].astype(int)

    print("\nCleaned shape:", df.shape)
    print("Cleaned columns:", df.columns.tolist())

    return df


if __name__ == "__main__":
    # Run this directly to inspect the dataset
    # From backend/ folder: python -m app.services.data_loader
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    dataset_path = os.path.join(base_dir, 'dataset', 'recruitment_dataset.csv')
    df = load_recruitment_dataset(dataset_path)

    print("\n--- Sample student text ---")
    print(df['student_text'].iloc[0][:300])
    print("\n--- Sample job text ---")
    print(df['job_text'].iloc[0][:300])
    print("\n--- Sample job role ---")
    print(df['job_role'].iloc[0])