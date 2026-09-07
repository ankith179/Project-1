import re
from typing import List, Dict, Tuple, Any, Optional
from traceability.ir_model import IRTraceabilityModel
from traceability.preprocessor import CodePreprocessor


class HybridTraceabilityModel:
    """
    Hybrid Traceability Baseline.
    Combines IR (TF-IDF/BM25) with structural signals:
    - Component/Class name match
    - File path and module hierarchy
    - Signature argument overlap
    - Explicit test annotations / requirement markers
    """

    def __init__(
        self,
        ir_weight: float = 0.65,
        name_weight: float = 0.25,
        structural_weight: float = 0.10,
        ir_method: str = "bm25"
    ):
        self.ir_weight = ir_weight
        self.name_weight = name_weight
        self.structural_weight = structural_weight
        self.ir_model = IRTraceabilityModel(method=ir_method)
        self.corpus_docs: List[Dict[str, Any]] = []

    def fit(self, artifacts: List[Dict[str, Any]], text_field_getter=None):
        self.corpus_docs = artifacts
        self.ir_model.fit(artifacts, text_field_getter=text_field_getter)

    def _compute_name_similarity(self, query_tokens: List[str], target: Dict[str, Any]) -> float:
        """Measures lexical overlap specifically with artifact names, class names, and file names."""
        name = target.get("name", "") or target.get("test_method", "")
        cls_name = target.get("class_name", "") or target.get("test_class", "") or ""
        file_path = target.get("file_path", "")

        target_identifiers = f"{name} {cls_name} {file_path}"
        target_tokens = set(CodePreprocessor.preprocess(target_identifiers))

        if not target_tokens or not query_tokens:
            return 0.0

        q_set = set(query_tokens)
        overlap = q_set.intersection(target_tokens)
        return len(overlap) / min(len(q_set), len(target_tokens))

    def _compute_annotation_match(self, query_id: str, target: Dict[str, Any]) -> float:
        """Checks for explicit requirement tags, e.g. in test target_refs."""
        target_refs = target.get("target_refs", [])
        if not target_refs:
            # Check docstring or content directly
            content = target.get("test_content", "") or target.get("code_content", "") or target.get("docstring", "")
            if query_id.lower() in content.lower():
                return 1.0
            return 0.0

        norm_qid = query_id.upper().replace("_", "-")
        for ref in target_refs:
            if ref.upper().replace("_", "-") == norm_qid:
                return 1.0
        return 0.0

    def query_similarity(self, query_id: str, query_text: str) -> List[Tuple[Dict[str, Any], float]]:
        """Computes hybrid similarity score for a single query."""
        ir_results = self.ir_model.query_similarity(query_text)
        ir_score_map = {}
        for doc, score in ir_results:
            d_id = doc.get("artifact_identifier") or doc.get("test_identifier") or id(doc)
            ir_score_map[d_id] = score

        q_tokens = CodePreprocessor.preprocess(query_text)

        hybrid_scores = []
        for doc in self.corpus_docs:
            doc_id = doc.get("artifact_identifier") or doc.get("test_identifier") or id(doc)
            s_ir = ir_score_map.get(doc_id, 0.0)
            s_name = self._compute_name_similarity(q_tokens, doc)
            s_tag = self._compute_annotation_match(query_id, doc)

            # If explicit tag is present, it gives strong boost
            if s_tag > 0.0:
                final_score = min(1.0, 0.5 + 0.5 * s_ir)
            else:
                final_score = (
                    self.ir_weight * s_ir +
                    self.name_weight * s_name +
                    self.structural_weight * (s_ir * s_name)
                )

            hybrid_scores.append((doc, round(final_score, 4)))

        hybrid_scores.sort(key=lambda x: x[1], reverse=True)
        return hybrid_scores

    def predict_links(
        self,
        queries: List[Dict[str, Any]],
        threshold: float = 0.25,
        query_id_key: str = "req_identifier",
        target_id_key: str = "artifact_identifier",
        query_text_key: str = "description"
    ) -> List[Dict[str, Any]]:
        links = []
        for q in queries:
            q_id = q.get(query_id_key)
            q_text = f"{q.get('title', '')} {q.get(query_text_key, '')}"
            ranked = self.query_similarity(q_id, q_text)

            for target, score in ranked:
                if score >= threshold:
                    links.append({
                        "source": q_id,
                        "target": target.get(target_id_key) or target.get("test_identifier"),
                        "confidence": score,
                        "method": "HYBRID_IR_STRUCTURAL",
                        "status": "CANDIDATE"
                    })
        return links
