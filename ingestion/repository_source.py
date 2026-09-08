from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from typing import List, Optional

from ingestion.git_parser import GitHistoryParser, ParsedCommit


@dataclass(frozen=True)
class RepositorySnapshot:
    root_path: str
    commit_id: Optional[str]
    commits: List[ParsedCommit]


class LocalGitRepository:
    """Read Git metadata without executing repository code."""

    def __init__(self, repo_path: str):
        self.root_path = os.path.abspath(repo_path)
        if not os.path.isdir(self.root_path):
            raise FileNotFoundError(f"Repository path does not exist: {repo_path}")

    def is_git_repository(self) -> bool:
        result = self._run_git("rev-parse", "--is-inside-work-tree", check=False)
        return result.stdout.strip().lower() == "true"

    def current_commit(self) -> Optional[str]:
        if not self.is_git_repository():
            return None
        result = self._run_git("rev-parse", "HEAD")
        return result.stdout.strip() or None

    def read_history(self, max_commits: int = 50) -> RepositorySnapshot:
        if max_commits < 1:
            raise ValueError("max_commits must be at least 1")
        if not self.is_git_repository():
            raise ValueError(f"Not a Git work tree: {self.root_path}")

        result = self._run_git(
            "log",
            f"-n{max_commits}",
            "--no-ext-diff",
            "--full-diff",
            "--patch",
            "--format=fuller",
        )
        commits = GitHistoryParser().parse_commit_log(result.stdout)
        return RepositorySnapshot(self.root_path, self.current_commit(), commits)

    def diff(self, base: str, target: Optional[str] = None) -> str:
        """Return a patch between two refs without executing repository code."""
        if not self.is_git_repository():
            raise ValueError(f"Not a Git work tree: {self.root_path}")
        if not base:
            raise ValueError("base ref is required")
        args = ["diff", "--no-ext-diff", "--patch", base]
        if target:
            args.append(target)
        return self._run_git(*args).stdout

    def _run_git(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", self.root_path, *args],
            check=check,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
