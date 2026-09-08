# VIGILANT Architecture

## Research purpose

VIGILANT is a change-aware, multi-artifact traceability and consistency
assurance framework. It investigates software evolution across requirements,
source code, APIs, tests, and Git history. It is not a generic chatbot or a
generic coding agent.

## Target system architecture

```text
Local Git repository / approved repository import
                         |
                         v
                 Repository ingestion
       requirements | source | tests | APIs | Git
                         |
                         v
                 Canonical artifact model
                         |
          +--------------+--------------+
          |                             |
          v                             v
   Relational persistence          Graph projection
          |                             |
          v                             v
  Versioned artifacts, changes,   Traversal and impact
  links, evidence, analyses       relationships
          |                             |
          +--------------+--------------+
                         |
                         v
               Traceability and RAG services
       lexical -> semantic -> structural -> evidence
                         |
                         v
                  Change detection
                         |
                         v
              Controlled investigation agent
       planner -> artifact/graph/RAG tools -> review
                         |
                         v
              Deterministic consistency engine
                    + optional LLM verifier
                         |
                         v
              Structured analysis and evaluation report
```

## Component responsibilities

### Repository ingestion

The ingestion layer discovers supported artifacts, parses Python and Java
source/tests, parses requirements, reads Git history/diffs, calculates content
hashes, and writes versioned records. It must never execute repository code
automatically.

Existing parsers remain the first implementation:

- `ingestion/requirements_parser.py`
- `ingestion/code_parser.py`
- `ingestion/test_parser.py`
- `ingestion/git_parser.py`
- `ingestion/pipeline.py`

### Canonical artifact model

All downstream components consume a stable artifact contract containing at
least:

- stable `artifact_id`
- `project_id`
- `artifact_type`
- normalized path and name
- content and content hash
- version/commit
- timestamp
- source location
- structured metadata
- optional embedding reference

Parser-specific dataclasses and legacy dictionaries are compatibility inputs,
not separate domain models.

### Relational database

SQLAlchemy remains the persistence boundary. It stores repositories and
versioned artifacts, requirements, source/test records, commits, file changes,
trace links, graph relationships, evidence, analyses, consistency results, and
evaluation runs. Existing tables should be extended or adapted before new
redundant tables are introduced.

### Traceability service

The traceability service keeps the current TF-IDF, BM25, and hybrid methods as
reproducible baselines. It adds semantic and structural evidence, supports:

- requirement -> code
- requirement -> test
- code -> test

Every link includes source/target identity, relationship type, score, method,
evidence, confidence, version, and validation status. LLM output may verify or
explain a candidate but cannot invent an unsupported link.

### Knowledge graph

The first graph is a local projection compatible with SQLAlchemy rather than a
new external graph infrastructure. Nodes represent projects, requirements,
files, classes, methods, tests, commits, and APIs. Edges represent
implementation, testing, dependency, calls, API implementation, and commit
modification relationships.

The graph is operational: it supports traversal, traceability queries, and
change-impact discovery. It is not only a visualization layer.

### RAG

The local RAG corpus includes requirements and acceptance criteria, source,
tests, APIs, documentation, commits, diffs, and traceability evidence. The
retriever returns provenance-rich evidence:

- artifact ID
- path
- source location
- relevance score
- content
- retrieval reason

Local embedding/vector components are preferred. Repository contents must not
be sent to an external provider unless explicitly configured.

### Change detection

Change analysis compares repository versions and classifies artifacts as:

- `DIRECTLY_CHANGED`
- `POTENTIALLY_AFFECTED`
- `UNRELATED`

It combines changed files/symbols, graph neighbors, trace links, dependency
and call relationships, test relationships, and requirement references.

### Agent

VIGILANT uses one controlled investigator rather than many decorative agents.
The investigator receives a change, gathers graph/RAG/artifact evidence,
inspects relevant source/tests, checks evidence sufficiency, and emits a
structured result. Missing evidence produces `UNCERTAIN`; it must not be
filled with speculation or private chain-of-thought.

### LLM layer

