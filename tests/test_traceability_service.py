from traceability.service import TraceabilityService


def test_traceability_service_generates_evidence_bearing_links():
    requirements = [
        {
            "req_identifier": "REQ-001",
            "title": "Authenticate user",
            "description": "The system authenticates users with credentials.",
        }
    ]
    code = [
        {
            "artifact_identifier": "src/auth.py::authenticate_user",
            "name": "authenticate_user",
            "signature": "authenticate_user(username, password)",
            "docstring": "Authenticate user credentials.",
            "code_content": "return verify_password(password)",
            "file_path": "src/auth.py",
        }
    ]
    tests = [
        {
            "test_identifier": "tests/test_auth.py::test_authenticate_user",
            "test_method": "test_authenticate_user",
            "test_content": "assert authenticate_user('u', 'p')",
            "file_path": "tests/test_auth.py",
        }
    ]

    links = TraceabilityService(threshold=0.1).generate_links(
        requirements, code, tests, version="commit-a"
    )

    relationships = {link["relationship_type"] for link in links}
    assert "REQUIREMENT_TO_CODE" in relationships
    assert "REQUIREMENT_TO_TEST" in relationships
    assert "CODE_TO_TEST" in relationships
    assert all(link["evidence"]["matched_terms"] for link in links)
    assert all(link["validation_status"] == "CANDIDATE" for link in links)
