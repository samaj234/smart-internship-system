from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity as sklearn_cosine
import numpy as np
from app.services.preprocessing import preprocess_for_tfidf


class TFIDFMatcher:
    """
    TF-IDF based semantic matcher.

    Why a class instead of a function?
    The TfidfVectorizer must be fit on a corpus before it can
    transform individual documents — fitting builds the vocabulary
    and computes IDF weights across all seen documents. A class
    lets us fit once and reuse the fitted vectorizer across multiple
    calls, which is both more efficient and more correct (the IDF
    weights stay stable rather than changing each call).

    This mirrors how SBERT works — the model is loaded once at
    startup and reused — making the two methods architecturally
    equivalent and their comparison fairer.
    """

    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),   # unigrams + bigrams
            min_df=1,             # ignore terms appearing in fewer than 2 docs
            max_df=1.0,          # ignore terms appearing in more than 95% of docs
            sublinear_tf=True     # apply log normalization to term frequency
        )
        self._is_fitted = False

    def fit(self, texts: list[str]) -> None:
        """
        Fit the vectorizer on a corpus of texts.
        Call this once with your full dataset before calling
        transform or similarity methods.

        texts: list of raw strings (preprocessing happens inside)
        """
        cleaned = [preprocess_for_tfidf(t) for t in texts]
        self.vectorizer.fit(cleaned)
        self._is_fitted = True
        print(f"TF-IDF vocabulary size: {len(self.vectorizer.vocabulary_)}")

    def transform(self, texts: list[str]):
        """
        Convert a list of texts into TF-IDF vectors.
        Vectorizer must be fitted first.
        """
        if not self._is_fitted:
            raise RuntimeError("TFIDFMatcher must be fitted before transforming. Call fit() first.")
        cleaned = [preprocess_for_tfidf(t) for t in texts]
        return self.vectorizer.transform(cleaned)

    def similarity(self, text_a: str, text_b: str) -> float:
        """
        Compute cosine similarity between two individual texts.
        Both texts are transformed using the fitted vectorizer.
        Returns a float between 0 and 1.
        """
        if not self._is_fitted:
            raise RuntimeError("TFIDFMatcher must be fitted before computing similarity.")
        vectors = self.transform([text_a, text_b])
        score = sklearn_cosine(vectors[0], vectors[1])[0][0]
        return float(score)

    def batch_similarity(self, query_texts: list[str], corpus_texts: list[str]) -> np.ndarray:
        """
        Compute cosine similarity between each query text and
        every text in the corpus. Returns a 2D numpy array of
        shape (len(query_texts), len(corpus_texts)).

        This is the efficient batch version — used during evaluation
        to score all 10,000 pairs at once rather than one at a time.
        Sklearn's cosine_similarity is vectorized and handles this
        in a single matrix operation, which is orders of magnitude
        faster than looping.
        """
        if not self._is_fitted:
            raise RuntimeError("TFIDFMatcher must be fitted before computing similarity.")
        query_vectors = self.transform(query_texts)
        corpus_vectors = self.transform(corpus_texts)
        return sklearn_cosine(query_vectors, corpus_vectors)

    def get_top_terms(self, text: str, n: int = 10) -> list[str]:
        """
        Returns the top N TF-IDF weighted terms for a given text.
        Used by the XAI (explainability) layer to show which words
        most influenced a match score.

        For your presentation: this is what makes TF-IDF interpretable
        in a way that raw SBERT embeddings are not — you can literally
        show a user 'these 5 terms drove your match score.'
        """
        if not self._is_fitted:
            raise RuntimeError("TFIDFMatcher must be fitted before getting top terms.")
        cleaned = preprocess_for_tfidf(text)
        vector = self.vectorizer.transform([cleaned])
        feature_names = self.vectorizer.get_feature_names_out()
        scores = vector.toarray()[0]
        top_indices = scores.argsort()[::-1][:n]
        return [
            {"term": feature_names[i], "score": round(float(scores[i]), 4)}
            for i in top_indices
            if scores[i] > 0
        ]


# Module-level singleton — loaded once, reused across all requests
# (same pattern as SBERT's model singleton in embedder.py)
tfidf_matcher = TFIDFMatcher()