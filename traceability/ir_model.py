import math
from typing import List, Dict, Tuple, Any, Optional
from collections import Counter
from traceability.preprocessor import CodePreprocessor


class IRTraceabilityModel:
    """
    Classic Information Retrieval (IR) Baseline for Software Traceability.
    Implements TF-IDF Vector Space Model (VSM) and BM25 ranking.
    """

    def __init__(self, method: str = "tfidf", k1: float = 1.5, b: float = 0.75):
        self.method = method.lower()  # "tfidf" or "bm25"
        self.k1 = k1
        self.b = b

        self.corpus_docs: List[Dict[str, Any]] = []
        self.doc_tokens: List[List[str]] = []
        self.doc_lengths: List[int] = []
        self.avg_doc_len: float = 0.0
        self.vocab: Dict[str, int] = {}  # term -> index
        self.doc_freqs: Dict[str, int] = Counter()
        self.idf: Dict[str, float] = {}
        self.doc_vectors: List[Dict[str, float]] = []

    def fit(self, artifacts: List[Dict[str, Any]], text_field_getter=None):
        """
        Fits the IR model on a target corpus of code or test artifacts.
        artifacts: list of dicts with artifact data (e.g. CodeArtifact or TestArtifact)
        text_field_getter: callable to extract search content from artifact
        """
        self.corpus_docs = artifacts
        self.doc_tokens = []
        self.doc_lengths = []
        self.doc_freqs = Counter()

        for art in artifacts:
            if text_field_getter:
                raw_text = text_field_getter(art)
            else:
                # Default aggregation: name + signature + docstring + content
                parts = [
                    art.get("name", ""),
                    art.get("class_name", "") or "",
                    art.get("signature", "") or "",
                    art.get("docstring", "") or "",
                    art.get("code_content", "") or art.get("test_content", "") or "",
                    art.get("file_path", "")
                ]
                raw_text = " ".join(parts)

            tokens = CodePreprocessor.preprocess(raw_text)
            self.doc_tokens.append(tokens)
            self.doc_lengths.append(len(tokens))

            # Update document frequency
            unique_terms = set(tokens)
            for term in unique_terms:
                self.doc_freqs[term] += 1

        total_docs = len(self.corpus_docs)
        self.avg_doc_len = sum(self.doc_lengths) / total_docs if total_docs > 0 else 0.0

        # Calculate IDF
        self.idf = {}
        for term, df in self.doc_freqs.items():
            if self.method == "bm25":
                # Standard Robertson-Spärck Jones IDF for BM25
                self.idf[term] = math.log(1.0 + (total_docs - df + 0.5) / (df + 0.5))
            else:
                # Standard smoothed TF-IDF
                self.idf[term] = math.log((1.0 + total_docs) / (1.0 + df)) + 1.0

        # Compute TF-IDF document vectors if method is tfidf
        if self.method == "tfidf":
            self.doc_vectors = []
            for tokens in self.doc_tokens:
                vec = self._compute_tfidf_vector(tokens)
                self.doc_vectors.append(vec)

    def _compute_tfidf_vector(self, tokens: List[str]) -> Dict[str, float]:
        tf = Counter(tokens)
        total_terms = len(tokens) if tokens else 1
        vec = {}
        norm_sq = 0.0

        for term, count in tf.items():
            if term in self.idf:
                weight = (count / total_terms) * self.idf[term]
                vec[term] = weight
                norm_sq += weight * weight

        # Normalize vector
        norm = math.sqrt(norm_sq)
        if norm > 0:
            for term in vec:
                vec[term] /= norm

        return vec

    def query_similarity(self, query_text: str) -> List[Tuple[Dict[str, Any], float]]:
        """
        Computes similarity scores between the query (e.g. requirement description)
        and all documents in the fitted corpus.
        Returns: list of (artifact, similarity_score) sorted descending by score.
        """
        query_tokens = CodePreprocessor.preprocess(query_text)
        if not query_tokens or not self.corpus_docs:
            return [(doc, 0.0) for doc in self.corpus_docs]

        scores = []
        if self.method == "bm25":
            q_freq = Counter(query_tokens)
            for idx, (doc, d_tokens, d_len) in enumerate(zip(self.corpus_docs, self.doc_tokens, self.doc_lengths)):
                doc_term_counts = Counter(d_tokens)
                score = 0.0
                for term in q_freq:
                    if term in doc_term_counts and term in self.idf:
                        tf = doc_term_counts[term]
                        numerator = tf * (self.k1 + 1.0)
                        denominator = tf + self.k1 * (1.0 - self.b + self.b * (d_len / self.avg_doc_len if self.avg_doc_len > 0 else 1.0))
                        score += self.idf[term] * (numerator / denominator)
                scores.append((doc, score))

            # Normalize BM25 scores to [0, 1] range for threshold consistency
            max_score = max((s[1] for s in scores), default=1.0)
            if max_score > 0:
                scores = [(doc, s / max_score) for doc, s in scores]

        else:
            # TF-IDF Cosine Similarity
            q_vec = self._compute_tfidf_vector(query_tokens)
            for idx, (doc, d_vec) in enumerate(zip(self.corpus_docs, self.doc_vectors)):
                dot_product = 0.0
                for term, q_weight in q_vec.items():
                    if term in d_vec:
                        dot_product += q_weight * d_vec[term]
                scores.append((doc, dot_product))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores

    def predict_links(
        self,
        queries: List[Dict[str, Any]],
        threshold: float = 0.20,
        query_id_key: str = "req_identifier",
        target_id_key: str = "artifact_identifier",
        query_text_key: str = "description"
    ) -> List[Dict[str, Any]]:
        """
        Generates candidate traceability links above a given confidence threshold.
        """
        links = []
        for q in queries:
            q_id = q.get(query_id_key)
            q_text = f"{q.get('title', '')} {q.get(query_text_key, '')}"
            ranked = self.query_similarity(q_text)

            for target, score in ranked:
                if score >= threshold:
                    links.append({
                        "source": q_id,
                        "target": target.get(target_id_key) or target.get("test_identifier"),
                        "confidence": round(score, 4),
                        "method": f"IR_{self.method.upper()}",
                        "status": "CANDIDATE"
                    })
        return links
