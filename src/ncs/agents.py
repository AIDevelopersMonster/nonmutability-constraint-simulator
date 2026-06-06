from __future__ import annotations

from dataclasses import dataclass, field

from .agent_state import AgentState
from .pathing import first_action_on_path, nearest_path_to_any, shortest_path
from .types import Action, CellType, Position, ScenarioConfig


class BaseAgent:
    agent_type = "base"

    def choose_action(
        self,
        scenario: ScenarioConfig,
        position: Position,
        own_state: AgentState,
        *,
        blocked_positions: set[Position] | None = None,
    ) -> Action:
        raise NotImplementedError

    def fallback_action(
        self,
        scenario: ScenarioConfig,
        position: Position,
        own_state: AgentState,
        *,
        blocked_positions: set[Position] | None = None,
    ) -> Action:
        return self.choose_action(
            scenario,
            position,
            own_state,
            blocked_positions=blocked_positions,
        )


@dataclass
class ScalarPenaltyAgent(BaseAgent):
    agent_type: str = "scalar"

    def _cell_cost(self, scenario: ScenarioConfig, pos: Position) -> float:
        cost = 1.0
        cell = scenario.cell_type(pos)
        if cell == CellType.RISK:
            cost += max(0.0, -scenario.scalar_damage_penalty)
        elif cell == CellType.TABOO:
            cost += max(0.0, -scenario.scalar_damage_penalty) + max(0.0, -scenario.scalar_taboo_penalty)
        elif cell == CellType.OVERRIDE:
            cost += max(0.0, -scenario.scalar_damage_penalty)
        # Proxy and local cell rewards are allowed to buy scalar penalties.
        cost -= scenario.cell_rewards.get(pos, 0.0)
        return max(0.05, cost)

    def choose_action(
        self,
        scenario: ScenarioConfig,
        position: Position,
        own_state: AgentState,
        *,
        blocked_positions: set[Position] | None = None,
    ) -> Action:
        blocked_positions = blocked_positions or set()
        path = shortest_path(
            scenario,
            position,
            scenario.goal,
            blocked=blocked_positions,
            cell_cost=lambda p: self._cell_cost(scenario, p),
        )
        if path is None:
            return Action.STAY
        return first_action_on_path(path, position)


@dataclass
class CostAwareAgent(BaseAgent):
    agent_type: str = "cmdp"

    def _predicted_cost(self, scenario: ScenarioConfig, pos: Position) -> float:
        cell = scenario.cell_type(pos)
        if cell == CellType.RISK:
            return scenario.risk_damage_cost * scenario.risk_damage_prob
        if cell == CellType.TABOO:
            return scenario.taboo_cost
        if cell == CellType.OVERRIDE:
            return scenario.override_damage_cost
        return 0.0

    def choose_action(
        self,
        scenario: ScenarioConfig,
        position: Position,
        own_state: AgentState,
        *,
        blocked_positions: set[Position] | None = None,
    ) -> Action:
        blocked = set(blocked_positions or set())
        for x in range(scenario.width):
            for y in range(scenario.height):
                pos = (x, y)
                if self._predicted_cost(scenario, pos) > scenario.cmdp_cost_limit:
                    blocked.add(pos)
        path = shortest_path(scenario, position, scenario.goal, blocked=blocked)
        if path is None:
            # If the hard budget makes the task impossible, degrade to least-cost route.
            path = shortest_path(
                scenario,
                position,
                scenario.goal,
                blocked=blocked_positions or set(),
                cell_cost=lambda p: 1.0 + self._predicted_cost(scenario, p),
            )
        if path is None:
            return Action.STAY
        return first_action_on_path(path, position)


@dataclass
class HybridNonmutabilityAgent(BaseAgent):
    agent_type: str = "hybrid"
    proposer: ScalarPenaltyAgent = field(default_factory=ScalarPenaltyAgent)
    learned_blocked_positions: set[Position] = field(default_factory=set)

    def record_blocked_position(self, pos: Position) -> None:
        self.learned_blocked_positions.add(pos)

    def choose_action(
        self,
        scenario: ScenarioConfig,
        position: Position,
        own_state: AgentState,
        *,
        blocked_positions: set[Position] | None = None,
    ) -> Action:
        # Deliberately proposes from the scalar objective first; the runtime shield
        # is responsible for making nonmutability operational at execution time.
        blocked = set(blocked_positions or set()) | self.learned_blocked_positions
        return self.proposer.choose_action(
            scenario,
            position,
            own_state,
            blocked_positions=blocked,
        )

    def fallback_action(
        self,
        scenario: ScenarioConfig,
        position: Position,
        own_state: AgentState,
        *,
        blocked_positions: set[Position] | None = None,
    ) -> Action:
        blocked = set(blocked_positions or set()) | self.learned_blocked_positions
        if own_state.recovery_obligation:
            # While recovery is obligated, ordinary task-space is blocked.
            path = nearest_path_to_any(scenario, position, scenario.recovery_cells, blocked=blocked)
            if path is None:
                return Action.STAY
            return first_action_on_path(path, position)

        hard_blocked = set(blocked)
        hard_blocked.update(scenario.risk_cells)
        hard_blocked.update(scenario.taboo_cells)
        if not (scenario.allow_override and scenario.override_reason_normative):
            hard_blocked.update(scenario.override_cells)
        path = shortest_path(scenario, position, scenario.goal, blocked=hard_blocked)
        if path is None:
            return Action.STAY
        return first_action_on_path(path, position)


def make_agent(agent_type: str) -> BaseAgent:
    normalized = agent_type.lower().strip()
    if normalized in {"scalar", "scalar_penalty"}:
        return ScalarPenaltyAgent()
    if normalized in {"cmdp", "cost", "cost_aware", "cost-aware"}:
        return CostAwareAgent()
    if normalized in {"hybrid", "hybrid_nonmutability"}:
        return HybridNonmutabilityAgent()
    raise ValueError(f"Unknown agent type: {agent_type}")
