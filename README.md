# VIGILANT

**LLM- and RAG-Enhanced Agentic Framework for Continuous Software Traceability and Consistency Assurance across Requirements, Code, and Tests**

VIGILANT is an M.Tech research prototype and engineering framework that bridges the gap between software engineering artifacts (Natural Language Requirements, Java Source Code, and Test Suites) through hybrid Information Retrieval (IR), Vector-based Retrieval-Augmented Generation (RAG), and Large Language Model (LLM) reasoning agents.

---

## Key Features

- **Multi-Modal Artifact Ingestion & Parsing**:
  - Requirements Parser (`ingestion/requirements_parser.py`)
  - Java AST Code Parser (`ingestion/code_parser.py`) powered by `javalang`
  - Test Suite Parser (`ingestion/test_parser.py`)
  - Git Commit & Diff History Parser (`ingestion/git_parser.py`)
- **Classical IR Traceability Baselines (Phase 1)**:
  - Vector Space Model (TF-IDF + Cosine Similarity)
  - BM25 Okapi Probabilistic Retrieval (`traceability/ir_model.py`)
  - Hybrid Weighted Fusion (`traceability/hybrid_model.py`)
- **RAG Semantic Layer (Phase 2)**:
  - Dense text embeddings via `sentence-transformers` (`all-MiniLM-L6-v2`)
  - Fast local vector storage with FAISS (`rag/vector_store.py`)
  - Hybrid RAG Retriever (`rag/retriever.py`)
- **LLM Reasoning & Consistency Checking (Phase 3)**:
  - Gemini API integration with structured Pydantic outputs (`llm/gemini_client.py`)
  - Automated link justification and re-ranking
  - Multi-artifact consistency verification (Requirement ↔ Code ↔ Tests)
- **FastAPI REST Service & Database**:
  - Full relational persistence via SQLAlchemy SQLite (`database/models.py`)
  - REST endpoints for artifact exploration, ingestion, and link querying (`backend/`)
- **Benchmark Evaluation Suite**:
  - Research evaluation metrics: Precision@K, Recall@K, Mean Average Precision (MAP), Mean Reciprocal Rank (MRR)
  - Automated benchmark runner with benchmark datasets (`evaluation/benchmark_runner.py`)

---

## Project Structure

```text
├── agents/             # Autonomous agent orchestrators
├── backend/            # FastAPI REST backend and endpoints
│   └── routes/         # API routes for artifacts, ingestion, links
├── database/           # SQLAlchemy database models and connection engine
├── datasets/           # Software traceability benchmark datasets (e.g. eTour)
├── evaluation/         # Traceability evaluation metrics (MAP, MRR, P@K, R@K)
├── experiments/        # Research benchmark experiment scripts
├── ingestion/          # Parsers for requirements, Java code, tests, and git
├── llm/                # Gemini client, prompt templates, and reasoning
├── rag/                # Embeddings, FAISS vector store, and semantic retriever
├── scripts/            # CLI utilities and benchmark execution runners
├── tests/              # Pytest test suite
├── .gitignore          # Git exclusion rules
├── requirements.txt    # Python package dependencies
└── README.md           # Project documentation
```

---

## Getting Started

### 1. Prerequisites
- Python 3.10+
- Git

### 2. Setup Virtual Environment
```bash
# Windows
py -m venv .venv
.venv\Scripts\activate

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configuration
Copy the example environment file and set your Gemini API key (optional for mock testing):
```bash
copy .env.example .env
```

### 5. Run the Test Suite
```bash
pytest tests/
```

### 6. Start the API Server
```bash
uvicorn backend.app:app --reload --port 8000
```
API Documentation will be available at `http://127.0.0.1:8000/docs`.

---

## Research & Authors
- **Repository**: [https://github.com/ankith179/Project-1](https://github.com/ankith179/Project-1)
