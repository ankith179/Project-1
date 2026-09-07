"""
rag/vector_store.py
-------------------
FAISS-backed vector store for VIGILANT semantic retrieval.
Falls back to pure-numpy brute-force cosine similarity if faiss
is unavailable (e.g. no native lib on the platform).
"""
from __future__ import annotations

import os
import json
import numpy as np
from typing import List, Dict, Any, Tuple, Optional


class FAISSVectorStore:
    """
    Stores artifact embeddings and supports fast nearest-neighbour search.

    Uses faiss.IndexFlatIP (inner-product on L2-normalised vectors = cosine).
    Falls back to numpy matrix-multiply if faiss is not installed.
    """

    def __init__(self, dim: int = 384):
        self.dim = dim
        self._index = None          # faiss index
        self._matrix: Optional[np.ndarray] = None   # numpy fallback
        self._artifacts: List[Dict[str, Any]] = []
        self._use_faiss: bool = False
        self._try_init_faiss()

    def _try_init_faiss(self):
        try:
            import faiss
            self._faiss = faiss
            self._use_faiss = True
        except ImportError:
            self._use_faiss = False

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def build(self, artifacts: List[Dict[str, Any]], embeddings: np.ndarray):
        """
        Index a list of artifact dicts alongside their embeddings.

        Parameters
        ----------
        artifacts : list of dicts  (same order as embeddings rows)
        embeddings: np.ndarray shape (N, dim), float32, L2-normalised
        """
        if len(artifacts) == 0:
            self._artifacts = []
            self._matrix = np.zeros((0, self.dim), dtype=np.float32)
            return

        self._artifacts = list(artifacts)
        vecs = embeddings.astype(np.float32)

        if self._use_faiss:
            self._index = self._faiss.IndexFlatIP(self.dim)
            self._faiss.normalize_L2(vecs)
            self._index.add(vecs)
        else:
            # Numpy fallback — store the matrix
            norms = np.linalg.norm(vecs, axis=1, keepdims=True)
            norms = np.where(norms == 0, 1.0, norms)
            self._matrix = vecs / norms

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 10
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Returns the top-K most similar artifacts with their cosine scores.
        Returns: list of (artifact_dict, score) sorted descending.
        """
        if not self._artifacts:
            return []

        q = query_embedding.astype(np.float32).reshape(1, -1)
        norm = np.linalg.norm(q)
        if norm > 0:
            q = q / norm

        top_k = min(top_k, len(self._artifacts))

        if self._use_faiss and self._index is not None:
            scores, indices = self._index.search(q, top_k)
            results = []
            for idx, score in zip(indices[0], scores[0]):
                if idx >= 0:
                    results.append((self._artifacts[idx], float(score)))
            return results
        else:
            # Numpy brute-force inner product
            sims = (self._matrix @ q.T).flatten()
            top_indices = np.argsort(sims)[::-1][:top_k]
            return [(self._artifacts[i], float(sims[i])) for i in top_indices]

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, directory: str):
        """Save index + artifact metadata to directory."""
        os.makedirs(directory, exist_ok=True)
        # Save artifact metadata
        with open(os.path.join(directory, "artifacts.json"), "w", encoding="utf-8") as f:
            json.dump(self._artifacts, f, default=str, indent=2)
        # Save matrix (numpy fallback always saved; faiss index also saved if available)
        if self._matrix is not None:
            np.save(os.path.join(directory, "embeddings.npy"), self._matrix)
        if self._use_faiss and self._index is not None:
            self._faiss.write_index(self._index, os.path.join(directory, "faiss.index"))

    def load(self, directory: str):
        """Load index + artifact metadata from directory."""
        artifacts_path = os.path.join(directory, "artifacts.json")
        if not os.path.exists(artifacts_path):
            raise FileNotFoundError(f"No saved store at {directory}")
        with open(artifacts_path, "r", encoding="utf-8") as f:
            self._artifacts = json.load(f)

        emb_path = os.path.join(directory, "embeddings.npy")
        if os.path.exists(emb_path):
            self._matrix = np.load(emb_path)

        faiss_path = os.path.join(directory, "faiss.index")
        if self._use_faiss and os.path.exists(faiss_path):
            self._index = self._faiss.read_index(faiss_path)

    def __len__(self):
        return len(self._artifacts)
