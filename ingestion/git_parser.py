import os
import re
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class ParsedFileChange:
    change_type: str  # ADDED, MODIFIED, DELETED, RENAMED
    file_path: str
    old_path: Optional[str] = None
    diff_content: str = ""
    added_lines: List[int] = field(default_factory=list)
    deleted_lines: List[int] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ParsedCommit:
    commit_hash: str
    author: str
    timestamp: Optional[datetime] = None
    message: str = ""
    changes: List[ParsedFileChange] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["timestamp"] = self.timestamp.isoformat() if self.timestamp else None
        return d


class GitHistoryParser:
    """
    Parser for Git history, commit messages, file modifications, and unified diffs.
    Supports pure-Python diff parsing to ensure zero-dependency portability.
    """

    DIFF_HEADER_PATTERN = re.compile(r'^diff --git a/(.*?) b/(.*?)$', re.MULTILINE)
    HUNK_HEADER_PATTERN = re.compile(r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@', re.MULTILINE)
    COMMIT_HEADER_PATTERN = re.compile(r'^commit ([a-f0-9]{40}|[a-f0-9]{7,8})\b', re.MULTILINE)

    def parse_unified_diff(self, diff_text: str) -> List[ParsedFileChange]:
        """
        Parses a unified git diff into individual file changes with line addition/deletion tracking.
        """
        if not diff_text or not diff_text.strip():
            return []

        changes: List[ParsedFileChange] = []
        # Split into per-file diff sections
        sections = re.split(r'(?=^diff --git )', diff_text, flags=re.MULTILINE)

        for sec in sections:
            sec = sec.strip()
            if not sec.startswith("diff --git"):
                continue

            header_match = self.DIFF_HEADER_PATTERN.search(sec)
            if not header_match:
                continue

            old_file = header_match.group(1)
            new_file = header_match.group(2)

            change_type = "MODIFIED"
            if "new file mode" in sec:
                change_type = "ADDED"
            elif "deleted file mode" in sec:
                change_type = "DELETED"
            elif "similarity index" in sec or "rename from" in sec:
                change_type = "RENAMED"

            # Parse line changes from hunks
            added_lines = []
            deleted_lines = []

            for hunk_match in self.HUNK_HEADER_PATTERN.finditer(sec):
                hunk_start = hunk_match.start()
                new_start_line = int(hunk_match.group(3))
                current_new_line = new_start_line

                hunk_body = sec[hunk_match.end():]
                next_hunk = self.HUNK_HEADER_PATTERN.search(hunk_body)
                if next_hunk:
                    hunk_lines = hunk_body[:next_hunk.start()].splitlines()
                else:
                    hunk_lines = hunk_body.splitlines()

                for line in hunk_lines:
                    if line.startswith("+") and not line.startswith("+++"):
                        added_lines.append(current_new_line)
                        current_new_line += 1
                    elif line.startswith("-") and not line.startswith("---"):
                        deleted_lines.append(current_new_line)
                    elif line.startswith(" "):
                        current_new_line += 1

            changes.append(
                ParsedFileChange(
                    change_type=change_type,
                    file_path=new_file,
                    old_path=old_file if change_type == "RENAMED" else None,
                    diff_content=sec,
                    added_lines=added_lines,
                    deleted_lines=deleted_lines
                )
            )

        return changes

    def parse_commit_log(self, log_text: str) -> List[ParsedCommit]:
        """
        Parses raw git log output with patch/stat information.
        """
        if not log_text or not log_text.strip():
            return []

        commits: List[ParsedCommit] = []
        raw_commits = re.split(r'(?=^commit [a-f0-9]{7,40})', log_text, flags=re.MULTILINE)

        for rc in raw_commits:
            rc = rc.strip()
            if not rc.startswith("commit "):
                continue

            lines = rc.splitlines()
            commit_hash = lines[0].split()[1]

            author = "Unknown"
            ts = None
            msg_lines = []
            in_msg = False
            diff_lines = []
            in_diff = False

            for line in lines[1:]:
                if line.startswith("Author:"):
                    author = line[len("Author:"):].strip()
                elif line.startswith("Date:"):
                    raw_date = line[len("Date:"):].strip()
                    try:
                        from dateutil import parser as dt_parser
                        ts = dt_parser.parse(raw_date)
                    except Exception:
                        ts = datetime.now(timezone.utc)
                elif line.startswith("diff --git"):
                    in_diff = True
                    diff_lines.append(line)
                elif in_diff:
                    diff_lines.append(line)
                elif line.startswith("    "):
                    msg_lines.append(line.strip())

            diff_text = "\n".join(diff_lines)
            changes = self.parse_unified_diff(diff_text) if diff_text else []

            commits.append(
                ParsedCommit(
                    commit_hash=commit_hash,
                    author=author,
                    timestamp=ts or datetime.now(timezone.utc),
                    message="\n".join(msg_lines),
                    changes=changes
                )
            )

        return commits
