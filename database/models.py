import json
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database.connection import Base


class Repository(Base):
    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    root_path = Column(String(1024), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    requirements = relationship("Requirement", back_populates="repository", cascade="all, delete-orphan")
    code_artifacts = relationship("CodeArtifact", back_populates="repository", cascade="all, delete-orphan")
    test_artifacts = relationship("TestArtifact", back_populates="repository", cascade="all, delete-orphan")
    commits = relationship("Commit", back_populates="repository", cascade="all, delete-orphan")
    links = relationship("CandidateLink", back_populates="repository", cascade="all, delete-orphan")


class Requirement(Base):
    __tablename__ = "requirements"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    repo_id = Column(Integer, ForeignKey("repositories.id"), nullable=False, index=True)
    req_identifier = Column(String(100), nullable=False, index=True)
    title = Column(String(512), nullable=False)
    description = Column(Text, nullable=False)
    acceptance_criteria = Column(Text, nullable=True)  # JSON list
    priority = Column(String(50), default="MEDIUM")
    category = Column(String(100), default="FUNCTIONAL")
    source_file = Column(String(1024), nullable=False)
    line_start = Column(Integer, nullable=False)
    line_end = Column(Integer, nullable=False)
    version = Column(String(50), default="1.0")
    raw_content = Column(Text, nullable=True)
    metadata_json = Column(Text, nullable=True)  # JSON dict
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    repository = relationship("Repository", back_populates="requirements")

    def to_dict(self):
        return {
            "id": self.id,
            "repo_id": self.repo_id,
            "req_identifier": self.req_identifier,
            "title": self.title,
            "description": self.description,
            "acceptance_criteria": json.loads(self.acceptance_criteria) if self.acceptance_criteria else [],
            "priority": self.priority,
            "category": self.category,
            "source_file": self.source_file,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "version": self.version,
            "metadata": json.loads(self.metadata_json) if self.metadata_json else {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class CodeArtifact(Base):
    __tablename__ = "code_artifacts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    repo_id = Column(Integer, ForeignKey("repositories.id"), nullable=False, index=True)
    artifact_identifier = Column(String(512), nullable=False, index=True)
    artifact_type = Column(String(50), nullable=False)  # MODULE, CLASS, METHOD, FUNCTION
    file_path = Column(String(1024), nullable=False, index=True)
    class_name = Column(String(255), nullable=True)
    name = Column(String(255), nullable=False)
    signature = Column(Text, nullable=True)
    docstring = Column(Text, nullable=True)
    line_start = Column(Integer, nullable=False)
    line_end = Column(Integer, nullable=False)
    code_content = Column(Text, nullable=False)
    imports = Column(Text, nullable=True)  # JSON list
    calls = Column(Text, nullable=True)    # JSON list
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    repository = relationship("Repository", back_populates="code_artifacts")

    def to_dict(self):
        return {
            "id": self.id,
            "repo_id": self.repo_id,
            "artifact_identifier": self.artifact_identifier,
            "artifact_type": self.artifact_type,
            "file_path": self.file_path,
            "class_name": self.class_name,
            "name": self.name,
            "signature": self.signature,
            "docstring": self.docstring,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "code_content": self.code_content,
            "imports": json.loads(self.imports) if self.imports else [],
            "calls": json.loads(self.calls) if self.calls else [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class TestArtifact(Base):
    __tablename__ = "test_artifacts"
    __test__ = False

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    repo_id = Column(Integer, ForeignKey("repositories.id"), nullable=False, index=True)
    test_identifier = Column(String(512), nullable=False, index=True)
    test_class = Column(String(255), nullable=True)
    test_method = Column(String(255), nullable=False)
    file_path = Column(String(1024), nullable=False, index=True)
    docstring = Column(Text, nullable=True)
    line_start = Column(Integer, nullable=False)
    line_end = Column(Integer, nullable=False)
    test_content = Column(Text, nullable=False)
    assertions_count = Column(Integer, default=0)
    target_refs = Column(Text, nullable=True)  # JSON list of explicit/heuristic targets or annotations
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    repository = relationship("Repository", back_populates="test_artifacts")

    def to_dict(self):
        return {
            "id": self.id,
            "repo_id": self.repo_id,
            "test_identifier": self.test_identifier,
            "test_class": self.test_class,
            "test_method": self.test_method,
            "file_path": self.file_path,
            "docstring": self.docstring,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "test_content": self.test_content,
            "assertions_count": self.assertions_count,
            "target_refs": json.loads(self.target_refs) if self.target_refs else [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Commit(Base):
    __tablename__ = "commits"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    repo_id = Column(Integer, ForeignKey("repositories.id"), nullable=False, index=True)
    commit_hash = Column(String(64), nullable=False, index=True)
    author = Column(String(255), nullable=True)
    timestamp = Column(DateTime, nullable=True)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    repository = relationship("Repository", back_populates="commits")
    changes = relationship("FileChange", back_populates="commit", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "repo_id": self.repo_id,
            "commit_hash": self.commit_hash,
            "author": self.author,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "message": self.message,
            "changes": [c.to_dict() for c in self.changes] if self.changes else [],
        }


class FileChange(Base):
    __tablename__ = "file_changes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    commit_id = Column(Integer, ForeignKey("commits.id"), nullable=False, index=True)
    change_type = Column(String(50), nullable=False)  # ADDED, MODIFIED, DELETED, RENAMED
    file_path = Column(String(1024), nullable=False)
    old_path = Column(String(1024), nullable=True)
    diff_content = Column(Text, nullable=True)
    line_changes = Column(Text, nullable=True)  # JSON dict with additions/deletions

    commit = relationship("Commit", back_populates="changes")

    def to_dict(self):
        return {
            "id": self.id,
            "commit_id": self.commit_id,
            "change_type": self.change_type,
            "file_path": self.file_path,
            "old_path": self.old_path,
            "diff_content": self.diff_content,
            "line_changes": json.loads(self.line_changes) if self.line_changes else {},
        }


class CandidateLink(Base):
    __tablename__ = "candidate_links"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    repo_id = Column(Integer, ForeignKey("repositories.id"), nullable=False, index=True)
    source_type = Column(String(50), nullable=False)  # REQUIREMENT, CODE, TEST
    source_id = Column(String(255), nullable=False, index=True)
    target_type = Column(String(50), nullable=False)  # REQUIREMENT, CODE, TEST
    target_id = Column(String(512), nullable=False, index=True)
    relationship_type = Column(String(50), nullable=False)  # REQUIREMENT_TO_CODE, etc.
    confidence = Column(Float, nullable=False)
    status = Column(String(50), default="CANDIDATE")  # CANDIDATE, VALIDATED, REJECTED, SUSPECT
    evidence = Column(Text, nullable=True)  # JSON structured evidence
    method = Column(String(50), nullable=False)  # IR_BM25, VECTOR_EMBEDDING, etc.
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    repository = relationship("Repository", back_populates="links")

    def to_dict(self):
        return {
            "id": self.id,
            "repo_id": self.repo_id,
            "source_type": self.source_type,
            "source_id": self.source_id,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "relationship_type": self.relationship_type,
            "confidence": self.confidence,
            "status": self.status,
            "evidence": json.loads(self.evidence) if self.evidence else {},
            "method": self.method,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
