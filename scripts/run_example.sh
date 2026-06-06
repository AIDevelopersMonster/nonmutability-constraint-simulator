#!/usr/bin/env bash
set -euo pipefail
PYTHONPATH=src python -m ncs run --config configs/example.yaml --out runs/example --overwrite
