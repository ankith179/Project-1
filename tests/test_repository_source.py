import subprocess

import pytest

from ingestion.repository_source import LocalGitRepository


def _git(path, *args):
    return subprocess.run(
        ["git", "-C", str(path), *args],
        check=True,
        capture_output=True,
        text=True,
    )


def test_local_git_repository_reads_snapshot(tmp_path):
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test User")
    source_file = tmp_path / "service.py"
    source_file.write_text("def serve():\n    return True\n", encoding="utf-8")
    _git(tmp_path, "add", "service.py")
    _git(tmp_path, "commit", "-m", "Add service")

    source_file.write_text("def serve():\n    return False\n", encoding="utf-8")
    _git(tmp_path, "add", "service.py")
    _git(tmp_path, "commit", "-m", "Change service")

    snapshot = LocalGitRepository(str(tmp_path)).read_history(max_commits=2)

    assert snapshot.commit_id
    assert len(snapshot.commits) == 2
    assert snapshot.commits[0].message == "Change service"
    assert snapshot.commits[0].changes[0].file_path == "service.py"


def test_non_git_directory_is_rejected(tmp_path):
    source = LocalGitRepository(str(tmp_path))

    assert source.is_git_repository() is False
    with pytest.raises(ValueError, match="Not a Git work tree"):
        source.read_history()
