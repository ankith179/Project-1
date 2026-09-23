# Phase 0: Reference System Analysis for VIGILANT

This document records the evidence-based analysis of the reference systems that most directly inform the VIGILANT research direction. The goal is to identify reusable ideas, where they are strong, and where VIGILANT must improve beyond them.

## 1. LiSSA (ArDoCo)

- Repository: https://github.com/ArDoCo/LiSSA
- Related replication package: https://github.com/ArDoCo/Replication-Package-ICSE25_LiSSA-Toward-Generic-Traceability-Link-Recovery-through-RAG

### Repository purpose
LiSSA is a generic traceability-link recovery framework that combines LLMs with RAG to recover links between software artifacts such as requirements, documentation, code, and architecture models. Its emphasis is on generic TLR rather than a single project-specific method.

### Useful components
- Config-driven evaluation pipeline and reproducible execution setup.
- Retrieval-augmented generation pipeline for artifact linking.
- Gold-standard evaluation outputs in CSV and Markdown result files.
- Caching to make LLM-based experiments reproducible.
- Prompt optimization / configurable retrieval strategies.

### Algorithms
- Retrieval-first TLR using contextual evidence retrieval from artifact corpora.
- Hybrid reasoning over textual similarity and retrieved evidence to produce candidate trace links.
- LLM-powered scoring and reranking of candidate links.
- Evaluation framework centered on gold-standard precision/recall/F1 on paired artifact datasets.

### Datasets
- Requirements-to-code and documentation-to-code benchmarks from the replication package.
- Artifact pairs with explicit gold links used to compute ranking quality.
- Configuration-based benchmark definitions for different software-engineering tasks.

### Evaluation
- Standard TLR evaluation metrics: true positives, false positives, false negatives, precision, recall, and F1.
- Evaluation is configured through artifact-specific settings rather than ad hoc scripts.
- Results are stored as structured output files and support experiment reproducibility.

### Limitations
- Strongly centered on retrieval and LLM reasoning for link recovery; not built around continuous change analysis.
- Heavy reliance on configuration and LLM APIs, which can reduce local reproducibility and make evaluation more costly.
- Not designed specifically for multi-artifact consistency investigation across evolving repositories.
- Limited concept of repository history, commit-aware impact, and requirement-to-code-to-test change propagation.

### What VIGILANT will reuse conceptually
- Generic TLR framing beyond a single artifact pair.
- RAG-grounded evidence retrieval for link generation.
- Gold-standard evaluation mindset with explicit metrics and reproducible configs.
- Configuration-driven experimentation and artifact-pair benchmarks.

### What VIGILANT will improve
- Add change-aware and history-aware tracing over repository commits and diffs.
- Model multi-artifact relationships: Requirement → Code, Requirement → Test, Code → Test, and API ↔ implementation.
- Incorporate repository-level evidence, source location, and change impact rather than only static candidate links.
- Move from link recovery alone to consistency assurance and impact diagnosis.

## 2. ARDoCo / TLR ecosystem

- Repository: https://github.com/ardoco/ardoco
- Additional TLR repo: https://github.com/ardoco/tlr

### Repository purpose
ARDoCo focuses on connecting architecture documentation and models with traceability-link recovery while detecting missing or deviating elements and inconsistencies. The project is broader than pure retrieval and includes inconsistency identification after links are established.

### Useful components
- Traceability pipeline design that separates link recovery from later inconsistency detection.
- Architecture/documentation and model alignment concepts.
- Explicit focus on missing and deviating elements rather than only retrieval accuracy.
- Strong research framing around documentation-driven software understanding.

### Algorithms
- Link recovery plus downstream inconsistency detection.
- Likely combination of textual similarity, structured model information, and trace links.
- Systems-level emphasis on aligning artifacts in software architecture contexts.

### Datasets
- Architecture/documentation and model benchmark data used for traceability and inconsistency studies.
- Research assets and evaluation setups tied to requirement/model artifacts.

### Evaluation
- Traceability and inconsistency evaluation based on aligned artifact structures and known ground truth.
- Strong emphasis on correctness of relationships between documentation and software architecture artifacts.

