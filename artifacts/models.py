from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Mapping, Optional


class ArtifactType(str, Enum):
    REQUIREMENT = "REQUIREMENT"
    MODULE = "MODULE"
    SOURCE_FILE = "SOURCE_FILE"
    CLASS = "CLASS"
    FUNCTION = "FUNCTION"
    METHOD = "METHOD"
    TEST_FILE = "TEST_FILE"
    TEST_CASE = "TEST_CASE"
    API = "API"
    COMMIT = "COMMIT"
    CHANGE = "CHANGE"


@dataclass(frozen=True)
class SourceLocation:
    path: str
    line_start: Optional[int] = None
    line_end: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "line_start": self.line_start,
            "line_end": self.line_end,
        }


@dataclass(frozen=True)
class ArtifactRecord:
    """Stable, serializable representation shared by VIGILANT components."""

    project_id: str
    artifact_type: ArtifactType
    path: str
    name: str
    content: str = ""
    version: Optional[str] = None
    commit_id: Optional[str] = None
    source_location: Optional[SourceLocation] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Mapping[str, Any] = field(default_factory=dict)
    embedding_reference: Optional[str] = None
    content_hash: str = field(init=False)
    artifact_id: str = field(init=False)

    def __post_init__(self) -> None:
        normalized_path = _normalize_path(self.path)
        normalized_content = self.content or ""
        object.__setattr__(
            self,
            "content_hash",
            hashlib.sha256(normalized_content.encode("utf-8")).hexdigest(),
        )
        identity = "|".join(
            (
                self.project_id,
                self.artifact_type.value,
                normalized_path,
                self.name,
                self.version or "",
            )
        )
        object.__setattr__(
            self,
            "artifact_id",
            f"artifact:{hashlib.sha256(identity.encode('utf-8')).hexdigest()[:32]}",
        )
        if self.source_location is None:
            object.__setattr__(self, "source_location", SourceLocation(normalized_path))
        elif self.source_location.path != normalized_path:
            object.__setattr__(
                self,
                "source_location",
                SourceLocation(
                    normalized_path,
                    self.source_location.line_start,
                    self.source_location.line_end,
                ),
            )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "project_id": self.project_id,
            "artifact_type": self.artifact_type.value,
            "path": _normalize_path(self.path),
            "name": self.name,
            "content": self.content,
            "version": self.version,
            "commit_id": self.commit_id,
            "source_location": self.source_location.to_dict() if self.source_location else None,
            "timestamp": self.timestamp.isoformat(),
            "metadata": dict(self.metadata),
            "content_hash": self.content_hash,
            "embedding_reference": self.embedding_reference,
        }


def artifact_from_requirement(
    requirement: Any,
    project_id: str,
    version: Optional[str] = None,
    commit_id: Optional[str] = None,
) -> ArtifactRecord:
    content = getattr(requirement, "raw_content", "") or getattr(requirement, "description", "")
    metadata = {
        "req_identifier": requirement.req_identifier,
        "priority": requirement.priority,
        "category": requirement.category,
        "acceptance_criteria": list(requirement.acceptance_criteria),
    }
    return ArtifactRecord(
        project_id=project_id,
        artifact_type=ArtifactType.REQUIREMENT,
        path=requirement.source_file,
        name=requirement.req_identifier,
        content=content,
        version=version or requirement.version,
        commit_id=commit_id,
        source_location=SourceLocation(
            requirement.source_file,
            requirement.line_start,
            requirement.line_end,
        ),
        metadata=metadata,
    )


def artifact_from_code(
    code_artifact: Any,
    project_id: str,
    version: Optional[str] = None,
    commit_id: Optional[str] = None,
) -> ArtifactRecord:
    artifact_type = ArtifactType(code_artifact.artifact_type)
    if artifact_type == ArtifactType.MODULE:
        artifact_type = ArtifactType.SOURCE_FILE
    metadata = {
        "class_name": code_artifact.class_name,
        "signature": code_artifact.signature,
        "docstring": code_artifact.docstring,
        "imports": list(code_artifact.imports),
        "calls": list(code_artifact.calls),
    }
    return ArtifactRecord(
        project_id=project_id,
        artifact_type=artifact_type,
        path=code_artifact.file_path,
        name=code_artifact.artifact_identifier,
        content=code_artifact.code_content,
        version=version,
        commit_id=commit_id,
        source_location=SourceLocation(
            code_artifact.file_path,
            code_artifact.line_start,
            code_artifact.line_end,
        ),
        metadata=metadata,
    )


def artifact_from_test(
    test_artifact: Any,
    project_id: str,
    version: Optional[str] = None,
    commit_id: Optional[str] = None,
) -> ArtifactRecord:
    metadata = {
        "test_class": test_artifact.test_class,
        "test_method": test_artifact.test_method,
        "docstring": test_artifact.docstring,
        "assertions_count": test_artifact.assertions_count,
        "target_refs": list(test_artifact.target_refs),
    }
    return ArtifactRecord(
        project_id=project_id,
        artifact_type=ArtifactType.TEST_CASE,
        path=test_artifact.file_path,
        name=test_artifact.test_method,
        content=test_artifact.test_content,
        version=version,
        commit_id=commit_id,
        source_location=SourceLocation(
            test_artifact.file_path,
            test_artifact.line_start,
            test_artifact.line_end,
        ),
        metadata=metadata,
    )


def _normalize_path(path: str) -> str:
    return os.path.normpath(path).replace("\\", "/")
