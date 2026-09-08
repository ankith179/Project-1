from __future__ import annotations

import json
import os
import subprocess
import hashlib
import tempfile
from urllib.parse import urlparse
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from artifacts.models import (
    artifact_from_code,
    artifact_from_requirement,
    artifact_from_test,
)
from consistency.engine import ConsistencyEngine
from database.models import (
    AnalysisRun,
    CandidateLink,
    CanonicalArtifact,
    Commit,
    ConsistencyFinding,
    EvidenceRecord,
    FileChange,
    GraphRelationship,
    Repository,
)
from graph.software_graph import SoftwareArtifactGraph
from ingestion.git_parser import GitHistoryParser
from ingestion.pipeline import IngestionPipeline
from ingestion.repository_source import LocalGitRepository
from traceability.service import TraceabilityService
from rag.evidence import TargetedEvidenceRetriever


class VigilantService:
    """Coordinates safe ingestion, evidence, graph projection and analysis."""

    def __init__(self, db: Session, link_threshold: float = 0.15):
        self.db = db
        self.linker = TraceabilityService(threshold=link_threshold)
        self.consistency = ConsistencyEngine()
        self.rag = TargetedEvidenceRetriever()

    def import_repository(
        self,
        repo_name: str,
        repo_path: str = "",
        repository_url: Optional[str] = None,
        requirements_path: Optional[str] = None,
        max_commits: int = 50,
    ) -> dict[str, Any]:
        repo_path = self._resolve_repository_path(repo_path, repository_url)
        if requirements_path and not os.path.isabs(requirements_path):
            candidate = os.path.join(os.path.abspath(repo_path), requirements_path)
            if os.path.exists(candidate):
                requirements_path = candidate
        if requirements_path and not os.path.isfile(requirements_path):
            raise ValueError(f"Requirements file does not exist: {requirements_path}")
        summary = IngestionPipeline(db_session=self.db).ingest_repository(
            repo_name=repo_name,
            repo_path=repo_path,
            requirements_path=requirements_path,
        )
        repo = self.db.get(Repository, summary["repository_id"])
        if repo is None:
            raise ValueError("Repository was not persisted")
        # Bulk deletes in the legacy pipeline intentionally preserve its
        # compatibility behavior; expire relationship collections before
        # building the new projections on a reused SQLAlchemy session.
        self.db.expire(repo, ["requirements", "code_artifacts", "test_artifacts", "links"])

        self._persist_canonical(repo)
        git_summary = self._persist_git_history(repo, max_commits=max_commits)
        links = self._generate_and_persist_links(repo)
        graph_relationship_count = self._persist_graph_relationships(repo, links)
        summary.update(
            {
                "project_id": repo.id,
                "snapshot": {
                    "version": git_summary.get("commit_id"),
                    "commits_ingested": git_summary.get("commits_ingested", 0),
                },
                "links_ingested": len(links),
                "artifact_counts": {
                    "requirements": summary["requirements_ingested"],
                    "code": summary["code_artifacts_ingested"],
                    "tests": summary["tests_ingested"],
                    "canonical": self.db.query(CanonicalArtifact)
                    .filter(CanonicalArtifact.repo_id == repo.id)
                    .count(),
                },
                "commit_count": git_summary.get("commits_ingested", 0),
                "trace_link_count": len(links),
                "graph_relationship_count": graph_relationship_count,
                "rag_index_status": "READY_TARGETED_LEXICAL",
                "status": "SUCCESS",
            }
        )
        return summary

    def analyze_change(
        self,
        project_id: int,
        base_commit: str,
        target_commit: Optional[str] = None,
        max_depth: int = 3,
    ) -> dict[str, Any]:
        repo = self.db.get(Repository, project_id)
        if repo is None:
            raise ValueError(f"Project not found: {project_id}")
        source = LocalGitRepository(repo.root_path)
        if not source.is_git_repository():
            raise ValueError("Change analysis requires a Git repository")
        try:
            patch = source.diff(base_commit, target_commit)
        except subprocess.CalledProcessError as exc:
            detail = (exc.stderr or "").strip() or "invalid Git reference"
            raise ValueError(f"Unable to compute Git change: {detail}") from exc
        changes = GitHistoryParser().parse_unified_diff(patch)
        target_version = target_commit or source.current_commit()
        requirements, code, tests = self._artifact_dicts(repo)
        links = [link.to_dict() for link in repo.links]
        structural = self._structural_relationships(code)

        changed_paths = {change.file_path for change in changes}
        changed_ids = [
            str(item.get("artifact_identifier"))
            for item in code
            if item.get("file_path") in changed_paths
        ]
        changed_ids.extend(
            str(item.get("test_identifier"))
            for item in tests
            if item.get("file_path") in changed_paths
        )

        graph = self._build_graph(links + structural)
        affected = graph.affected_artifacts(changed_ids, max_depth=max_depth)
        findings = self.consistency.analyze(
            requirements, code, tests, links, changed_ids=changed_ids
        )
        run_result = {
            "changed_files": [change.to_dict() for change in changes],
            "changed_artifacts": changed_ids,
            "impacted_artifacts": affected,
            "consistency_findings": findings,
        }
        run = AnalysisRun(
            repo_id=repo.id,
            run_type="CHANGE_ANALYSIS",
            base_version=base_commit,
            target_version=target_version,
            status="COMPLETED",
            result_json=json.dumps(run_result, default=str, sort_keys=True),
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(run)
        self.db.flush()
        evidence = self._targeted_evidence(changed_ids, links, code, tests)
        for item in evidence:
            evidence_id = item.get("evidence_id") or hashlib.sha256(
                json.dumps(item, sort_keys=True, default=str).encode("utf-8")
            ).hexdigest()[:24]
            item["evidence_id"] = evidence_id
            evidence_record = self.db.query(EvidenceRecord).filter(
                EvidenceRecord.repo_id == repo.id,
                EvidenceRecord.evidence_id == evidence_id,
            ).first()
            if evidence_record is None:
                evidence_record = EvidenceRecord(
                    repo_id=repo.id,
                    evidence_id=evidence_id,
                    created_at=datetime.now(timezone.utc),
                )
                self.db.add(evidence_record)
            evidence_record.run_id = run.id
            evidence_record.artifact_id = item.get("artifact_id") or item.get("source")
            evidence_record.path = item.get("path")
            evidence_record.version = item.get("version")
            evidence_record.score = item.get("score")
            evidence_record.reason = item.get("reason")
            evidence_record.payload_json = json.dumps(item, default=str, sort_keys=True)
        for finding in findings:
            self.db.add(
                ConsistencyFinding(
                    repo_id=repo.id,
                    run_id=run.id,
                    rule_id=finding["rule_id"],
                    status=finding["status"],
                    severity=finding["severity"],
                    confidence=finding.get("confidence", 0.0),
                    subject_id=finding["subject_id"],
                    message=finding["message"],
                    evidence=json.dumps(finding.get("evidence", []), default=str),
                    created_at=datetime.now(timezone.utc),
                )
            )
        self.db.commit()
        return {
            "project_id": repo.id,
            "repository_id": repo.id,
            "base_version": base_commit,
            "target_version": target_version,
            "status": "COMPLETED",
            "changed_files": [change.to_dict() for change in changes],
            "changed_artifacts": changed_ids,
            "impacted_artifacts": [
                {"artifact_id": key, "classification": value}
                for key, value in affected.items()
            ],
            "rag_evidence": evidence,
            "consistency_findings": findings,
            "analysis_run_id": run.id,
        }

    @staticmethod
    def _resolve_repository_path(repo_path: str, repository_url: Optional[str]) -> str:
        if repository_url:
            parsed = urlparse(repository_url)
            if parsed.scheme not in {"http", "https", "git"} or not parsed.netloc:
                raise ValueError("repository_url must be an absolute HTTP(S) or Git URL")
            cache_key = hashlib.sha256(repository_url.encode("utf-8")).hexdigest()[:16]
            destination = os.path.join(tempfile.gettempdir(), "vigilant-repositories", cache_key)
            if not os.path.isdir(os.path.join(destination, ".git")):
                os.makedirs(os.path.dirname(destination), exist_ok=True)
                subprocess.run(
                    ["git", "clone", "--", repository_url, destination],
                    check=True,
                    capture_output=True,
                    text=True,
                )
            return destination
        if not repo_path or not os.path.isdir(repo_path):
            raise ValueError(f"Repository path does not exist: {repo_path}")
        return repo_path

    def _persist_git_history(self, repo: Repository, max_commits: int) -> dict[str, Any]:
        source = LocalGitRepository(repo.root_path)
        if not source.is_git_repository():
            return {"commit_id": None, "commits_ingested": 0}
        snapshot = source.read_history(max_commits=max_commits)
        for parsed in snapshot.commits:
            commit = (
                self.db.query(Commit)
                .filter(Commit.repo_id == repo.id, Commit.commit_hash == parsed.commit_hash)
                .first()
            )
            if commit is None:
                commit = Commit(
                    repo_id=repo.id,
                    commit_hash=parsed.commit_hash,
                    author=parsed.author,
                    timestamp=parsed.timestamp,
                    message=parsed.message,
                    created_at=datetime.now(timezone.utc),
                )
                self.db.add(commit)
                self.db.flush()
            else:
                commit.message = parsed.message
            existing = {change.file_path for change in commit.changes}
            for parsed_change in parsed.changes:
                if parsed_change.file_path in existing:
                    continue
                self.db.add(
                    FileChange(
                        commit_id=commit.id,
                        change_type=parsed_change.change_type,
                        file_path=parsed_change.file_path,
                        old_path=parsed_change.old_path,
                        diff_content=parsed_change.diff_content,
                        line_changes=json.dumps(
                            {
                                "added": parsed_change.added_lines,
                                "deleted": parsed_change.deleted_lines,
                            }
                        ),
                    )
                )
        self.db.commit()
        return {
            "commit_id": snapshot.commit_id,
            "commits_ingested": len(snapshot.commits),
        }

    def _persist_canonical(self, repo: Repository) -> None:
        self.db.query(CanonicalArtifact).filter(
            CanonicalArtifact.repo_id == repo.id
        ).delete(synchronize_session=False)
        project_id = str(repo.id)
        version = self._current_version(repo.root_path)
        for model, adapter in (
            (repo.requirements, artifact_from_requirement),
            (repo.code_artifacts, artifact_from_code),
            (repo.test_artifacts, artifact_from_test),
        ):
            for item in model:
                record = adapter(item, project_id=project_id, version=version)
                self.db.add(
                    CanonicalArtifact(
                        repo_id=repo.id,
                        artifact_id=record.artifact_id,
                        artifact_type=record.artifact_type.value,
                        path=record.path,
                        name=record.name,
                        version=record.version,
                        commit_id=record.commit_id,
                        content_hash=record.content_hash,
                        content=record.content,
                        source_location=json.dumps(
                            record.source_location.to_dict() if record.source_location else {}
                        ),
                        metadata_json=json.dumps(dict(record.metadata), default=str),
                        created_at=record.timestamp,
                    )
                )
        self.db.commit()

    def _generate_and_persist_links(self, repo: Repository) -> list[dict[str, Any]]:
        self.db.query(CandidateLink).filter(CandidateLink.repo_id == repo.id).delete(
            synchronize_session=False
        )
        requirements, code, tests = self._artifact_dicts(repo)
        links = self.linker.generate_links(
            requirements,
            code,
            tests,
            version=self._current_version(repo.root_path),
        )
        for link in links:
            relation = link["relationship_type"]
            source_type, target_type = {
                "REQUIREMENT_TO_CODE": ("REQUIREMENT", "CODE"),
                "REQUIREMENT_TO_TEST": ("REQUIREMENT", "TEST"),
                "CODE_TO_TEST": ("CODE", "TEST"),
            }.get(relation, ("ARTIFACT", "ARTIFACT"))
            self.db.add(
                CandidateLink(
                    repo_id=repo.id,
                    source_type=source_type,
                    source_id=link["source_id"],
                    target_type=target_type,
                    target_id=link["target_id"],
                    relationship_type=relation,
                    confidence=link["confidence"],
                    status=link.get("validation_status", "CANDIDATE"),
                    evidence=json.dumps(link.get("evidence", {}), default=str),
                    method=link["method"],
                )
            )
        self.db.commit()
        return links

    def _persist_graph_relationships(
        self, repo: Repository, links: list[dict[str, Any]]
    ) -> int:
        self.db.query(GraphRelationship).filter(GraphRelationship.repo_id == repo.id).delete(
            synchronize_session=False
        )
        requirements, code, tests = self._artifact_dicts(repo)
        all_links = links + self._structural_relationships(code)
        count = 0
        seen: set[tuple[str, str, str]] = set()
        for link in all_links:
            for source_id, target_id, relationship in (
                (link["source_id"], link["target_id"], link["relationship_type"]),
                (link["target_id"], link["source_id"], f"REVERSE_{link['relationship_type']}"),
            ):
                identity = (source_id, target_id, relationship)
                if identity in seen:
                    continue
                seen.add(identity)
                self.db.add(
                    GraphRelationship(
                        repo_id=repo.id,
                        source_id=source_id,
                        target_id=target_id,
                        relationship=relationship,
                        metadata_json=json.dumps(
                            {
                                "confidence": link.get("confidence"),
                                "evidence": link.get("evidence", {}),
                            },
                            default=str,
                        ),
                    )
                )
                count += 1
        self.db.commit()
        return count

    @staticmethod
    def _structural_relationships(code: list[dict[str, Any]]) -> list[dict[str, Any]]:
        relationships: list[dict[str, Any]] = []
        modules = {item["file_path"]: item for item in code if item["artifact_type"] == "MODULE"}
        for item in code:
            module = modules.get(item["file_path"])
            if module is None:
                continue
            if item["artifact_type"] == "API" and item["artifact_identifier"] != module["artifact_identifier"]:
                relation = "EXPOSES_API" if item["signature"].split(" ", 1)[0] in {
                    "GET", "POST", "PUT", "PATCH", "DELETE", "ROUTE"
                } else "CONSUMES_API"
                relationships.append({
                    "source_id": module["artifact_identifier"],
                    "target_id": item["artifact_identifier"],
                    "relationship_type": relation,
                    "confidence": 1.0,
                    "evidence": {"path": item["file_path"], "line": item["line_start"]},
                })
            for imported in item.get("imports", []):
                relationships.append({
                    "source_id": item["artifact_identifier"],
                    "target_id": imported,
                    "relationship_type": "IMPORTS",
                    "confidence": 0.7,
                    "evidence": {"path": item["file_path"]},
                })
        return relationships

    def _artifact_dicts(self, repo: Repository):
        return (
            [item.to_dict() for item in repo.requirements],
            [item.to_dict() for item in repo.code_artifacts],
            [item.to_dict() for item in repo.test_artifacts],
        )

    @staticmethod
    def _current_version(path: str) -> Optional[str]:
        try:
            return LocalGitRepository(path).current_commit()
        except (FileNotFoundError, OSError):
            return None

    @staticmethod
    def _build_graph(links: list[dict[str, Any]]) -> SoftwareArtifactGraph:
        graph = SoftwareArtifactGraph()
        for link in links:
            source = link["source_id"]
            target = link["target_id"]
            graph.add_node(source, link.get("source_type", "ARTIFACT"))
            graph.add_node(target, link.get("target_type", "ARTIFACT"))
            graph.add_edge(
                source, target, link["relationship_type"],
                confidence=link.get("confidence"), evidence=link.get("evidence", {}),
            )
            # Reverse projection permits impact traversal from changed code to
            # requirements while retaining the original directed evidence.
            graph.add_edge(
                target, source, f"REVERSE_{link['relationship_type']}",
                confidence=link.get("confidence"), evidence=link.get("evidence", {}),
            )
        return graph

    def _targeted_evidence(
        self,
        changed_ids: list[str],
        links: list[dict[str, Any]],
        code: list[dict[str, Any]],
        tests: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        related = [
            link for link in links
            if link.get("source_id") in changed_ids or link.get("target_id") in changed_ids
        ]
        link_evidence = [
            {
                "source": item.get("source_id"),
                "target": item.get("target_id"),
                "relationship": item.get("relationship_type"),
                "score": item.get("confidence"),
                "reason": "deterministic traceability evidence",
                "evidence": item.get("evidence", {}),
            }
            for item in related
        ]
        rag_evidence = self.rag.retrieve(changed_ids, code + tests)
        return link_evidence + rag_evidence
