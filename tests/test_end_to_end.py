from pathlib import Path

from vigilant.agent import InvestigationAgent


def test_repository_analysis_is_evidence_grounded(tmp_path: Path) -> None:
    (tmp_path / "requirements.md").write_text("# Authentication\nUsers authenticate with login.\n", encoding="utf-8")
    (tmp_path / "auth.py").write_text("def login(user):\n    return authenticate(user)\n", encoding="utf-8")
    (tmp_path / "test_auth.py").write_text("def test_login():\n    assert login('u')\n", encoding="utf-8")

    report = InvestigationAgent().investigate(str(tmp_path))

    assert len(report.artifacts) >= 4
    assert report.links
    assert all(link.evidence["target_path"] for link in report.links)
    assert report.to_dict()["findings"] == []
