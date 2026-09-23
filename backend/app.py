from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from vigilant.agent import InvestigationAgent

app = FastAPI(title="VIGILANT")


class AnalyzeRequest(BaseModel):
    repository: str
    requirements_path: str | None = None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze")
def analyze(request: AnalyzeRequest) -> dict:
    try:
        return InvestigationAgent().investigate(request.repository, request.requirements_path).to_dict()
    except (OSError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
