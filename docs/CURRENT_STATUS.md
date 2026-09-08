# VIGILANT Current Status

Audit date: 2026-09-08

## Evidence

- Existing test command: `.venv\Scripts\python.exe -m pytest tests`
- Initial audit result: **14 passed**, with two dependency deprecation warnings.
- Current implementation result: **20 passed**, with the same two dependency
  deprecation warnings.
- Python environment: Python 3.13.2 in `.venv`.
- The working tree was clean for tracked files. `OmniRoute/` is an existing untracked directory and was not modified.
- Pylance import audit found one unresolved top-level import name, `llm`; this is the repository's local package and is not a missing external dependency.

## Module audit

| MODULE | STATUS | PROBLEM | ACTION |
|---|---|---|---|
| `backend/app.py` | Working baseline | Provides health and evaluation endpoints, but no traceability, consistency, change-impact, or agent endpoints. | Preserve; add research workflows through explicit routes/services. |
| `backend/routes/artifacts.py` | Working baseline | Lists requirements, code, and tests only; no links, commits, diffs, or consistency findings. | Preserve; extend with repository-scoped traceability views. |
| `backend/routes/ingestion.py` | Partial | Ingests a local path synchronously and has no Git history/change ingestion or validation of a requirements path. | Preserve; add change-aware ingestion and clear input validation. |
| `database/connection.py` | Working baseline | Creates tables with `create_all`; no migrations or transaction/service boundary. | Preserve for prototype; add migration/versioning only when schema evolution begins. |
| `database/models.py` | Partial | Models exist for repositories, requirements, code, tests, commits, file changes, and candidate links, but commit/link models are not populated by the pipeline. | Reuse models; wire persistence to ingestion and analysis results. |
| `ingestion/requirements_parser.py` | Working baseline | Parses Markdown/text identifiers, metadata, descriptions, and acceptance criteria. | Keep; add parser fixtures for edge cases as formats expand. |
| `ingestion/code_parser.py` | Working baseline | Extracts Python/Java code artifacts and structural fields. | Keep; verify identifiers and call/import relations against research datasets. |
| `ingestion/test_parser.py` | Working baseline | Extracts Python and basic Java test artifacts, assertions, and heuristic requirement tags. | Keep; improve explicit requirement/API target extraction and error reporting. |
| `ingestion/git_parser.py` | Partial | Parses supplied Git log/diff text, including changed line numbers, but is not called by the pipeline. | Wire to repository ingestion and use changes to scope affected artifacts. |
| `ingestion/pipeline.py` | Partial | Persists requirements/code/tests and supports re-ingestion, but does not persist commits, file changes, links, versions, or analysis snapshots. | Refactor into staged, change-aware ingestion services without replacing parsers. |
| `traceability/preprocessor.py` | Working baseline | Provides identifier splitting, stopword removal, and lightweight stemming. | Preserve as a baseline preprocessing component; measure impact in evaluation. |
| `traceability/ir_model.py` | Working baseline | Implements TF-IDF and normalized BM25 ranking and candidate generation. | Preserve as reproducible baselines; document score calibration and limitations. |
| `traceability/hybrid_model.py` | Working baseline | Fuses IR with name and annotation signals. | Preserve; add evidence output and multi-hop requirement-code-test reasoning. |
| `rag/embedder.py` | Partial | Uses a local SentenceTransformer lazily, but the fallback is a random hash vector and is explicitly unsuitable for production. | Keep for CI fallback; make model identity/cache/device reproducible for experiments. |
| `rag/vector_store.py` | Partial | FAISS/numpy retrieval and persistence work, but loading does not validate dimensions or store metadata/version. | Add metadata validation and repository/version isolation. |
| `rag/retriever.py` | Partial | Retrieves code/tests and optionally fuses externally supplied IR scores, but has no persistent index lifecycle or requirement-to-code-to-test graph traversal. | Reuse; integrate with stored artifacts, snapshots, and evidence. |
| `llm/gemini_client.py` | Partial | Gemini calls and structured parsing exist, but broad exception handling converts initialization/API failures into mock/error-shaped responses. | Preserve mock mode for tests; surface production failures and add consistency-specific schemas. |
| `agents/` | Placeholder | Contains only `__init__.py`; no agent state machine, tools, planning, change analysis, or verification loop exists. | Implement after ingestion, evidence, and traceability contracts are stable. |
| `evaluation/metrics.py` | Working baseline | Computes set metrics, MRR, MAP, and Top-K accuracy. | Preserve; add change-impact/consistency metrics and dataset split protocols. |
| `evaluation/benchmark_runner.py` | Working baseline | Runs TF-IDF, BM25, and hybrid R-to-code/test evaluation on `benchmark_banking`. | Preserve; add RAG/LLM/agent comparisons and leakage-safe experiment configuration. |
| `datasets/benchmark_banking/` | Working fixture | Contains 10 requirements, 34 code artifacts, 18 tests, and a ground-truth matrix. | Preserve; add versioned changes and API artifacts for the stated research objective. |
| `experiments/benchmark_results.json` | Generated result | Stores a benchmark snapshot, but provenance/configuration/model versions are not recorded. | Regenerate from a reproducible runner after evaluation protocol changes. |
| `scripts/run_evaluation.py` | Working utility | Runs the current benchmark and writes results. | Extend with explicit experiment configuration and result metadata. |
| `tests/` | Working baseline | 14 tests cover parsers, API, DB, metrics, Git parser, and IR/hybrid models. | Add focused tests for change-aware ingestion, persisted links, RAG metadata, and agent contracts. |
| `README.md` | Partially current | Documents phases 1–3 and baseline structure, but describes agent functionality that is not present and omits current limitations. | Update after the first implementation increment. |
| `requirements.txt` | Working environment manifest | Declares core, parsing, IR, RAG, Gemini, and test dependencies; does not describe optional/model/download constraints. | Preserve; separate optional heavyweight/runtime dependencies when packaging. |
| `OmniRoute/` | Untracked existing surface | Not part of the tracked baseline audit; its ownership and intended integration are unclear. | Do not modify until its role is confirmed. |

