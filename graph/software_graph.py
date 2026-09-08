from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Set


@dataclass
class GraphNode:
    node_id: str
    node_type: str
    metadata: Dict[str, Any] = field(default_factory=lambda: dict[str, Any]())


@dataclass(frozen=True)
class GraphEdge:
    source_id: str
    target_id: str
    relationship: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class SoftwareArtifactGraph:
    """Small directed graph with bounded relationship traversal."""

    def __init__(self) -> None:
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []
        self._outgoing: Dict[str, List[GraphEdge]] = {}

    def add_node(self, node_id: str, node_type: str, **metadata: Any) -> None:
        self.nodes[node_id] = GraphNode(node_id, node_type, dict(metadata))

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        relationship: str,
        **metadata: Any,
    ) -> None:
        if source_id not in self.nodes or target_id not in self.nodes:
            raise KeyError("Both edge endpoints must be present as graph nodes")
        edge = GraphEdge(source_id, target_id, relationship, dict(metadata))
        self.edges.append(edge)
        self._outgoing.setdefault(source_id, []).append(edge)

    def add_trace_links(self, links: Iterable[Dict[str, Any]]) -> None:
        for link in links:
            source_id = link["source_id"]
            target_id = link["target_id"]
            self.add_node(source_id, link.get("source_type", "ARTIFACT"))
            self.add_node(target_id, link.get("target_type", "ARTIFACT"))
            self.add_edge(
                source_id,
                target_id,
                link["relationship_type"],
                score=link.get("score"),
                confidence=link.get("confidence"),
                evidence=link.get("evidence", {}),
            )

    def traverse(
        self,
        start_id: str,
        relationships: Set[str] | None = None,
        max_depth: int = 3,
    ) -> List[str]:
        if start_id not in self.nodes:
            return []
        if max_depth < 0:
            raise ValueError("max_depth must be non-negative")
        visited = {start_id}
        queue = deque([(start_id, 0)])
        result: List[str] = []
        while queue:
            current, depth = queue.popleft()
            if depth >= max_depth:
                continue
            for edge in self._outgoing.get(current, []):
                if relationships is not None and edge.relationship not in relationships:
                    continue
                if edge.target_id in visited:
                    continue
                visited.add(edge.target_id)
                result.append(edge.target_id)
                queue.append((edge.target_id, depth + 1))
        return result

    def affected_artifacts(self, changed_ids: Iterable[str], max_depth: int = 3) -> Dict[str, str]:
        affected: Dict[str, str] = {}
        for changed_id in changed_ids:
            if changed_id not in self.nodes:
                continue
            for artifact_id in self.traverse(changed_id, max_depth=max_depth):
                affected.setdefault(artifact_id, "POTENTIALLY_AFFECTED")
        for changed_id in changed_ids:
            if changed_id in self.nodes:
                affected[changed_id] = "DIRECTLY_CHANGED"
        return affected
