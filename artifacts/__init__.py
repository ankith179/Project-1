"""Canonical artifact contracts used across VIGILANT services."""

from artifacts.models import (
    ArtifactRecord,
    ArtifactType,
    SourceLocation,
    artifact_from_code,
    artifact_from_requirement,
    artifact_from_test,
)

__all__ = [
    "ArtifactRecord",
    "ArtifactType",
    "SourceLocation",
    "artifact_from_code",
    "artifact_from_requirement",
    "artifact_from_test",
]
