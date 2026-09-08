from artifacts.models import (
    ArtifactType,
    SourceLocation,
    artifact_from_code,
    artifact_from_requirement,
    artifact_from_test,
)
from ingestion.code_parser import ParsedCodeArtifact
from ingestion.requirements_parser import ParsedRequirement
from ingestion.test_parser import ParsedTestArtifact


def test_artifact_identity_is_stable_and_content_hash_is_deterministic():
    first = artifact_from_requirement(
        ParsedRequirement(
            req_identifier="REQ-001",
            title="Authentication",
            description="Authenticate users.",
            source_file=r"requirements.md",
            raw_content="Authenticate users.",
        ),
        project_id="banking",
    )
    second = artifact_from_requirement(
        ParsedRequirement(
            req_identifier="REQ-001",
            title="Authentication",
            description="Authenticate users.",
            source_file="requirements.md",
            raw_content="Authenticate users.",
        ),
        project_id="banking",
    )

    assert first.artifact_id == second.artifact_id
    assert first.content_hash == second.content_hash
    assert first.artifact_type == ArtifactType.REQUIREMENT
    assert first.source_location == SourceLocation("requirements.md", 1, 1)


def test_parser_adapters_produce_canonical_records():
    code = artifact_from_code(
        ParsedCodeArtifact(
            artifact_identifier="src/auth.py::login",
            artifact_type="FUNCTION",
            file_path="src/auth.py",
            name="login",
            line_start=4,
            line_end=8,
            code_content="def login(): pass",
        ),
        project_id="banking",
        version="commit-a",
    )
    test = artifact_from_test(
        ParsedTestArtifact(
            test_identifier="tests/test_auth.py::test_login",
            test_class=None,
            test_method="test_login",
            file_path="tests/test_auth.py",
            line_start=2,
            line_end=5,
            test_content="def test_login(): assert True",
        ),
        project_id="banking",
    )

    assert code.artifact_type == ArtifactType.FUNCTION
    assert code.version == "commit-a"
    assert code.source_location.line_start == 4
    assert test.artifact_type == ArtifactType.TEST_CASE
    assert test.metadata["test_method"] == "test_login"
