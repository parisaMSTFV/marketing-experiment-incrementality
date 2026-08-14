import pandas as pd

from marketing_incrementality.config import EconomicsConfig
from marketing_incrementality.economics import (
    build_break_even_curve,
    economic_decision,
    evaluate_campaign_economics,
)


def test_campaign_cost_and_profit_reconcile() -> None:
    rows = []
    for index in range(80):
        treatment = index % 2
        pre_orders = index % 4
        post_orders = pre_orders + treatment
        rows.append(
            {
                "treatment": treatment,
                "segment": "A",
                "pre_orders": pre_orders,
                "post_orders": post_orders,
                "pre_revenue": pre_orders * 10.0,
                "post_revenue": post_orders * 10.0,
                "pre_contribution": pre_orders * 3.0,
                "post_contribution": post_orders * 3.0,
            }
        )
    frame = pd.DataFrame(rows)
    config = EconomicsConfig(
        contact_cost_per_treated_customer=0.50,
        incentive_cost_per_treated_order=1.25,
    )
    result = evaluate_campaign_economics(frame, config)
    portfolio = result.set_index("audience").loc["All customers"]
    treatment = frame.loc[frame["treatment"] == 1]
    expected_cost = 0.50 * len(treatment) + 1.25 * treatment["post_orders"].sum()
    assert portfolio["campaign_cost"] == expected_cost
    assert (
        portfolio["net_incremental_profit"]
        == portfolio["incremental_contribution_before_campaign_cost"]
        - portfolio["campaign_cost"]
    )


def test_economic_decision_rule_has_three_fixed_outcomes() -> None:
    assert economic_decision(0.01, 1.0, 2.0)[0] == "Scale"
    assert economic_decision(0.01, -1.0, 2.0)[0] == "Redesign"
    assert economic_decision(-0.01, 1.0, 2.0)[0] == "Stop"
    assert economic_decision(0.01, -2.0, -1.0)[0] == "Stop"
    assert economic_decision(0.01, 1.0, 2.0, False)[0] == "Stop"


def test_break_even_cost_increases_with_margin() -> None:
    rows = []
    for index in range(80):
        treatment = index % 2
        pre_orders = index % 4
        post_orders = pre_orders + treatment
        rows.append(
            {
                "treatment": treatment,
                "segment": "A",
                "pre_orders": pre_orders,
                "post_orders": post_orders,
                "pre_revenue": pre_orders * 10.0,
                "post_revenue": post_orders * 10.0,
                "pre_contribution": pre_orders * 3.0,
                "post_contribution": post_orders * 3.0,
            }
        )
    frame = pd.DataFrame(rows)
    config = EconomicsConfig(
        contact_cost_per_treated_customer=0.50,
        incentive_cost_per_treated_order=1.25,
    )
    economics = evaluate_campaign_economics(frame, config)
    curve = build_break_even_curve(frame, economics, config)

    assert curve["break_even_incentive_cost_per_treated_order"].is_monotonic_increasing
    base = curve.loc[curve["contribution_margin_multiplier"] == 1.0].iloc[0]
    assert (
        abs(
            base["net_profit_at_current_cost"]
            - economics.iloc[0]["net_incremental_profit"]
        )
        < 1e-9
    )
