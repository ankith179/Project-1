import os
import ast
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class ParsedCodeArtifact:
    artifact_identifier: str
    artifact_type: str  # MODULE, CLASS, METHOD, FUNCTION
    file_path: str
    name: str
    class_name: Optional[str] = None
    signature: Optional[str] = None
    docstring: Optional[str] = None
    line_start: int = 1
    line_end: int = 1
    code_content: str = ""
    imports: List[str] = field(default_factory=list)
    calls: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PythonASTVisitor(ast.NodeVisitor):
    def __init__(self, file_path: str, source_lines: List[str]):
        self.file_path = file_path
        self.source_lines = source_lines
        self.artifacts: List[ParsedCodeArtifact] = []
        self.current_class: Optional[str] = None
        self.file_imports: List[str] = []

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.file_imports.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        mod = node.module or ""
        for alias in node.names:
            self.file_imports.append(f"{mod}.{alias.name}" if mod else alias.name)
        self.generic_visit(node)

    def _extract_calls(self, node: ast.AST) -> List[str]:
        calls = []
        for sub in ast.walk(node):
            if isinstance(sub, ast.Call):
                if isinstance(sub.func, ast.Name):
                    calls.append(sub.func.id)
                elif isinstance(sub.func, ast.Attribute):
                    calls.append(sub.func.attr)
        return list(set(calls))

    def visit_ClassDef(self, node: ast.ClassDef):
        class_name = node.name
        line_start = node.lineno
        line_end = getattr(node, 'end_lineno', line_start)
        code_content = "".join(self.source_lines[line_start - 1:line_end])
        docstring = ast.get_docstring(node)

        base_names = []
        for b in node.bases:
            if isinstance(b, ast.Name):
                base_names.append(b.id)
            elif isinstance(b, ast.Attribute):
                base_names.append(b.attr)
        sig = f"class {class_name}({', '.join(base_names)})"

        artifact = ParsedCodeArtifact(
            artifact_identifier=f"{self.file_path}::{class_name}",
            artifact_type="CLASS",
            file_path=self.file_path,
            name=class_name,
            class_name=None,
            signature=sig,
            docstring=docstring,
            line_start=line_start,
            line_end=line_end,
            code_content=code_content,
            imports=list(self.file_imports),
            calls=self._extract_calls(node)
        )
        self.artifacts.append(artifact)

        prev_class = self.current_class
        self.current_class = class_name
        self.generic_visit(node)
        self.current_class = prev_class

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._handle_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._handle_function(node, is_async=True)

    def _handle_function(self, node, is_async: bool = False):
        func_name = node.name
        line_start = node.lineno
        line_end = getattr(node, 'end_lineno', line_start)
        code_content = "".join(self.source_lines[line_start - 1:line_end])
        docstring = ast.get_docstring(node)

        # Build signature representation
        args_list = [arg.arg for arg in node.args.args]
        prefix = "async def" if is_async else "def"
        sig = f"{prefix} {func_name}({', '.join(args_list)})"

        if self.current_class:
            artifact_type = "METHOD"
            artifact_id = f"{self.file_path}::{self.current_class}::{func_name}"
            class_name = self.current_class
        else:
            artifact_type = "FUNCTION"
            artifact_id = f"{self.file_path}::{func_name}"
            class_name = None

        artifact = ParsedCodeArtifact(
            artifact_identifier=artifact_id,
            artifact_type=artifact_type,
            file_path=self.file_path,
            name=func_name,
            class_name=class_name,
            signature=sig,
            docstring=docstring,
            line_start=line_start,
            line_end=line_end,
            code_content=code_content,
            imports=list(self.file_imports),
            calls=self._extract_calls(node)
        )
        self.artifacts.append(artifact)


