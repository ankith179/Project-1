from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import Requirement, CodeArtifact, TestArtifact

router = APIRouter(prefix="/api/artifacts", tags=["Artifacts"])


@router.get("/requirements")
def list_requirements(
    repo_id: Optional[int] = Query(None),
    priority: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Requirement)
    if repo_id is not None:
        query = query.filter(Requirement.repo_id == repo_id)
    if priority is not None:
        query = query.filter(Requirement.priority == priority.upper())
    items = query.all()
    return [item.to_dict() for item in items]


@router.get("/requirements/{req_id}")
def get_requirement(req_id: str, db: Session = Depends(get_db)):
    item = db.query(Requirement).filter(Requirement.req_identifier == req_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Requirement not found")
    return item.to_dict()


@router.get("/code")
def list_code_artifacts(
    repo_id: Optional[int] = Query(None),
    artifact_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(CodeArtifact)
    if repo_id is not None:
        query = query.filter(CodeArtifact.repo_id == repo_id)
    if artifact_type is not None:
        query = query.filter(CodeArtifact.artifact_type == artifact_type.upper())
    items = query.all()
    return [item.to_dict() for item in items]


@router.get("/tests")
def list_test_artifacts(
    repo_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(TestArtifact)
    if repo_id is not None:
        query = query.filter(TestArtifact.repo_id == repo_id)
    items = query.all()
    return [item.to_dict() for item in items]
