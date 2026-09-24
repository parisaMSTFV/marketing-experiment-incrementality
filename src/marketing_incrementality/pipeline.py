from __future__ import annotations

import json
import math
import tempfile
from pathlib import Path

import pandas as pd

from marketing_incrementality.config import (
    AnalysisConfig,
    EconomicsConfig,
    SimulationConfig,
)
from marketing_incrementality.diagnostics import balance_table, sample_ratio_check
from marketing_incrementality.economics import (
    build_break_even_curve,
    evaluate_campaign_economics,
)
from marketing_incrementality.estimation import (
    cuped_estimate,
    difference_in_means,
    estimate_segment_effects,
)
from marketing_incrementality.power import build_power_curve
from marketing_incrementality.reporting import (
    plot_before_after_vs_experiment,
    plot_economic_break_even,
    plot_effect_estimates,
    plot_power_curve,
    plot_precision_comparison,
    plot_segment_effects,
    plot_segment_profitability,
)
from marketing_incrementality.simulate import simulate_experiment


def _json_value(value: object) -> object:
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _records(frame: pd.DataFrame) -> list[dict[str, object]]:
    return [
        {key: _json_value(value) for key, value in row.items()}
        for row in frame.to_dict(orient="records")
    ]


def _write_run_summary(
    path: Path,
    metrics: dict[str, object],
    segment_effects: pd.DataFrame,
    economics: pd.DataFrame,
    break_even_curve: pd.DataFrame,
) -> None:
    health = metrics["experiment_health"]
    primary = metrics["primary_effect"]
    cuped = metrics["cuped_effect"]
    portfolio = economics.set_index("audience").loc["All customers"]
    base_break_even = break_even_curve.loc[
        break_even_curve["contribution_margin_multiplier"] == 1.0
    ].iloc[0]
    profitable_segments = economics.loc[
        (economics["audience"] != "All customers")
        & (economics["net_incremental_profit"] > 0),
        "audience",
    ].tolist()
    significant_segments = segment_effects.loc[
        segment_effects["significant_after_holm"], "segment"
    ].tolist()
    content = f"""# Reproducible run summary

This report was generated from a fully synthetic randomized experiment with seed
`{metrics["run"]["seed"]}`.

## Experiment health

- {metrics["run"]["simulated_customers"]:,} randomized customers
- {health["control_customers"]:,} control and {health["treatment_customers"]:,} treatment
- Sample ratio check p-value: {health["p_value"]:.3f}
- Largest absolute standardized pre-treatment difference:
  {metrics["balance"]["maximum_absolute_smd"]:.3f}

## Incremental effect

- Control mean: {primary["control_mean"]:.3f} orders per customer
- Unadjusted effect: {primary["absolute_effect"]:.3f} orders per customer
  ({primary["relative_lift"]:.1%} relative lift)
- 95% confidence interval: [{primary["ci_lower"]:.3f}, {primary["ci_upper"]:.3f}]
- CUPED effect: {cuped["absolute_effect"]:.3f} orders per customer
- CUPED variance reduction: {cuped["variance_reduction"]:.1%}

## Economics

- Estimated incremental orders: {portfolio["incremental_orders"]:,.0f}
- Incremental contribution before campaign cost:
  {portfolio["incremental_contribution_before_campaign_cost"]:,.0f}
- Campaign cost: {portfolio["campaign_cost"]:,.0f}
- Net incremental profit: {portfolio["net_incremental_profit"]:,.0f}
- 95% net-profit interval: [{portfolio["net_profit_ci_lower"]:,.0f},
  {portfolio["net_profit_ci_upper"]:,.0f}]
- Incremental ROI: {portfolio["incremental_roi"]:.1%}
- Portfolio recommendation: **{portfolio["recommendation"]}**
- Point break-even incentive cost at the base margin: \
{base_break_even["break_even_incentive_cost_per_treated_order"]:.2f} per treated order

The profit interval applies CUPED to customer-level net value after realized contact
and order-linked incentive costs. It captures sampling variation in those realized
costs, but not uncertainty in future unit costs or margin assumptions. The break-even
scenario changes contribution margin mechanically; it is not a probability model for
future margins.

Profitable segment estimates: {", ".join(profitable_segments) or "none"}.
Segments significant after Holm adjustment: {", ".join(significant_segments) or "none"}.

These figures validate the analysis workflow on simulated data. They are not evidence
of real campaign performance.
"""
    path.write_text(content, encoding="utf-8")


