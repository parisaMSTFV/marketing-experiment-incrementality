from __future__ import annotations

import argparse
from pathlib import Path

from marketing_incrementality.pipeline import run_pipeline


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
        default=Path.cwd(),
        help="Directory where data and reports are written.",
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


if __name__ == "__main__":
    main()
