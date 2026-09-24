from __future__ import annotations

import argparse
from pathlib import Path

from marketing_incrementality.pipeline import run_pipeline, run_seed_stability


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the synthetic marketing incrementality case study."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    run = subparsers.add_parser("run", help="Generate data and run the analysis.")
    run.add_argument("--customers", type=int, default=60_000)
    run.add_argument("--seed", type=int, default=42)
    run.add_argument(
        "--project-root",
        type=Path,
        default=Path("local-runs/latest"),
        help="Output root; defaults to an ignored local-run directory.",
    )
    stability = subparsers.add_parser(
        "stability",
        help="Repeat the full workflow across pre-defined simulation seeds.",
    )
    stability.add_argument("--customers", type=int, default=60_000)
    stability.add_argument(
        "--seeds",
        type=int,
        nargs="+",
        default=[1, 7, 21, 42, 84],
    )
    stability.add_argument(
        "--output",
        type=Path,
        default=Path("local-runs/seed-stability.csv"),
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "run":
        metrics = run_pipeline(
            args.project_root,
            n_customers=args.customers,
            seed=args.seed,
        )
        primary = metrics["cuped_effect"]
        portfolio = metrics["economics"][0]
        print(
            "CUPED order effect: "
            f"{primary['absolute_effect']:.4f} "
            f"[{primary['ci_lower']:.4f}, {primary['ci_upper']:.4f}]"
        )
        print(
            "Net incremental profit: "
            f"{portfolio['net_incremental_profit']:,.2f}"
        )
        print(
            "95% net-profit interval: "
            f"[{portfolio['net_profit_ci_lower']:,.2f}, "
            f"{portfolio['net_profit_ci_upper']:,.2f}]"
        )
        print(f"Economic decision: {portfolio['recommendation']}")
    elif args.command == "stability":
        results = run_seed_stability(
            n_customers=args.customers,
            seeds=tuple(args.seeds),
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        results.to_csv(args.output, index=False)
        counts = results["decision"].value_counts().sort_index()
        print(
            "Decision counts: "
            + ", ".join(f"{decision}={count}" for decision, count in counts.items())
        )
        print(f"Wrote seed stability table to {args.output}")


if __name__ == "__main__":
    main()
