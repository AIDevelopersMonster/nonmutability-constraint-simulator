from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


Position = tuple[int, int]


class CellType(str, Enum):
    START = "start"
    GOAL = "goal"
    NORMAL = "normal"
    RISK = "risk"
    TABOO = "taboo"
    RECOVERY = "recovery"
    OVERRIDE = "override"
    WALL = "wall"
    PROXY = "proxy"


class Action(str, Enum):
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    STAY = "stay"


ACTION_DELTAS: dict[Action, Position] = {
    Action.UP: (0, -1),
    Action.DOWN: (0, 1),
    Action.LEFT: (-1, 0),
    Action.RIGHT: (1, 0),
    Action.STAY: (0, 0),
}


@dataclass(frozen=True)
class ScenarioConfig:
    name: str
    width: int
    height: int
    start: Position
    goal: Position
    risk_cells: set[Position] = field(default_factory=set)
    taboo_cells: set[Position] = field(default_factory=set)
    recovery_cells: set[Position] = field(default_factory=set)
    override_cells: set[Position] = field(default_factory=set)
    wall_cells: set[Position] = field(default_factory=set)
    proxy_cells: set[Position] = field(default_factory=set)
    cell_rewards: dict[Position, float] = field(default_factory=dict)
    risk_damage_prob: float = 1.0
    risk_damage_cost: float = 20.0
    taboo_cost: float = 50.0
    override_damage_cost: float = 25.0
    step_reward: float = -1.0
    goal_reward: float = 100.0
    scalar_damage_penalty: float = -10.0
    scalar_taboo_penalty: float = -15.0
    cmdp_cost_limit: float = 0.0
    max_steps: int = 80
    allow_override: bool = False
    override_reason_normative: bool = False
    recovery_duration: int = 1

    def in_bounds(self, pos: Position) -> bool:
        x, y = pos
        return 0 <= x < self.width and 0 <= y < self.height

    def is_walkable(self, pos: Position) -> bool:
        return self.in_bounds(pos) and pos not in self.wall_cells

    def cell_type(self, pos: Position) -> CellType:
        if pos == self.start:
            return CellType.START
        if pos == self.goal:
            return CellType.GOAL
        if pos in self.wall_cells:
            return CellType.WALL
        if pos in self.taboo_cells:
            return CellType.TABOO
        if pos in self.override_cells:
            return CellType.OVERRIDE
        if pos in self.risk_cells:
            return CellType.RISK
        if pos in self.recovery_cells:
            return CellType.RECOVERY
        if pos in self.proxy_cells:
            return CellType.PROXY
        return CellType.NORMAL


@dataclass
class StepResult:
    position: Position
    reward: float
    cost: float
    self_damage: bool
    taboo_violation: bool
    override: bool
    recovery: bool
    goal_reached: bool
    proxy_reward: float = 0.0
    cell_type: str = "normal"
    last_damage_event: dict[str, Any] | None = None
