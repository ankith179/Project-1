import os
import json
from typing import Dict, Any, List, Set, Tuple
from ingestion.requirements_parser import RequirementsParser
from ingestion.code_parser import CodeParser
from ingestion.test_parser import TestParser
from traceability.ir_model import IRTraceabilityModel
from traceability.hybrid_model import HybridTraceabilityModel
from evaluation.metrics import MetricsCalculator, EvaluationMetrics


class BenchmarkRunner:
    """
    Executes empirical benchmark evaluation on software traceability models.
    Compares IR baselines (TF-IDF, BM25) and Hybrid structural models against
    the ground truth matrix.
    """

    def __init__(self, dataset_dir: str):
        self.dataset_dir = os.path.abspath(dataset_dir)
        self.req_parser = RequirementsParser()
        self.code_parser = CodeParser()
        self.test_parser = TestParser()

        self.requirements: List[Dict[str, Any]] = []
        self.code_artifacts: List[Dict[str, Any]] = []
        self.test_artifacts: List[Dict[str, Any]] = []
        self.ground_truth: Dict[str, Any] = {}

    def load_dataset(self):
        """Loads and parses all requirements, code files, test files, and ground truth."""
        req_file = os.path.join(self.dataset_dir, "requirements.md")
        src_dir = os.path.join(self.dataset_dir, "src")
        tests_dir = os.path.join(self.dataset_dir, "tests")
        gt_file = os.path.join(self.dataset_dir, "ground_truth_matrix.json")

        project_root = os.path.dirname(os.path.dirname(self.dataset_dir))

        def normalize_id(identifier: str) -> str:
            norm = identifier.replace("\\", "/").strip().lstrip("/")
            if norm.startswith("benchmark_banking/"):
                norm = "datasets/" + norm
            return norm

        # Ingest requirements
        parsed_reqs = self.req_parser.parse_file(req_file)
        self.requirements = [r.to_dict() for r in parsed_reqs]

        # Ingest code
        self.code_artifacts = []
        for root, _, files in os.walk(src_dir):
            for file in files:
                if file.endswith((".py", ".java")):
                    full_path = os.path.join(root, file)
                    arts = self.code_parser.parse_file(full_path)
                    for a in arts:
                        d = a.to_dict()
                        rel_id = normalize_id(os.path.relpath(full_path, project_root))
                        if a.artifact_type == "METHOD" and a.class_name:
                            d["artifact_identifier"] = f"{rel_id}::{a.class_name}::{a.name}"
                        elif a.artifact_type == "CLASS":
                            d["artifact_identifier"] = f"{rel_id}::{a.name}"
                        elif a.artifact_type == "FUNCTION":
                            d["artifact_identifier"] = f"{rel_id}::{a.name}"
                        else:
                            d["artifact_identifier"] = rel_id
                        self.code_artifacts.append(d)

        # Ingest tests
        self.test_artifacts = []
        for root, _, files in os.walk(tests_dir):
            for file in files:
                if file.endswith((".py", ".java")):
                    full_path = os.path.join(root, file)
                    tests = self.test_parser.parse_file(full_path)
                    for t in tests:
                        d = t.to_dict()
                        rel_id = normalize_id(os.path.relpath(full_path, project_root))
                        if t.test_class:
                            d["test_identifier"] = f"{rel_id}::{t.test_class}::{t.test_method}"
                        else:
                            d["test_identifier"] = f"{rel_id}::{t.test_method}"
                        self.test_artifacts.append(d)

        # Ingest Ground Truth
        with open(gt_file, "r", encoding="utf-8") as f:
            self.ground_truth = json.load(f)

    def run_evaluation(self, thresholds: List[float] = None) -> Dict[str, Any]:
        """
        Runs comprehensive evaluation on all models across thresholds.
        """
        if thresholds is None:
            thresholds = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.50]

        def norm(s: str) -> str:
            s = s.replace("\\", "/").strip().lstrip("/")
            if s.startswith("benchmark_banking/"):
                s = "datasets/" + s
            return s

        gt_req_to_code = {k: set(norm(t) for t in v) for k, v in self.ground_truth.get("requirement_to_code", {}).items()}
        gt_req_to_test = {k: set(norm(t) for t in v) for k, v in self.ground_truth.get("requirement_to_test", {}).items()}

        models = [
            ("IR_TFIDF", IRTraceabilityModel(method="tfidf")),
            ("IR_BM25", IRTraceabilityModel(method="bm25")),
            ("HYBRID", HybridTraceabilityModel(ir_method="bm25"))
        ]

        results = {
            "dataset": self.ground_truth.get("dataset_name", "benchmark"),
            "num_requirements": len(self.requirements),
            "num_code_artifacts": len(self.code_artifacts),
            "num_test_artifacts": len(self.test_artifacts),
            "requirement_to_code": {},
            "requirement_to_test": {}
        }

        # 1. Evaluate Requirement -> Code Traceability
        for model_name, model in models:
            model.fit(self.code_artifacts)
            query_rankings = {}
            for req in self.requirements:
                q_id = req["req_identifier"]
                q_text = f"{req.get('title', '')} {req.get('description', '')}"
                if isinstance(model, HybridTraceabilityModel):
                    ranked = model.query_similarity(q_id, q_text)
                else:
                    ranked = model.query_similarity(q_text)

                ranked_tuples = [(target["artifact_identifier"], score) for target, score in ranked]
                query_rankings[q_id] = ranked_tuples

            best_metric = None
            best_thresh = 0.0
            threshold_metrics = []

            for thresh in thresholds:
                m = MetricsCalculator.evaluate_ranked_queries(query_rankings, gt_req_to_code, threshold=thresh)
                threshold_metrics.append({"threshold": thresh, "metrics": m.to_dict()})
                if best_metric is None or m.f1_score > best_metric.f1_score:
                    best_metric = m
                    best_thresh = thresh

            results["requirement_to_code"][model_name] = {
                "best_threshold": best_thresh,
                "best_metrics": best_metric.to_dict() if best_metric else None,
                "sweep": threshold_metrics
            }

        # 2. Evaluate Requirement -> Test Traceability
        for model_name, model in models:
            model.fit(self.test_artifacts)
            query_rankings = {}
            for req in self.requirements:
                q_id = req["req_identifier"]
                q_text = f"{req.get('title', '')} {req.get('description', '')}"
                if isinstance(model, HybridTraceabilityModel):
                    ranked = model.query_similarity(q_id, q_text)
                else:
                    ranked = model.query_similarity(q_text)

                ranked_tuples = [(target["test_identifier"], score) for target, score in ranked]
                query_rankings[q_id] = ranked_tuples

            best_metric = None
            best_thresh = 0.0
            threshold_metrics = []

            for thresh in thresholds:
                m = MetricsCalculator.evaluate_ranked_queries(query_rankings, gt_req_to_test, threshold=thresh)
                threshold_metrics.append({"threshold": thresh, "metrics": m.to_dict()})
                if best_metric is None or m.f1_score > best_metric.f1_score:
                    best_metric = m
                    best_thresh = thresh

            results["requirement_to_test"][model_name] = {
                "best_threshold": best_thresh,
                "best_metrics": best_metric.to_dict() if best_metric else None,
                "sweep": threshold_metrics
            }

        return results