class CodeParser:
    """
    Parser for source code repositories.
    Supports Python (via native AST), Java, and lightweight JavaScript/TypeScript
    extraction for functions and HTTP API references.
    """

    def parse_file(self, file_path: str, repo_root: Optional[str] = None) -> List[ParsedCodeArtifact]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Source file not found: {file_path}")

        rel_path = os.path.relpath(file_path, repo_root).replace("\\", "/") if repo_root else os.path.basename(file_path)

        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".py":
            return self._parse_python(file_path, rel_path)
        elif ext == ".java":
            return self._parse_java(file_path, rel_path)
        elif ext in {".js", ".jsx", ".ts", ".tsx"}:
            return self._parse_javascript(file_path, rel_path)
        return []

    def _parse_python(self, file_path: str, rel_path: str) -> List[ParsedCodeArtifact]:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            source = f.read()

        lines = source.splitlines(keepends=True)
        try:
            tree = ast.parse(source, filename=file_path)
        except SyntaxError:
            # Fallback for files with syntax issues: treat file as module-level artifact
            return [
                ParsedCodeArtifact(
                    artifact_identifier=rel_path,
                    artifact_type="MODULE",
                    file_path=rel_path,
                    name=os.path.basename(file_path),
                    line_start=1,
                    line_end=len(lines),
                    code_content=source
                )
            ]

        visitor = PythonASTVisitor(rel_path, lines)
        visitor.visit(tree)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for decorator in node.decorator_list:
                if not isinstance(decorator, ast.Call) or not isinstance(decorator.func, ast.Attribute):
                    continue
                if decorator.func.attr not in {"route", "get", "post", "put", "patch", "delete"}:
                    continue
                if not decorator.args or not isinstance(decorator.args[0], ast.Constant):
                    continue
                endpoint = str(decorator.args[0].value)
                method = "ROUTE" if decorator.func.attr == "route" else decorator.func.attr.upper()
                visitor.artifacts.append(
                    ParsedCodeArtifact(
                        artifact_identifier=f"{rel_path}::API::{method}::{endpoint}",
                        artifact_type="API",
                        file_path=rel_path,
                        name=endpoint,
                        signature=f"{method} {endpoint}",
                        line_start=node.lineno,
                        line_end=getattr(node, "end_lineno", node.lineno),
                        code_content="".join(lines[node.lineno - 1:getattr(node, "end_lineno", node.lineno)]),
                        calls=[node.name],
                    )
                )

        # Also add module-level artifact
        module_doc = ast.get_docstring(tree)
        module_art = ParsedCodeArtifact(
            artifact_identifier=rel_path,
            artifact_type="MODULE",
            file_path=rel_path,
            name=os.path.basename(file_path),
            signature=f"module {rel_path}",
            docstring=module_doc,
            line_start=1,
            line_end=len(lines),
            code_content=source,
            imports=visitor.file_imports
        )
        unique: dict[str, ParsedCodeArtifact] = {}
        for artifact in [module_art] + visitor.artifacts:
            unique.setdefault(artifact.artifact_identifier, artifact)
        return list(unique.values())

    def _parse_java(self, file_path: str, rel_path: str) -> List[ParsedCodeArtifact]:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            source = f.read()
        lines = source.splitlines(keepends=True)

        try:
            import javalang
            tree = javalang.parse.parse(source)
            artifacts = []
            # Extract classes and methods
            for _, class_decl in tree.filter(javalang.tree.ClassDeclaration):
                cls_name = class_decl.name
                artifacts.append(
                    ParsedCodeArtifact(
                        artifact_identifier=f"{rel_path}::{cls_name}",
                        artifact_type="CLASS",
                        file_path=rel_path,
                        name=cls_name,
                        line_start=class_decl.position.line if class_decl.position else 1,
                        line_end=len(lines),
                        code_content=source
                    )
                )
                for method in class_decl.methods:
                    m_name = method.name
                    artifacts.append(
                        ParsedCodeArtifact(
                            artifact_identifier=f"{rel_path}::{cls_name}::{m_name}",
                            artifact_type="METHOD",
                            file_path=rel_path,
                            name=m_name,
                            class_name=cls_name,
                            signature=f"{method.return_type.name if method.return_type else 'void'} {m_name}()",
                            line_start=method.position.line if method.position else 1,
                            line_end=len(lines),
                            code_content=""
                        )
                    )
            return artifacts
        except Exception:
            return [
                ParsedCodeArtifact(
                    artifact_identifier=rel_path,
                    artifact_type="MODULE",
                    file_path=rel_path,
                    name=os.path.basename(file_path),
                    line_start=1,
                    line_end=len(lines),
                    code_content=source,
                )
            ]

    def _parse_javascript(self, file_path: str, rel_path: str) -> List[ParsedCodeArtifact]:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            source = f.read()
        lines = source.splitlines(keepends=True)
        artifacts = [
            ParsedCodeArtifact(
                artifact_identifier=rel_path,
                artifact_type="MODULE",
                file_path=rel_path,
                name=os.path.basename(file_path),
                line_start=1,
                line_end=len(lines),
                code_content=source,
            )
        ]
        function_pattern = re.compile(
            r"(?m)^(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\("
            r"|^(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*"
            r"(?:async\s*)?\([^)]*\)\s*=>"
        )
        for match in function_pattern.finditer(source):
            name = match.group(1) or match.group(2)
            line_start = source[: match.start()].count("\n") + 1
            artifacts.append(
                ParsedCodeArtifact(
                    artifact_identifier=f"{rel_path}::{name}",
                    artifact_type="FUNCTION",
                    file_path=rel_path,
                    name=name,
                    line_start=line_start,
                    line_end=line_start,
                    code_content=match.group(0),
                )
            )
        api_pattern = re.compile(
            r"(?m)(?:fetch|axios\.(?:get|post|put|patch|delete)|request)"
            r"\s*\(\s*[`'\"]([^`'\"]+)[`'\"]"
        )
        for index, match in enumerate(api_pattern.finditer(source), start=1):
            endpoint = match.group(1)
            line_start = source[: match.start()].count("\n") + 1
            artifacts.append(
                ParsedCodeArtifact(
                    artifact_identifier=f"{rel_path}::API::{index}",
                    artifact_type="API",
                    file_path=rel_path,
                    name=endpoint,
                    signature=f"HTTP client reference {endpoint}",
                    line_start=line_start,
                    line_end=line_start,
                    code_content=match.group(0),
                    calls=["fetch", "http"],
                )
            )
        return artifacts
