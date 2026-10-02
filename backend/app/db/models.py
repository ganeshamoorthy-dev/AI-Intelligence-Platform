from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, JSON, Enum as SQLEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import enum

class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models.
    
    Spring Boot Analogy: In Java, you often have a base `@MappedSuperclass` for shared fields 
    like ID, createdAt, etc. Here, `DeclarativeBase` acts as the root registry for all 
    entity classes (equivalent to all classes marked with `@Entity`).
    """
    pass

class SCMProvider(str, enum.Enum):
    github = "github"
    gitlab = "gitlab"
    bitbucket = "bitbucket"

class IssueSeverity(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"

class PlatformSettings(Base):
    __tablename__ = "platform_settings"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    openai_api_key: Mapped[Optional[str]] = mapped_column(String(1024))
    google_api_key: Mapped[Optional[str]] = mapped_column(String(1024))
    default_llm_model: Mapped[str] = mapped_column(String(255), default="ollama/qwen2.5-coder:7b")
    severity_threshold: Mapped[str] = mapped_column(String(50), default="low")
    custom_instructions: Mapped[Optional[str]] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class ScmAccount(Base):
    __tablename__ = "scm_accounts"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    provider: Mapped[SCMProvider] = mapped_column(SQLEnum(SCMProvider))
    access_token: Mapped[str] = mapped_column(String(1024))
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    projects: Mapped[List["Project"]] = relationship(back_populates="scm_account")

class ScmWebhook(Base):
    __tablename__ = "scm_webhooks"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    provider_hook_id: Mapped[str] = mapped_column(String(255))
    secret_token: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(default=True)
    events: Mapped[Optional[dict]] = mapped_column(JSON)
    llm_model: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    project: Mapped["Project"] = relationship(back_populates="webhooks")

class Project(Base):
    """
    Database Entity representing a registered SCM Project (Repository).
    
    Spring Boot Analogy: This is exactly like an `@Entity` class.
    - `__tablename__` is equivalent to `@Table(name = "projects")`.
    - `Mapped[int]` paired with `mapped_column(primary_key=True)` is equivalent to `@Id @GeneratedValue`.
    - `relationship` is equivalent to `@OneToMany` or `@ManyToOne`.
    """
    __tablename__ = "projects"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    scm_account_id: Mapped[Optional[int]] = mapped_column(ForeignKey("scm_accounts.id"))
    name: Mapped[str] = mapped_column(String(255), index=True)
    scm_provider: Mapped[SCMProvider] = mapped_column(SQLEnum(SCMProvider))
    repository_url: Mapped[str] = mapped_column(String(1024))
    default_branch: Mapped[str] = mapped_column(String(255), default="main")
    webhook_secret: Mapped[Optional[str]] = mapped_column(String(255)) # Legacy, keeping for backwards compat during migration
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Phase 8: Project-level Review Policies
    ignore_paths: Mapped[Optional[str]] = mapped_column(Text, default="")
    review_mode: Mapped[str] = mapped_column(String(50), default="standard")
    focus_categories: Mapped[Optional[str]] = mapped_column(Text, default="")
    
    scm_account: Mapped[Optional["ScmAccount"]] = relationship(back_populates="projects")
    webhooks: Mapped[List["ScmWebhook"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    pull_requests: Mapped[List["PullRequest"]] = relationship(back_populates="project", cascade="all, delete-orphan")

class PullRequest(Base):
    __tablename__ = "pull_requests"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    pr_number: Mapped[int] = mapped_column(Integer, index=True)
    title: Mapped[str] = mapped_column(String(512))
    author: Mapped[str] = mapped_column(String(255))
    head_sha: Mapped[str] = mapped_column(String(40))
    base_sha: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(50), default="open") # open, closed, merged
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    project: Mapped["Project"] = relationship(back_populates="pull_requests")
    review_runs: Mapped[List["ReviewRun"]] = relationship(back_populates="pull_request", cascade="all, delete-orphan")

class ReviewRun(Base):
    __tablename__ = "review_runs"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    pull_request_id: Mapped[int] = mapped_column(ForeignKey("pull_requests.id"))
    commit_sha: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(50)) # pending, processing, completed, failed
    llm_model: Mapped[str] = mapped_column(String(255))
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer)
    input_tokens: Mapped[Optional[int]] = mapped_column(Integer)
    output_tokens: Mapped[Optional[int]] = mapped_column(Integer)
    total_tokens: Mapped[Optional[int]] = mapped_column(Integer)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    blast_radius_summary: Mapped[Optional[str]] = mapped_column(Text)
    changed_files_count: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    changed_lines_count: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    changed_symbols_count: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    affected_files_count: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    affected_symbols_count: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    related_tests_count: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    risk_level: Mapped[Optional[str]] = mapped_column(String(50))
    findings_count: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    high_severity_findings_count: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    impact_graph_data: Mapped[Optional[JSON]] = mapped_column(JSON)
    diff_data: Mapped[Optional[str]] = mapped_column(Text)
    
    pull_request: Mapped["PullRequest"] = relationship(back_populates="review_runs")
    findings: Mapped[List["ReviewFinding"]] = relationship(back_populates="review_run", cascade="all, delete-orphan")

class ReviewFinding(Base):
    __tablename__ = "review_findings"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    review_run_id: Mapped[int] = mapped_column(ForeignKey("review_runs.id"))
    file_path: Mapped[str] = mapped_column(String(1024))
    line_number: Mapped[Optional[int]] = mapped_column(Integer)
    severity: Mapped[IssueSeverity] = mapped_column(SQLEnum(IssueSeverity))
    category: Mapped[str] = mapped_column(String(255)) # e.g. security, performance, logic, style
    description: Mapped[str] = mapped_column(Text)
    suggested_fix: Mapped[Optional[str]] = mapped_column(Text)
    evidence: Mapped[Optional[str]] = mapped_column(Text)          # Phase 7: Supporting code evidence
    why_it_matters: Mapped[Optional[str]] = mapped_column(Text)    # Phase 7: Explanation of impact
    confidence: Mapped[Optional[str]] = mapped_column(String(50))  # Phase 7: e.g. High, Medium, Low
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    review_run: Mapped["ReviewRun"] = relationship(back_populates="findings")
