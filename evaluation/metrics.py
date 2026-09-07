from typing import List, Dict, Set, Tuple, Any
from dataclasses import dataclass, asdict


@dataclass
class EvaluationMetrics:
    total_queries: int
    ground_truth_count: int
    predicted_count: int
    true_positives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float
    f1_score: float
    mrr: float  # Mean Reciprocal Rank
    map_score: float  # Mean Average Precision
    top_1_accuracy: float
    top_3_accuracy: float
    top_5_accuracy: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MetricsCalculator:
    """
    Standard Software Engineering Information Retrieval Evaluation Engine.
    Computes Precision, Recall, F1, MRR, MAP, and Top-K accuracy against Ground Truth.
    """

    @staticmethod
    def evaluate_links(
        predicted_links: List[Dict[str, Any]],
        ground_truth_links: List[Tuple[str, str]]
    ) -> Dict[str, float]:
        """
        Binary set-based classification evaluation.
        predicted_links: list of dicts with 'source' and 'target'
        ground_truth_links: list of (source, target) tuples
        """
        gt_set = set((str(s), str(t)) for s, t in ground_truth_links)
        pred_set = set((str(p["source"]), str(p["target"])) for p in predicted_links)

        tp = len(pred_set.intersection(gt_set))
        fp = len(pred_set - gt_set)
        fn = len(gt_set - pred_set)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        return {
            "ground_truth_count": len(gt_set),
            "predicted_count": len(pred_set),
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
        }

    @staticmethod
    def evaluate_ranked_queries(
        query_rankings: Dict[str, List[Tuple[str, float]]],
        ground_truth_map: Dict[str, Set[str]],
        threshold: float = 0.0
    ) -> EvaluationMetrics:
        """
        Rank-aware evaluation computing MRR, MAP, and Top-K across all queries.
        query_rankings: dict of query_id -> [(target_id, score), ...] sorted descending
        ground_truth_map: dict of query_id -> set of relevant target_ids
        threshold: confidence score cutoff for prediction
        """
        total_queries = len(ground_truth_map)
        if total_queries == 0:
            return EvaluationMetrics(0, 0, 0, 0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

        total_gt = sum(len(targets) for targets in ground_truth_map.values())
        predicted_links = []
        reciprocal_ranks = []
        average_precisions = []
        top_1_hits = 0
        top_3_hits = 0
        top_5_hits = 0

        for q_id, gt_targets in ground_truth_map.items():
            ranked_list = query_rankings.get(q_id, [])
            if not gt_targets:
                continue

            # Check Top-K hits
            top_1_targets = [t[0] for t in ranked_list[:1]]
            top_3_targets = [t[0] for t in ranked_list[:3]]
            top_5_targets = [t[0] for t in ranked_list[:5]]

            if any(t in gt_targets for t in top_1_targets):
                top_1_hits += 1
            if any(t in gt_targets for t in top_3_targets):
                top_3_hits += 1
            if any(t in gt_targets for t in top_5_targets):
                top_5_hits += 1

            # Reciprocal Rank
            rr = 0.0
            for rank_idx, (target_id, score) in enumerate(ranked_list, start=1):
                if target_id in gt_targets:
                    rr = 1.0 / rank_idx
                    break
            reciprocal_ranks.append(rr)

            # Average Precision (AP)
            hits = 0
            prec_sum = 0.0
            for rank_idx, (target_id, score) in enumerate(ranked_list, start=1):
                if target_id in gt_targets:
                    hits += 1
                    prec_sum += hits / rank_idx
            ap = prec_sum / len(gt_targets) if len(gt_targets) > 0 else 0.0
            average_precisions.append(ap)

            # Accumulate unique predictions based on threshold
            seen_targets = set()
            for target_id, score in ranked_list:
                if target_id not in seen_targets and score >= threshold:
                    seen_targets.add(target_id)
                    predicted_links.append({"source": q_id, "target": target_id, "confidence": score})

        # Set-based metrics at current threshold
        flat_gt = [(q_id, target) for q_id, targets in ground_truth_map.items() for target in targets]
        set_metrics = MetricsCalculator.evaluate_links(predicted_links, flat_gt)

        mrr = sum(reciprocal_ranks) / len(reciprocal_ranks) if reciprocal_ranks else 0.0
        map_score = sum(average_precisions) / len(average_precisions) if average_precisions else 0.0

        return EvaluationMetrics(
            total_queries=total_queries,
            ground_truth_count=total_gt,
            predicted_count=set_metrics["predicted_count"],
            true_positives=set_metrics["true_positives"],
            false_positives=set_metrics["false_positives"],
            false_negatives=set_metrics["false_negatives"],
            precision=set_metrics["precision"],
            recall=set_metrics["recall"],
            f1_score=set_metrics["f1_score"],
            mrr=round(mrr, 4),
            map_score=round(map_score, 4),
            top_1_accuracy=round(top_1_hits / total_queries, 4),
            top_3_accuracy=round(top_3_hits / total_queries, 4),
            top_5_accuracy=round(top_5_hits / total_queries, 4),
        )
