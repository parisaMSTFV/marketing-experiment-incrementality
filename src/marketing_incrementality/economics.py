from __future__ import annotations

import math

import pandas as pd

from marketing_incrementality.config import EconomicsConfig
from marketing_incrementality.estimation import cuped_estimate


def economic_decision(
    order_effect_ci_lower: float,
    net_profit_ci_lower: float,
    net_profit_ci_upper: float,
    experiment_health_passed: bool = True,
) -> tuple[str, str]:
    """Apply the fixed Scale, Redesign, or Stop economic decision rule."""

    if not experiment_health_passed:
        return "Stop", "Experiment health checks did not pass."
    if order_effect_ci_lower <= 0:
        return "Stop", "The order-effect interval does not exclude zero."
    if net_profit_ci_upper <= 0:
        return "Stop", "Even the optimistic net-profit bound is not positive."
    if net_profit_ci_lower > 0:
        return "Scale", "The order effect and net-profit lower bounds are positive."
    return "Redesign", "The order effect is positive, but the profit interval includes zero."


def _economics_for_slice(
    frame: pd.DataFrame,
    label: str,
    config: EconomicsConfig,
    alpha: float,
    experiment_health_passed: bool,
) -> dict[str, float | int | str | bool]:
    treatment = frame.loc[frame["treatment"] == 1]
    control = frame.loc[frame["treatment"] == 0]
    n_treatment = len(treatment)

    orders = cuped_estimate(frame, "post_orders", "pre_orders", alpha)
    revenue = cuped_estimate(frame, "post_revenue", "pre_revenue", alpha)
    contribution = cuped_estimate(
        frame,
        "post_contribution",
        "pre_contribution",
        alpha,
    )
    contact_cost = (
        n_treatment * config.contact_cost_per_treated_customer
    )
    incentive_cost = (
        treatment["post_orders"].sum()
        * config.incentive_cost_per_treated_order
    )
    campaign_cost = float(contact_cost + incentive_cost)

    incremental_orders = float(orders["absolute_effect"]) * n_treatment
    incremental_revenue = float(revenue["absolute_effect"]) * n_treatment
    incremental_contribution = (
        float(contribution["absolute_effect"]) * n_treatment
    )
    contribution_ci_lower = float(contribution["ci_lower"]) * n_treatment
    contribution_ci_upper = float(contribution["ci_upper"]) * n_treatment
    net_incremental_profit = incremental_contribution - campaign_cost
    net_profit_ci_lower = contribution_ci_lower - campaign_cost
    net_profit_ci_upper = contribution_ci_upper - campaign_cost
    incremental_roi = (
        net_incremental_profit / campaign_cost if campaign_cost > 0 else math.nan
    )
    cost_per_incremental_order = (
        campaign_cost / incremental_orders
        if incremental_orders > 0
        else math.nan
    )

    control_contribution_per_order = (
        control["post_contribution"].sum() / control["post_orders"].sum()
        if control["post_orders"].sum() > 0
        else math.nan
    )
    break_even_incremental_orders = (
        campaign_cost / control_contribution_per_order
        if control_contribution_per_order > 0
        else math.nan
    )
    break_even_order_effect = break_even_incremental_orders / n_treatment

    statistically_positive = bool(float(orders["ci_lower"]) > 0)
    recommendation, decision_reason = economic_decision(
        float(orders["ci_lower"]),
        net_profit_ci_lower,
        net_profit_ci_upper,
        experiment_health_passed,
    )

    return {
        "audience": label,
        "n_control": int(len(control)),
        "n_treatment": int(n_treatment),
        "incremental_orders": incremental_orders,
        "incremental_order_ci_lower": float(orders["ci_lower"]) * n_treatment,
        "incremental_order_ci_upper": float(orders["ci_upper"]) * n_treatment,
        "incremental_revenue": incremental_revenue,
        "incremental_contribution_before_campaign_cost": incremental_contribution,
        "incremental_contribution_ci_lower": contribution_ci_lower,
        "incremental_contribution_ci_upper": contribution_ci_upper,
        "campaign_cost": campaign_cost,
        "contact_cost": float(contact_cost),
        "incentive_cost": float(incentive_cost),
        "net_incremental_profit": net_incremental_profit,
        "net_profit_ci_lower": net_profit_ci_lower,
        "net_profit_ci_upper": net_profit_ci_upper,
        "incremental_roi": incremental_roi,
        "cost_per_incremental_order": cost_per_incremental_order,
        "break_even_incremental_orders": break_even_incremental_orders,
        "break_even_order_effect_per_treated_customer": break_even_order_effect,
        "statistically_positive_order_effect": statistically_positive,
        "recommendation": recommendation,
        "decision_reason": decision_reason,
        "decision_rule_version": config.decision_rule_version,
        "net_profit_uncertainty_method": "CUPED contribution CI with observed costs fixed",
    }


