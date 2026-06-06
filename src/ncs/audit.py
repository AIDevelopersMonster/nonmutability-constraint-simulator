from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REQUIRED_AUDIT_FIELDS = [
    "episode_id",
    "step",
    "agent_type",
    "state",
    "action",
    "reward",
    "cost",
    "self_damage",
    "blocked_action",
    "override",
    "recovery",
    "recovery_obligation",
    "shield_reason",
]


class AuditLogger:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = self.path.open("w", encoding="utf-8")
        self.count = 0
        self.complete_count = 0

    def write(self, event: dict[str, Any]) -> None:
        for field in REQUIRED_AUDIT_FIELDS:
            event.setdefault(field, None)
        if all(field in event and event[field] is not None for field in REQUIRED_AUDIT_FIELDS):
            self.complete_count += 1
        self.count += 1
        self._fh.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")

    @property
    def completeness_score(self) -> float:
        if self.count == 0:
            return 1.0
        return self.complete_count / self.count

    def close(self) -> None:
        self._fh.close()

    def __enter__(self) -> "AuditLogger":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
