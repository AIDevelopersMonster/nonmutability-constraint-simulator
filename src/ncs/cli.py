from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import load_config
from .runner import run_experiment


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ncs", description="Nonmutability Constraint Simulator")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="Run a batch experiment")
    run.add_argument("--config", required=True, help="Path to YAML or JSON config")
    run.add_argument("--out", required=True, help="Output directory for run artifacts")
    run.add_argument("--overwrite", action="store_true", help="Allow replacing an existing output directory")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "run":
        config_path = Path(args.config)
        try:
            config = load_config(config_path)
            rows = run_experiment(
                config,
                out_dir=args.out,
                config_path=config_path,
                overwrite=args.overwrite,
            )
        except Exception as exc:  # noqa: BLE001 - CLI should return a user-facing error.
            print(f"ncs: error: {exc}", file=sys.stderr)
            return 2
        print(f"NCS run completed: {len(rows)} episode rows written to {args.out}")
        return 0
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
