"""Small deterministic retrieval adapter used by the service layer.

It deliberately does not construct a SentenceTransformer, so importing or
running the API never downloads a model.  The existing RAGRetriever remains
available for optional semantic experiments.
"""

from __future__ import annotations

import hashlib
from typing import Any, Iterable

from traceability.preprocessor import CodePreprocessor


class TargetedEvidenceRetriever:
    """Retrieve only artifacts related to a changed identifier or path."""

    def retrieve(
        self,
        queries: Iterable[str],
        artifacts: Iterable[dict[str, Any]],
        top_k: int = 10,
    ) -> list[dict[str, Any]]:
        query_terms = set(CodePreprocessor.preprocess(" ".join(queries)))
        if not query_terms:
            return []
        results = []
        for artifact in artifacts:
            text = " ".join(str(value) for value in artifact.values() if value is not None)
            terms = set(CodePreprocessor.preprocess(text))
            overlap = query_terms.intersection(terms)
            if not overlap:
                continue
            score = len(overlap) / max(len(query_terms), 1)
            artifact_id = (
                artifact.get("artifact_identifier")
                or artifact.get("test_identifier")
                or artifact.get("artifact_id")
            )
            evidence_id = hashlib.sha256(
                f"{artifact_id}|{artifact.get('file_path', '')}|{sorted(overlap)}".encode("utf-8")
            ).hexdigest()[:24]
            results.append(
                {
                    "evidence_id": evidence_id,
                    "artifact_id": artifact_id,
                    "artifact_type": artifact.get("artifact_type", "TEST"),
                    "path": artifact.get("file_path", ""),
                    "location": {
                        "line_start": artifact.get("line_start"),
                        "line_end": artifact.get("line_end"),
                    },
                    "score": round(score, 4),
                    "reason": "targeted deterministic lexical retrieval",
                    "method": "RAG_LEXICAL_NO_MODEL",
                    "version": artifact.get("version"),
                    "evidence": {"matched_terms": sorted(overlap)},
                }
            )
        results.sort(key=lambda item: (-item["score"], item["artifact_id"] or ""))
        return results[:top_k]
