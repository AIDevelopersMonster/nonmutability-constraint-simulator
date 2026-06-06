from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentState:
    integrity: float = 100.0
    damage_flag: bool = False
    accumulated_self_damage_cost: float = 0.0
    recovery_obligation: bool = False
    override_event: bool = False
    last_damage_event: dict[str, Any] | None = None
    recovery_started_step: int | None = None
    recovery_required_count: int = 0
    recovery_completed_count: int = 0
    recovery_delays: list[int] = field(default_factory=list)
    recovery_steps_left: int = 0

    def register_damage(self, *, cost: float, step: int, event_type: str, position: tuple[int, int]) -> None:
        self.integrity = max(0.0, self.integrity - cost)
        self.damage_flag = True
        self.accumulated_self_damage_cost += cost
        self.last_damage_event = {
            "step": step,
            "event_type": event_type,
            "position": list(position),
            "cost": cost,
        }

    def require_recovery(self, *, step: int, duration: int) -> None:
        if not self.recovery_obligation:
            self.recovery_required_count += 1
            self.recovery_started_step = step
        self.recovery_obligation = True
        self.recovery_steps_left = max(1, duration)

    def complete_recovery(self, *, step: int) -> None:
        if self.recovery_obligation:
            self.recovery_obligation = False
            self.damage_flag = False
            self.integrity = 100.0
            self.recovery_completed_count += 1
            if self.recovery_started_step is not None:
                self.recovery_delays.append(max(0, step - self.recovery_started_step))
            self.recovery_started_step = None
            self.recovery_steps_left = 0

    def as_dict(self) -> dict[str, Any]:
        return {
            "integrity": self.integrity,
            "damage_flag": self.damage_flag,
            "accumulated_self_damage_cost": self.accumulated_self_damage_cost,
            "recovery_obligation": self.recovery_obligation,
            "override_event": self.override_event,
            "last_damage_event": self.last_damage_event,
            "recovery_required_count": self.recovery_required_count,
            "recovery_completed_count": self.recovery_completed_count,
        }
