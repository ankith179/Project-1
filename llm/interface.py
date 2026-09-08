"""Provider-independent structured assessment boundary."""

from __future__ import annotations

from typing import Any, Protocol, Sequence

from pydantic import BaseModel, Field


class StructuredAssessment(BaseModel):
    decision: str = "UNCERTAIN"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    affected_artifacts: list[str] = Field(default_factory=list)
    broken_links: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    reasoning_summary: str = ""
    provider: str = "none"

    @property
    def status(self) -> str:
        return self.decision


class StructuredLLM(Protocol):
    provider_name: str

    def assess_consistency(
        self, subject: dict[str, Any], evidence: Sequence[dict[str, Any]]
    ) -> StructuredAssessment:
        ...


class NoLLMProvider:
    """Explicit no-network provider used by the deterministic pipeline."""

    provider_name = "none"

    def assess_consistency(
        self, subject: dict[str, Any], evidence: Sequence[dict[str, Any]]
    ) -> StructuredAssessment:
        return StructuredAssessment(
            decision="UNCERTAIN",
            confidence=0.0,
            reasoning_summary="No LLM provider configured.",
            evidence_ids=[
                str(item.get("evidence_id") or item.get("artifact_id") or item.get("target") or "")
                for item in evidence
            ],
            provider=self.provider_name,
        )


class GeminiStructuredProvider:
    """Adapter retaining GeminiClient behind the generic interface."""

    provider_name = "gemini"

    def __init__(self, client=None):
        if client is None:
            from llm.gemini_client import GeminiClient

            client = GeminiClient()
        self.client = client

    def assess_consistency(
        self, subject: dict[str, Any], evidence: Sequence[dict[str, Any]]
    ) -> StructuredAssessment:
        result = self.client.generate_json(
            "Assess consistency using only this JSON evidence:\n"
            + __import__("json").dumps(
                {"subject": subject, "evidence": list(evidence)}, default=str
            )
        )
        try:
            return StructuredAssessment.model_validate(
                {**result, "provider": self.provider_name}
            )
        except Exception:
            return StructuredAssessment(
                decision="UNCERTAIN",
                reasoning_summary="Provider returned an invalid structured assessment.",
                evidence_ids=[
                    str(item.get("evidence_id") or item.get("artifact_id") or item.get("target") or "")
                    for item in evidence
                ],
                provider=self.provider_name,
            )
