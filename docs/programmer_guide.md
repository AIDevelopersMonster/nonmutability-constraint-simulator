# Programmer guide

Core modules:

- `environment.py`: grid-world transition logic and own-state effects.
- `agent_state.py`: integrity, damage flag, accumulated cost, recovery obligation, override event, and last damage event.
- `agents.py`: scalar, CMDP/cost-aware, and hybrid proposer/fallback policies.
- `shield.py`: runtime shield decisions for Hybrid.
- `audit.py`: JSONL audit writer and required field completeness score.
- `metrics.py`: metrics calculation, CSV writing, and Markdown summary.
- `runner.py`: experiment orchestration.
- `cli.py`: command-line interface.
- `config.py`: YAML/JSON config loading.

To add a scenario, append it to `configs/example.yaml` or provide a new YAML/JSON file with the same structure.
