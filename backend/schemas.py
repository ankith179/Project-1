from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RepositoryImportRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    repo_name: Optional[str] = Field(default=None, min_length=1)
    repo_path: Optional[str] = Field(default=None, min_length=1)
    # Friendly aliases accepted by the public endpoint.
    name: Optional[str] = None
    path: Optional[str] = None
    repository_name: Optional[str] = None
    repository_path: Optional[str] = None
    project_name: Optional[str] = None
    project_path: Optional[str] = None
    repository_url: Optional[str] = None
    requirements_path: Optional[str] = None
    max_commits: int = Field(default=50, ge=1, le=500)

    @model_validator(mode="after")
    def normalize_names(self):
        if not self.repo_name:
            self.repo_name = self.name or self.repository_name or self.project_name
        if not self.repo_path:
            self.repo_path = self.path or self.repository_path or self.project_path
        if not self.repo_name:
            self.repo_name = self.repository_url.rsplit("/", 1)[-1].removesuffix(".git") if self.repository_url else None
        if not self.repo_name or (not self.repo_path and not self.repository_url):
            raise ValueError("repo_name and either repo_path or repository_url are required")
        if self.repo_path and self.repository_url:
            raise ValueError("Provide only one of repo_path or repository_url")
        return self


class ChangeAnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    base_commit: Optional[str] = "HEAD~1"
    target_commit: Optional[str] = None
    base: Optional[str] = None
    target: Optional[str] = None
    max_depth: int = Field(default=3, ge=0, le=10)

    @model_validator(mode="after")
    def normalize_refs(self):
        if not self.base_commit:
            self.base_commit = self.base
        if not self.target_commit:
            self.target_commit = self.target
        return self


class AnalysisResponse(BaseModel):
    status: str
    project_id: int
    repository_id: int
    model_config = ConfigDict(extra="allow")


# Stable names for callers that use the endpoint-oriented terminology.
ImportRepositoryRequest = RepositoryImportRequest
AnalyzeChangeRequest = ChangeAnalysisRequest