## What already works

1. Local FastAPI application startup and health/evaluation endpoints.
2. Requirements, Python/Java code, Python/Java tests, and Git diff parsing.
3. SQLite persistence for repository and artifact records.
4. Idempotent artifact re-ingestion for requirements, code, and tests.
5. TF-IDF, BM25, and hybrid candidate ranking.
6. Sentence-transformer/FAISS retrieval when the model/runtime is available.
7. Gemini wrapper with deterministic mock behavior when no API key is configured.
8. Benchmark metrics and a banking-domain benchmark runner.

## Partially working or coupled limitations

- The database schema anticipates commits and candidate links, but the ingestion and API layers do not populate or expose them.
- Git parsing is disconnected from repository ingestion, so current analysis is not change-aware.
- RAG retrieval is not connected to the database or evaluation runner and has no artifact version/snapshot isolation.
- LLM support is a wrapper and reranker, not a complete consistency-verification workflow.
- The agent layer is absent despite README language describing autonomous agents.
- API CORS is fully permissive (`*`) and should be restricted for deployment.
- Error handling in the Gemini client hides initialization and request failures behind mock/error strings.

## Missing research capabilities

- Change-to-artifact impact analysis.
- Persistent, evidence-backed multi-artifact links across requirements, code, APIs, and tests.
- Consistency rules/findings with reproducible provenance.
- Agent/tool orchestration with bounded actions and verification.
- API artifact extraction and requirement-code-test API relationship modeling.
- Versioned snapshots, incremental re-analysis, and regression tracking.
- Evaluation protocols for change-aware traceability, consistency assurance, and agent ablations.

## Implemented since the initial audit

- Added `artifacts/` with a canonical, typed `ArtifactRecord`, stable
  identity, SHA-256 content hashes, normalized source locations, version/commit
  metadata, and adapters for existing requirement/code/test parser outputs.
- Added `ingestion/repository_source.py` for safe local Git metadata inspection
  and parsed commit snapshots without executing repository code.
- Added `traceability/service.py` for deterministic evidence-bearing
  requirement-code, requirement-test, and code-test candidate links.
- Added `graph/software_graph.py` for bounded local traversal and direct versus
  potentially affected artifact classification.
- Extended RAG results with artifact ID/type, path, source location, score, and
  retrieval reason fields.
- Added `services.VigilantService` for repository import and base/target Git
  change analysis, including canonical artifact persistence, commit/file-change
  persistence, candidate links, evidence, graph impact, deterministic local
  retrieval, and consistency findings.
- Added public `POST /repositories/import` and
  `POST /projects/{project_id}/analyze-change` contracts. Both paths are
  deterministic and do not download an embedding model.
- Added a provider-independent structured LLM interface, an explicit no-LLM
  provider, and a bounded investigation agent; `GeminiClient` remains
  available as an adapter.
- Added a reproducible fixture and end-to-end integration test. Validation:
  **24 passed**, with the existing two dependency deprecation warnings.
- Added lightweight JavaScript/TypeScript function, API-consumer, route, and
  test extraction; duplicate parser outputs and graph projections are
  de-duplicated before persistence.
- Added persisted evidence records and investigation-step records, with
  repository-scoped traceability, graph, evidence, findings, and investigation
  endpoints.
- Executed the live API against the public Flask repository. The import
  completed with 466 code artifacts, 397 tests, 863 canonical artifacts,
  46,135 trace links, and 109,134 graph relationships. Repeated change
  analysis completed without duplicate-evidence failures.

These increments are intentionally additive. The legacy `/api/ingest` route and
parser-specific tables remain compatible; the new public import route uses the
service orchestration and persists the additional research projections.

The first deterministic executable path is now available through
`POST /repositories/import` and `POST /projects/{project_id}/analyze-change`.
It performs repository ingestion, canonical persistence, Git diff analysis,
affected-artifact traversal, targeted provenance-preserving evidence
retrieval, and deterministic consistency findings. The LLM boundary and
bounded investigator are available, but no LLM is required.

## Recommended implementation order

1. Define versioned artifact/evidence/link contracts and wire Git changes into ingestion.
2. Persist traceability candidates and evidence, then expose repository-scoped APIs.
3. Integrate IR and RAG retrieval behind one reproducible analysis service.
4. Add consistency/change-impact analysis with deterministic rules before LLM augmentation.
5. Add LLM verification with strict schemas and surfaced failures.
6. Implement the agent workflow over the above tools.
7. Extend datasets, metrics, and experiments for research comparisons and ablations.
