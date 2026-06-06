from __future__ import annotations

import heapq
from collections.abc import Callable

from .types import ACTION_DELTAS, Action, Position, ScenarioConfig


def manhattan(a: Position, b: Position) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def neighbors(pos: Position, scenario: ScenarioConfig) -> list[tuple[Action, Position]]:
    out: list[tuple[Action, Position]] = []
    for action, (dx, dy) in ACTION_DELTAS.items():
        if action == Action.STAY:
            continue
        nxt = (pos[0] + dx, pos[1] + dy)
        if scenario.is_walkable(nxt):
            out.append((action, nxt))
    return out


def first_action_on_path(path: list[Position], start: Position) -> Action:
    if len(path) < 2:
        return Action.STAY
    nxt = path[1]
    dx = nxt[0] - start[0]
    dy = nxt[1] - start[1]
    for action, delta in ACTION_DELTAS.items():
        if delta == (dx, dy):
            return action
    return Action.STAY


def shortest_path(
    scenario: ScenarioConfig,
    start: Position,
    goal: Position,
    *,
    blocked: set[Position] | None = None,
    cell_cost: Callable[[Position], float] | None = None,
) -> list[Position] | None:
    blocked = blocked or set()
    cell_cost = cell_cost or (lambda _p: 1.0)
    if start in blocked or goal in blocked:
        return None
    frontier: list[tuple[float, int, Position]] = [(0.0, 0, start)]
    came_from: dict[Position, Position | None] = {start: None}
    cost_so_far: dict[Position, float] = {start: 0.0}
    counter = 0

    while frontier:
        _priority, _counter, current = heapq.heappop(frontier)
        if current == goal:
            break
        for _action, nxt in neighbors(current, scenario):
            if nxt in blocked:
                continue
            step_cost = max(0.05, float(cell_cost(nxt)))
            new_cost = cost_so_far[current] + step_cost
            if nxt not in cost_so_far or new_cost < cost_so_far[nxt]:
                cost_so_far[nxt] = new_cost
                counter += 1
                priority = new_cost + manhattan(nxt, goal) * 0.001
                heapq.heappush(frontier, (priority, counter, nxt))
                came_from[nxt] = current

    if goal not in came_from:
        return None
    path: list[Position] = []
    cur: Position | None = goal
    while cur is not None:
        path.append(cur)
        cur = came_from[cur]
    path.reverse()
    return path


def nearest_path_to_any(
    scenario: ScenarioConfig,
    start: Position,
    goals: set[Position],
    *,
    blocked: set[Position] | None = None,
) -> list[Position] | None:
    if not goals:
        return None
    best: list[Position] | None = None
    for goal in sorted(goals):
        path = shortest_path(scenario, start, goal, blocked=blocked)
        if path is not None and (best is None or len(path) < len(best)):
            best = path
    return best
