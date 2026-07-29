from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


def sample_ratio_check(
    frame: pd.DataFrame,
    expected_treatment_share: float = 0.50,
    alpha: float = 0.05,
) -> dict[str, float | int | bool]:
    """Test whether observed assignment matches the planned allocation."""

    counts = frame["treatment"].value_counts().reindex([0, 1], fill_value=0)
    total = int(counts.sum())
    expected = np.array(
        [total * (1 - expected_treatment_share), total * expected_treatment_share]
    )
    statistic, p_value = stats.chisquare(counts.to_numpy(), f_exp=expected)
    return {
        "control_customers": int(counts.loc[0]),
        "treatment_customers": int(counts.loc[1]),
        "observed_treatment_share": float(counts.loc[1] / total),
        "chi_square": float(statistic),
        "p_value": float(p_value),
        "passed": bool(p_value >= alpha),
    }


def _standardized_mean_difference(
    treatment_values: pd.Series,
    control_values: pd.Series,
) -> float:
    pooled_variance = (
        treatment_values.var(ddof=1) + control_values.var(ddof=1)
    ) / 2
    if pooled_variance <= 0 or np.isnan(pooled_variance):
        return (
            0.0
            if treatment_values.mean() == control_values.mean()
            else float("inf")
        )
    return float(
        (treatment_values.mean() - control_values.mean())
        / np.sqrt(pooled_variance)
    )


def balance_table(
    frame: pd.DataFrame,
    numeric_columns: list[str],
    categorical_column: str = "segment",
    threshold: float = 0.10,
) -> pd.DataFrame:
    """Report pre-treatment balance using absolute standardized differences."""

    treatment = frame.loc[frame["treatment"] == 1]
    control = frame.loc[frame["treatment"] == 0]
    rows: list[dict[str, object]] = []
    for column in numeric_columns:
        smd = _standardized_mean_difference(treatment[column], control[column])
        rows.append(
            {
                "covariate": column,
                "control_mean": float(control[column].mean()),
                "treatment_mean": float(treatment[column].mean()),
                "standardized_mean_difference": smd,
                "absolute_smd": abs(smd),
                "passed": abs(smd) < threshold,
            }
        )

    levels = sorted(frame[categorical_column].unique())
    for level in levels:
        treatment_indicator = (treatment[categorical_column] == level).astype(float)
        control_indicator = (control[categorical_column] == level).astype(float)
        smd = _standardized_mean_difference(treatment_indicator, control_indicator)
        rows.append(
            {
                "covariate": f"{categorical_column}: {level}",
                "control_mean": float(control_indicator.mean()),
                "treatment_mean": float(treatment_indicator.mean()),
                "standardized_mean_difference": smd,
                "absolute_smd": abs(smd),
                "passed": abs(smd) < threshold,
            }
        )
    return pd.DataFrame(rows).sort_values("absolute_smd", ascending=False)
