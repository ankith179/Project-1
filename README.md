# VIGILANT

VIGILANT is a local, evidence-grounded prototype for continuous traceability
and consistency analysis across requirements, source code, APIs, and tests.

The rebuilt implementation is intentionally deterministic by default so that
research experiments run on a CPU without API keys or model downloads.

## Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m vigilant.cli analyze . --requirements requirements.md
```

The analyzer ingests a repository, extracts artifacts, creates lexical
traceability links, builds a relationship graph, detects consistency findings,
and writes a JSON report.

## Architecture

- `vigilant/ingestion.py`: repository, requirements, Python, API, test, and Git
  change ingestion.
- `vigilant/traceability.py`: deterministic TF-IDF-like lexical retrieval and
  evidence-bearing links.
- `vigilant/graph.py`: bounded artifact traversal and change impact.
- `vigilant/consistency.py`: deterministic consistency rules.
- `vigilant/agent.py`: bounded evidence-gathering investigation loop.
- `backend/app.py`: optional FastAPI service over the analysis workflow.

LLM and embedding providers are extension points; no fabricated model output is
used when they are unavailable.
