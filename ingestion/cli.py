import argparse
import json
import sys
import os

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ingestion.pipeline import IngestionPipeline


def main():
    parser = argparse.ArgumentParser(description="VIGILANT — Repository Ingestion Tool")
    parser.add_argument("--repo-name", required=True, help="Display name for the repository")
    parser.add_argument("--repo-path", required=True, help="Path to repository root folder")
    parser.add_argument("--requirements-path", default="", help="Optional path to requirements.md")

    args = parser.parse_args()

    pipeline = IngestionPipeline()
    req_path = args.requirements_path or None

    print(f"[*] Ingesting repository: {args.repo_name} from {args.repo_path}...")
    summary = pipeline.ingest_repository(
        repo_name=args.repo_name,
        repo_path=args.repo_path,
        requirements_path=req_path
    )
    print("[+] Ingestion Completed Successfully!")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
