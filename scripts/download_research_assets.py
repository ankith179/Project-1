from __future__ import annotations

import csv
import hashlib
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
CATALOG = ROOT / "data" / "catalog.csv"
ASSETS = [
    {
        "dataset": "LiSSA README research asset",
        "source": "ArDoCo/LiSSA",
        "url": "https://raw.githubusercontent.com/ArDoCo/LiSSA/main/README.md",
        "artifact_types": "documentation",
        "ground_truth": "none",
        "license": "MIT",
        "purpose": "Inspect public TLR framework scope and evaluation claims",
        "filename": "lissa-readme.md",
        "usage": "reference only",
    },
    {
        "dataset": "ARDoCo README research asset",
        "source": "ardoco/ardoco",
        "url": "https://raw.githubusercontent.com/ardoco/ardoco/main/README.md",
        "artifact_types": "documentation",
        "ground_truth": "none",
        "license": "project license",
        "purpose": "Inspect architecture traceability and inconsistency framing",
        "filename": "ardoco-readme.md",
        "usage": "reference only",
    },
]


def download(asset: dict[str, str]) -> dict[str, str]:
    destination = RAW / asset["filename"]
    result = {
        "dataset": asset["dataset"],
        "source": asset["source"],
        "url": asset["url"],
        "artifact_types": asset["artifact_types"],
        "ground_truth": asset["ground_truth"],
        "license": asset["license"],
        "purpose": asset["purpose"],
        "download_status": "FAILED",
        "preprocessing_status": "NOT_STARTED",
        "vigilant_usage": asset["usage"],
        "sha256": "",
        "size_bytes": "0",
        "downloaded_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        RAW.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(asset["url"], timeout=30) as response:
            content = response.read()
        destination.write_bytes(content)
        result["download_status"] = "DOWNLOADED"
        result["preprocessing_status"] = "INSPECTED_TEXT"
        result["size_bytes"] = str(len(content))
        result["sha256"] = hashlib.sha256(content).hexdigest()
    except (OSError, urllib.error.URLError) as exc:
        result["download_status"] = f"FAILED: {exc}"
    return result


def main() -> int:
    rows = [download(asset) for asset in ASSETS]
    with CATALOG.open("w", newline="", encoding="utf-8") as handle:
        fields = [
            "dataset", "source", "url", "artifact_types", "size_bytes",
            "ground_truth", "license", "purpose", "download_status",
            "preprocessing_status", "vigilant_usage", "sha256", "downloaded_at",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    for row in rows:
        print(f'{row["download_status"]}: {row["dataset"]} ({row["size_bytes"]} bytes)')
    return 0 if all(row["download_status"] == "DOWNLOADED" for row in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
