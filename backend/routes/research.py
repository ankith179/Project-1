from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.schemas import ChangeAnalysisRequest, RepositoryImportRequest
from database.connection import get_db
from database.models import (
    CandidateLink,
    CanonicalArtifact,
    EvidenceRecord,
    GraphRelationship,
    ConsistencyFinding,
)
from agents.investigator import InvestigationAgent
from services.orchestration import VigilantService

router = APIRouter(tags=["Research workflows"])


@router.post("/repositories/import")
def import_repository(
    payload: RepositoryImportRequest,
    db: Session = Depends(get_db),
):
    try:
        return VigilantService(db).import_repository(
            repo_name=payload.repo_name or "",
            repo_path=payload.repo_path or "",
            repository_url=payload.repository_url,
            requirements_path=payload.requirements_path,
            max_commits=payload.max_commits,
        )
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/projects/{project_id}/analyze-change")
def analyze_change(
    project_id: int,
    payload: ChangeAnalysisRequest | None = None,
    base_commit: str | None = Query(default=None),
    target_commit: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    payload = payload or ChangeAnalysisRequest(
        base_commit=base_commit or "HEAD~1",
        target_commit=target_commit,
    )
    try:
        return VigilantService(db).analyze_change(
            project_id=project_id,
            base_commit=payload.base_commit or "",
            target_commit=payload.target_commit,
            max_depth=payload.max_depth,
        )
    except ValueError as exc:
        status = 404 if "Project not found" in str(exc) else 400
        raise HTTPException(status_code=status, detail=str(exc)) from exc


@router.get("/projects/{project_id}/traceability")
def get_traceability(project_id: int, db: Session = Depends(get_db)):
    return [
        item.to_dict()
        for item in db.query(CandidateLink).filter(CandidateLink.repo_id == project_id).all()
    ]


@router.get("/projects/{project_id}/graph")
def get_graph(project_id: int, db: Session = Depends(get_db)):
    return [
        item.to_dict()
        for item in db.query(GraphRelationship).filter(GraphRelationship.repo_id == project_id).all()
    ]


@router.get("/projects/{project_id}/evidence")
def get_evidence(project_id: int, db: Session = Depends(get_db)):
    return [
        {
            "evidence_id": item.evidence_id,
            "artifact_id": item.artifact_id,
            "path": item.path,
            "version": item.version,
            "score": item.score,
            "reason": item.reason,
            "payload": json.loads(item.payload_json or "{}"),
        }
        for item in db.query(EvidenceRecord).filter(EvidenceRecord.repo_id == project_id).all()
    ]


@router.get("/projects/{project_id}/artifacts")
def get_canonical_artifacts(project_id: int, db: Session = Depends(get_db)):
    return [
        item.to_dict()
        for item in db.query(CanonicalArtifact)
        .filter(CanonicalArtifact.repo_id == project_id)
        .all()
    ]


@router.get("/projects/{project_id}/findings")
def get_findings(project_id: int, db: Session = Depends(get_db)):
    return [
        item.to_dict()
        for item in db.query(ConsistencyFinding).filter(ConsistencyFinding.repo_id == project_id).all()
    ]


@router.post("/projects/{project_id}/investigate")
def investigate_change(
    project_id: int,
    payload: ChangeAnalysisRequest,
    db: Session = Depends(get_db),
):
    try:
        return InvestigationAgent(VigilantService(db)).investigate(
            project_id=project_id,
            base_commit=payload.base_commit or "",
            target_commit=payload.target_commit,
        )
    except ValueError as exc:
        status = 404 if "Project not found" in str(exc) else 400
        raise HTTPException(status_code=status, detail=str(exc)) from exc
