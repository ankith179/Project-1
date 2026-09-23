from __future__ import annotations

import ast
import subprocess
from pathlib import Path

from vigilant.models import Artifact, ArtifactType


class RepositoryIngestor:
    """Extracts deterministic artifacts without executing repository code."""

    source_suffixes = {".py", ".js", ".jsx", ".ts", ".tsx", ".java"}

    def ingest(self, root: str | Path, requirements_path: str | None = None) -> list[Artifact]:
        base = Path(root).resolve()
        artifacts: list[Artifact] = []
        req = Path(requirements_path) if requirements_path else base / "requirements.md"
        if not req.is_absolute():
            req = base / req
        if req.is_file():
            artifacts.extend(self._requirements(req, base))
        for path in sorted(base.rglob("*")):
            if not path.is_file() or any(part.startswith(".") for part in path.relative_to(base).parts):
                continue
            if path.suffix.lower() not in self.source_suffixes or path == req:
                continue
            artifacts.extend(self._source_file(path, base))
        return artifacts

    def _requirements(self, path: Path, base: Path) -> list[Artifact]:
        result: list[Artifact] = []
        current: list[str] = []
        start = 1
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if line.startswith("#") and current:
                result.append(self._requirement(path, base, current, start))
                current, start = [], number
            if line.strip() and not line.startswith("<!--"):
                current.append(line)
        if current:
            result.append(self._requirement(path, base, current, start))
        return result

    def _requirement(self, path: Path, base: Path, lines: list[str], start: int) -> Artifact:
        text = "\n".join(lines).strip()
        title = next((line.lstrip("# ").strip() for line in lines if line.startswith("#")), text[:80])
        return Artifact.create(ArtifactType.REQUIREMENT, str(path.relative_to(base)), title, text, line_start=start)

    def _source_file(self, path: Path, base: Path) -> list[Artifact]:
        relative = str(path.relative_to(base)).replace("\\", "/")
        text = path.read_text(encoding="utf-8", errors="replace")
        result = [Artifact.create(ArtifactType.SOURCE, relative, relative, text)]
        if path.suffix == ".py":
            try:
                tree = ast.parse(text)
            except SyntaxError:
                return result
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    name = node.name
                    content = ast.get_source_segment(text, node) or ""
                    kind = ArtifactType.API if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and name in {"get", "post", "put", "delete"} else ArtifactType.SOURCE
                    result.append(Artifact.create(kind, relative, name, content, line_start=node.lineno, line_end=node.end_lineno))
            if "/test" in f"/{relative.lower()}" or path.name.startswith("test_"):
                result.append(Artifact.create(ArtifactType.TEST, relative, path.stem, text))
        return result

    def changed_paths(self, root: str | Path, base: str, target: str | None = None) -> set[str]:
        command = ["git", "-C", str(Path(root).resolve()), "diff", "--name-only", base]
        if target:
            command.append(target)
        output = subprocess.check_output(command, text=True)
        return {line.strip().replace("\\", "/") for line in output.splitlines() if line.strip()}
