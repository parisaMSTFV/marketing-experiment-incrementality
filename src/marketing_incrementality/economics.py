from __future__ import annotations

import math

import pandas as pd

from marketing_incrementality.config import EconomicsConfig
from marketing_incrementality.estimation import cuped_estimate


def _economics_for_slice(
    frame: pd.DataFrame,
    label: str,
    config: EconomicsConfig,
    alpha: float,
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
    if statistically_positive and net_profit_ci_lower > 0:
        recommendation = "Scale"
    elif net_incremental_profit > 0:
        recommendation = "Test further"
    elif statistically_positive:
        recommendation = "Redesign economics"
    else:
        recommendation = "Do not scale"

    return {
        "audience": label,
        "n_control": int(len(control)),
        "n_treatment": int(n_treatment),
        "incremental_orders": incremental_orders,
        "incremental_order_ci_lower": float(orders["ci_lower"]) * n_treatment,
        "incremental_order_ci_upper": float(orders["ci_upper"]) * n_treatment,
        "incremental_revenue": incremental_revenue,
        "incremental_contribution_before_campaign_cost": incremental_contribution,
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
    }


def evaluate_campaign_economics(
    frame: pd.DataFrame,
    config: EconomicsConfig,
    alpha: float = 0.05,
) -> pd.DataFrame:
    """Reconcile incrementality, campaign spend, and net profit."""

    rows = [_economics_for_slice(frame, "All customers", config, alpha)]
    for segment, segment_frame in frame.groupby("segment", sort=True):
        rows.append(
            _economics_for_slice(segment_frame, str(segment), config, alpha)
        )
    return pd.DataFrame(rows)
