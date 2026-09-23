from __future__ import annotations

from vigilant.models import Artifact, ArtifactType, ConsistencyFinding, TraceLink


class ConsistencyEngine:
    def analyze(self, artifacts: list[Artifact], links: list[TraceLink]) -> list[ConsistencyFinding]:
        requirements = [a for a in artifacts if a.artifact_type is ArtifactType.REQUIREMENT]
        linked = {link.source_id for link in links if link.relationship == "REQUIREMENT_TO_CODE"}
        findings: list[ConsistencyFinding] = []
        for requirement in requirements:
            if requirement.artifact_id not in linked:
                findings.append(ConsistencyFinding(
                    "REQ-CODE-001", "BROKEN", "HIGH", 0.95,
                    f"No source-code evidence was linked to requirement {requirement.name}.",
                    [requirement.artifact_id], [{"reason": "no_candidate_above_threshold"}],
                ))
        return findings
