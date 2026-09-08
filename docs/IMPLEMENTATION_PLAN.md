# VIGILANT Implementation Plan

## Scope and baseline

This plan follows the completed Phase 1 audit and the initial Phase 2
implementation increments in
[CURRENT_STATUS.md](./CURRENT_STATUS.md). It is intentionally a plan only;
remaining Phase 2 work is tracked below.

Baseline evidence:

- Python 3.13.2 in `.venv`
- 14 existing tests pass
- Existing modules are retained unless a later phase demonstrates a concrete
  correctness or integration problem
- `OmniRoute/` is outside this plan and must not be modified
- No large ML model download is required for Phase 1

## Exact implementation sequence

| Phase | Current component | Current status | Problem | Required change | Reason | Dependencies | Expected output |
|---|---|---|---|---|---|---|---|
| 1. Audit and plan | Existing repository, tests, configuration | Complete | Architecture and gaps were not recorded centrally | Maintain audit and this plan | Prevent unnecessary rewrites and unsupported claims | None | Auditable baseline, architecture, and passing test result |
| 2. Unified artifact model | Parser dataclasses, SQLAlchemy artifact tables, RAG dictionaries, evaluation dictionaries | In progress | Multiple representations have different identifiers and fields | Introduce one typed canonical artifact contract and adapters from existing parsers/models | Stable identity and interoperability across ingestion, graph, RAG, agents, and evaluation | Phase 1 | Canonical artifact records with project/version/location metadata |
| 3. Repository ingestion | `ingestion/pipeline.py`, `requirements_parser.py`, `code_parser.py`, `test_parser.py`, `git_parser.py` | In progress | Git history and file changes are parsed but not persisted; no content hashes or version snapshots | Add safe repository discovery, hashes, commit/change persistence, and snapshot-aware ingestion | Unified artifact model | Versioned repository state and repeatable local ingestion |
| 4. Traceability | `traceability/ir_model.py`, `hybrid_model.py` | Working baseline | Candidate links are not persisted with evidence/version and code-to-test links are absent | Build a service that composes lexical, semantic, structural, and annotation signals and stores evidence-backed links | Canonical artifacts and persisted snapshots | Reproducible requirement-code-test links |
| 5. Knowledge graph | `database/models.py` has relationships but no graph service | Missing | No traversal or impact queries use relationships | Add a lightweight local graph projection and traversal service backed by stored artifacts/links/changes | Traceability and ingestion data | Graph nodes/edges and affected-artifact traversal |
| 6. Local RAG | `rag/embedder.py`, `vector_store.py`, `retriever.py` | Partial | RAG is disconnected from project snapshots and returns incomplete evidence metadata | Index canonical artifacts, diffs, commits, links, and docs with metadata validation and evidence-shaped results | Canonical artifacts and snapshot/version IDs | Project-scoped hybrid retrieval with provenance |
| 7. Change detection | `ingestion/git_parser.py` | Partial | Diff parsing is standalone and does not identify modified symbols or affected relationships | Compare snapshots, map changed files/symbols to graph neighbors, and classify direct/potential/unrelated impact | Ingestion, graph, traceability | Change-impact report with classifications |
| 8. LLM abstraction | `llm/gemini_client.py` | Partial | Provider-specific wrapper and broad fallback/error handling | Define provider-independent structured assessment interface; keep Gemini as an adapter and preserve explicit mock mode for tests | RAG evidence and consistency contracts | Validated decision schema without hidden reasoning |
| 9. Agent | `agents/` | Placeholder | No controlled investigation workflow or tools | Implement one bounded investigator orchestrating change, graph, RAG, source/test, and consistency services | Change detection, graph, RAG, LLM abstraction | Evidence-grounded investigation result or `UNCERTAIN` |
| 10. Consistency engine | No service; model support is indirect | Missing | No deterministic requirement-code-test consistency checks or broken-link findings | Add rule-based checks, then optional LLM assessment over collected evidence | Traceability, graph, change impact, RAG | Consistency findings with status, confidence, and evidence |
| 11. Evaluation | `evaluation/metrics.py`, `benchmark_runner.py` | Working baseline | Only baseline requirement-to-code/test ranking is evaluated | Add change-impact and consistency metrics plus model/component provenance | Stable analysis outputs and datasets | Comparable benchmark and research metrics |
| 12. Ablation | No ablation runner | Missing | No evidence for contribution of RAG, KG, agent, history, or execution evidence | Add configuration-driven ablation runs without fabricated labels | Evaluation protocol | Measured component contribution |
| 13. API integration | `backend/app.py`, `backend/routes/*` | Partial | Existing routes expose artifacts/ingestion only and contain some orchestration | Add Pydantic request/response schemas and service-backed project/repository/analysis routes | Completed services | Stable research API boundaries |
| 14. Frontend | `OmniRoute/` exists but is out of scope for Phase 1 | Not audited for integration | UI integration requirements are not yet mapped to backend contracts | Audit and extend only after API contracts stabilize; do not modify now | API integration | Research-oriented evidence/change screens |
| 15. Reports | No report service | Missing | Results are not consolidated into reproducible reports | Add persisted analysis/report DTOs and export formats | Consistency and evaluation outputs | Evidence-backed reports |
| 16. Documentation | README and audit docs | Partial | Current README overstates agent capability and omits limitations | Update documentation after each implemented phase | Prevent misleading research claims | Reproducible setup, limitations, and experiment protocol |

## Phase 2 implementation plan

Phase 2 is the next implementation phase and must be completed before graph,
RAG, agent, or API expansion:

1. Define typed `ArtifactRecord`, `SourceLocation`, `ArtifactVersion`, and
   relationship/evidence value objects in a new canonical module.
2. Define stable IDs from project identity, artifact type, normalized path,
   symbol identity, and version; do not use Python object IDs.
3. Add adapters from `ParsedRequirement`, `ParsedCodeArtifact`, and
   `ParsedTestArtifact` to canonical records.
4. Add database serialization helpers without removing existing tables or
   breaking current tests.
5. Update RAG and evaluation boundaries to accept canonical records through
   adapters, while preserving current dictionary APIs temporarily.
6. Add focused unit tests for identity stability, source locations, version
   handling, and adapter round trips.
7. Run the complete existing test suite and the new focused tests.

## Validation gates for every phase

Each phase must:

1. Run the complete existing test suite.
2. Run focused tests for changed behavior.
3. Exercise affected API routes where applicable.
4. Verify no regression in parser, database, IR, and benchmark behavior.
5. Update `docs/CURRENT_STATUS.md` with observed results.
6. Record measurable metrics and known limitations.

## Explicit non-goals for Phase 1

- No Phase 2 code implementation
- No database migration or schema rewrite
- No large model download
- No external repository cloning
- No arbitrary repository code execution
- No changes to `OmniRoute/`
- No claims that agents, knowledge graph, continuous analysis, or
  consistency assurance are implemented
