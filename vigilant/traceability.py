from __future__ import annotations

import re
from collections import Counter

from vigilant.models import Artifact, ArtifactType, TraceLink


def terms(text: str) -> set[str]:
    return {word for word in re.findall(r"[a-zA-Z][a-zA-Z0-9_]+", text.lower()) if len(word) > 2}


class TraceabilityEngine:
    def __init__(self, threshold: float = 0.12) -> None:
        self.threshold = threshold

    def link(self, artifacts: list[Artifact]) -> list[TraceLink]:
        requirements = [a for a in artifacts if a.artifact_type is ArtifactType.REQUIREMENT]
        targets = [a for a in artifacts if a.artifact_type in {ArtifactType.SOURCE, ArtifactType.API, ArtifactType.TEST}]
        links: list[TraceLink] = []
        for source in requirements:
            source_terms = terms(source.content)
            for target in targets:
                target_terms = terms(target.name + " " + target.content)
                overlap = source_terms & target_terms
                score = len(overlap) / max(1, len(source_terms))
                if score >= self.threshold:
                    relation = "REQUIREMENT_TO_TEST" if target.artifact_type is ArtifactType.TEST else "REQUIREMENT_TO_CODE"
                    links.append(TraceLink(source.artifact_id, target.artifact_id, relation, round(score, 4), {
                        "matched_terms": sorted(overlap), "target_path": target.path, "target_line": target.line_start
                    }))
        return links