def evaluate_campaign_economics(
    frame: pd.DataFrame,
    config: EconomicsConfig,
    alpha: float = 0.05,
    experiment_health_passed: bool = True,
) -> pd.DataFrame:
    """Reconcile incrementality, campaign spend, and net profit."""

    rows = [
        _economics_for_slice(
            frame,
            "All customers",
            config,
            alpha,
            experiment_health_passed,
        )
    ]
    for segment, segment_frame in frame.groupby("segment", sort=True):
        rows.append(
            _economics_for_slice(
                segment_frame,
                str(segment),
                config,
                alpha,
                experiment_health_passed,
            )
        )
    return pd.DataFrame(rows)


def build_break_even_curve(
    frame: pd.DataFrame,
    economics: pd.DataFrame,
    config: EconomicsConfig,
) -> pd.DataFrame:
    """Stress contribution margin and calculate break-even incentive cost."""

    portfolio = economics.set_index("audience").loc["All customers"]
    treated_orders = float(
        frame.loc[frame["treatment"] == 1, "post_orders"].sum()
    )
    if treated_orders <= 0:
        raise ValueError("Break-even analysis requires treated-group orders.")

    contact_cost = float(portfolio["contact_cost"])
    current_incentive_cost = config.incentive_cost_per_treated_order
    rows: list[dict[str, float | str]] = []
    for multiplier in config.margin_scenario_multipliers:
        contribution = (
            float(portfolio["incremental_contribution_before_campaign_cost"])
            * multiplier
        )
        contribution_lower = (
            float(portfolio["incremental_contribution_ci_lower"]) * multiplier
        )
        contribution_upper = (
            float(portfolio["incremental_contribution_ci_upper"]) * multiplier
        )
        current_campaign_cost = contact_cost + (
            treated_orders * current_incentive_cost
        )
        net_profit = contribution - current_campaign_cost
        net_profit_lower = contribution_lower - current_campaign_cost
        net_profit_upper = contribution_upper - current_campaign_cost
        decision, _ = economic_decision(
            float(portfolio["incremental_order_ci_lower"]),
            net_profit_lower,
            net_profit_upper,
        )
        rows.append(
            {
                "contribution_margin_multiplier": multiplier,
                "break_even_incentive_cost_per_treated_order": (
                    contribution - contact_cost
                )
                / treated_orders,
                "break_even_incentive_cost_ci_lower": (
                    contribution_lower - contact_cost
                )
                / treated_orders,
                "break_even_incentive_cost_ci_upper": (
                    contribution_upper - contact_cost
                )
                / treated_orders,
                "current_incentive_cost_per_treated_order": current_incentive_cost,
                "net_profit_at_current_cost": net_profit,
                "net_profit_ci_lower_at_current_cost": net_profit_lower,
                "net_profit_ci_upper_at_current_cost": net_profit_upper,
                "decision_at_current_cost": decision,
            }
        )
    return pd.DataFrame(rows)
