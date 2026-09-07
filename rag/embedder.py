"""
rag/embedder.py
---------------
Sentence-Transformer embedding engine for VIGILANT RAG layer.
Uses 'all-MiniLM-L6-v2' — fast, local, no API key required.
Produces 384-dim L2-normalised embeddings for cosine similarity.
"""
from __future__ import annotations

import os
import numpy as np
from typing import List, Dict, Any, Optional


class ArtifactEmbedder:
    """
    Wraps sentence-transformers for artifact text embedding.
    Model is loaded lazily on first call and cached for the session.
    Falls back gracefully if sentence-transformers is unavailable.
    """

    MODEL_NAME = "all-MiniLM-L6-v2"

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or self.MODEL_NAME
        self._model = None
        self._dim: int = 384  # default for MiniLM-L6-v2

    def _load_model(self):
        if self._model is not None:
            return
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
            self._dim = self._model.get_sentence_embedding_dimension()
        except ImportError:
            self._model = None  # fallback mode

    def embed_text(self, text: str) -> np.ndarray:
        """Embed a single text string → L2-normalised float32 vector."""
        return self.embed_batch([text])[0]

    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """
        Embed a list of strings.
        Returns: np.ndarray of shape (N, dim), float32, L2-normalised.
        """
        self._load_model()
        if not texts:
            return np.zeros((0, self._dim), dtype=np.float32)

        if self._model is not None:
            vecs = self._model.encode(
                texts,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False
            )
            return vecs.astype(np.float32)
        else:
            # Fallback: deterministic TF-based pseudo-embedding (no GPU/model)
            return self._fallback_embed(texts)

    def _fallback_embed(self, texts: List[str]) -> np.ndarray:
        """
        Deterministic character-hash pseudo-embedding for testing
        when sentence-transformers is unavailable.
        NOT suitable for production — only for CI/CD without GPU.
        """
        import hashlib
        vecs = []
        dim = self._dim
        for text in texts:
            seed = int(hashlib.md5(text.encode()).hexdigest(), 16) % (2**31)
            rng = np.random.RandomState(seed)
            vec = rng.randn(dim).astype(np.float32)
            norm = np.linalg.norm(vec)
            vecs.append(vec / norm if norm > 0 else vec)
        return np.array(vecs, dtype=np.float32)

    def artifact_to_text(self, artifact: Dict[str, Any], kind: str = "code") -> str:
        """
        Converts an artifact dict into a single text blob for embedding.
        Concatenates semantically rich fields in priority order.
        """
        if kind == "test":
            parts = [
                artifact.get("test_method", "") or "",
                artifact.get("test_class", "") or "",
                artifact.get("docstring", "") or "",
                artifact.get("test_content", "") or "",
                artifact.get("file_path", "") or "",
                " ".join(artifact.get("target_refs", [])),
            ]
        else:
            parts = [
                artifact.get("name", "") or "",
                artifact.get("class_name", "") or "",
                artifact.get("signature", "") or "",
                artifact.get("docstring", "") or "",
                artifact.get("code_content", "") or "",
                artifact.get("file_path", "") or "",
            ]
        return " ".join(p for p in parts if p).strip()

    def requirement_to_text(self, req: Dict[str, Any]) -> str:
        """Converts a requirement dict into text for embedding."""
        parts = [
            req.get("req_identifier", "") or "",
            req.get("title", "") or "",
            req.get("description", "") or "",
            " ".join(req.get("acceptance_criteria", [])),
            " ".join(req.get("tags", [])),
        ]
        return " ".join(p for p in parts if p).strip()

    @property
    def embedding_dim(self) -> int:
        self._load_model()
        return self._dim