def _write_decision_note(
    path: Path,
    metrics: dict[str, object],
    economics: pd.DataFrame,
    break_even_curve: pd.DataFrame,
) -> None:
    primary = metrics["cuped_effect"]
    portfolio = economics.set_index("audience").loc["All customers"]
    base_break_even = break_even_curve.loc[
        break_even_curve["contribution_margin_multiplier"] == 1.0
    ].iloc[0]
    segment_rows = economics.loc[economics["audience"] != "All customers"].copy()
    scale_candidates = segment_rows.loc[
        segment_rows["net_incremental_profit"] > 0, "audience"
    ].tolist()
    avoid = segment_rows.loc[
        segment_rows["net_incremental_profit"] <= 0, "audience"
    ].tolist()
    content = f"""# Campaign decision note

## Decision

**{portfolio["recommendation"]}.**

The randomized comparison estimates {primary["absolute_effect"]:.3f} incremental
orders per treated customer, with a 95% confidence interval from
{primary["ci_lower"]:.3f} to {primary["ci_upper"]:.3f}. The campaign therefore changes
behavior in the synthetic experiment.

At the current contact and incentive costs, estimated net incremental profit is
{portfolio["net_incremental_profit"]:,.0f}, with a 95% interval from
{portfolio["net_profit_ci_lower"]:,.0f} to {portfolio["net_profit_ci_upper"]:,.0f}.
The interval includes zero, so the fixed rule does not support scale. The main issue is
subsidy leakage: the incentive is paid on treatment-group orders that would have happened
without the campaign as well.

## Fixed economic decision rule

The versioned `{portfolio["decision_rule_version"]}` rule produces exactly one output:

| Output | Condition after experiment health checks pass |
|---|---|
| Scale | Order-effect lower bound > 0 and net-profit lower bound > 0 |
| Redesign | Order-effect lower bound > 0 and the net-profit interval includes zero |
| Stop | Order-effect lower bound <= 0 or net-profit upper bound <= 0 |

Current rule reason: {portfolio["decision_reason"]}

## Break-even evidence

At the base contribution margin, the point break-even incentive cost is
{base_break_even["break_even_incentive_cost_per_treated_order"]:.2f} per treated order,
compared with the current cost of
{base_break_even["current_incentive_cost_per_treated_order"]:.2f}. The 95% contribution-
effect interval maps to a break-even range from
{base_break_even["break_even_incentive_cost_ci_lower"]:.2f} to
{base_break_even["break_even_incentive_cost_ci_upper"]:.2f}.

The profit interval is estimated from customer-level net value, so realized order-linked
incentive variation is included. Future unit-cost and margin uncertainty is not. The
margin multipliers in `economic_break_even.csv` are deterministic stress scenarios, not
forecasts.

## Recommended next test

- Exclude or reduce spend on: {", ".join(avoid) or "none"}.
- Re-test the offer in: {", ".join(scale_candidates) or "none"}.
- Keep the randomized holdout and the same primary metric.
- Pre-register any new targeting rule before reading the next experiment outcome.
- Treat segment findings as decision inputs, not proof of permanent causal differences.

The separate `seed_stability.csv` artifact shows whether the portfolio decision and
segment point estimates persist across repeated synthetic samples.

All values in this note come from synthetic data and exist only to demonstrate the
decision workflow.
"""
    path.write_text(content, encoding="utf-8")


