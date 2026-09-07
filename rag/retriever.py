"""
rag/retriever.py
----------------
RAGRetriever — combines semantic embeddings + IR baseline scores
for hybrid retrieval. Core of VIGILANT Phase 2 RAG layer.
"""
from __future__ import annotations

import os
from typing import List, Dict, Any, Tuple, Optional

import numpy as np

from rag.embedder import ArtifactEmbedder
from rag.vector_store import FAISSVectorStore


class RAGRetriever:
    """
    Semantic retrieval over code and test artifacts using sentence-transformers.

    Usage:
        retriever = RAGRetriever()
        retriever.fit(code_artifacts, test_artifacts)
        results = retriever.retrieve(requirement, top_k=10)
    """

    def __init__(
        self,
        embedding_model: Optional[str] = None,
        ir_weight: float = 0.40,
        semantic_weight: float = 0.60,
    ):
        self.ir_weight = ir_weight
        self.semantic_weight = semantic_weight
        self.embedder = ArtifactEmbedder(model_name=embedding_model)

        # Separate stores for code and tests
        self._code_store: Optional[FAISSVectorStore] = None
        self._test_store: Optional[FAISSVectorStore] = None
        self._code_artifacts: List[Dict[str, Any]] = []
        self._test_artifacts: List[Dict[str, Any]] = []
        self._fitted = False

    # ------------------------------------------------------------------
    # Fit
    # ------------------------------------------------------------------

    def fit(
        self,
        code_artifacts: List[Dict[str, Any]],
        test_artifacts: List[Dict[str, Any]]
    ):
        """Build FAISS indices for code and test artifacts."""
        dim = self.embedder.embedding_dim

        # --- Code artifacts ---
        self._code_artifacts = code_artifacts
        if code_artifacts:
            code_texts = [
                self.embedder.artifact_to_text(a, kind="code")
                for a in code_artifacts
            ]
            code_embs = self.embedder.embed_batch(code_texts)
            self._code_store = FAISSVectorStore(dim=dim)
            self._code_store.build(code_artifacts, code_embs)

        # --- Test artifacts ---
        self._test_artifacts = test_artifacts
        if test_artifacts:
            test_texts = [
                self.embedder.artifact_to_text(a, kind="test")
                for a in test_artifacts
            ]
            test_embs = self.embedder.embed_batch(test_texts)
            self._test_store = FAISSVectorStore(dim=dim)
            self._test_store.build(test_artifacts, test_embs)

        self._fitted = True

    # ------------------------------------------------------------------
    # Retrieve
    # ------------------------------------------------------------------

    def retrieve(
        self,
        requirement: Dict[str, Any],
        top_k: int = 10,
        target: str = "code",   # "code" | "test" | "both"
        ir_scores: Optional[Dict[str, float]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve top-K semantically similar artifacts for a requirement.

        Parameters
        ----------
        requirement : dict with req_identifier, title, description, etc.
        top_k       : number of candidates to return
        target      : which artifact type to search ("code", "test", "both")
        ir_scores   : optional dict {artifact_id: ir_score} for fusion

        Returns
        -------
        list of dicts: each has keys:
            source          - requirement identifier
            target          - artifact identifier
            semantic_score  - cosine similarity from embedding
            ir_score        - IR score if provided, else 0.0
            final_score     - weighted fusion
            method          - "RAG_SEMANTIC" or "RAG_HYBRID"
            status          - "CANDIDATE"
        """
        if not self._fitted:
            raise RuntimeError("Call fit() before retrieve()")

        req_text = self.embedder.requirement_to_text(requirement)
        req_emb = self.embedder.embed_text(req_text)
        req_id = requirement.get("req_identifier", "UNK")

        results = []

        if target in ("code", "both") and self._code_store:
            hits = self._code_store.search(req_emb, top_k=top_k)
            for art, sem_score in hits:
                art_id = art.get("artifact_identifier", art.get("name", "?"))
                ir_score = (ir_scores or {}).get(art_id, 0.0)
                method = "RAG_HYBRID" if ir_scores else "RAG_SEMANTIC"
                final = (
                    self.semantic_weight * sem_score
                    + self.ir_weight * ir_score
                ) if ir_scores else sem_score
                results.append({
                    "source": req_id,
                    "target": art_id,
                    "target_type": "code",
                    "artifact": art,
                    "semantic_score": round(float(sem_score), 4),
                    "ir_score": round(float(ir_score), 4),
                    "final_score": round(float(final), 4),
                    "method": method,
                    "status": "CANDIDATE",
                })

        if target in ("test", "both") and self._test_store:
            hits = self._test_store.search(req_emb, top_k=top_k)
            for art, sem_score in hits:
                art_id = art.get("test_identifier", art.get("test_method", "?"))
                ir_score = (ir_scores or {}).get(art_id, 0.0)
                method = "RAG_HYBRID" if ir_scores else "RAG_SEMANTIC"
                final = (
                    self.semantic_weight * sem_score
                    + self.ir_weight * ir_score
                ) if ir_scores else sem_score
                results.append({
                    "source": req_id,
                    "target": art_id,
                    "target_type": "test",
                    "artifact": art,
                    "semantic_score": round(float(sem_score), 4),
                    "ir_score": round(float(ir_score), 4),
                    "final_score": round(float(final), 4),
                    "method": method,
                    "status": "CANDIDATE",
                })

        results.sort(key=lambda x: x["final_score"], reverse=True)
        return results[:top_k]

    def retrieve_all(
        self,
        requirements: List[Dict[str, Any]],
        top_k: int = 10,
        target: str = "code",
        ir_scores_per_req: Optional[Dict[str, Dict[str, float]]] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Batch retrieve for all requirements. Returns {req_id: [candidates]}."""
        out = {}
        for req in requirements:
            req_id = req.get("req_identifier", "UNK")
            ir_scores = (ir_scores_per_req or {}).get(req_id)
            out[req_id] = self.retrieve(req, top_k=top_k, target=target, ir_scores=ir_scores)
        return out

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, directory: str):
        os.makedirs(directory, exist_ok=True)
        if self._code_store:
            self._code_store.save(os.path.join(directory, "code"))
        if self._test_store:
            self._test_store.save(os.path.join(directory, "test"))

    def load(self, directory: str):
        dim = self.embedder.embedding_dim
        code_dir = os.path.join(directory, "code")
        if os.path.exists(code_dir):
            self._code_store = FAISSVectorStore(dim=dim)
            self._code_store.load(code_dir)
            self._code_artifacts = self._code_store._artifacts

        test_dir = os.path.join(directory, "test")
        if os.path.exists(test_dir):
            self._test_store = FAISSVectorStore(dim=dim)
            self._test_store.load(test_dir)
            self._test_artifacts = self._test_store._artifacts

        self._fitted = True
