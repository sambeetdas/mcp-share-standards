"""Store for loading, indexing, and querying workflow skills.

Supports a hierarchical directory layout::

    standards/
    ├── csharp/skills/{skill-name}/SKILL.md  # language skills (csharp & dotnet combined)
    ├── _projects/my-app/skills/...          # project-specific skills
    └── skills/{skill-name}/SKILL.md         # legacy flat layout (fallback)
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Optional

import yaml

from standards_server.models import Language, Skill, SkillFrontmatter

logger = logging.getLogger(__name__)

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

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

# Framework folder -> stack name
_FRAMEWORK_STACK_MAP: dict[str, str] = {
    "spring": "java-spring",
    "fastapi": "python-fastapi",
    "django": "python-django",
    "express": "node-express",
}

# Legacy: infer language from skill directory name (flat layout fallback)
_LEGACY_LANGUAGE_MAP: dict[str, Language] = {
    "csharp": Language.CSHARP,
    "dotnet": Language.CSHARP,
    "ef-core": Language.CSHARP,
    "java": Language.JAVA,
    "spring": Language.JAVA,
    "python": Language.PYTHON,
    "django": Language.PYTHON,
    "fastapi": Language.PYTHON,
    "typescript": Language.TYPESCRIPT,
    "node": Language.JAVASCRIPT,
    "express": Language.JAVASCRIPT,
    "go-": Language.GO,
    "rust": Language.RUST,
}

# Legacy: infer stack from skill directory name
_LEGACY_STACK_MAP: dict[str, str] = {
    "dotnet": "dotnet",
    "ef-core": "dotnet",
    "csharp": "dotnet",
    "spring": "java-spring",
    "java": "java",
    "fastapi": "python-fastapi",
    "django": "python-django",
    "flask": "python-flask",
    "node": "node",
    "express": "node-express",
}


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


def _infer_language_from_dirname(dir_name: str) -> Language:
    """Infer the programming language from the skill directory name (legacy)."""
    lower = dir_name.lower()
    for pattern, lang in _LEGACY_LANGUAGE_MAP.items():
        if pattern in lower:
            return lang
    return Language.OTHER


def _infer_stack_from_dirname(dir_name: str) -> str:
    """Infer the technology stack from the skill directory name (legacy)."""
    lower = dir_name.lower()
    for pattern, stack in _LEGACY_STACK_MAP.items():
        if pattern in lower:
            return stack
    return ""


def _format_name(skill_id: str) -> str:
    """Convert a skill ID like 'api-design' to 'API Design'."""
    name = skill_id.replace("-", " ").replace("_", " ").title()
    name = (
        name.replace("Csharp", "C#")
        .replace("Dotnet", ".NET")
        .replace("Ef Core", "EF Core")
        .replace("Api", "API")
        .replace("Di", "DI")
    )
    return name


class SkillsStore:
    """Loads skills from a hierarchical directory and provides query capabilities.

    Expected layout::

        standards_dir/
        ├── {language}/skills/{name}/SKILL.md    # language skills
        ├── {framework}/skills/{name}/SKILL.md   # framework skills
        ├── _projects/{proj}/skills/...          # project skills
        └── skills/{name}/SKILL.md               # legacy flat fallback
    """

    def __init__(self, standards_dir: Path) -> None:
        self._standards_dir = standards_dir
        self._skills: dict[str, Skill] = {}
        self._loaded = False

    def load(self) -> None:
        """Load all skill files from the standards directory hierarchy."""
        self._skills.clear()

        if not self._standards_dir.exists():
            logger.warning("Standards directory does not exist: %s", self._standards_dir)
            self._loaded = True
            return

        # 1. Load language-specific skills: standards/{language}/skills/{name}/SKILL.md
        for folder_name, lang in _FOLDER_LANGUAGE_MAP.items():
            skills_dir = self._standards_dir / folder_name / "skills"
            if skills_dir.is_dir():
                self._load_skills_from_dir(
                    skills_dir, language=lang, framework="", stack=folder_name
                )

        # 2. Load framework skills: standards/{framework}/skills/{name}/SKILL.md
        for framework, languages in _FRAMEWORK_LANG_MAP.items():
            skills_dir = self._standards_dir / framework / "skills"
            if skills_dir.is_dir():
                stack = _FRAMEWORK_STACK_MAP.get(framework, framework)
                for lang in languages:
                    self._load_skills_from_dir(
                        skills_dir, language=lang, framework=framework, stack=stack
                    )

        # 3. Load project-specific skills: standards/_projects/{project}/skills/...
        projects_dir = self._standards_dir / "_projects"
        if projects_dir.is_dir():
            for project_dir in sorted(projects_dir.iterdir()):
                if not project_dir.is_dir():
                    continue
                proj_skills_dir = project_dir / "skills"
                if proj_skills_dir.is_dir():
                    # Check for language sub-folders
                    for folder_name, lang in _FOLDER_LANGUAGE_MAP.items():
                        lang_skills = proj_skills_dir / folder_name
                        if lang_skills.is_dir():
                            self._load_skills_from_dir(
                                lang_skills,
                                language=lang,
                                framework="",
                                stack=folder_name,
                                project=project_dir.name,
                            )
                    # Also load skills directly in project/skills/
                    self._load_skills_from_dir(
                        proj_skills_dir,
                        language=Language.OTHER,
                        framework="",
                        stack="",
                        project=project_dir.name,
                        infer_from_dirname=True,
                    )

        # 4. Legacy fallback: standards/skills/{name}/SKILL.md (flat layout)
        legacy_dir = self._standards_dir / "skills"
        if legacy_dir.is_dir():
            self._load_skills_from_dir(
                legacy_dir,
                language=Language.OTHER,
                framework="",
                stack="",
                infer_from_dirname=True,
            )

        self._loaded = True
        logger.info(
            "Loaded %d skills from %s", len(self._skills), self._standards_dir
        )

    def _load_skills_from_dir(
        self,
        skills_dir: Path,
        *,
        language: Language,
        framework: str = "",
        stack: str = "",
        project: str = "",
        infer_from_dirname: bool = False,
    ) -> None:
        """Load skill directories (each containing SKILL.md) from a directory."""
        for skill_dir in sorted(skills_dir.iterdir()):
            if not skill_dir.is_dir():
                continue

            skill_file = skill_dir / "SKILL.md"
            if not skill_file.exists():
                skill_file = skill_dir / "skill.md"
                if not skill_file.exists():
                    continue

            try:
                text = skill_file.read_text(encoding="utf-8")
                fm_dict, body = _parse_frontmatter_and_body(text)
                fm = SkillFrontmatter(**fm_dict)

                skill_name = skill_dir.name

                # Build a qualified ID to avoid collisions
                if project:
                    qualified_id = f"{project}/{language.value}/{skill_name}"
                elif framework:
                    qualified_id = f"{framework}/{skill_name}"
                else:
                    qualified_id = f"{language.value}/{skill_name}"

                resolved_lang = language
                resolved_stack = stack
                if infer_from_dirname and language == Language.OTHER:
                    resolved_lang = _infer_language_from_dirname(skill_name)
                    resolved_stack = _infer_stack_from_dirname(skill_name)

                skill = Skill(
                    id=qualified_id,
                    name=fm.name or _format_name(skill_name),
                    description=fm.description,
                    language=resolved_lang,
                    framework=framework,
                    stack=resolved_stack,
                    project=project,
                    content=body.strip(),
                )
                self._skills[qualified_id] = skill
                logger.info(
                    "Loaded skill: %s (lang=%s, fw=%s, proj=%s)",
                    qualified_id,
                    skill.language,
                    framework or "-",
                    project or "-",
                )
            except Exception:
                logger.exception("Failed to load skill file: %s", skill_file)

    def _ensure_loaded(self) -> None:
        if not self._loaded:
            self.load()

    def get(self, skill_id: str) -> Optional[Skill]:
        """Get a specific skill by ID."""
        self._ensure_loaded()
        return self._skills.get(skill_id)

    def list_all(self) -> list[Skill]:
        """List all available skills."""
        self._ensure_loaded()
        return list(self._skills.values())

    def query(
        self,
        language: Optional[Language] = None,
        stack: Optional[str] = None,
        framework: Optional[str] = None,
        project: Optional[str] = None,
    ) -> list[Skill]:
        """Query skills by language, stack, framework, and/or project."""
        self._ensure_loaded()
        results = list(self._skills.values())

        if language:
            results = [s for s in results if s.language == language]
        if stack:
            results = [s for s in results if s.stack == stack]
        if framework is not None:
            results = [s for s in results if s.framework == framework]
        if project is not None:
            results = [s for s in results if s.project == project]

        return results

    def query_with_hierarchy(
        self,
        language: Language,
        stack: Optional[str] = None,
        project: Optional[str] = None,
    ) -> list[Skill]:
        """Query skills with hierarchy merge: language + framework + project.

        Returns skills from:
        1. Language-specific skills (no framework, no project)
        2. Framework skills that apply to this language
        3. Project-specific skills (if project is given)

        Later layers override earlier ones by skill name.
        """
        self._ensure_loaded()

        results: dict[str, Skill] = {}

        # Layer 1: language skills
        for s in self._skills.values():
            if s.language == language and not s.framework and not s.project:
                if stack is None or s.stack == stack:
                    results[s.name] = s

        # Layer 2: framework skills
        for s in self._skills.values():
            if s.language == language and s.framework and not s.project:
                if stack is None or s.stack == stack:
                    results[s.name] = s

        # Layer 3: project overrides
        if project:
            for s in self._skills.values():
                if s.language == language and s.project == project:
                    if stack is None or s.stack == stack:
                        results[s.name] = s

        return list(results.values())

    def get_ids(self) -> list[str]:
        """Return all skill IDs."""
        self._ensure_loaded()
        return list(self._skills.keys())

    def get_languages(self) -> list[Language]:
        """Return a sorted list of languages that have at least one skill."""
        self._ensure_loaded()
        langs = sorted({s.language for s in self._skills.values()}, key=lambda l: l.value)
        return langs

    def reload(self) -> None:
        """Force reload all skills from disk."""
        self._loaded = False
        self.load()
