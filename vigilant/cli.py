from __future__ import annotations

import argparse
import json
from pathlib import Path

from vigilant.agent import InvestigationAgent


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("repository")
    parser.add_argument("--requirements")
    parser.add_argument("--output", default="vigilant-report.json")
    args = parser.parse_args()
    report = InvestigationAgent().investigate(args.repository, args.requirements)
    Path(args.output).write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    print(json.dumps({"artifacts": len(report.artifacts), "links": len(report.links), "findings": len(report.findings), "output": args.output}))


if __name__ == "__main__":
    main()
