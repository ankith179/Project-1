import os
import re
import ast
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class ParsedTestArtifact:
    test_identifier: str
    test_class: Optional[str]
    test_method: str
    file_path: str
    docstring: Optional[str] = None
    line_start: int = 1
    line_end: int = 1
    test_content: str = ""
    assertions_count: int = 0
    target_refs: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PythonTestVisitor(ast.NodeVisitor):
    def __init__(self, file_path: str, source_lines: List[str]):
        self.file_path = file_path
        self.source_lines = source_lines
        self.tests: List[ParsedTestArtifact] = []
        self.current_class: Optional[str] = None

    def visit_ClassDef(self, node: ast.ClassDef):
        # In pytest or unittest, test classes typically start with Test or end with Tests/TestCase
        prev_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = prev_class

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._handle_test_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._handle_test_function(node)

    def _handle_test_function(self, node):
        func_name = node.name
        # Typically test functions start with 'test_' or 'test'
        is_test = func_name.lower().startswith("test") or (self.current_class and "test" in self.current_class.lower())
        if not is_test:
            return

        line_start = node.lineno
        line_end = getattr(node, 'end_lineno', line_start)
        content = "".join(self.source_lines[line_start - 1:line_end])
        docstring = ast.get_docstring(node)

        # Count assertions
        assertions_count = 0
        target_refs = []
        for sub in ast.walk(node):
            if isinstance(sub, ast.Assert):
                assertions_count += 1
            elif isinstance(sub, ast.Call):
                # Check for self.assert* in unittest
                if isinstance(sub.func, ast.Attribute) and sub.func.attr.startswith("assert"):
                    assertions_count += 1
                elif isinstance(sub.func, ast.Name):
                    target_refs.append(sub.func.id)
                elif isinstance(sub.func, ast.Attribute):
                    target_refs.append(sub.func.attr)

        # Look for explicit REQ tags in docstring, function name, or decorators
        # e.g., @pytest.mark.req("REQ-001") or in docstring: "Tests REQ-001"
        req_tags = re.findall(r'\b(REQ[-_ ]?\d+|US[-_ ]?\d+)\b', content, re.IGNORECASE)
        for r in req_tags:
            norm_r = r.upper().replace(" ", "-").replace("_", "-")
            if not re.search(r'[-_]', norm_r):
                norm_r = re.sub(r'([A-Za-z]+)(\d+)', r'\1-\2', norm_r)
            target_refs.append(norm_r)

        target_refs = list(set(target_refs))

        if self.current_class:
            test_id = f"{self.file_path}::{self.current_class}::{func_name}"
        else:
            test_id = f"{self.file_path}::{func_name}"

        artifact = ParsedTestArtifact(
            test_identifier=test_id,
            test_class=self.current_class,
            test_method=func_name,
            file_path=self.file_path,
            docstring=docstring,
            line_start=line_start,
            line_end=line_end,
            test_content=content,
            assertions_count=assertions_count,
            target_refs=target_refs
        )
        self.tests.append(artifact)


class TestParser:
    """
    Extracts test artifacts from test suites.
    Supports pytest and unittest (Python) and JUnit (Java).
    """

    def parse_file(self, file_path: str, repo_root: Optional[str] = None) -> List[ParsedTestArtifact]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Test file not found: {file_path}")

        rel_path = os.path.relpath(file_path, repo_root).replace("\\", "/") if repo_root else os.path.basename(file_path)

        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".py":
            return self._parse_python_tests(file_path, rel_path)
        elif ext == ".java":
            return self._parse_java_tests(file_path, rel_path)
        return []

    def _parse_python_tests(self, file_path: str, rel_path: str) -> List[ParsedTestArtifact]:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            source = f.read()

        lines = source.splitlines(keepends=True)
        try:
            tree = ast.parse(source, filename=file_path)
        except SyntaxError:
            return []

        visitor = PythonTestVisitor(rel_path, lines)
        visitor.visit(tree)
        return visitor.tests

    def _parse_java_tests(self, file_path: str, rel_path: str) -> List[ParsedTestArtifact]:
        # Basic Java test extraction regex matching @Test
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            source = f.read()
        lines = source.splitlines(keepends=True)

        pattern = re.compile(r'@Test[\s\S]*?(?:public\s+void|void)\s+([a-zA-Z0-9_]+)\s*\(', re.MULTILINE)
        tests = []
        for m in pattern.finditer(source):
            method_name = m.group(1)
            line_start = source[:m.start()].count("\n") + 1
            tests.append(
                ParsedTestArtifact(
                    test_identifier=f"{rel_path}::{method_name}",
                    test_class=None,
                    test_method=method_name,
                    file_path=rel_path,
                    line_start=line_start,
                    line_end=line_start + 10,
                    test_content=m.group(0),
                    assertions_count=1
                )
            )
        return tests
