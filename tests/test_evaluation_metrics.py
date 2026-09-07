import pytest
from evaluation.metrics import MetricsCalculator


def test_evaluate_links_exact():
    predicted = [
        {"source": "REQ-1", "target": "CodeA"},
        {"source": "REQ-1", "target": "CodeB"},
        {"source": "REQ-2", "target": "CodeC"},  # False positive
    ]
    ground_truth = [
        ("REQ-1", "CodeA"),
        ("REQ-1", "CodeB"),
        ("REQ-2", "CodeD"),  # False negative
    ]

    res = MetricsCalculator.evaluate_links(predicted, ground_truth)
    assert res["true_positives"] == 2
    assert res["false_positives"] == 1
    assert res["false_negatives"] == 1
    assert abs(res["precision"] - 2 / 3) < 1e-3
    assert abs(res["recall"] - 2 / 3) < 1e-3
    assert abs(res["f1_score"] - 2 / 3) < 1e-3


def test_evaluate_ranked_queries_mrr_map():
    query_rankings = {
        "REQ-1": [("CodeA", 0.9), ("CodeB", 0.8), ("CodeC", 0.5)],
        "REQ-2": [("CodeX", 0.9), ("CodeY", 0.7)],  # CodeY is relevant at rank 2
    }
    ground_truth = {
        "REQ-1": {"CodeA"},  # relevant at rank 1 -> RR = 1.0
        "REQ-2": {"CodeY"},  # relevant at rank 2 -> RR = 0.5
    }

    metrics = MetricsCalculator.evaluate_ranked_queries(query_rankings, ground_truth, threshold=0.0)
    assert metrics.mrr == 0.75  # (1.0 + 0.5) / 2
    assert metrics.top_1_accuracy == 0.5  # REQ-1 is in top 1, REQ-2 is not
    assert metrics.top_3_accuracy == 1.0  # both are in top 3
