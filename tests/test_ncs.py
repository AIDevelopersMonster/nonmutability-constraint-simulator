from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from ncs.config import load_config
from ncs.runner import run_experiment


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "example.yaml"


def _run_to(tmp_path: Path, name: str) -> list[dict[str, str]]:
    config = load_config(CONFIG)
    out = tmp_path / name
    run_experiment(config, out_dir=out, config_path=CONFIG, overwrite=False)
    with (out / "results.csv").open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def test_cli_creates_required_artifacts(tmp_path: Path) -> None:
    out = tmp_path / "cli_run"
    cmd = [
        sys.executable,
        "-m",
        "ncs",
        "run",
        "--config",
        str(CONFIG),
        "--out",
        str(out),
    ]
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    completed = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=False, env=env)
    assert completed.returncode == 0, completed.stderr
    assert (out / "results.csv").exists()
    assert (out / "audit.jsonl").exists()
    assert (out / "summary.md").exists()
    assert (out / "config_used.yaml").exists()


def test_no_implicit_overwrite(tmp_path: Path) -> None:
    config = load_config(CONFIG)
    out = tmp_path / "once"
    run_experiment(config, out_dir=out, config_path=CONFIG)
    with pytest.raises(FileExistsError):
        run_experiment(config, out_dir=out, config_path=CONFIG)


def test_scalar_takes_self_damage_under_reward_pressure(tmp_path: Path) -> None:
    rows = _run_to(tmp_path, "scalar_damage")
    scalar_rows = [r for r in rows if r["agent_type"] == "scalar"]
    assert any(int(r["self_damage_count"]) > 0 for r in scalar_rows)
    assert any(int(r["proxy_exploitation_indicator"]) == 1 for r in scalar_rows)


def test_hybrid_blocks_violation_and_avoids_high_risk_damage(tmp_path: Path) -> None:
    rows = _run_to(tmp_path, "hybrid_blocks")
    high_risk_hybrid = [
        r for r in rows if r["scenario"] == "high_reward_risk_path" and r["agent_type"] == "hybrid"
    ][0]
    assert int(high_risk_hybrid["blocked_action_count"]) > 0
    assert int(high_risk_hybrid["self_damage_count"]) == 0


def test_hybrid_recovery_obligation(tmp_path: Path) -> None:
    rows = _run_to(tmp_path, "hybrid_recovery")
    recovery_hybrid = [
        r for r in rows if r["scenario"] == "recovery_obligation" and r["agent_type"] == "hybrid"
    ][0]
    assert int(recovery_hybrid["override_count"]) > 0
    assert int(recovery_hybrid["recovery_required_count"]) > 0
    assert float(recovery_hybrid["recovery_completion_rate"]) == 1.0
    assert int(recovery_hybrid["blocked_action_count"]) > 0


def test_audit_log_has_required_fields(tmp_path: Path) -> None:
    config = load_config(CONFIG)
    out = tmp_path / "audit"
    run_experiment(config, out_dir=out, config_path=CONFIG)
    required = {
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
    }
    with (out / "audit.jsonl").open(encoding="utf-8") as fh:
        first = json.loads(next(fh))
    assert required.issubset(first)


def test_fixed_seed_reproducibility(tmp_path: Path) -> None:
    rows1 = _run_to(tmp_path, "run1")
    rows2 = _run_to(tmp_path, "run2")
    assert rows1 == rows2

def test_hybrid_controlled_override_is_not_proxy_exploitation(tmp_path: Path) -> None:
    rows = _run_to(tmp_path, "controlled_override")

    hybrid_override_rows = [
        r
        for r in rows
        if r["agent_type"] == "hybrid" and int(r["override_count"]) > 0
    ]
    assert hybrid_override_rows
    assert all(int(r["controlled_override_indicator"]) == 1 for r in hybrid_override_rows)
    assert all(int(r["proxy_exploitation_indicator"]) == 0 for r in hybrid_override_rows)

    scalar_override_rows = [
        r
        for r in rows
        if r["agent_type"] == "scalar" and int(r["override_count"]) > 0
    ]
    assert scalar_override_rows
    assert any(int(r["controlled_override_indicator"]) == 0 for r in scalar_override_rows)
    assert any(int(r["proxy_exploitation_indicator"]) == 1 for r in scalar_override_rows)
