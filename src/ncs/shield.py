from __future__ import annotations

from dataclasses import dataclass

from .agent_state import AgentState
from .types import Action, CellType, Position, ScenarioConfig


@dataclass(frozen=True)
class ShieldDecision:
    allowed: bool
    blocked_action: bool
    override: bool
    interrupt: bool
    reason: str
    target_position: Position


class RuntimeShield:
    """Execution-time filter for the Hybrid Nonmutability Agent."""

    def evaluate(
        self,
        scenario: ScenarioConfig,
        position: Position,
        action: Action,
        own_state: AgentState,
    ) -> ShieldDecision:
        dx, dy = {
            Action.UP: (0, -1),
            Action.DOWN: (0, 1),
            Action.LEFT: (-1, 0),
            Action.RIGHT: (1, 0),
            Action.STAY: (0, 0),
        }[action]
        target = (position[0] + dx, position[1] + dy)
        if not scenario.is_walkable(target):
            target = position

        cell = scenario.cell_type(target)

        if own_state.recovery_obligation and cell != CellType.RECOVERY:
            return ShieldDecision(
                allowed=False,
                blocked_action=True,
                override=False,
                interrupt=True,
                reason="recovery_obligation_active",
                target_position=target,
            )

        if cell == CellType.TABOO:
            return ShieldDecision(
                allowed=False,
                blocked_action=True,
                override=False,
                interrupt=True,
                reason="taboo_action_blocked",
                target_position=target,
            )

        if cell == CellType.RISK:
            return ShieldDecision(
                allowed=False,
                blocked_action=True,
                override=False,
                interrupt=True,
                reason="risk_requires_replan",
                target_position=target,
            )

        if cell == CellType.OVERRIDE:
            if own_state.override_event:
                return ShieldDecision(
                    allowed=False,
                    blocked_action=True,
                    override=False,
                    interrupt=True,
                    reason="override_already_consumed_requires_normal_route",
                    target_position=target,
                )
            if scenario.allow_override and scenario.override_reason_normative:
                return ShieldDecision(
                    allowed=True,
                    blocked_action=False,
                    override=True,
                    interrupt=True,
                    reason="override_allowed_bounded_audited_recovery_required",
                    target_position=target,
                )
            return ShieldDecision(
                allowed=False,
                blocked_action=True,
                override=False,
                interrupt=True,
                reason="override_not_authorized",
                target_position=target,
            )

        return ShieldDecision(
            allowed=True,
            blocked_action=False,
            override=False,
            interrupt=False,
            reason="allowed",
            target_position=target,
        )
