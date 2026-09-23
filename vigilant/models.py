from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class ArtifactType(str, Enum):
    REQUIREMENT = "requirement"
    SOURCE = "source"
    API = "api"
    TEST = "test"
    CHANGE = "change"


@dataclass(frozen=True)
class Artifact:
    artifact_id: str
    artifact_type: ArtifactType
    path: str
    name: str
    content: str
    line_start: int | None = None
    line_end: int | None = None
    version: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def create(
        artifact_type: ArtifactType,
        path: str,
        name: str,
        content: str,
        **kwargs: Any,
    ) -> "Artifact":
        identity = "|".join((artifact_type.value, path.replace("\\", "/"), name, kwargs.get("version") or ""))
        artifact_id = "artifact:" + hashlib.sha256(identity.encode()).hexdigest()[:24]
        return Artifact(artifact_id, artifact_type, path.replace("\\", "/"), name, content, **kwargs)

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["artifact_type"] = self.artifact_type.value
        return result


@dataclass
class TraceLink:
    source_id: str
    target_id: str
    relationship: str
    score: float
    evidence: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ConsistencyFinding:
    rule_id: str
    status: str
    severity: str
    confidence: float
    message: str
    artifact_ids: list[str]
    evidence: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AnalysisReport:
    repository: str
    artifacts: list[Artifact]
    links: list[TraceLink]
    findings: list[ConsistencyFinding]
    impact: dict[str, str]
    evidence: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "repository": self.repository,
            "artifacts": [item.to_dict() for item in self.artifacts],
            "links": [item.to_dict() for item in self.links],
            "findings": [item.to_dict() for item in self.findings],
            "impact": self.impact,
            "evidence": self.evidence,
        }
