import os
import re
import json
import time
import requests
import pandas as pd
from datetime import datetime

ADZUNA_APP_ID = os.environ.get('ADZUNA_APP_ID')
ADZUNA_APP_KEY = os.environ.get('ADZUNA_APP_KEY')
BASE_URL = "https://api.adzuna.com/v1/api/jobs"

OUTPUT_PATH = os.path.join(
    os.path.dirname(__file__), '..', '..', 'dataset', 'real_jobs.csv'
)

# Internship-relevant search queries
# Multiple queries give us broader coverage across domains
SEARCH_QUERIES = [
    "software engineering internship",
    "data science internship",
    "marketing internship",
    "finance internship",
    "mechanical engineering internship",
    "business analyst internship",
    "graphic design internship",
    "accounting internship",
    "healthcare internship",
    "project management internship",
    "cybersecurity internship",
    "machine learning internship",
    "web development internship",
    "human resources internship",
    "supply chain internship",
]


def clean_html(text: str) -> str:
    """
    Removes HTML tags and decodes common HTML entities.
    Job descriptions from APIs often contain raw HTML.
    """
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', ' ', text)
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&#39;', "'")
    text = text.replace('&quot;', '"')
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def extract_skills_from_description(description: str) -> list:
    """
    Extracts skill keywords from job description text.
    Same approach as generate_labels.py for consistency.
    """
    from app.services.generate_labels import (
        extract_skills_from_text, SKILLS_VOCABULARY
    )
    skills = extract_skills_from_text(description)
    return list(skills)


def fetch_jobs_from_adzuna(
    query: str,
    country: str = "gb",
    pages: int = 5,
    results_per_page: int = 20
) -> list:
    """
    Fetches job listings from Adzuna API for a given search query.

    country="gb" uses the UK endpoint — Adzuna has the most
    comprehensive international coverage there, and the job
    descriptions are in English. You can also use "us" for US jobs.

    pages=5, results_per_page=20 gives 100 jobs per query.
    With 15 queries that's up to 1,500 real job postings.

    We add a 0.5 second delay between requests to respect
    Adzuna's rate limits and avoid being blocked.
    """
    jobs = []

    for page in range(1, pages + 1):
        try:
            url = f"{BASE_URL}/{country}/search/{page}"
            params = {
                "app_id": ADZUNA_APP_ID,
                "app_key": ADZUNA_APP_KEY,
                "results_per_page": results_per_page,
                "what": query,
                "content-type": "application/json"
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code != 200:
                print(f"  Error {response.status_code} on page {page}: {response.text[:100]}")
                break

            data = response.json()
            results = data.get('results', [])

            if not results:
                break

            for job in results:
                description = clean_html(job.get('description', ''))
                title = job.get('title', '')
                company = job.get('company', {}).get('display_name', '')
                location = job.get('location', {}).get('display_name', '')
                salary_min = job.get('salary_min')
                salary_max = job.get('salary_max')
                created = job.get('created', '')
                redirect_url = job.get('redirect_url', '')

                if not description or len(description) < 50:
                    continue

                jobs.append({
                    "title": title,
                    "company": company,
                    "location": location,
                    "description": description,
                    "salary_min": salary_min,
                    "salary_max": salary_max,
                    "created": created,
                    "url": redirect_url,
                    "query": query,
                    "required_skills": extract_skills_from_description(description)
                })

            print(f"  Page {page}: fetched {len(results)} jobs (total so far: {len(jobs)})")
            time.sleep(0.5)

        except requests.exceptions.RequestException as e:
            print(f"  Request error on page {page}: {e}")
            break
        except Exception as e:
            print(f"  Unexpected error on page {page}: {e}")
            break

    return jobs


def fetch_all_jobs(pages_per_query: int = 5) -> pd.DataFrame:
    """
    Runs all search queries and combines results into
    a single DataFrame, deduplicating by description.
    """
    all_jobs = []

    for i, query in enumerate(SEARCH_QUERIES):
        print(f"\n[{i+1}/{len(SEARCH_QUERIES)}] Fetching: '{query}'")
        jobs = fetch_jobs_from_adzuna(query, pages=pages_per_query)
        all_jobs.extend(jobs)
        print(f"  Subtotal: {len(jobs)} jobs fetched")

    df = pd.DataFrame(all_jobs)

    if df.empty:
        print("No jobs fetched — check your API credentials")
        return df

    # Deduplicate by description (same job posted under different queries)
    before = len(df)
    df = df.drop_duplicates(subset=['description'])
    after = len(df)
    print(f"\nDeduplication: {before} → {after} jobs ({before - after} duplicates removed)")

    # Save to CSV
    df['required_skills'] = df['required_skills'].apply(json.dumps)
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"Saved {len(df)} real job listings to {OUTPUT_PATH}")

    return df


if __name__ == "__main__":
    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        print("ERROR: Missing Adzuna credentials.")
        print("Add ADZUNA_APP_ID and ADZUNA_APP_KEY to your .env file")
    else:
        print(f"Fetching jobs from Adzuna API...")
        print(f"Queries: {len(SEARCH_QUERIES)}")
        print(f"Max jobs: ~{len(SEARCH_QUERIES) * 5 * 20}")
        df = fetch_all_jobs(pages_per_query=5)
        print(f"\nFinal dataset: {len(df)} unique job listings")
        print(df[['title', 'company', 'location']].head(10))