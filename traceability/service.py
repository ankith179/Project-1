from __future__ import annotations

from typing import Any, Dict, List, Sequence

from traceability.hybrid_model import HybridTraceabilityModel
from traceability.ir_model import IRTraceabilityModel
from traceability.preprocessor import CodePreprocessor


class TraceabilityService:
    """Deterministic, evidence-bearing trace-link generation."""

    def __init__(self, threshold: float = 0.25):
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("threshold must be between 0 and 1")
        self.threshold = threshold

    def generate_links(
        self,
        requirements: Sequence[Dict[str, Any]],
        code_artifacts: Sequence[Dict[str, Any]],
        test_artifacts: Sequence[Dict[str, Any]],
        version: str | None = None,
    ) -> List[Dict[str, Any]]:
        links: List[Dict[str, Any]] = []
        links.extend(
            self._rank_requirement_targets(
                requirements, code_artifacts, "REQUIREMENT_TO_CODE", "artifact_identifier", version
            )
        )
        links.extend(
            self._rank_requirement_targets(
                requirements, test_artifacts, "REQUIREMENT_TO_TEST", "test_identifier", version
            )
        )
        links.extend(self._rank_code_tests(code_artifacts, test_artifacts, version))
        return links

    def _rank_requirement_targets(
        self,
        requirements: Sequence[Dict[str, Any]],
        targets: Sequence[Dict[str, Any]],
        relationship_type: str,
        target_key: str,
        version: str | None,
    ) -> List[Dict[str, Any]]:
        if not requirements or not targets:
            return []
        model = HybridTraceabilityModel(ir_method="bm25")
        model.fit(list(targets))
        links: List[Dict[str, Any]] = []
        for requirement in requirements:
            req_id = requirement.get("req_identifier")
            query = f"{requirement.get('title', '')} {requirement.get('description', '')}"
            for target, score in model.query_similarity(req_id, query):
                if score < self.threshold:
                    continue
                target_id = target.get(target_key)
                links.append(
                    self._link(
                        req_id,
                        target_id,
                        relationship_type,
                        score,
                        version,
                        query,
                        target,
                        "HYBRID_IR_STRUCTURAL",
                    )
                )
        return links

    def _rank_code_tests(
        self,
        code_artifacts: Sequence[Dict[str, Any]],
        test_artifacts: Sequence[Dict[str, Any]],
        version: str | None,
    ) -> List[Dict[str, Any]]:
        if not code_artifacts or not test_artifacts:
            return []
        model = IRTraceabilityModel(method="bm25")
        model.fit(list(test_artifacts))
        links: List[Dict[str, Any]] = []
        for code in code_artifacts:
            code_id = code.get("artifact_identifier")
            query = " ".join(
                (
                    code.get("name", ""),
                    code.get("class_name", "") or "",
                    code.get("signature", "") or "",
                    code.get("docstring", "") or "",
                )
            )
            for target, score in model.query_similarity(query):
                if score < self.threshold:
                    continue
                links.append(
                    self._link(
                        code_id,
                        target.get("test_identifier"),
                        "CODE_TO_TEST",
                        score,
                        version,
                        query,
                        target,
                        "BM25",
                    )
                )
        return links

    @staticmethod
    def _link(
        source_id: str,
        target_id: str,
        relationship_type: str,
        score: float,
        version: str | None,
        query: str,
        target: Dict[str, Any],
        method: str,
    ) -> Dict[str, Any]:
        query_terms = set(CodePreprocessor.preprocess(query))
        target_text = " ".join(str(value) for value in target.values() if isinstance(value, str))
        target_terms = set(CodePreprocessor.preprocess(target_text))
        return {
            "source_id": source_id,
            "target_id": target_id,
            "relationship_type": relationship_type,
            "score": round(float(score), 4),
            "confidence": round(float(score), 4),
            "evidence": {
                "query_terms": sorted(query_terms),
                "matched_terms": sorted(query_terms.intersection(target_terms)),
                "target_path": target.get("file_path"),
                "target_location": {
                    "line_start": target.get("line_start"),
                    "line_end": target.get("line_end"),
                },
            },
            "method": method,
            "version": version,
            "validation_status": "CANDIDATE",
        }
