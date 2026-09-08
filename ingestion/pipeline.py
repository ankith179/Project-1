import os
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from database.connection import init_db, SessionLocal
from database.models import Repository, Requirement, CodeArtifact, TestArtifact
from ingestion.requirements_parser import RequirementsParser
from ingestion.code_parser import CodeParser
from ingestion.test_parser import TestParser


class IngestionPipeline:
    """
    Coordinates repository artifact extraction and relational database persistence.
    """

    def __init__(self, db_session: Optional[Session] = None):
        self.db = db_session or SessionLocal()
        self.req_parser = RequirementsParser()
        self.code_parser = CodeParser()
        self.test_parser = TestParser()

    def ingest_repository(
        self,
        repo_name: str,
        repo_path: str,
        requirements_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes full artifact ingestion for a repository.
        Parses requirements, code, and test suites and writes to database.
        """
        init_db()
        abs_repo_path = os.path.abspath(repo_path)

        # 1. Create or retrieve Repository record
        repo = self.db.query(Repository).filter(Repository.root_path == abs_repo_path).first()
        if not repo:
            repo = Repository(
                name=repo_name,
                root_path=abs_repo_path,
                description=f"Ingested repository for {repo_name}",
                created_at=datetime.now(timezone.utc)
            )
            self.db.add(repo)
            self.db.commit()
            self.db.refresh(repo)
        else:
            repo.name = repo_name
            # Clear previous artifacts to ensure idempotent re-ingestion
            self.db.query(Requirement).filter(Requirement.repo_id == repo.id).delete()
            self.db.query(CodeArtifact).filter(CodeArtifact.repo_id == repo.id).delete()
            self.db.query(TestArtifact).filter(TestArtifact.repo_id == repo.id).delete()
            self.db.commit()

        req_count = 0
        code_count = 0
        test_count = 0

        # 2. Parse Requirements
        req_target = requirements_path or os.path.join(abs_repo_path, "requirements.md")
        if os.path.exists(req_target):
            parsed_reqs = self.req_parser.parse_file(req_target)
            for pr in parsed_reqs:
                req_obj = Requirement(
                    repo_id=repo.id,
                    req_identifier=pr.req_identifier,
                    title=pr.title,
                    description=pr.description,
                    acceptance_criteria=json.dumps(pr.acceptance_criteria),
                    priority=pr.priority,
                    category=pr.category,
                    source_file=pr.source_file,
                    line_start=pr.line_start,
                    line_end=pr.line_end,
                    version=pr.version,
                    raw_content=pr.raw_content,
                    metadata_json=json.dumps(pr.metadata),
                    created_at=datetime.now(timezone.utc)
                )
                self.db.add(req_obj)
                req_count += 1

        # 3. Parse Source Code and Tests
        for root, _, files in os.walk(abs_repo_path):
            for file in files:
                if file.endswith((".py", ".java", ".js", ".jsx", ".ts", ".tsx")):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, abs_repo_path).replace("\\", "/")

                    # Disregard virtualenv or hidden folders
                    if any(part.startswith(".") for part in rel_path.split("/")):
                        continue

                    # If file is in test directory or starts with test_
                    is_test = "tests" in rel_path.split("/") or os.path.basename(file).startswith("test_")

                    if is_test:
                        parsed_tests = self.test_parser.parse_file(full_path, repo_root=abs_repo_path)
                        for pt in parsed_tests:
                            test_obj = TestArtifact(
                                repo_id=repo.id,
                                test_identifier=pt.test_identifier,
                                test_class=pt.test_class,
                                test_method=pt.test_method,
                                file_path=pt.file_path,
                                docstring=pt.docstring,
                                line_start=pt.line_start,
                                line_end=pt.line_end,
                                test_content=pt.test_content,
                                assertions_count=pt.assertions_count,
                                target_refs=json.dumps(pt.target_refs),
                                created_at=datetime.now(timezone.utc)
                            )
                            self.db.add(test_obj)
                            test_count += 1
                    else:
                        parsed_code = self.code_parser.parse_file(full_path, repo_root=abs_repo_path)
                        for pc in parsed_code:
                            code_obj = CodeArtifact(
                                repo_id=repo.id,
                                artifact_identifier=pc.artifact_identifier,
                                artifact_type=pc.artifact_type,
                                file_path=pc.file_path,
                                class_name=pc.class_name,
                                name=pc.name,
                                signature=pc.signature,
                                docstring=pc.docstring,
                                line_start=pc.line_start,
                                line_end=pc.line_end,
                                code_content=pc.code_content,
                                imports=json.dumps(pc.imports),
                                calls=json.dumps(pc.calls),
                                created_at=datetime.now(timezone.utc)
                            )
                            self.db.add(code_obj)
                            code_count += 1

        self.db.commit()

        return {
            "repository_id": repo.id,
            "repository_name": repo.name,
            "requirements_ingested": req_count,
            "code_artifacts_ingested": code_count,
            "tests_ingested": test_count,
            "status": "SUCCESS"
        }
