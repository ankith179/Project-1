# VIGILANT Reference Implementations

This review records public engineering references inspected before rebuilding
the VIGILANT core. VIGILANT reimplements the useful ideas locally and does
not copy source code from these projects.

| Repository | Purpose | Useful component | Dataset | Method | VIGILANT adopts | VIGILANT changes | Known limitation |
|---|---|---|---|---|---|---|---|
| [LiSSA](https://github.com/ArDoCo/LiSSA) | Generic traceability-link recovery | Configured RAG retrieval, caching, gold-link evaluation | Requirements/code and documentation/code replication tasks | Retrieve candidate evidence, then use LLM scoring/reranking | Evidence-first retrieval and reproducible evaluation | Adds Git history, tests, APIs, change impact, and deterministic CPU mode | LLM/API cost and limited continuous change analysis |
| [ARDoCo](https://github.com/ardoco/ardoco) | Architecture documentation/model alignment and inconsistency detection | Separate link recovery from inconsistency analysis | Architecture/documentation/model research datasets | Trace links followed by deviation detection | Two-stage traceability then consistency reasoning | Extends the artifact graph to requirements, code, tests, APIs, and commits | Primarily architecture-focused |
| [ARDoCo TLR](https://github.com/ardoco/tlr) | Traceability-link recovery pipeline | Modular pipeline and artifact-pair evaluation | TLR benchmark artifacts | Candidate generation and link classification | Modular link generation contracts | Uses repository-scoped stable IDs and provenance | Not a complete repository change analyzer |
| [LiSSA replication package](https://github.com/ArDoCo/Replication-Package-ICSE25_LiSSA-Toward-Generic-Traceability-Link-Recovery-through-RAG) | Reproducible LiSSA experiments | Configs, gold links, result files | Published traceability benchmarks | Precision, recall, F1 over gold pairs | Explicit experiment metadata and non-fabricated outputs | Adds change-impact and consistency metrics | Dataset scope is not necessarily multi-artifact |
| [Requirements TLR via RAG replication package](https://github.com/ardoco/Replication-Package-REFSQ25_Requirements-TLR-via-RAG) | Requirements traceability research | Requirements-oriented retrieval experiments | Requirements benchmark artifacts | RAG-assisted TLR | Requirements as first-class artifacts | Connects requirements to code and tests in evolving repos | Requirement-centric scope |
| [Neo4j GraphRAG](https://github.com/neo4j/neo4j-graphrag-python) | Graph retrieval for RAG applications | Graph neighborhood retrieval and provenance | General graph/document corpora | Traverse graph context before generation | Bounded local graph traversal | Uses software-specific typed edges without requiring Neo4j | Graph construction and maintenance cost |
| [Microsoft GraphRAG](https://github.com/microsoft/graphrag) | Graph extraction and community summaries for private text | Entity extraction, graph communities, summarized context | Narrative/private document corpora | LLM extraction, communities, graph-aware retrieval | Structured context assembly | Keeps repository graph deterministic and lightweight | Expensive indexing; not code/test aware |
| [SWE-agent](https://github.com/SWE-agent/SWE-agent) | Agentic repository issue resolution | Inspect, act, verify loop | SWE-bench-style repository tasks | Tool-mediated planning and test verification | Bounded evidence-gathering investigation loop | Does not modify code; reports traceability and consistency evidence | Coding-agent objective differs from assurance |
| [mini-SWE-agent](https://github.com/SWE-agent/mini-swe-agent) | Lightweight software engineering agent | Small tool loop and simple orchestration | SWE-bench-like tasks | Minimal agent/tool protocol | Small local agent surface | Constrains tools to analysis and reporting | Reduced planning sophistication |

## Synthesis

The common reusable pattern is retrieval or structured traversal followed by
explicit verification. VIGILANT’s differentiator is applying that pattern to
versioned requirements, source, APIs, tests, and Git changes while preserving
evidence and uncertainty.
