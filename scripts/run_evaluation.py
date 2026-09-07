import os
import sys
import json
from datetime import datetime, timezone

# Ensure project root is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from evaluation.benchmark_runner import BenchmarkRunner


def format_table(headers, rows):
    """Formats an aligned ASCII table."""
    widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            widths[i] = max(widths[i], len(str(val)))

    sep = "+" + "+".join(["-" * (w + 2) for w in widths]) + "+"
    header_line = "| " + " | ".join([h.ljust(widths[i]) for i, h in enumerate(headers)]) + " |"

    lines = [sep, header_line, sep]
    for row in rows:
        r_line = "| " + " | ".join([str(val).ljust(widths[i]) for i, val in enumerate(row)]) + " |"
        lines.append(r_line)
    lines.append(sep)
    return "\n".join(lines)


def main():
    print("=" * 80)
    print("  VIGILANT RESEARCH PLATFORM — TRACEABILITY ACCURACY EVALUATION")
    print("=" * 80)

    dataset_path = os.path.join(os.path.dirname(__file__), "..", "datasets", "benchmark_banking")
    print(f"[*] Loading benchmark dataset from: {os.path.abspath(dataset_path)}")

    runner = BenchmarkRunner(dataset_path)
    runner.load_dataset()

    print(f"[+] Loaded {len(runner.requirements)} Requirements (REQ-001 to REQ-010)")
    print(f"[+] Extracted {len(runner.code_artifacts)} Source Code Artifacts (Classes, Methods, Modules)")
    print(f"[+] Extracted {len(runner.test_artifacts)} Test Cases across 5 Test Suites")

    gt_code_links = sum(len(v) for v in runner.ground_truth.get("requirement_to_code", {}).values())
    gt_test_links = sum(len(v) for v in runner.ground_truth.get("requirement_to_test", {}).values())
    print(f"[+] Ground Truth Links: {gt_code_links} (Req->Code), {gt_test_links} (Req->Test)")
    print("-" * 80)
    print("[*] Executing Information Retrieval (TF-IDF, BM25) and Hybrid Models across thresholds...")

    results = runner.run_evaluation()

    # Display Requirement -> Code Traceability
    print("\n" + "=" * 80)
    print("  1. REQUIREMENT -> CODE TRACEABILITY RESULTS (R -> C)")
    print("=" * 80)
    headers = ["Model", "Threshold", "Precision", "Recall", "F1-Score", "MRR", "MAP", "Top-1", "Top-3"]
    rows = []
    for model_name, data in results["requirement_to_code"].items():
        m = data["best_metrics"]
        rows.append([
            model_name,
            f"{data['best_threshold']:.2f}",
            f"{m['precision']:.4f}",
            f"{m['recall']:.4f}",
            f"{m['f1_score']:.4f}",
            f"{m['mrr']:.4f}",
            f"{m['map_score']:.4f}",
            f"{m['top_1_accuracy'] * 100:.1f}%",
            f"{m['top_3_accuracy'] * 100:.1f}%",
        ])
    print(format_table(headers, rows))

    # Display Requirement -> Test Traceability
    print("\n" + "=" * 80)
    print("  2. REQUIREMENT -> TEST TRACEABILITY RESULTS (R -> T)")
    print("=" * 80)
    rows_test = []
    for model_name, data in results["requirement_to_test"].items():
        m = data["best_metrics"]
        rows_test.append([
            model_name,
            f"{data['best_threshold']:.2f}",
            f"{m['precision']:.4f}",
            f"{m['recall']:.4f}",
            f"{m['f1_score']:.4f}",
            f"{m['mrr']:.4f}",
            f"{m['map_score']:.4f}",
            f"{m['top_1_accuracy'] * 100:.1f}%",
            f"{m['top_3_accuracy'] * 100:.1f}%",
        ])
    print(format_table(headers, rows_test))

    # Precision-Recall Trade-off Detail for Best Model (Hybrid)
    print("\n" + "=" * 80)
    print("  3. THRESHOLD SWEEP (HYBRID MODEL: R -> C TRADEOFF)")
    print("=" * 80)
    sweep_headers = ["Threshold (tau)", "Predicted Links", "True Positives (TP)", "False Positives (FP)", "Precision", "Recall", "F1-Score"]
    sweep_rows = []
    for step in results["requirement_to_code"]["HYBRID"]["sweep"]:
        sm = step["metrics"]
        sweep_rows.append([
            f"{step['threshold']:.2f}",
            sm["predicted_count"],
            sm["true_positives"],
            sm["false_positives"],
            f"{sm['precision']:.4f}",
            f"{sm['recall']:.4f}",
            f"{sm['f1_score']:.4f}"
        ])
    print(format_table(sweep_headers, sweep_rows))

    # Save to experiments directory
    exp_dir = os.path.join(os.path.dirname(__file__), "..", "experiments")
    os.makedirs(exp_dir, exist_ok=True)
    out_file = os.path.join(exp_dir, "benchmark_results.json")
    results["timestamp"] = datetime.now(timezone.utc).isoformat()
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\n[+] Full experiment results successfully exported to:")
    print(f"    {os.path.abspath(out_file)}")
    print("=" * 80)


if __name__ == "__main__":
    main()
