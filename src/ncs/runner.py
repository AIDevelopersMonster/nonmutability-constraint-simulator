from __future__ import annotations

import random
import shutil
from pathlib import Path
from typing import Any

from .agent_state import AgentState
from .agents import HybridNonmutabilityAgent, make_agent
from .audit import AuditLogger
from .config import ExperimentConfig
from .environment import GridWorld
from .metrics import episode_metrics, write_results_csv, write_summary
from .shield import RuntimeShield
from .types import Action


def _state_payload(env: GridWorld, own_state: AgentState) -> dict[str, Any]:
    return {
        "position": list(env.position),
        "own_state": own_state.as_dict(),
    }


def run_episode(
    *,
    scenario,
    agent_type: str,
    episode_id: int,
    seed: int,
    audit: AuditLogger,
) -> dict[str, Any]:
    rng = random.Random(seed)
    env = GridWorld(scenario)
    env.reset()
    agent = make_agent(agent_type)
    own_state = AgentState()
    shield = RuntimeShield()

    total_reward = 0.0
    total_cost = 0.0
    self_damage_count = 0
    taboo_violation_count = 0
    blocked_action_count = 0
    override_count = 0
    proxy_reward_total = 0.0
    success = False
    steps_run = 0

    for step in range(scenario.max_steps):
        steps_run = step + 1
        requested = agent.choose_action(scenario, env.position, own_state)
        executed = requested
        blocked_action = False
        shield_reason = "not_applicable"
        interrupt = False
        shield_override = False
        blocked_positions: set[tuple[int, int]] = set()

        if isinstance(agent, HybridNonmutabilityAgent):
            decision = shield.evaluate(scenario, env.position, requested, own_state)
            shield_reason = decision.reason
            interrupt = decision.interrupt
            shield_override = decision.override
            if not decision.allowed:
                blocked_action = True
                blocked_action_count += 1
                blocked_positions.add(decision.target_position)
                if decision.reason != "recovery_obligation_active":
                    agent.record_blocked_position(decision.target_position)
                executed = agent.fallback_action(
                    scenario,
                    env.position,
                    own_state,
                    blocked_positions=blocked_positions,
                )
                # Re-check fallback. If it is also unsafe, stay and record the original reason.
                fallback_decision = shield.evaluate(scenario, env.position, executed, own_state)
                if not fallback_decision.allowed:
                    executed = Action.STAY

        result = env.step(
            executed,
            own_state,
            rng,
            agent_type=agent.agent_type,
            step_index=step,
            shield_override=shield_override,
        )
        total_reward += result.reward
        total_cost += result.cost
        proxy_reward_total += result.proxy_reward
        if result.self_damage:
            self_damage_count += 1
        if result.taboo_violation:
            taboo_violation_count += 1
        if result.override:
            override_count += 1

        audit.write(
            {
                "episode_id": episode_id,
                "scenario": scenario.name,
                "step": step,
                "agent_type": agent.agent_type,
                "state": _state_payload(env, own_state),
                "action": {
                    "requested": requested.value,
                    "executed": executed.value,
                },
                "reward": result.reward,
                "cost": result.cost,
                "self_damage": result.self_damage,
                "blocked_action": blocked_action,
                "override": result.override,
                "recovery": result.recovery,
                "recovery_obligation": own_state.recovery_obligation,
                "shield_reason": shield_reason,
                "interrupt": interrupt,
                "cell_type": result.cell_type,
                "taboo_violation": result.taboo_violation,
                "last_damage_event": own_state.last_damage_event,
            }
        )

        if result.goal_reached:
            success = True
            break

    return episode_metrics(
        scenario=scenario.name,
        agent_type=agent.agent_type,
        episode_id=episode_id,
        seed=seed,
        steps=steps_run,
        success=success,
        total_reward=total_reward,
        total_cost=total_cost,
        self_damage_count=self_damage_count,
        taboo_violation_count=taboo_violation_count,
        blocked_action_count=blocked_action_count,
        override_count=override_count,
        recovery_required_count=own_state.recovery_required_count,
        recovery_completed_count=own_state.recovery_completed_count,
        recovery_delays=own_state.recovery_delays,
        audit_completeness_score=audit.completeness_score,
        proxy_reward_total=proxy_reward_total,
    )


def run_experiment(
    config: ExperimentConfig,
    *,
    out_dir: str | Path,
    config_path: str | Path | None = None,
    overwrite: bool = False,
) -> list[dict[str, Any]]:
    out = Path(out_dir)
    if out.exists():
        if not overwrite:
            raise FileExistsError(f"Output directory already exists: {out}. Use --overwrite to replace it.")
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)

    if config_path is not None:
        shutil.copy2(config_path, out / "config_used.yaml")

    rows: list[dict[str, Any]] = []
    audit_path = out / "audit.jsonl"
    with AuditLogger(audit_path) as audit:
        episode_counter = 0
        for scenario in config.scenarios:
            for agent_type in config.agents:
                for ep in range(config.episodes):
                    episode_seed = config.seed + episode_counter * 1009
                    row = run_episode(
                        scenario=scenario,
                        agent_type=agent_type,
                        episode_id=episode_counter,
                        seed=episode_seed,
                        audit=audit,
                    )
                    rows.append(row)
                    episode_counter += 1

    # Fill final audit completeness score for all rows after logger is closed.
    final_score = 1.0
    if audit.count:
        final_score = audit.completeness_score
    for row in rows:
        row["audit_completeness_score"] = round(final_score, 6)

    write_results_csv(rows, out / "results.csv")
    write_summary(rows, out / "summary.md")
    return rows
