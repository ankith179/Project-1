from graph.software_graph import SoftwareArtifactGraph


def test_graph_traversal_and_impact_classification():
    graph = SoftwareArtifactGraph()
    graph.add_node("function:login", "FUNCTION")
    graph.add_node("requirement:auth", "REQUIREMENT")
    graph.add_node("test:login", "TEST")
    graph.add_edge("function:login", "test:login", "TESTED_BY")
    graph.add_edge("function:login", "requirement:auth", "IMPLEMENTS")

    assert set(graph.traverse("function:login", max_depth=1)) == {
        "test:login",
        "requirement:auth",
    }
    assert graph.affected_artifacts(["function:login"]) == {
        "function:login": "DIRECTLY_CHANGED",
        "test:login": "POTENTIALLY_AFFECTED",
        "requirement:auth": "POTENTIALLY_AFFECTED",
    }