def run_pipeline(
    project_root: Path,
    n_customers: int = 60_000,
    seed: int = 42,
) -> dict[str, object]:
    """Generate data, validate the experiment, estimate impact, and report economics."""

    project_root = project_root.resolve()
    data_dir = project_root / "data" / "generated"
    reports_dir = project_root / "reports"
    figures_dir = reports_dir / "figures"
    for directory in [data_dir, reports_dir, figures_dir]:
        directory.mkdir(parents=True, exist_ok=True)

    simulation_config = SimulationConfig(n_customers=n_customers, seed=seed)
    analysis_config = AnalysisConfig()
    economics_config = EconomicsConfig()
    experiment, truth = simulate_experiment(simulation_config)
    experiment.to_csv(
        data_dir / "synthetic_experiment.csv.gz",
        index=False,
        compression={"method": "gzip", "mtime": 0},
    )

    srm = sample_ratio_check(
        experiment,
        analysis_config.expected_treatment_share,
        analysis_config.alpha,
    )
    balance = balance_table(
        experiment,
        [
            "customer_age_days",
            "pre_orders",
            "pre_revenue",
            "pre_contribution",
        ],
        threshold=analysis_config.balance_smd_threshold,
    )
    balance.to_csv(reports_dir / "balance_checks.csv", index=False)

    estimate_rows: list[dict[str, object]] = []
    for outcome, covariate in [
        ("post_orders", "pre_orders"),
        ("post_purchase", "pre_orders"),
        ("post_revenue", "pre_revenue"),
        ("post_contribution", "pre_contribution"),
    ]:
        estimate_rows.append(
            difference_in_means(experiment, outcome, analysis_config.alpha)
        )
        estimate_rows.append(
            cuped_estimate(
                experiment,
                outcome,
                covariate,
                analysis_config.alpha,
            )
        )
    estimates = pd.DataFrame(estimate_rows)
    estimates.to_csv(reports_dir / "effect_estimates.csv", index=False)

    segment_effects = estimate_segment_effects(
        experiment,
        alpha=analysis_config.alpha,
    )
    segment_effects.to_csv(reports_dir / "segment_effects.csv", index=False)
    economics = evaluate_campaign_economics(
        experiment,
        economics_config,
        analysis_config.alpha,
        experiment_health_passed=bool(srm["passed"]),
    )
    economics.to_csv(reports_dir / "campaign_economics.csv", index=False)
    break_even_curve = build_break_even_curve(
        experiment,
        economics,
        economics_config,
    )
    break_even_curve.to_csv(reports_dir / "economic_break_even.csv", index=False)
    power_curve = build_power_curve(
        experiment,
        alpha=analysis_config.alpha,
        power=analysis_config.power,
    )
    power_curve.to_csv(reports_dir / "power_curve.csv", index=False)

    plot_before_after_vs_experiment(
        experiment,
        figures_dir / "before_after_vs_experiment.png",
    )
    plot_effect_estimates(estimates, figures_dir / "effect_estimates.png")
    plot_precision_comparison(estimates, figures_dir / "cuped_precision.png")
    plot_segment_effects(segment_effects, figures_dir / "segment_effects.png")
    plot_segment_profitability(
        economics,
        figures_dir / "segment_profitability.png",
    )
    plot_economic_break_even(
        break_even_curve,
        figures_dir / "economic_break_even.png",
    )
    plot_power_curve(power_curve, figures_dir / "power_curve.png")

    primary = estimates.loc[
        (estimates["outcome"] == "post_orders")
        & (estimates["method"] == "Unadjusted difference in means")
    ].iloc[0]
    cuped = estimates.loc[
        (estimates["outcome"] == "post_orders")
        & (estimates["method"] == "CUPED")
    ].iloc[0]
    metrics: dict[str, object] = {
        "run": {
            "seed": seed,
            "simulated_customers": n_customers,
            "data_is_synthetic": True,
        },
        "experiment_health": srm,
        "balance": {
            "maximum_absolute_smd": float(balance["absolute_smd"].max()),
            "all_checks_passed": bool(balance["passed"].all()),
        },
        "primary_effect": {
            key: _json_value(value) for key, value in primary.to_dict().items()
        },
        "cuped_effect": {
            key: _json_value(value) for key, value in cuped.to_dict().items()
        },
        "simulation_truth": truth,
        "segment_effects": _records(segment_effects),
        "economics": _records(economics),
        "economic_break_even": _records(break_even_curve),
    }
    (reports_dir / "metrics.json").write_text(
        json.dumps(metrics, indent=2, allow_nan=False),
        encoding="utf-8",
    )
    _write_run_summary(
        reports_dir / "run_summary.md",
        metrics,
        segment_effects,
        economics,
        break_even_curve,
    )
    _write_decision_note(
        reports_dir / "decision_note.md",
        metrics,
        economics,
        break_even_curve,
    )
    return metrics


def run_seed_stability(
    n_customers: int = 60_000,
    seeds: tuple[int, ...] = (1, 7, 21, 42, 84),
) -> pd.DataFrame:
    """Repeat the full decision workflow and summarize sensitivity to simulation seed."""

    if not seeds:
        raise ValueError("at least one seed is required")
    rows: list[dict[str, object]] = []
    for seed in seeds:
        with tempfile.TemporaryDirectory(prefix=f"incrementality-seed-{seed}-") as run_dir:
            metrics = run_pipeline(Path(run_dir), n_customers=n_customers, seed=seed)
        effect = metrics["cuped_effect"]
        portfolio = metrics["economics"][0]
        positive_segments = sorted(
            row["audience"]
            for row in metrics["economics"]
            if row["audience"] != "All customers"
            and float(row["net_incremental_profit"]) > 0
        )
        rows.append(
            {
                "seed": seed,
                "customers": n_customers,
                "cuped_order_effect": effect["absolute_effect"],
                "order_ci_lower": effect["ci_lower"],
                "order_ci_upper": effect["ci_upper"],
                "net_incremental_profit": portfolio["net_incremental_profit"],
                "net_profit_ci_lower": portfolio["net_profit_ci_lower"],
                "net_profit_ci_upper": portfolio["net_profit_ci_upper"],
                "decision": portfolio["recommendation"],
                "positive_point_estimate_segments": "|".join(positive_segments),
            }
        )
    return pd.DataFrame(rows)
