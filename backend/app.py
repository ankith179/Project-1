import os
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database.connection import init_db
from backend.routes import artifacts, ingestion


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="VIGILANT — Research Platform API",
    description="LLM- and RAG-Enhanced Framework for Continuous Software Traceability and Consistency Assurance",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingestion.router)
app.include_router(artifacts.router)


@app.get("/api/health")
def healthcheck():
    return {
        "status": "HEALTHY",
        "service": "VIGILANT Research Platform",
        "phase": "PHASE_1_INFRASTRUCTURE_AND_EVALUATION"
    }


@app.get("/api/evaluation/latest")
def get_latest_evaluation():
    exp_file = os.path.join(os.path.dirname(__file__), "..", "experiments", "benchmark_results.json")
    if not os.path.exists(exp_file):
        return {"status": "NO_EXPERIMENTS_FOUND"}
    with open(exp_file, "r", encoding="utf-8") as f:
        return json.load(f)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, reload=True)