### Limitations
- Primarily architecture-centric; less focus on evolving Git repositories and code/test traceability at commit granularity.
- Less aligned with continuous software change and agentic impact analysis than the VIGILANT objective requires.

### What VIGILANT will reuse conceptually
- A two-stage view: recover links, then decide whether they are consistent or broken.
- Structured artifact alignment across natural-language and modeled artifacts.
- The notion that traceability is not only retrieval but also inconsistency diagnosis.

### What VIGILANT will improve
- Extend beyond architecture/documentation to source code, tests, APIs, and repository evolution.
- Add change metadata and evidence-based impact analysis over each commit.
- Support dynamic validation of artifacts against requirements and tests after code changes.

## 3. Neo4j GraphRAG

- Repository: https://github.com/neo4j/neo4j-graphrag-python

### Repository purpose
Neo4j GraphRAG packages a production-oriented graph-based retrieval layer for RAG workflows. It demonstrates how graph structure can be used to preserve relationships among entities and improve contextual grounding for LLM answers.

### Useful components
- Graph-native retrieval and traversal abstractions.
- Entity/relationship extraction patterns for text-based corpora.
- Graph-backed context formation for LLM queries.
- Retrieval over graph neighborhoods rather than plain chunk similarity alone.

### Algorithms
- Knowledge graph construction from text or semi-structured sources.
- Neighborhood retrieval and graph walk strategies to gather relevant context.
- LLM answer synthesis grounded in graph neighborhoods and connected entities.

### Datasets
- General-purpose graph-enabled knowledge corpora and document data.
- No single software-traceability benchmark is central to the project.

### Evaluation
- QA-oriented evaluations emphasizing answer grounding, factuality, and contextual coverage.
- Not primarily benchmarked for requirement-to-code traceability or change-impact tasks.

### Limitations
- Focused on graph-enhanced QA rather than software engineering traceability.
- Requires graph construction and index maintenance, which can be operationally expensive.
- Not naturally aligned with code/test/repository diff semantics.

### What VIGILANT will reuse conceptually
- Graph structure as a retrieval and reasoning substrate.
- Neighborhood-based contextualization over connected artifact nodes.
- Multi-hop reasoning over entities relevant to a change.

### What VIGILANT will improve
- Use graph nodes and edges that correspond to repository artifacts, versions, requirements, code elements, tests, and API contracts.
- Add traceability-specific edges such as REQUIREMENT_TO_CODE, CODE_TO_TEST, API_TO_IMPLEMENTATION, and CHANGE_IMPACT.
- Keep the graph local, deterministic, and repository-scoped for software engineering tasks.

## 4. Microsoft GraphRAG

- Repository: https://github.com/microsoft/graphrag

### Repository purpose
Microsoft GraphRAG is a research-oriented pipeline that builds a graph from unstructured text and then uses graph communities and summaries to improve retrieval and question answering on private or narrative corpora.

### Useful components
- Knowledge graph extraction from large text corpora.
- Community detection and graph summarization.
- Context assembly through graph and entity-aware retrieval.
- Scalable pipeline suited for unstructured documents.

### Algorithms
- LLM-assisted extraction of entities, relationships, and community summaries.
- Graph summarization to form high-level context for downstream reasoning.
- Retrieval from graph communities rather than random document slices.

### Datasets
- Document-centric corpora, especially narrative/private data.
- Research benchmarks in conversational and exploratory question answering, not software traceability.

### Evaluation
- Quality evaluations based on answer usefulness and evidence grounding over document corpora.
- Not directly aligned with software engineering precision/recall on trace links.

### Limitations
- Expensive indexing and summarization pipeline.
- Not tailored to code, test, requirement, API, or commit-level software semantics.
- Requires substantial compute and configuration for large corpora.

### What VIGILANT will reuse conceptually
- Graph community and contextual summarization as evidence synthesis.
- Retrieval that benefits from structured semantic neighborhoods.
- The principle that graph structure can improve answer quality and explainability.

