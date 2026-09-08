from __future__ import annotations

from typing import Any, Iterable, Mapping


class ConsistencyEngine:
    """Rule-based, provider-independent consistency analysis.

    Rules intentionally operate on supplied evidence rather than executing
    repository code.  This keeps results repeatable in CI and when no LLM is
    configured.
    """

    def analyze(
        self,
        requirements: Iterable[Mapping[str, Any]],
        code_artifacts: Iterable[Mapping[str, Any]],
        test_artifacts: Iterable[Mapping[str, Any]],
        links: Iterable[Mapping[str, Any]],
        changed_ids: Iterable[str] = (),
    ) -> list[dict[str, Any]]:
        requirements = list(requirements)
        code_artifacts = list(code_artifacts)
        test_artifacts = list(test_artifacts)
        links = list(links)
        changed = set(changed_ids)
        findings: list[dict[str, Any]] = []

        req_code: dict[str, list[Mapping[str, Any]]] = {}
        req_test: dict[str, list[Mapping[str, Any]]] = {}
        code_test: dict[str, list[Mapping[str, Any]]] = {}
        known_code = {
            str(item.get("artifact_identifier") or item.get("artifact_id"))
            for item in code_artifacts
        }
        known_tests = {
            str(item.get("test_identifier") or item.get("artifact_id"))
            for item in test_artifacts
        }
        for link in links:
            relation = link.get("relationship_type")
            source = str(link.get("source_id", ""))
            target = str(link.get("target_id", ""))
            if relation == "REQUIREMENT_TO_CODE":
                req_code.setdefault(source, []).append(link)
                if target not in known_code:
                    findings.append(
                        self._finding(
                            "ORPHAN_CODE_LINK", "ERROR", source,
                            f"Requirement link targets unknown code artifact {target}.",
                            [link],
                        )
                    )
            elif relation == "REQUIREMENT_TO_TEST":
                req_test.setdefault(source, []).append(link)
                if target not in known_tests:
                    findings.append(
                        self._finding(
                            "ORPHAN_TEST_LINK", "ERROR", source,
                            f"Requirement link targets unknown test artifact {target}.",
                            [link],
                        )
                    )
            elif relation == "CODE_TO_TEST":
                code_test.setdefault(source, []).append(link)

        for requirement in requirements:
            req_id = str(requirement.get("req_identifier") or requirement.get("artifact_id"))
            code_links = req_code.get(req_id, [])
            test_links = req_test.get(req_id, [])
            if not code_links:
                findings.append(self._finding(
                    "REQUIREMENT_WITHOUT_CODE", "ERROR", req_id,
                    "Requirement has no evidence-backed implementation link.", [],
                ))
            elif not test_links:
                findings.append(self._finding(
                    "REQUIREMENT_WITHOUT_TEST", "WARNING", req_id,
                    "Requirement has implementation evidence but no test link.",
                    code_links,
                ))
            else:
                findings.append(self._finding(
                    "REQUIREMENT_TRACEABLE", "INFO", req_id,
                    "Requirement has implementation and test evidence.",
                    code_links + test_links,
                ))

        for code in code_artifacts:
            code_id = str(code.get("artifact_identifier") or code.get("artifact_id"))
            if code_id in changed and not code_test.get(code_id):
                findings.append(self._finding(
                    "CHANGED_CODE_WITHOUT_TEST", "ERROR", code_id,
                    "Changed code artifact has no code-to-test evidence.", [],
                ))

        if not findings:
            findings.append(self._finding(
                "NO_FINDINGS", "INFO", "project",
                "No deterministic consistency findings were produced.", [],
            ))
        return findings

    @staticmethod
    def _finding(
        rule_id: str,
        severity: str,
        subject_id: str,
        message: str,
        evidence: list[Mapping[str, Any]],
    ) -> dict[str, Any]:
        status = "CONSISTENT" if severity == "INFO" else "INCONSISTENT"
        return {
            "rule_id": rule_id,
            "status": status,
            "severity": severity,
            "confidence": 0.95 if severity == "ERROR" else (0.8 if severity == "WARNING" else 0.9),
            "subject_id": subject_id,
            "message": message,
            "evidence": list(evidence),
            "method": "DETERMINISTIC_RULES",
        }
