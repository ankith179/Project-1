from __future__ import annotations

import json
from datetime import datetime, timezone

from typing import Any, Optional

from llm.interface import NoLLMProvider, StructuredLLM
from database.models import InvestigationStep


class InvestigationAgent:
    """Bounded investigator that delegates all facts to application services."""

    def __init__(self, service: Any, provider: Optional[StructuredLLM] = None, max_depth: int = 3):
        self.service = service
        self.provider = provider or NoLLMProvider()
        self.max_depth = max(0, min(max_depth, 10))

    def investigate(
        self, project_id: int, base_commit: str, target_commit: Optional[str] = None
    ) -> dict[str, Any]:
        steps: list[tuple[str, dict[str, Any], dict[str, Any]]] = []
        steps.append(("inspect_change", {"base_commit": base_commit, "target_commit": target_commit}, {}))
        result = self.service.analyze_change(
            project_id,
            base_commit=base_commit,
            target_commit=target_commit,
            max_depth=self.max_depth,
        )
        steps[-1] = (
            "inspect_change",
            {"base_commit": base_commit, "target_commit": target_commit},
            {"changed_files": result.get("changed_files", []), "changed_artifacts": result.get("changed_artifacts", [])},
        )
        steps.append(("get_artifact", {}, {"changed_artifacts": result.get("changed_artifacts", [])}))
        steps.append(("get_trace_links", {}, {"trace_links": result.get("rag_evidence", [])}))
        steps.append(("query_graph", {}, {"impacted_artifacts": result.get("impacted_artifacts", [])}))
        steps.append(("retrieve_evidence", {}, {"evidence": result.get("rag_evidence", [])}))
        steps.append(("inspect_related_test", {}, {
            "tests": [
                item for item in result.get("rag_evidence", [])
                if item.get("artifact_type") == "TEST"
            ]
        }))
        steps.append(("consistency_check", {}, {"findings": result.get("consistency_findings", [])}))
        assessment = self.provider.assess_consistency(
            {"project_id": project_id, "status": result.get("status")},
            result.get("rag_evidence", []),
        )
        steps.append(("llm_assessment", {}, assessment.model_dump()))
        result["llm_assessment"] = assessment.model_dump()
        steps.append(("final_result", {}, {
            "decision": assessment.decision,
            "confidence": assessment.confidence,
        }))
        run_id = result.get("analysis_run_id")
        if hasattr(self.service, "db"):
            for order, (tool_name, input_data, output_data) in enumerate(steps, start=1):
                self.service.db.add(
                    InvestigationStep(
                        repo_id=project_id,
                        run_id=run_id,
                        step_order=order,
                        tool_name=tool_name,
                        input_json=json.dumps(input_data, default=str, sort_keys=True),
                        output_json=json.dumps(output_data, default=str, sort_keys=True),
                        created_at=datetime.now(timezone.utc),
                    )
                )
            self.service.db.commit()
        result["agent"] = {
            "name": "bounded-investigator",
            "provider": self.provider.provider_name,
            "max_depth": self.max_depth,
            "steps": [tool_name for tool_name, _, _ in steps],
        }
        return result
