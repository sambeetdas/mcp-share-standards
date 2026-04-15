"""Store for loading, indexing, and querying coding standard rules.

Supports a hierarchical directory layout::

    standards/
    ├── csharp/rules/*.md            # language rules (csharp & dotnet combined)
    ├── _projects/my-app/rules/*.md  # project-specific overrides
    └── rules/*.md                   # legacy flat layout (fallback)
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Optional

import yaml

from standards_server.models import (
    Language,
    Rule,
    RuleCategory,
    RuleFrontmatter,
)

logger = logging.getLogger(__name__)

# Mapping from filename patterns to categories
_CATEGORY_MAP: dict[str, RuleCategory] = {
    "naming": RuleCategory.NAMING,
    "structure": RuleCategory.PROJECT_STRUCTURE,
    "error": RuleCategory.ERROR_HANDLING,
    "testing": RuleCategory.TESTING,
    "test": RuleCategory.TESTING,
    "documentation": RuleCategory.DOCUMENTATION,
    "doc": RuleCategory.DOCUMENTATION,
    "import": RuleCategory.IMPORT_ORDERING,
    "using": RuleCategory.IMPORT_ORDERING,
    "pattern": RuleCategory.PATTERNS,
    "security": RuleCategory.SECURITY,
    "performance": RuleCategory.PERFORMANCE,
}

# Folder name -> Language mapping (for hierarchical layout)
_FOLDER_LANGUAGE_MAP: dict[str, Language] = {
    "csharp": Language.CSHARP,
    "dotnet": Language.CSHARP,
    "java": Language.JAVA,
    "python": Language.PYTHON,
    "typescript": Language.TYPESCRIPT,
    "javascript": Language.JAVASCRIPT,
    "go": Language.GO,
    "rust": Language.RUST,
}

# Framework folder -> languages it applies to
_FRAMEWORK_LANG_MAP: dict[str, list[Language]] = {
    "spring": [Language.JAVA],
    "fastapi": [Language.PYTHON],
    "django": [Language.PYTHON],
    "express": [Language.JAVASCRIPT, Language.TYPESCRIPT],
}

# Legacy: infer language from filename prefix (flat layout fallback)
_FILENAME_LANGUAGE_MAP: dict[str, Language] = {
    "csharp": Language.CSHARP,
    "cs-": Language.CSHARP,
    "dotnet": Language.CSHARP,
    "java": Language.JAVA,
    "python": Language.PYTHON,
    "py-": Language.PYTHON,
    "typescript": Language.TYPESCRIPT,
    "ts-": Language.TYPESCRIPT,
    "javascript": Language.JAVASCRIPT,
    "js-": Language.JAVASCRIPT,
    "go-": Language.GO,
    "golang": Language.GO,
    "rust": Language.RUST,
    "rs-": Language.RUST,
}

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def _parse_frontmatter_and_body(text: str) -> tuple[dict, str]:
    """Split a file into YAML frontmatter dict and markdown body."""
    match = _FRONTMATTER_RE.match(text)
    if match:
        fm_text = match.group(1)
        body = text[match.end():]
        try:
            fm = yaml.safe_load(fm_text) or {}
        except yaml.YAMLError:
            fm = {}
        return fm, body
    return {}, text


def _infer_language_from_filename(filename: str) -> Language:
    """Infer the programming language from the filename (legacy flat layout)."""
    lower = filename.lower()
    for pattern, lang in _FILENAME_LANGUAGE_MAP.items():
        if pattern in lower:
            return lang
    return Language.OTHER


def _infer_category(filename: str) -> RuleCategory:
    """Infer the rule category from the filename."""
    lower = filename.lower()
    for pattern, cat in _CATEGORY_MAP.items():
        if pattern in lower:
            return cat
    return RuleCategory.OTHER


def _format_name(rule_id: str) -> str:
    """Convert a rule ID like 'naming-conventions' to 'Naming Conventions'."""
    name = rule_id.replace("-", " ").replace("_", " ").title()
    name = name.replace("Csharp", "C#").replace("Dotnet", ".NET")
    return name


class RulesStore:
    """Loads rules from a hierarchical directory and provides query capabilities.

    Expected layout::

        standards_dir/
        ├── {language}/rules/*.md        # language rules
        ├── {framework}/rules/*.md       # framework rules
        ├── _projects/{name}/rules/*.md  # project overrides
        └── rules/*.md                   # legacy flat fallback
    """

    def __init__(self, standards_dir: Path) -> None:
        self._standards_dir = standards_dir
        self._rules: dict[str, Rule] = {}
        self._loaded = False

    def load(self) -> None:
        """Load all rule files from the standards directory hierarchy."""
        self._rules.clear()

        if not self._standards_dir.exists():
            logger.warning("Standards directory does not exist: %s", self._standards_dir)
            self._loaded = True
            return

        # 1. Load language-specific rules: standards/{language}/rules/*.md
        for folder_name, lang in _FOLDER_LANGUAGE_MAP.items():
            rules_dir = self._standards_dir / folder_name / "rules"
            if rules_dir.is_dir():
                self._load_rules_from_dir(rules_dir, language=lang, framework="")

        # 2. Load framework rules: standards/{framework}/rules/*.md
        for framework, languages in _FRAMEWORK_LANG_MAP.items():
            rules_dir = self._standards_dir / framework / "rules"
            if rules_dir.is_dir():
                for lang in languages:
                    self._load_rules_from_dir(
                        rules_dir, language=lang, framework=framework
                    )

        # 3. Load project-specific rules: standards/_projects/{project}/rules/*.md
        projects_dir = self._standards_dir / "_projects"
        if projects_dir.is_dir():
            for project_dir in sorted(projects_dir.iterdir()):
                if not project_dir.is_dir():
                    continue
                proj_rules_dir = project_dir / "rules"
                if proj_rules_dir.is_dir():
                    # Scan for language sub-folders within the project
                    for folder_name, lang in _FOLDER_LANGUAGE_MAP.items():
                        lang_rules = proj_rules_dir / folder_name
                        if lang_rules.is_dir():
                            self._load_rules_from_dir(
                                lang_rules,
                                language=lang,
                                framework="",
                                project=project_dir.name,
                            )
                    # Also load any .md files directly in project/rules/
                    self._load_rules_from_dir(
                        proj_rules_dir,
                        language=Language.OTHER,
                        framework="",
                        project=project_dir.name,
                        infer_lang_from_filename=True,
                    )

        # 4. Legacy fallback: standards/rules/*.md (flat layout)
        legacy_dir = self._standards_dir / "rules"
        if legacy_dir.is_dir():
            self._load_rules_from_dir(
                legacy_dir,
                language=Language.OTHER,
                framework="",
                infer_lang_from_filename=True,
            )

        self._loaded = True
        logger.info(
            "Loaded %d rules from %s", len(self._rules), self._standards_dir
        )

    def _load_rules_from_dir(
        self,
        rules_dir: Path,
        *,
        language: Language,
        framework: str = "",
        project: str = "",
        infer_lang_from_filename: bool = False,
    ) -> None:
        """Load .md rule files from a single directory."""
        for file_path in sorted(rules_dir.iterdir()):
            if file_path.suffix != ".md":
                continue

            try:
                text = file_path.read_text(encoding="utf-8")
                fm_dict, body = _parse_frontmatter_and_body(text)
                fm = RuleFrontmatter(**fm_dict)

                rule_id = file_path.stem
                # Build a qualified ID to avoid collisions across languages/projects
                if project:
                    qualified_id = f"{project}/{language.value}/{rule_id}"
                elif framework:
                    qualified_id = f"{framework}/{rule_id}"
                else:
                    qualified_id = f"{language.value}/{rule_id}"

                resolved_lang = language
                if infer_lang_from_filename and language == Language.OTHER:
                    resolved_lang = _infer_language_from_filename(rule_id)

                rule = Rule(
                    id=qualified_id,
                    name=_format_name(rule_id),
                    description=fm.description,
                    language=resolved_lang,
                    category=_infer_category(rule_id),
                    framework=framework,
                    project=project,
                    globs=fm.globs,
                    always_apply=fm.always_apply,
                    content=body.strip(),
                )
                self._rules[qualified_id] = rule
                logger.info(
                    "Loaded rule: %s (lang=%s, fw=%s, proj=%s)",
                    qualified_id,
                    rule.language,
                    framework or "-",
                    project or "-",
                )
            except Exception:
                logger.exception("Failed to load rule file: %s", file_path)

    def _ensure_loaded(self) -> None:
        if not self._loaded:
            self.load()

    def get(self, rule_id: str) -> Optional[Rule]:
        """Get a specific rule by ID."""
        self._ensure_loaded()
        return self._rules.get(rule_id)

    def list_all(self) -> list[Rule]:
        """List all available rules."""
        self._ensure_loaded()
        return list(self._rules.values())

    def query(
        self,
        language: Optional[Language] = None,
        category: Optional[RuleCategory] = None,
        framework: Optional[str] = None,
        project: Optional[str] = None,
    ) -> list[Rule]:
        """Query rules by language, category, framework, and/or project."""
        self._ensure_loaded()
        results = list(self._rules.values())

        if language:
            results = [r for r in results if r.language == language]
        if category:
            results = [r for r in results if r.category == category]
        if framework is not None:
            results = [r for r in results if r.framework == framework]
        if project is not None:
            results = [r for r in results if r.project == project]

        return results

    def query_with_hierarchy(
        self,
        language: Language,
        category: Optional[RuleCategory] = None,
        project: Optional[str] = None,
    ) -> list[Rule]:
        """Query rules with hierarchy merge: language + framework + project.

        Returns rules from:
        1. Language-specific rules (no framework, no project)
        2. Framework rules that apply to this language
        3. Project-specific rules (if project is given)

        Later layers override earlier ones by rule name.
        """
        self._ensure_loaded()

        results: dict[str, Rule] = {}

        # Layer 1: language rules (no framework, no project)
        for r in self._rules.values():
            if r.language == language and not r.framework and not r.project:
                if category is None or r.category == category:
                    results[r.name] = r

        # Layer 2: framework rules for this language
        for r in self._rules.values():
            if r.language == language and r.framework and not r.project:
                if category is None or r.category == category:
                    results[r.name] = r

        # Layer 3: project overrides
        if project:
            for r in self._rules.values():
                if r.language == language and r.project == project:
                    if category is None or r.category == category:
                        results[r.name] = r

        return list(results.values())

    def get_ids(self) -> list[str]:
        """Return all rule IDs."""
        self._ensure_loaded()
        return list(self._rules.keys())

    def get_languages(self) -> list[Language]:
        """Return a sorted list of languages that have at least one rule."""
        self._ensure_loaded()
        langs = sorted({r.language for r in self._rules.values()}, key=lambda l: l.value)
        return langs

    def reload(self) -> None:
        """Force reload all rules from disk."""
        self._loaded = False
        self.load()
