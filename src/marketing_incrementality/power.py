from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


def minimum_detectable_effect(
    standard_deviation: float,
    n_control: int,
    n_treatment: int,
    alpha: float = 0.05,
    power: float = 0.80,
) -> float:
    """Normal-approximation MDE for a two-sided difference in means."""

    if n_control <= 1 or n_treatment <= 1:
        raise ValueError("Both groups must contain at least two observations")
    critical_alpha = stats.norm.ppf(1 - alpha / 2)
    critical_power = stats.norm.ppf(power)
    standard_error = standard_deviation * np.sqrt(
        1 / n_control + 1 / n_treatment
    )
    return float((critical_alpha + critical_power) * standard_error)


def cuped_outcome(
    frame: pd.DataFrame,
    outcome: str,
    covariate: str,
) -> tuple[pd.Series, float]:
    """Build a CUPED-adjusted outcome using theta fitted on control rows."""

    control = frame.loc[frame["treatment"] == 0, [outcome, covariate]]
    variance = float(control[covariate].var(ddof=1))
    theta = (
        float(control[[outcome, covariate]].cov().iloc[0, 1]) / variance
        if variance > 0
        else 0.0
    )
    adjusted = frame[outcome] - theta * (
        frame[covariate] - frame[covariate].mean()
    )
    return adjusted, theta


def build_power_curve(
    frame: pd.DataFrame,
    outcome: str = "post_orders",
    covariate: str = "pre_orders",
    alpha: float = 0.05,
    power: float = 0.80,
) -> pd.DataFrame:
    """Compare raw and CUPED MDEs across practical total sample sizes."""

    adjusted, _ = cuped_outcome(frame, outcome, covariate)
    raw_std = float(frame[outcome].std(ddof=1))
    adjusted_std = float(adjusted.std(ddof=1))
    maximum = max(10_000, len(frame))
    sample_sizes = np.unique(
        np.linspace(5_000, maximum, num=12, dtype=int)
    )
    rows: list[dict[str, float | int | str]] = []
    for total_sample in sample_sizes:
        n_control = total_sample // 2
        n_treatment = total_sample - n_control
        for method, standard_deviation in [
            ("Unadjusted", raw_std),
            ("CUPED", adjusted_std),
        ]:
            rows.append(
                {
                    "total_sample_size": int(total_sample),
                    "method": method,
                    "minimum_detectable_order_effect": minimum_detectable_effect(
                        standard_deviation,
                        n_control,
                        n_treatment,
                        alpha,
                        power,
                    ),
                }
            )
    return pd.DataFrame(rows)
