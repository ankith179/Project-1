from __future__ import annotations

from collections import defaultdict, deque

from vigilant.models import TraceLink


class ArtifactGraph:
    def __init__(self, links: list[TraceLink]) -> None:
        self.outgoing: dict[str, list[str]] = defaultdict(list)
        for link in links:
            self.outgoing[link.source_id].append(link.target_id)

    def affected(self, changed_ids: list[str], depth: int = 2) -> dict[str, str]:
        result: dict[str, str] = {}
        for start in changed_ids:
            result[start] = "DIRECTLY_CHANGED"
            queue = deque([(start, 0)])
            seen = {start}
            while queue:
                current, level = queue.popleft()
                if level >= depth:
                    continue
                for target in self.outgoing.get(current, []):
                    if target not in seen:
                        seen.add(target)
                        result.setdefault(target, "POTENTIALLY_AFFECTED")
                        queue.append((target, level + 1))
        return result
