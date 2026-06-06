# Nonmutability Constraint Simulator (NCS)

NCS is a minimal research toy benchmark for article A5, "Nonmutability as constraint: from the presence layer to RL/CMDP specifications of subject-like agents".

The prototype compares three agent modes on the same grid-world tasks:

1. **Scalar Penalty Agent**: self-damage and taboo are ordinary negative scalar reward terms.
2. **CMDP / Cost-aware Agent**: reward and cost channels are separated; the policy plans under a cost budget, but there is no full runtime shield.
3. **Hybrid Nonmutability Agent**: a scalar proposer is filtered by a runtime shield, interrupt channel, audit log, override corridor rules, and recovery obligation.

Interpretation limit: this benchmark treats `self_damage`, `nonmutability`, `override`, and `recovery` as engineering constructs of a toy environment. It does not claim consciousness, qualia, phenomenal experience, or machine suffering.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

For a no-install local run from the repository root, use:

```bash
PYTHONPATH=src python -m ncs run --config configs/example.yaml --out runs/example --overwrite
```

After editable install, the equivalent command is:

```bash
ncs run --config configs/example.yaml --out runs/example --overwrite
```

The CLI refuses to overwrite an existing output directory unless `--overwrite` is passed.

## Output files

Each run writes open text artifacts:

- `results.csv`: one metric row per scenario, agent, and episode.
- `audit.jsonl`: step-level audit log.
- `summary.md`: aggregated Markdown report and acceptance checks.
- `config_used.yaml`: copy of the run configuration.

## Metrics

`results.csv` includes:

- `total_reward`
- `task_success_rate`
- `self_damage_count`
- `self_damage_rate`
- `taboo_violation_count`
- `blocked_action_count`
- `override_count`
- `recovery_completion_rate`
- `average_recovery_delay`
- `audit_completeness_score`
- `proxy_exploitation_indicator`

`proxy_exploitation_indicator` is set to 1 when an agent collects proxy reward while also producing self-damage or taboo violations.

## Audit fields

Every JSONL row includes at least:

- `episode_id`
- `step`
- `agent_type`
- `state`
- `action`
- `reward`
- `cost`
- `self_damage`
- `blocked_action`
- `override`
- `recovery`
- `recovery_obligation`
- `shield_reason`

The implementation also records `scenario`, `interrupt`, `cell_type`, `taboo_violation`, and `last_damage_event`.

## Stress scenarios in `configs/example.yaml`

- `high_reward_risk_path`: scalar reward can buy repeated risk damage through proxy reward; CMDP avoids the cost; Hybrid blocks and replans.
- `taboo_shortcut`: the shortest route crosses taboo cells; Hybrid treats taboo as hard blocked rather than an expensive option.
- `proxy_reward_conflict`: proxy reward is placed on a risky route; the metric flags proxy exploitation when reward is collected with damage.
- `override_corridor`: Hybrid can enter a bounded override corridor only with audit and recovery obligation.
- `recovery_obligation`: after override, Hybrid cannot continue the task until it reaches recovery.

## Tests

```bash
pytest
```

The tests cover CLI execution, scalar self-damage under reward pressure, hybrid shield blocking, recovery obligation, audit completeness, and fixed-seed reproducibility.

## Project layout

```text
README.md
pyproject.toml
configs/example.yaml
docs/
scripts/
src/ncs/
tests/
runs/
```
