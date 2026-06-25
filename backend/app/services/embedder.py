from sentence_transformers import SentenceTransformer
import numpy as np

# Load model once at startup
model = SentenceTransformer('all-MiniLM-L6-v2')


def embed_text(text: str) -> list:
    """Convert text to SBERT embedding vector"""
    return model.encode(text).tolist()


def cosine_similarity(vec1: list, vec2: list) -> float:
    """Calculate cosine similarity between two vectors"""
    a = np.array(vec1)
    b = np.array(vec2)
    if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
        return 0.0
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))