The application depends on a provider-independent interface. Gemini is an
adapter, not the domain contract. Providers return validated structured
decisions containing status, confidence, affected artifacts, broken links,
evidence, concise reasoning summary, and recommended action. Malformed or
failed responses are surfaced as failures or uncertainty, not silently treated
as successful analysis.

### Consistency engine

Deterministic rules are evaluated first:

- requirement vs. implementation
- requirement vs. tests
- code vs. tests
- change vs. existing trace links

RAG, graph, traceability, execution evidence (when safely available), and
optional LLM assessment are supporting evidence sources. The final status is
`CONSISTENT`, `INCONSISTENT`, or `UNCERTAIN`, with confidence and provenance.

### Evaluation

The current benchmark runner remains the baseline path. Future experiments
compare classical IR, embedding/ML, LLM-only, LLM+RAG, LLM+RAG+KG, and full
VIGILANT. Metrics include traceability ranking, change-impact, consistency,
latency, retrieval cost, agent steps, and resource usage. Ablations must be
configuration-driven and must not fabricate labels.

## Data flow

1. Import a local or explicitly approved repository.
2. Discover and parse requirements, source, tests, APIs, and Git history.
3. Normalize all records into canonical artifacts with stable IDs and versions.
4. Persist artifacts and changes in SQLAlchemy.
5. Build graph relationships from explicit metadata and validated trace links.
6. Build a project/version-scoped RAG index with provenance.
7. Compare versions and discover direct/potentially affected artifacts.
8. Run controlled agent investigation over graph, RAG, artifact, and diff tools.
9. Run deterministic consistency checks and optional structured LLM verification.
10. Persist findings, evidence, metrics, and reports.

## API boundaries

Existing baseline routes:

- `GET /api/health`
- `GET /api/evaluation/latest`
- `POST /api/ingest`
- `GET /api/ingest/repositories`
- `GET /api/ingest/repositories/{repo_id}/summary`
- `GET /api/artifacts/requirements`
- `GET /api/artifacts/code`
- `GET /api/artifacts/tests`

Target service-backed routes, to be implemented only after their contracts are
stable:

- `POST /projects`
- `GET /projects`
- `POST /repositories/import`
- `GET /repositories/{id}`
- `POST /projects/{id}/ingest`
- `GET /projects/{id}/artifacts`
- `GET /projects/{id}/traceability`
- `GET /projects/{id}/graph`
- `POST /projects/{id}/analyze-change`
- `GET /projects/{id}/impact/{commit}`
- `POST /projects/{id}/investigate`
- `GET /projects/{id}/consistency`
- `POST /projects/{id}/evaluate`
- `GET /projects/{id}/reports`

Routes should validate Pydantic schemas and delegate to services; business
logic must not be placed directly in route handlers.

## Security and reliability boundaries

- Never execute untrusted repository code as part of ingestion.
- Any future test/build execution requires sandboxing, timeout, resource
  limits, restricted filesystem/network, and captured output.
- Secrets remain in environment configuration and are never committed.
- External LLM use is opt-in and must be visible in configuration.
- Errors must be surfaced with structured status; broad silent fallbacks are
  not acceptable in production analysis.

## Current-to-target mapping

| Target responsibility | Existing implementation | Decision |
|---|---|---|
| Requirements parsing | `ingestion/requirements_parser.py` | Retain and adapt |
| Source parsing | `ingestion/code_parser.py` | Retain and adapt |
| Test parsing | `ingestion/test_parser.py` | Retain and adapt |
| Git parsing | `ingestion/git_parser.py` | Retain, wire into ingestion |
| Persistence | `database/connection.py`, `database/models.py` | Retain and extend |
| Classical traceability | `traceability/ir_model.py`, `hybrid_model.py` | Retain as baselines |
| Local RAG | `rag/*` | Retain, add canonical metadata/provenance |
| LLM adapter | `llm/gemini_client.py` | Retain as provider adapter, tighten contract |
| Agent orchestration | `agents/` | Implement after prerequisites |
| Evaluation | `evaluation/*` | Retain and extend |
| API | `backend/*` | Retain routes, move new logic into services |
| Frontend | `OmniRoute/` | Do not modify during Phase 1 |
