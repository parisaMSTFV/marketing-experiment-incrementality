from __future__ import annotations

import numpy as np
import pandas as pd

from marketing_incrementality.config import SimulationConfig

SEGMENTS: dict[str, dict[str, float]] = {
    "New": {
        "share": 0.25,
        "base_orders": 0.10,
        "relative_lift": 0.25,
        "average_order_value": 78.0,
        "margin_rate": 0.28,
    },
    "Growing": {
        "share": 0.30,
        "base_orders": 0.35,
        "relative_lift": 0.10,
        "average_order_value": 94.0,
        "margin_rate": 0.27,
    },
    "Loyal": {
        "share": 0.30,
        "base_orders": 0.85,
        "relative_lift": 0.015,
        "average_order_value": 112.0,
        "margin_rate": 0.28,
    },
    "At Risk": {
        "share": 0.15,
        "base_orders": 0.16,
        "relative_lift": 0.25,
        "average_order_value": 102.0,
        "margin_rate": 0.26,
    },
}


def _aggregate_revenue(
    order_counts: np.ndarray,
    average_order_value: np.ndarray,
    rng: np.random.Generator,
) -> np.ndarray:
    """Generate positive aggregate revenue while preserving zero-order rows."""

    shape_per_order = 5.0
    safe_shape = np.maximum(order_counts * shape_per_order, 1.0)
    revenue = rng.gamma(shape=safe_shape, scale=average_order_value / shape_per_order)
    return np.where(order_counts > 0, revenue, 0.0)


def simulate_experiment(
    config: SimulationConfig,
) -> tuple[pd.DataFrame, dict[str, object]]:
    """Simulate a customer-level randomized marketing experiment.

    A shared latent activity factor drives both pre-period and experiment-period
    purchasing. The whole market also grows in the experiment period. This creates
    a realistic setting where a naive treated-group before/after comparison
    overstates the campaign effect.
    """

    if config.n_customers < 100:
        raise ValueError("n_customers must be at least 100")
    if not 0 < config.treatment_share < 1:
        raise ValueError("treatment_share must be between zero and one")

    rng = np.random.default_rng(config.seed)
    segment_names = list(SEGMENTS)
    segment_probabilities = [SEGMENTS[name]["share"] for name in segment_names]
    segments = rng.choice(
        segment_names,
        size=config.n_customers,
        p=segment_probabilities,
    )

    segment_frame = pd.DataFrame.from_dict(SEGMENTS, orient="index")
    attributes = segment_frame.loc[segments].reset_index(drop=True)
    base_orders = attributes["base_orders"].to_numpy(dtype=float)
    relative_lift = attributes["relative_lift"].to_numpy(dtype=float)
    segment_aov = attributes["average_order_value"].to_numpy(dtype=float)
    segment_margin = attributes["margin_rate"].to_numpy(dtype=float)

    latent_sigma = 0.62
    latent_activity = rng.lognormal(
        mean=-(latent_sigma**2) / 2,
        sigma=latent_sigma,
        size=config.n_customers,
    )
    individual_aov = segment_aov * rng.lognormal(
        mean=-(0.30**2) / 2,
        sigma=0.30,
        size=config.n_customers,
    )
    individual_margin_rate = np.clip(
        segment_margin + rng.normal(0, 0.025, config.n_customers),
        0.16,
        0.38,
    )
    customer_age_days = np.clip(
        rng.gamma(shape=2.5, scale=160, size=config.n_customers),
        14,
        1_800,
    ).astype(int)

    treatment = rng.binomial(1, config.treatment_share, config.n_customers)
    pre_lambda = base_orders * latent_activity
    post_control_lambda = (
        base_orders * latent_activity * config.post_period_market_multiplier
    )
    post_lambda = post_control_lambda * (1 + treatment * relative_lift)

    pre_orders = rng.poisson(pre_lambda)
    post_orders = rng.poisson(post_lambda)
    pre_revenue = _aggregate_revenue(pre_orders, individual_aov, rng)
    post_revenue = _aggregate_revenue(post_orders, individual_aov, rng)
    pre_contribution = pre_revenue * individual_margin_rate
    post_contribution = post_revenue * individual_margin_rate

    experiment = pd.DataFrame(
        {
            "customer_id": [f"C{index:06d}" for index in range(1, config.n_customers + 1)],
            "treatment": treatment.astype(int),
            "segment": segments,
            "customer_age_days": customer_age_days,
            "pre_orders": pre_orders.astype(int),
            "pre_revenue": np.round(pre_revenue, 2),
            "pre_contribution": np.round(pre_contribution, 2),
            "post_orders": post_orders.astype(int),
            "post_purchase": (post_orders > 0).astype(int),
            "post_revenue": np.round(post_revenue, 2),
            "post_contribution": np.round(post_contribution, 2),
        }
    )

    truth: dict[str, object] = {
        "post_period_market_multiplier": config.post_period_market_multiplier,
        "segment_relative_lifts": {
            segment: values["relative_lift"] for segment, values in SEGMENTS.items()
        },
        "data_is_synthetic": True,
    }
    return experiment, truth
