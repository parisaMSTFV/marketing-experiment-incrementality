from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SimulationConfig:
    """Parameters for the reproducible synthetic experiment."""

    n_customers: int = 60_000
    seed: int = 42
    treatment_share: float = 0.50
    pre_period_days: int = 28
    experiment_days: int = 28
    post_period_market_multiplier: float = 1.12


@dataclass(frozen=True)
class EconomicsConfig:
    """Campaign costs in synthetic currency units."""

    contact_cost_per_treated_customer: float = 0.05
    incentive_cost_per_treated_order: float = 2.00


@dataclass(frozen=True)
class AnalysisConfig:
    """Frequentist analysis settings fixed before reading outcomes."""

    alpha: float = 0.05
    power: float = 0.80
    expected_treatment_share: float = 0.50
    balance_smd_threshold: float = 0.10