### What VIGILANT will improve
- Ground graph data in repository artifacts, code properties, call relations, requirement semantics, and Git changes.
- Focus on software traceability and consistency instead of general private-document QA.
- Add deterministic, cheaper local graph projection for research prototypes and standard workstations.

## 5. SWE-agent / mini-SWE-agent

- Repository: https://github.com/SWE-agent/SWE-agent
- Related lighter variant: https://github.com/SWE-agent/mini-swe-agent

### Repository purpose
SWE-agent is an autonomous software engineering agent designed to take a repository issue, explore files, edit code, and validate fixes by running tests. The project demonstrates a realistic agent loop for software tasks.

### Useful components
- Agentic task loop: inspect → reason → act → verify.
- Tool-execution patterns for file search, read, patch, and command execution.
- Validation loop that runs tests to check correctness.
- Workflow decomposition for real repository tasks.

### Algorithms
- Iterative planning and execution over project files.
- Evidence gathering through repository navigation and tooling.
- Syntax/test validation loop as a correctness signal.

### Datasets
- SWE-bench-like issue-to-fix tasks and repository-level benchmark suites.
- Execution-based validation using repository tests.

### Evaluation
- End-to-end task success on issue resolution and test pass rates.
- Not traceability-specific, but strongly relevant to verification in agentic engineering workflows.

### Limitations
- Focused on code modification rather than change-impact analysis across requirements, tests, and APIs.
- Agent loop is broad and tool-heavy; it does not isolate traceability evidence or consistency explanation as first-class outputs.
- The main objective is patch generation, not repository-wide traceability assurance.

### What VIGILANT will reuse conceptually
- Agent loop with evidence acquisition and verification.
- Structured tool use for repository investigation.
- Test-based verification as a final correctness gate.

### What VIGILANT will improve
- Restrict the agent to traceability and consistency investigation instead of unrestricted code modification.
- Make the agent evidence-grounded: cite artifact links, change sets, tests, and API contracts.
- Produce explainable assessments such as traceable, broken, uncertain, or impacted, not just a patch.

## Cross-system synthesis

Across LiSSA, ARDoCo, Neo4j GraphRAG, Microsoft GraphRAG, and SWE-agent, four patterns are consistently useful:

1. Start from artifact evidence and retrieval, not just raw model output.
2. Use structured relationships to improve reasoning and context.
3. Evaluate results against explicit ground truth or execution-based validation.
4. Treat LLMs as reasoning components, not as the sole source of truth.

The most important gap across these systems is that they do not directly model the software-engineering lifecycle that VIGILANT targets: requirement-to-code-to-test continuity, API contract alignment, repository history, and continuous change impact over time.

## Research positioning for VIGILANT

VIGILANT will not copy these systems wholesale. Instead, it will combine their strengths into a software traceability and consistency framework for evolving repositories:

- Use RAG and retrieval for evidence gathering across requirements, code, tests, and APIs.
- Use a lightweight graph for artifact connectivity and affected-node traversal.
- Use Git history and change diffs to drive impact analysis.
- Use deterministic traceability baselines and LLM reasoning as complementary components.
- Keep the system local, reproducible, and grounded in repository evidence rather than opaque model behavior.

## Expected VIGILANT improvements over the reference systems

- Continuous, change-aware traceability over repository history and commit sequences.
- Multi-artifact coverage across requirements, code, tests, APIs, and frontend/backend interfaces.
- Deterministic evidence collections with explicit citation and score provenance.
- Consistency assessment that classifies broken, uncertain, or preserved relationships.
- Agentic investigation constrained to analysis and explanation rather than unrestricted code patching.
- Local research prototype design suitable for CPU-only workstations and reproducible experiments.

## Summary

The reference systems confirm the research direction but also highlight the missing gap: current methods are strong for retrieval, graph reasoning, or agentic coding, yet not for evidence-grounded, continuous, multi-artifact software consistency assurance across evolving repositories. VIGILANT is positioned to bridge that gap by combining traceability services, local graph traversals, Git-aware change analysis, retrieval evidence, and explicit consistency evaluation on real repository data.
