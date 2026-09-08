from agents.investigator import InvestigationAgent
from llm.interface import NoLLMProvider, StructuredAssessment


def test_no_llm_provider_returns_valid_uncertain_schema():
    assessment = NoLLMProvider().assess_consistency(
        {"status": "COMPLETED"},
        [{"artifact_id": "code:login"}],
    )

    assert isinstance(assessment, StructuredAssessment)
    assert assessment.decision == "UNCERTAIN"
    assert assessment.evidence_ids == ["code:login"]
    assert assessment.status == "UNCERTAIN"


def test_investigator_delegates_to_deterministic_service():
    class FakeService:
        def analyze_change(self, *args, **kwargs):
            return {"status": "COMPLETED", "rag_evidence": []}

    result = InvestigationAgent(FakeService()).investigate(1, "base", "target")

    assert result["agent"]["name"] == "bounded-investigator"
    assert result["llm_assessment"]["decision"] == "UNCERTAIN"
