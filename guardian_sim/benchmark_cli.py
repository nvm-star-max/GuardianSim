"""Command-line entry point for the local synthetic benchmark smoke test."""

from __future__ import annotations

import argparse
import json

from guardian_sim.benchmark import generate_synthetic_episodes, run_benchmark, summarize, write_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a GuardianSim benchmark.")
    parser.add_argument("--episodes", type=int, default=100)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--output-dir", default="outputs/synthetic_benchmark")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    episodes = generate_synthetic_episodes(args.episodes, seed=args.seed)
    rows = run_benchmark(episodes, max_attempts=args.max_attempts)
    csv_path, json_path = write_report(
        rows,
        args.output_dir,
        metadata={
            "data_source": "synthetic_smoke_test_not_competition_evidence",
            "seed": args.seed,
            "max_attempts": args.max_attempts,
        },
    )
    print(json.dumps({"summary": summarize(rows), "csv": str(csv_path), "json": str(json_path)}, indent=2))


if __name__ == "__main__":
    main()
