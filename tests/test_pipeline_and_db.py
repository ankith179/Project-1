import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base, Repository, Requirement, CodeArtifact, TestArtifact
from ingestion.pipeline import IngestionPipeline


@pytest.fixture
def test_db_session(tmp_path):
    db_file = tmp_path / "test_vigilant.db"
    engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()


def test_ingestion_pipeline_end_to_end(test_db_session):
    benchmark_dir = os.path.join(os.path.dirname(__file__), "..", "datasets", "benchmark_banking")
    assert os.path.exists(benchmark_dir)

    pipeline = IngestionPipeline(db_session=test_db_session)
    summary = pipeline.ingest_repository(
        repo_name="BenchmarkBanking",
        repo_path=benchmark_dir,
        requirements_path=os.path.join(benchmark_dir, "requirements.md")
    )

    assert summary["status"] == "SUCCESS"
    assert summary["requirements_ingested"] == 10
    assert summary["code_artifacts_ingested"] >= 15
    assert summary["tests_ingested"] >= 10

    # Verify database queryability
    reqs = test_db_session.query(Requirement).filter(Requirement.repo_id == summary["repository_id"]).all()
    assert len(reqs) == 10
    req_ids = [r.req_identifier for r in reqs]
    assert "REQ-001" in req_ids
    assert "REQ-010" in req_ids

    # Verify code artifacts
    code_arts = test_db_session.query(CodeArtifact).all()
    assert len(code_arts) >= 15
    func_names = [c.name for c in code_arts]
    assert "authenticate_user" in func_names
    assert "create_account" in func_names
    assert "process_transfer" in func_names

    # Verify tests
    tests = test_db_session.query(TestArtifact).all()
    assert len(tests) >= 10
    test_methods = [t.test_method for t in tests]
    assert "test_authenticate_valid_credentials" in test_methods
    assert "test_process_transfer_success" in test_methods
