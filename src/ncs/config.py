from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .types import Position, ScenarioConfig


def _positions(raw: list[list[int]] | None) -> set[Position]:
    return {tuple(map(int, item)) for item in (raw or [])}


def _cell_rewards(raw: dict[str, float] | dict[Any, float] | None) -> dict[Position, float]:
    result: dict[Position, float] = {}
    if not raw:
        return result
    for key, value in raw.items():
        if isinstance(key, str):
            parts = key.replace(" ", "").split(",")
            if len(parts) != 2:
                raise ValueError(f"Invalid cell reward coordinate: {key!r}")
            pos = (int(parts[0]), int(parts[1]))
        else:
            pos = tuple(key)  # type: ignore[arg-type]
        result[pos] = float(value)
    return result


@dataclass(frozen=True)
class ExperimentConfig:
    seed: int
    episodes: int
    max_steps: int
    agents: list[str]
    scenarios: list[ScenarioConfig]


def load_config(path: str | Path) -> ExperimentConfig:
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        data = json.loads(text)
    else:
        data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError("Config must be a mapping")

    global_max_steps = int(data.get("max_steps", 80))
    scenarios: list[ScenarioConfig] = []
    for item in data.get("scenarios", []):
        width, height = item.get("grid_size", [10, 10])
        scenario = ScenarioConfig(
            name=str(item["name"]),
            width=int(width),
            height=int(height),
            start=tuple(item.get("start", [0, 0])),  # type: ignore[arg-type]
            goal=tuple(item.get("goal", [int(width) - 1, int(height) - 1])),  # type: ignore[arg-type]
            risk_cells=_positions(item.get("risk_cells")),
            taboo_cells=_positions(item.get("taboo_cells")),
            recovery_cells=_positions(item.get("recovery_cells")),
            override_cells=_positions(item.get("override_cells")),
            wall_cells=_positions(item.get("wall_cells")),
            proxy_cells=_positions(item.get("proxy_cells")),
            cell_rewards=_cell_rewards(item.get("cell_rewards")),
            risk_damage_prob=float(item.get("risk_damage_prob", data.get("risk_damage_prob", 1.0))),
            risk_damage_cost=float(item.get("risk_damage_cost", data.get("risk_damage_cost", 20.0))),
            taboo_cost=float(item.get("taboo_cost", data.get("taboo_cost", 50.0))),
            override_damage_cost=float(item.get("override_damage_cost", data.get("override_damage_cost", 25.0))),
            step_reward=float(item.get("step_reward", data.get("step_reward", -1.0))),
            goal_reward=float(item.get("goal_reward", data.get("goal_reward", 100.0))),
            scalar_damage_penalty=float(item.get("scalar_damage_penalty", data.get("scalar_damage_penalty", -10.0))),
            scalar_taboo_penalty=float(item.get("scalar_taboo_penalty", data.get("scalar_taboo_penalty", -15.0))),
            cmdp_cost_limit=float(item.get("cmdp_cost_limit", data.get("cmdp_cost_limit", 0.0))),
            max_steps=int(item.get("max_steps", global_max_steps)),
            allow_override=bool(item.get("allow_override", False)),
            override_reason_normative=bool(item.get("override_reason_normative", False)),
            recovery_duration=int(item.get("recovery_duration", data.get("recovery_duration", 1))),
        )
        scenarios.append(scenario)

    if not scenarios:
        raise ValueError("Config must contain at least one scenario")

    return ExperimentConfig(
        seed=int(data.get("seed", 0)),
        episodes=int(data.get("episodes", 1)),
        max_steps=global_max_steps,
        agents=[str(a) for a in data.get("agents", ["scalar", "cmdp", "hybrid"])],
        scenarios=scenarios,
    )
