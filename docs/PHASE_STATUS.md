# Rebuild status

## Reset

- Existing implementation archived outside the repository at
  `C:\Users\H-B-RS-720-17\Downloads\VIGILANT-backup-20260923-1143`.
- `.git`, `.venv`, `.vscode`, and `OmniRoute` were preserved.
- The previous implementation and generated database were removed.

## Initial rebuilt increment

The new deterministic core implements repository ingestion, artifact extraction,
lexical traceability, graph impact traversal, consistency findings, a bounded
investigation agent, a CLI, and a FastAPI endpoint. It is CPU-only and does not
execute repository code.

Validation performed on 2026-09-23:

- `.\.venv\Scripts\python.exe -m pytest -q`: **1 passed**
- FastAPI `/health`: **200**, `{"status": "ok"}`
- CLI against the rebuilt repository: **44 artifacts**, report written to the
  external backup directory

The repository-root CLI run produced zero links because the rebuilt root does
not yet contain a requirements artifact. The end-to-end test uses a real
requirements file and verifies links and evidence provenance.
