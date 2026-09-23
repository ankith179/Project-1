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

## Phase 0/1 research assets

- Added [reference_implementations.md](./reference_implementations.md),
  [dataset_strategy.md](./dataset_strategy.md), and
  [evaluation_protocol.md](./evaluation_protocol.md).
- Added `scripts/download_research_assets.py` with URL, checksum, byte-count,
  and failure metadata.
- Executed the downloader successfully:
  - LiSSA README: 7,658 bytes, SHA-256 recorded.
  - ARDoCo README: 2,610 bytes, SHA-256 recorded.
- Inspected both downloaded files and stored their catalog rows in
  `data/catalog.csv`.
- Research-asset tests and the rebuilt end-to-end test: **2 passed**.

These two files are public research reference assets, not labeled benchmark
datasets. Full traceability benchmark archives will only be added after their
official release asset and license are verified.
