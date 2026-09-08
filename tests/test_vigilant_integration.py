import shutil
import subprocess

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import AnalysisRun, Base, CanonicalArtifact, CandidateLink, GraphRelationship
from services.orchestration import VigilantService


def _git(path, *args):
    return subprocess.run(
        ["git", "-C", str(path), *args],
        check=True,
        capture_output=True,
        text=True,
    )


def test_import_and_change_analysis_are_reproducible(tmp_path):
    fixture = tmp_path / "demo"
    shutil.copytree("tests/fixtures/vigilant_demo", fixture)
    _git(fixture, "init")
    _git(fixture, "config", "user.email", "test@example.com")
    _git(fixture, "config", "user.name", "Test User")
    _git(fixture, "add", ".")
    _git(fixture, "commit", "-m", "Initial implementation")
    base = _git(fixture, "rev-parse", "HEAD").stdout.strip()

    source = fixture / "service.py"
    source.write_text(
        source.read_text(encoding="utf-8").replace("bool(username and password)", "False"),
        encoding="utf-8",
    )
    _git(fixture, "add", "service.py")
    _git(fixture, "commit", "-m", "Change authentication")
    target = _git(fixture, "rev-parse", "HEAD").stdout.strip()

    engine = create_engine(f"sqlite:///{tmp_path / 'vigilant.db'}")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        service = VigilantService(session)
        imported = service.import_repository("demo", str(fixture))
        assert imported["links_ingested"] > 0
        assert imported["artifact_counts"]["canonical"] > 0
        assert imported["graph_relationship_count"] == session.query(GraphRelationship).count()
        assert imported["rag_index_status"] == "READY_TARGETED_LEXICAL"
        assert session.query(CanonicalArtifact).count() > 0
        assert session.query(CandidateLink).count() == imported["links_ingested"]

        result = service.analyze_change(imported["project_id"], base, target)
        assert result["status"] == "COMPLETED"
        assert result["changed_files"][0]["file_path"] == "service.py"
        assert result["analysis_run_id"] == session.query(AnalysisRun).one().id
        assert result["consistency_findings"]
    finally:
        session.close()
