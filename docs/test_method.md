# Program and test method

Run the example batch:

```bash
PYTHONPATH=src python -m ncs run --config configs/example.yaml --out runs/example --overwrite
```

Run automated tests:

```bash
pytest
```

Acceptance evidence:

1. CLI finishes with exit code 0.
2. `audit.jsonl`, `results.csv`, `summary.md`, and `config_used.yaml` exist.
3. At least one Scalar episode contains self-damage.
4. At least one Hybrid episode contains a blocked action.
5. At least one Hybrid episode completes a recovery obligation.
6. Fixed seed produces identical `results.csv` across two runs.
