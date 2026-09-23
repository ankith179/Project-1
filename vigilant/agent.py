from __future__ import annotations

from vigilant.consistency import ConsistencyEngine
from vigilant.graph import ArtifactGraph
from vigilant.ingestion import RepositoryIngestor
from vigilant.models import AnalysisReport
from vigilant.traceability import TraceabilityEngine


class InvestigationAgent:
    """Bounded investigator: ingest, link, traverse, assess, report."""

    def investigate(self, root: str, requirements_path: str | None = None, changed_paths: set[str] | None = None) -> AnalysisReport:
        artifacts = RepositoryIngestor().ingest(root, requirements_path)
        links = TraceabilityEngine().link(artifacts)
        findings = ConsistencyEngine().analyze(artifacts, links)
        changed_ids = [a.artifact_id for a in artifacts if changed_paths and a.path in changed_paths]
        impact = ArtifactGraph(links).affected(changed_ids)
        evidence = [link.evidence | {"source_id": link.source_id, "target_id": link.target_id} for link in links]
        return AnalysisReport(root, artifacts, links, findings, impact, evidence)
