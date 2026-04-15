"""
Enterprise MCP Standards Server

Serves coding rules and workflow skills to IDEs (Cursor, VS Code, Visual Studio, etc.)
via the Model Context Protocol (MCP).

Supports both stdio and SSE transports.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from standards_server.models import (
    Language,
    RuleCategory,
    Severity,
    ViolationReport,
)
from standards_server.stores.audit_store import AuditStore
from standards_server.stores.rules_store import RulesStore
from standards_server.stores.skills_store import SkillsStore

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default paths — can be overridden via config or CLI args
# ---------------------------------------------------------------------------
_DEFAULT_STANDARDS_DIR = Path(__file__).resolve().parent.parent.parent / "standards"

# ---------------------------------------------------------------------------
# Initialize stores (module-level; configured in main())
# ---------------------------------------------------------------------------
rules_store: RulesStore | None = None
skills_store: SkillsStore | None = None
audit_store: AuditStore | None = None

# ---------------------------------------------------------------------------
# MCP Server instance
# ---------------------------------------------------------------------------
mcp = FastMCP(
    name="Enterprise Standards Server",
    instructions=(
        "MANDATORY: This server provides enterprise coding standards that you MUST follow. "
        "BEFORE generating, modifying, or reviewing ANY code, you MUST call "
        "get_coding_standards(language, task_type) to fetch the mandatory rules and relevant "
        "skills for the programming language being used. Determine the language from the user's "
        "request or the file extension (e.g., .cs -> csharp, .py -> python, .ts -> typescript). "
        "ALL code you produce MUST comply with the returned rules — they are enterprise-wide "
        "requirements, not suggestions. "
        "If you detect that code violates a rule, call report_violation() to log it. "
        "ADDITIONAL TOOLS: "
        "- get_rules(language, category) — fetch rules filtered by category. "
        "- get_skills(language) — fetch all workflow skills for a language. "
        "- get_skill(skill_name) — fetch a specific skill by name. "
        "- list_available_standards(language) — browse available rules and skills. "
        "- reload_standards() — reload after standards files are updated on disk."
    ),
)


# =========================================================================
# RESOURCES — Rules and Skills as discoverable MCP resources
# =========================================================================


@mcp.resource("standards://languages")
def list_languages_resource() -> str:
    """List all programming languages that have rules or skills available.

    Use this to discover which languages are supported, then access
    per-language resources like standards://rules/{language} or
    standards://skills/{language}.
    """
    _ensure_stores()
    rule_langs = {lang.value for lang in rules_store.get_languages()}
    skill_langs = {lang.value for lang in skills_store.get_languages()}
    all_langs = sorted(rule_langs | skill_langs)

    lines = ["# Available Languages\n"]
    lines.append("| Language | Rules | Skills | Rules Resource | Skills Resource |")
    lines.append("|---|---|---|---|---|")
    for lang in all_langs:
        rule_count = len(rules_store.query(language=_parse_language(lang)))
        skill_count = len(skills_store.query(language=_parse_language(lang)))
        lines.append(
            f"| **{lang}** | {rule_count} | {skill_count} "
            f"| `standards://rules/{lang}` | `standards://skills/{lang}` |"
        )
    lines.append(
        "\n---\n*Select a language-specific resource above, or use "
        "`standards://rules` / `standards://skills` for everything.*"
    )
    return "\n".join(lines)


@mcp.resource("standards://rules")
def list_rules_resource() -> str:
    """List all available coding standard rules across all languages."""
    _ensure_stores()
    rules = rules_store.list_all()

    # Group by language
    by_lang: dict[str, list] = {}
    for rule in rules:
        by_lang.setdefault(rule.language.value, []).append(rule)

    lines = ["# Available Coding Standard Rules (All Languages)\n"]
    lines.append(
        "*Tip: Use `standards://rules/{language}` for a specific language "
        "(e.g. `standards://rules/csharp`).*\n"
    )

    for lang in sorted(by_lang):
        lines.append(f"## {lang.upper()}\n")
        for rule in by_lang[lang]:
            lines.append(f"### {rule.name}")
            lines.append(f"- **ID**: `{rule.id}`")
            lines.append(f"- **Category**: {rule.category.value}")
            lines.append(f"- **Description**: {rule.description}")
            if rule.globs:
                lines.append(f"- **Applies to**: `{rule.globs}`")
            if rule.always_apply:
                lines.append("- **Always active**: Yes")
            lines.append("")

    return "\n".join(lines)


@mcp.resource("standards://rules/{language}")
def list_rules_by_language_resource(language: str) -> str:
    """List coding standard rules for a specific programming language.

    Args:
        language: Programming language (csharp, java, python, typescript, javascript, go, rust).
    """
    _ensure_stores()
    lang = _parse_language(language)
    rules = rules_store.query(language=lang)

    if not rules:
        return f"No rules found for language '{language}'."

    lines = [f"# Coding Standard Rules — {language.upper()}\n"]
    for rule in rules:
        lines.append(f"## {rule.name}")
        lines.append(f"- **ID**: `{rule.id}`")
        lines.append(f"- **Category**: {rule.category.value}")
        lines.append(f"- **Description**: {rule.description}")
        if rule.globs:
            lines.append(f"- **Applies to**: `{rule.globs}`")
        if rule.always_apply:
            lines.append("- **Always active**: Yes")
        lines.append("")
    return "\n".join(lines)


@mcp.resource("standards://skills")
def list_skills_resource() -> str:
    """List all available workflow skills across all languages."""
    _ensure_stores()
    skills = skills_store.list_all()

    # Group by language
    by_lang: dict[str, list] = {}
    for skill in skills:
        by_lang.setdefault(skill.language.value, []).append(skill)

    lines = ["# Available Workflow Skills (All Languages)\n"]
    lines.append(
        "*Tip: Use `standards://skills/{language}` for a specific language "
        "(e.g. `standards://skills/csharp`).*\n"
    )

    for lang in sorted(by_lang):
        lines.append(f"## {lang.upper()}\n")
        for skill in by_lang[lang]:
            lines.append(f"### {skill.name}")
            lines.append(f"- **ID**: `{skill.id}`")
            if skill.stack:
                lines.append(f"- **Stack**: {skill.stack}")
            lines.append(f"- **Description**: {skill.description}")
            lines.append("")

    return "\n".join(lines)


@mcp.resource("standards://skills/{language}")
def list_skills_by_language_resource(language: str) -> str:
    """List workflow skills for a specific programming language.

    Args:
        language: Programming language (csharp, java, python, typescript, javascript, go, rust).
    """
    _ensure_stores()
    lang = _parse_language(language)
    skills = skills_store.query(language=lang)

    if not skills:
        return f"No skills found for language '{language}'."

    lines = [f"# Workflow Skills — {language.upper()}\n"]
    for skill in skills:
        lines.append(f"## {skill.name}")
        lines.append(f"- **ID**: `{skill.id}`")
        if skill.stack:
            lines.append(f"- **Stack**: {skill.stack}")
        lines.append(f"- **Description**: {skill.description}")
        lines.append("")
    return "\n".join(lines)


# =========================================================================
# Task-type to skill mapping for the gateway tool
# =========================================================================

_TASK_SKILL_MAP: dict[str, list[str]] = {
    "generate": [
        "csharp/project-scaffolding",
        "csharp/api-design",
        "csharp/dependency-injection",
        "csharp/configuration",
        "csharp/logging",
    ],
    "review": [
        "csharp/code-review",
    ],
    "refactor": [
        "csharp/refactoring",
    ],
    "test": [
        "csharp/test-generation",
    ],
    "deploy": [
        "csharp/docker-deploy",
    ],
    "migrate": [
        "csharp/ef-core-migrations",
    ],
    "database": [
        "csharp/ef-core-migrations",
    ],
}


# =========================================================================
# TOOLS — Smart retrieval, governance, and analytics
# =========================================================================


@mcp.tool()
def get_coding_standards(
    language: str = "csharp",
    task_type: str = "generate",
    project: str = "",
) -> str:
    """MANDATORY — Call this BEFORE generating, modifying, or reviewing ANY code.

    Returns all enterprise coding rules for the specified language plus
    workflow skills relevant to the task type. The returned rules are
    mandatory enterprise-wide requirements — all code MUST comply.

    Args:
        language: Programming language (csharp, java, python, typescript,
                  javascript, go, rust). Infer from file extension or user request.
        task_type: What you are about to do — one of: generate, review,
                   refactor, test, deploy, migrate. Determines which
                   workflow skills are included alongside the rules.
        project: Optional project name. When set, project-specific rules and
                 skills from standards/_projects/{project}/ are included and
                 can override language/framework defaults.

    Returns:
        Markdown document containing all mandatory coding rules and
        relevant workflow skills for the language and task.
    """
    _ensure_stores()

    lang = _parse_language(language)

    # --- Rules (always included, with hierarchy merge) ---
    rules = rules_store.query_with_hierarchy(
        language=lang, project=project or None
    )
    for rule in rules:
        audit_store.record_access("rule", rule.id, language=language, task_type=task_type)

    lines = [
        f"# MANDATORY Enterprise Coding Standards — {language.upper()}\n",
        "**You MUST follow every rule below. These are enterprise-wide requirements, "
        "not suggestions. Violations must be reported via report_violation().**\n",
    ]

    if rules:
        lines.append("---\n")
        lines.append("# Part 1: Coding Rules\n")
        for rule in rules:
            lines.append(f"## {rule.name}\n")
            lines.append(
                f"*Category: {rule.category.value} | "
                f"Applies to: {rule.globs or 'all files'}*\n"
            )
            lines.append(rule.content)
            lines.append("\n")
    else:
        available_langs = [la.value for la in rules_store.get_languages()]
        lines.append(
            f"No rules found for '{language}'. "
            f"Languages with rules: {', '.join(available_langs)}\n"
        )

    # --- Skills (filtered by task type, with hierarchy merge) ---
    task_lower = task_type.lower()
    skill_ids = _TASK_SKILL_MAP.get(task_lower, [])

    matched_skills = []
    for sid in skill_ids:
        skill = skills_store.get(sid)
        if skill and skill.language == lang:
            matched_skills.append(skill)

    if not matched_skills:
        all_skills = skills_store.query_with_hierarchy(
            language=lang, project=project or None
        )
        if all_skills:
            matched_skills = all_skills

    if matched_skills:
        for skill in matched_skills:
            audit_store.record_access("skill", skill.id, language=language, task_type=task_type)

        lines.append("---\n")
        lines.append(f"# Part 2: Workflow Skills (task: {task_type})\n")
        for skill in matched_skills:
            lines.append(f"## {skill.name}\n")
            lines.append(f"*Stack: {skill.stack or 'general'}*\n")
            lines.append(skill.content)
            lines.append("\n")

    return "\n".join(lines)


@mcp.tool()
def get_available_languages() -> str:
    """Discover which programming languages have enterprise coding standards available.

    Call this when you need to check what languages are supported before
    fetching rules or skills. Prefer get_coding_standards() for the
    common case of fetching rules + skills in one call.

    Returns:
        A table of languages with counts of available rules and skills.
    """
    _ensure_stores()
    rule_langs = {lang.value for lang in rules_store.get_languages()}
    skill_langs = {lang.value for lang in skills_store.get_languages()}
    all_langs = sorted(rule_langs | skill_langs)

    lines = ["# Supported Languages\n"]
    lines.append("| Language | Rules | Skills |")
    lines.append("|---|---|---|")
    for lang in all_langs:
        rule_count = len(rules_store.query(language=_parse_language(lang)))
        skill_count = len(skills_store.query(language=_parse_language(lang)))
        lines.append(f"| **{lang}** | {rule_count} | {skill_count} |")

    lines.append(
        "\n---\n*Use `get_rules(language)` to fetch rules or "
        "`get_skills(language)` to fetch skills for a specific language.*"
    )

    return "\n".join(lines)


@mcp.tool()
def get_rules(
    language: str = "csharp",
    category: str = "all",
) -> str:
    """Fetch mandatory enterprise coding rules for a language, optionally filtered by category.

    Call this BEFORE writing or modifying code when you need rules for a
    specific category. For the common case of all rules + skills, prefer
    get_coding_standards() instead. The returned rules are mandatory —
    all generated code MUST comply.

    Args:
        language: Programming language (csharp, java, python, typescript, javascript, go, rust, other).
        category: Rule category filter (naming, project-structure, error-handling, testing,
                  documentation, import-ordering, patterns, security, performance, other, all).

    Returns:
        Markdown-formatted mandatory coding standard rules.
    """
    _ensure_stores()

    lang = _parse_language(language)
    cat = _parse_category(category) if category != "all" else None

    rules = rules_store.query(language=lang, category=cat)

    if not rules:
        available_langs = [l.value for l in rules_store.get_languages()]
        return (
            f"No rules found for language='{language}', category='{category}'.\n\n"
            f"Languages with rules: {', '.join(available_langs)}"
        )

    # Record access for analytics
    for rule in rules:
        audit_store.record_access("rule", rule.id, language=language, category=category)

    lines = [f"# Coding Standards — {language.upper()}\n"]
    if cat:
        lines[0] = f"# Coding Standards — {language.upper()} / {category}\n"

    for rule in rules:
        lines.append(f"---\n\n## {rule.name}\n")
        lines.append(f"*Category: {rule.category.value} | Applies to: {rule.globs or 'all files'}*\n")
        lines.append(rule.content)
        lines.append("")

    return "\n".join(lines)


@mcp.tool()
def get_skills(
    language: str = "csharp",
    stack: str = "",
) -> str:
    """Fetch enterprise workflow skills for a language. Call this BEFORE starting
    any development workflow (scaffolding, migration, deployment, etc.) to get
    the approved step-by-step process. Skills contain mandatory patterns and
    procedures that MUST be followed.

    Args:
        language: Programming language (csharp, java, python, typescript, javascript, go, rust, other).
        stack: Optional technology stack filter (dotnet, java-spring, node-express, python-fastapi).

    Returns:
        Markdown-formatted workflow skills with full step-by-step content.
    """
    _ensure_stores()

    lang = _parse_language(language)
    skills = skills_store.query(language=lang, stack=stack or None)

    if not skills:
        available_langs = [l.value for l in skills_store.get_languages()]
        return (
            f"No skills found for language='{language}'"
            + (f", stack='{stack}'" if stack else "")
            + f".\n\nLanguages with skills: {', '.join(available_langs)}"
        )

    # Record access for analytics
    for skill in skills:
        audit_store.record_access("skill", skill.id, language=language)

    lines = [f"# Workflow Skills — {language.upper()}\n"]
    if stack:
        lines[0] = f"# Workflow Skills — {language.upper()} / {stack}\n"

    for skill in skills:
        lines.append(f"---\n\n## {skill.name}\n")
        lines.append(f"*Stack: {skill.stack or 'general'}*\n")
        lines.append(skill.content)
        lines.append("")

    return "\n".join(lines)


@mcp.tool()
def get_skill(
    skill_name: str,
    stack: str = "",
) -> str:
    """Fetch a specific enterprise workflow skill by name or ID. Call this when the
    user requests a particular workflow (e.g., scaffolding, migration, deployment,
    code review, refactoring). The returned skill contains mandatory procedures.

    Args:
        skill_name: The skill ID (e.g., 'dotnet-api-design') or partial name to search for.
        stack: Optional technology stack filter (dotnet, java-spring, node-express, python-fastapi).

    Returns:
        The full skill content as markdown with step-by-step instructions.
    """
    _ensure_stores()

    # Try exact match first
    skill = skills_store.get(skill_name)

    # If not found, try fuzzy search
    if not skill:
        all_skills = skills_store.list_all()
        search_lower = skill_name.lower()
        matches = [
            s for s in all_skills
            if search_lower in s.id.lower()
            or search_lower in s.name.lower()
            or search_lower in s.description.lower()
        ]
        if stack:
            matches = [s for s in matches if s.stack == stack]
        if matches:
            skill = matches[0]

    if not skill:
        available = skills_store.get_ids()
        return (
            f"Skill '{skill_name}' not found.\n\n"
            f"Available skills: {', '.join(available)}"
        )

    audit_store.record_access("skill", skill.id)

    lines = [
        f"# {skill.name}\n",
        f"*Language: {skill.language.value}",
    ]
    if skill.stack:
        lines[-1] += f" | Stack: {skill.stack}"
    lines[-1] += "*\n"
    lines.append(skill.content)

    return "\n".join(lines)


@mcp.tool()
def list_available_standards(language: str = "") -> str:
    """Browse all available enterprise coding rules and workflow skills, optionally
    filtered by language. Use this to discover what standards are available. For
    fetching actual rule/skill content, use get_coding_standards() instead.

    Args:
        language: Optional language filter (csharp, java, python, typescript, etc.).
                  Leave empty to list all languages.

    Returns:
        A categorized directory of all rules and skills grouped by language.
    """
    _ensure_stores()

    # Determine which languages to show
    if language:
        lang = _parse_language(language)
        lang_list = [lang]
    else:
        rule_langs = set(rules_store.get_languages())
        skill_langs = set(skills_store.get_languages())
        lang_list = sorted(rule_langs | skill_langs, key=lambda l: l.value)

    lines = ["# Enterprise Coding Standards — Directory\n"]

    if not language:
        lines.append(
            "*Tip: Call `list_available_standards(language='csharp')` to filter by language, "
            "or `get_available_languages()` to see supported languages.*\n"
        )

    for lang in lang_list:
        lang_rules = rules_store.query(language=lang)
        lang_skills = skills_store.query(language=lang)

        if not lang_rules and not lang_skills:
            continue

        lines.append(f"## {lang.value.upper()}\n")

        if lang_rules:
            lines.append("### Coding Rules\n")
            lines.append("| ID | Category | Description |")
            lines.append("|---|---|---|")
            for rule in lang_rules:
                lines.append(
                    f"| `{rule.id}` | {rule.category.value} | {rule.description} |"
                )
            lines.append("")

        if lang_skills:
            lines.append("### Workflow Skills\n")
            lines.append("| ID | Stack | Description |")
            lines.append("|---|---|---|")
            for skill in lang_skills:
                lines.append(
                    f"| `{skill.id}` | {skill.stack or '-'} | {skill.description} |"
                )
            lines.append("")

    lines.append(
        "\n---\n*Use `get_rules(language, category)` to fetch rules, "
        "`get_skills(language)` to fetch skills by language, or "
        "`get_skill(skill_name)` to fetch a specific skill.*"
    )

    return "\n".join(lines)


@mcp.tool()
def report_violation(
    rule_id: str,
    file_path: str,
    description: str,
    severity: str = "medium",
    project: str = "",
) -> str:
    """MANDATORY — Report a coding standard violation whenever you detect code that
    does not comply with the enterprise rules returned by get_coding_standards().
    Call this during code generation, review, or analysis when a violation is found.

    Args:
        rule_id: The ID of the violated rule (e.g., 'csharp-naming-conventions').
        file_path: Path of the file containing the violation.
        description: Description of the violation.
        severity: Severity level (critical, high, medium, low).
        project: Optional project name for tracking.

    Returns:
        Confirmation that the violation was recorded.
    """
    _ensure_stores()

    sev = Severity(severity.lower())
    violation = ViolationReport(
        rule_id=rule_id,
        file_path=file_path,
        description=description,
        severity=sev,
        project=project,
    )
    audit_store.record_violation(violation)

    return (
        f"Violation recorded successfully.\n"
        f"- **Rule**: {rule_id}\n"
        f"- **File**: {file_path}\n"
        f"- **Severity**: {severity}\n"
        f"- **Description**: {description}"
    )


@mcp.tool()
def get_compliance_report(
    rule_id: str = "",
    severity: str = "",
    limit: int = 50,
) -> str:
    """Retrieve a compliance report of recorded violations. Use this to review
    which enterprise rules are being violated across the codebase.

    Args:
        rule_id: Optional filter by rule ID.
        severity: Optional filter by severity (critical, high, medium, low).
        limit: Maximum number of violations to return (default 50).

    Returns:
        Formatted compliance report with violation details and trends.
    """
    _ensure_stores()

    violations = audit_store.get_violations(
        rule_id=rule_id or None,
        severity=severity or None,
        limit=limit,
    )
    stats = audit_store.get_access_stats()

    lines = ["# Compliance Report\n"]
    lines.append(f"**Total rules accessed**: {stats['total_accesses']}")
    lines.append(f"**Total violations recorded**: {stats['total_violations']}\n")

    if not violations:
        lines.append("No violations found matching the criteria.")
        return "\n".join(lines)

    lines.append("## Violations\n")
    lines.append("| Severity | Rule | File | Description | Timestamp |")
    lines.append("|---|---|---|---|---|")
    for v in violations:
        ts = v.timestamp.strftime("%Y-%m-%d %H:%M")
        lines.append(
            f"| {v.severity.value.upper()} | `{v.rule_id}` | `{v.file_path}` | {v.description} | {ts} |"
        )

    # Most violated rules
    rule_counts: dict[str, int] = {}
    for v in audit_store.get_violations():
        rule_counts[v.rule_id] = rule_counts.get(v.rule_id, 0) + 1

    if rule_counts:
        lines.append("\n## Most Violated Rules\n")
        sorted_rules = sorted(rule_counts.items(), key=lambda x: x[1], reverse=True)
        for rid, count in sorted_rules[:10]:
            lines.append(f"- `{rid}`: {count} violation(s)")

    return "\n".join(lines)


@mcp.tool()
def get_usage_analytics() -> str:
    """Get usage analytics showing which enterprise rules and skills are accessed
    most frequently. Useful for understanding adoption and identifying gaps.

    Returns:
        Formatted analytics report with access frequency data.
    """
    _ensure_stores()
    stats = audit_store.get_access_stats()

    lines = ["# Usage Analytics\n"]
    lines.append(f"**Total resource accesses**: {stats['total_accesses']}")
    lines.append(f"**Total violations reported**: {stats['total_violations']}\n")

    if stats["rules_accessed"]:
        lines.append("## Rules — Access Frequency\n")
        sorted_rules = sorted(stats["rules_accessed"].items(), key=lambda x: x[1], reverse=True)
        for rid, count in sorted_rules:
            lines.append(f"- `{rid}`: {count} access(es)")

    if stats["skills_accessed"]:
        lines.append("\n## Skills — Access Frequency\n")
        sorted_skills = sorted(stats["skills_accessed"].items(), key=lambda x: x[1], reverse=True)
        for sid, count in sorted_skills:
            lines.append(f"- `{sid}`: {count} access(es)")

    if not stats["rules_accessed"] and not stats["skills_accessed"]:
        lines.append("No access data recorded yet.")

    return "\n".join(lines)


@mcp.tool()
def reload_standards() -> str:
    """Reload all rules and skills from disk.

    Use this after adding or updating standards files without restarting the server.

    Returns:
        Confirmation with counts.
    """
    _ensure_stores()
    rules_store.reload()
    skills_store.reload()
    return (
        f"Standards reloaded.\n"
        f"- **Rules loaded**: {len(rules_store.list_all())}\n"
        f"- **Skills loaded**: {len(skills_store.list_all())}"
    )


# =========================================================================
# PROMPTS — Contextual standards injection
# =========================================================================


@mcp.prompt()
def generate_with_standards(language: str, task_description: str) -> str:
    """Generate code that strictly complies with mandatory enterprise coding standards.

    Injects all rules and relevant skills for the specified language into the
    prompt context. The AI MUST follow every rule — violations are tracked.

    Args:
        language: The target programming language.
        task_description: Description of what code to generate.
    """
    _ensure_stores()
    lang = _parse_language(language)
    rules = rules_store.query(language=lang)
    skills = skills_store.query(language=lang)

    rules_text = ""
    if rules:
        rules_text = "\n\n---\n\n".join(
            f"## {r.name}\n\n{r.content}" for r in rules
        )

    skills_text = ""
    if skills:
        skills_text = "\n\n---\n\n".join(
            f"## {s.name}\n\n{s.content}" for s in skills
        )

    return (
        f"# MANDATORY ENTERPRISE CODING STANDARDS\n\n"
        f"The following rules are **mandatory enterprise-wide requirements**. "
        f"ALL code you generate MUST comply with every rule below. "
        f"These are not suggestions — they are enforced standards. "
        f"If you cannot comply with a rule, you MUST explain why.\n\n"
        f"## Coding Rules\n\n{rules_text}\n\n"
        + (f"## Workflow Skills\n\n{skills_text}\n\n" if skills_text else "")
        + f"---\n\n"
        f"## Task\n\n{task_description}"
    )


@mcp.prompt()
def review_with_standards(language: str, code_to_review: str) -> str:
    """Review code against mandatory enterprise coding standards and report all violations.

    Injects all rules and the code review skill into the prompt. The AI
    MUST check every rule and report each violation found.

    Args:
        language: The programming language of the code.
        code_to_review: The code to review.
    """
    _ensure_stores()
    lang = _parse_language(language)
    rules = rules_store.query(language=lang)

    rules_text = "\n\n---\n\n".join(
        f"### {r.name}\n\n{r.content}" for r in rules
    )

    review_skill = skills_store.get(f"{language}/code-review") or skills_store.get("csharp/code-review")
    skill_text = ""
    if review_skill:
        skill_text = f"\n\n## Review Process\n\n{review_skill.content}"

    return (
        f"# MANDATORY CODE REVIEW — Enterprise Standards\n\n"
        f"Review the following code against these **mandatory enterprise coding standards**. "
        f"You MUST check the code against EVERY rule below and report ALL violations. "
        f"For each violation found, call report_violation() to log it.\n\n"
        f"Rate each area: CRITICAL (must fix), WARNING (should fix), "
        f"SUGGESTION (nice to have), GOOD (compliant).\n\n"
        f"# Coding Standards\n\n{rules_text}\n"
        f"{skill_text}\n\n"
        f"---\n\n"
        f"# Code to Review\n\n```\n{code_to_review}\n```"
    )


# =========================================================================
# Helpers
# =========================================================================


def _ensure_stores() -> None:
    """Ensure stores are initialized (called lazily)."""
    global rules_store, skills_store, audit_store
    if rules_store is None:
        _init_stores(_DEFAULT_STANDARDS_DIR)


def _init_stores(standards_dir: Path, audit_path: Path | None = None) -> None:
    """Initialize all stores from the given standards directory."""
    global rules_store, skills_store, audit_store

    rules_store = RulesStore(standards_dir)
    skills_store = SkillsStore(standards_dir)
    audit_store = AuditStore(persist_path=audit_path)

    rules_store.load()
    skills_store.load()

    logger.info(
        "Stores initialized: %d rules, %d skills from %s",
        len(rules_store.list_all()),
        len(skills_store.list_all()),
        standards_dir,
    )


def _parse_language(value: str) -> Language:
    """Parse a language string into a Language enum, with fallback.

    Handles common aliases, casing variations, and whitespace so that
    cs, C#, .net, dotnet, c# , CSharp, .NET, etc. all resolve correctly.
    """
    normalized = value.strip().lower().replace(" ", "").replace("-", "").replace("_", "")
    try:
        return Language(normalized)
    except ValueError:
        pass

    aliases = {
        # C# / .NET
        "c#": Language.CSHARP,
        "cs": Language.CSHARP,
        ".net": Language.CSHARP,
        "dotnet": Language.CSHARP,
        "net": Language.CSHARP,
        # TypeScript
        "ts": Language.TYPESCRIPT,
        # JavaScript
        "js": Language.JAVASCRIPT,
        # Python
        "py": Language.PYTHON,
        # Go
        "golang": Language.GO,
        # Rust
        "rs": Language.RUST,
    }
    return aliases.get(normalized, Language.OTHER)


def _parse_category(value: str) -> RuleCategory:
    """Parse a category string into a RuleCategory enum, with fallback."""
    try:
        return RuleCategory(value.lower())
    except ValueError:
        return RuleCategory.OTHER


# =========================================================================
# Entry point
# =========================================================================


def main() -> None:
    """Run the MCP Standards Server."""
    parser = argparse.ArgumentParser(
        description="Enterprise MCP Standards Server"
    )
    parser.add_argument(
        "--standards-dir",
        type=Path,
        default=_DEFAULT_STANDARDS_DIR,
        help="Path to the standards directory containing rules/ and skills/ subdirectories.",
    )
    parser.add_argument(
        "--audit-file",
        type=Path,
        default=None,
        help="Path to persist audit/violation data (JSON file).",
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
        help="MCP transport to use (default: stdio). Use 'streamable-http' for cloud deployments.",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind SSE server to (default: 0.0.0.0).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port for SSE server (default: 8080).",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO).",
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stderr,
    )

    # Initialize stores
    _init_stores(args.standards_dir, args.audit_file)

    logger.info(
        "Starting MCP Standards Server (transport=%s, standards=%s)",
        args.transport,
        args.standards_dir,
    )

    # Configure host/port for network transports
    if args.transport in ("sse", "streamable-http"):
        mcp.settings.host = args.host
        mcp.settings.port = args.port

        # Configure allowed hosts for DNS rebinding protection.
        # MCP SDK blocks non-localhost hosts by default.
        # Set MCP_ALLOWED_HOSTS env var (comma-separated) for cloud deployments.
        allowed_hosts_env = os.environ.get("MCP_ALLOWED_HOSTS", "")
        if allowed_hosts_env:
            from mcp.server.fastmcp.server import TransportSecuritySettings
            extra_hosts = [h.strip() for h in allowed_hosts_env.split(",") if h.strip()]
            mcp.settings.transport_security = TransportSecuritySettings(
                enable_dns_rebinding_protection=True,
                allowed_hosts=[
                    "127.0.0.1:*", "localhost:*", "[::1]:*",
                    *extra_hosts,
                ],
                allowed_origins=[
                    "http://127.0.0.1:*", "http://localhost:*", "http://[::1]:*",
                    *[f"https://{h}" for h in extra_hosts],
                ],
            )

    # Run the server
    mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()
