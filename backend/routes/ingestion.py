import os
from datetime import datetime
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import Repository
from ingestion.pipeline import IngestionPipeline

router = APIRouter(prefix="/api/ingest", tags=["Ingestion"])


class IngestionRequest(BaseModel):
    repo_name: str
    repo_path: str
    requirements_path: str = ""


@router.post("")
def trigger_ingestion(payload: IngestionRequest, db: Session = Depends(get_db)):
    if not os.path.exists(payload.repo_path):
        raise HTTPException(status_code=400, detail=f"Repository path does not exist: {payload.repo_path}")

    pipeline = IngestionPipeline(db_session=db)
    req_path = payload.requirements_path or None
    summary = pipeline.ingest_repository(
        repo_name=payload.repo_name,
        repo_path=payload.repo_path,
        requirements_path=req_path
    )
    return summary


@router.get("/repositories")
def list_repositories(db: Session = Depends(get_db)):
    repos = db.query(Repository).all()
    res = []
    for r in repos:
        res.append({
            "id": r.id,
            "name": r.name,
            "root_path": r.root_path,
            "requirements_count": len(r.requirements),
            "code_artifacts_count": len(r.code_artifacts),
            "tests_count": len(r.test_artifacts),
            "created_at": r.created_at.isoformat() if r.created_at else None
        })
    return res


@router.get("/repositories/{repo_id}/summary")
def get_repository_summary(repo_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    created_at = repo.created_at
    return {
        "repository_id": repo.id,
        "name": repo.name,
        "root_path": repo.root_path,
        "requirements_count": len(repo.requirements),
        "code_artifacts_count": len(repo.code_artifacts),
        "tests_count": len(repo.test_artifacts),
        "created_at": created_at.isoformat() if isinstance(created_at, datetime) else None
    }

