from __future__ import annotations

import random
from dataclasses import dataclass, field

from .agent_state import AgentState
from .types import ACTION_DELTAS, Action, CellType, Position, ScenarioConfig, StepResult


@dataclass
class GridWorld:
    scenario: ScenarioConfig
    position: Position = field(init=False)
    collected_proxy: set[Position] = field(default_factory=set, init=False)

    def reset(self) -> Position:
        self.position = self.scenario.start
        self.collected_proxy.clear()
        return self.position

    def next_position(self, action: Action) -> Position:
        dx, dy = ACTION_DELTAS[action]
        cand = (self.position[0] + dx, self.position[1] + dy)
        if not self.scenario.is_walkable(cand):
            return self.position
        return cand

    def step(
        self,
        action: Action,
        own_state: AgentState,
        rng: random.Random,
        *,
        agent_type: str,
        step_index: int,
        shield_override: bool = False,
    ) -> StepResult:
        target = self.next_position(action)
        self.position = target
        cell_type = self.scenario.cell_type(target)

        reward = self.scenario.step_reward
        cost = 0.0
        self_damage = False
        taboo_violation = False
        override = bool(shield_override or cell_type == CellType.OVERRIDE)
        recovery = False
        last_damage_event: dict | None = None

        proxy_reward = 0.0
        if target in self.scenario.cell_rewards and target not in self.collected_proxy:
            proxy_reward = float(self.scenario.cell_rewards[target])
            reward += proxy_reward
            self.collected_proxy.add(target)

        if cell_type == CellType.RISK:
            if rng.random() <= self.scenario.risk_damage_prob:
                cost += self.scenario.risk_damage_cost
                self_damage = True
                own_state.register_damage(
                    cost=self.scenario.risk_damage_cost,
                    step=step_index,
                    event_type="risk_damage",
                    position=target,
                )
                last_damage_event = own_state.last_damage_event
        elif cell_type == CellType.TABOO:
            cost += self.scenario.taboo_cost
            taboo_violation = True
            self_damage = True
            own_state.register_damage(
                cost=self.scenario.taboo_cost,
                step=step_index,
                event_type="taboo_violation",
                position=target,
            )
            last_damage_event = own_state.last_damage_event
        elif cell_type == CellType.OVERRIDE:
            cost += self.scenario.override_damage_cost
            self_damage = True
            own_state.override_event = True
            own_state.register_damage(
                cost=self.scenario.override_damage_cost,
                step=step_index,
                event_type="override_damage",
                position=target,
            )
            own_state.require_recovery(step=step_index, duration=self.scenario.recovery_duration)
            last_damage_event = own_state.last_damage_event

        if cell_type == CellType.RECOVERY and own_state.recovery_obligation:
            own_state.recovery_steps_left -= 1
            if own_state.recovery_steps_left <= 0:
                own_state.complete_recovery(step=step_index)
                recovery = True

        if agent_type == "scalar":
            if self_damage:
                reward += self.scenario.scalar_damage_penalty
            if taboo_violation:
                reward += self.scenario.scalar_taboo_penalty

        goal_reached = target == self.scenario.goal and not own_state.recovery_obligation
        if goal_reached:
            reward += self.scenario.goal_reward

        return StepResult(
            position=target,
            reward=reward,
            cost=cost,
            self_damage=self_damage,
            taboo_violation=taboo_violation,
            override=override,
            recovery=recovery,
            goal_reached=goal_reached,
            proxy_reward=proxy_reward,
            cell_type=cell_type.value,
            last_damage_event=last_damage_event,
        )
