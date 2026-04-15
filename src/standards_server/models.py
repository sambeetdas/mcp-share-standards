"""Data models for rules, skills, and audit entries."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class RuleCategory(str, Enum):
    """Categories for coding standard rules."""

    NAMING = "naming"
    PROJECT_STRUCTURE = "project-structure"
    ERROR_HANDLING = "error-handling"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    IMPORT_ORDERING = "import-ordering"
    PATTERNS = "patterns"
    SECURITY = "security"
    PERFORMANCE = "performance"
    OTHER = "other"


class Language(str, Enum):
    """Supported programming languages."""

    CSHARP = "csharp"
    JAVA = "java"
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    JAVASCRIPT = "javascript"
    GO = "go"
    RUST = "rust"
    OTHER = "other"


class Severity(str, Enum):
    """Violation severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RuleFrontmatter(BaseModel):
    """Parsed YAML frontmatter from a rule .md file."""

    description: str = ""
    globs: Optional[str] = None
    always_apply: bool = Field(default=False, alias="alwaysApply")

    model_config = {"populate_by_name": True}


class Rule(BaseModel):
    """A coding standard rule with metadata and content."""

    id: str
    name: str
    description: str
    language: Language
    category: RuleCategory
    framework: str = ""
    project: str = ""
    globs: Optional[str] = None
    always_apply: bool = False
    content: str
    version: str = "1.0.0"
    tags: list[str] = Field(default_factory=list)


class SkillFrontmatter(BaseModel):
    """Parsed YAML frontmatter from a SKILL.md file."""

    name: str = ""
    description: str = ""


class Skill(BaseModel):
    """A workflow skill with metadata and content."""

    id: str
    name: str
    description: str
    language: Language
    framework: str = ""
    stack: str = ""
    project: str = ""
    content: str
    version: str = "1.0.0"
    tags: list[str] = Field(default_factory=list)


class ViolationReport(BaseModel):
    """A compliance violation report."""

    rule_id: str
    file_path: str
    description: str
    severity: Severity
    project: str = ""
    reporter: str = ""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AuditEntry(BaseModel):
    """An audit log entry for tracking rule/skill access."""

    action: str
    resource_type: str  # "rule" or "skill"
    resource_id: str
    language: Optional[str] = None
    category: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict = Field(default_factory=dict)
