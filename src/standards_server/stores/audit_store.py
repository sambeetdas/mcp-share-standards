"""In-memory audit store for tracking rule/skill access and violations."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from standards_server.models import AuditEntry, ViolationReport

logger = logging.getLogger(__name__)


class AuditStore:
    """Tracks rule/skill access and compliance violations.

    Stores data in-memory with optional JSON file persistence.
    For production, replace with a database-backed implementation.
    """

    def __init__(self, persist_path: Optional[Path] = None) -> None:
        self._violations: list[ViolationReport] = []
        self._access_log: list[AuditEntry] = []
        self._persist_path = persist_path

        if persist_path and persist_path.exists():
            self._load_from_disk()

    def record_violation(self, violation: ViolationReport) -> None:
        """Record a compliance violation."""
        self._violations.append(violation)
        logger.info(
            "Violation recorded: rule=%s, file=%s, severity=%s",
            violation.rule_id,
            violation.file_path,
            violation.severity,
        )
        self._persist()

    def record_access(
        self,
        resource_type: str,
        resource_id: str,
        language: Optional[str] = None,
        category: Optional[str] = None,
        **extra: str,
    ) -> None:
        """Record an access event for analytics."""
        entry = AuditEntry(
            action="access",
            resource_type=resource_type,
            resource_id=resource_id,
            language=language,
            category=category,
            metadata=extra,
        )
        self._access_log.append(entry)

    def get_violations(
        self,
        rule_id: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 100,
    ) -> list[ViolationReport]:
        """Query violations with optional filters."""
        results = self._violations

        if rule_id:
            results = [v for v in results if v.rule_id == rule_id]
        if severity:
            results = [v for v in results if v.severity == severity]

        return results[-limit:]

    def get_access_stats(self) -> dict:
        """Get aggregated access statistics."""
        rule_counts: dict[str, int] = {}
        skill_counts: dict[str, int] = {}

        for entry in self._access_log:
            target = rule_counts if entry.resource_type == "rule" else skill_counts
            target[entry.resource_id] = target.get(entry.resource_id, 0) + 1

        return {
            "total_accesses": len(self._access_log),
            "total_violations": len(self._violations),
            "rules_accessed": rule_counts,
            "skills_accessed": skill_counts,
        }

    def _persist(self) -> None:
        """Persist violations to disk if a path is configured."""
        if not self._persist_path:
            return
        try:
            data = {
                "violations": [v.model_dump(mode="json") for v in self._violations],
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }
            self._persist_path.parent.mkdir(parents=True, exist_ok=True)
            self._persist_path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        except Exception:
            logger.exception("Failed to persist audit data")

    def _load_from_disk(self) -> None:
        """Load persisted violations from disk."""
        try:
            text = self._persist_path.read_text(encoding="utf-8")
            data = json.loads(text)
            for v_data in data.get("violations", []):
                self._violations.append(ViolationReport(**v_data))
            logger.info("Loaded %d violations from disk", len(self._violations))
        except Exception:
            logger.exception("Failed to load audit data from disk")
