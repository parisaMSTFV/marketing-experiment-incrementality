from __future__ import annotations

import math

import numpy as np
import pandas as pd
from scipy import stats


def difference_in_means(
    frame: pd.DataFrame,
    outcome: str,
    alpha: float = 0.05,
) -> dict[str, float | int | str]:
    """Estimate an intent-to-treat difference with an unpooled standard error."""

    if not 0 < alpha < 1:
        raise ValueError("alpha must be between zero and one")
    if outcome not in frame or "treatment" not in frame:
        raise ValueError("frame must contain treatment and the requested outcome")
    if frame[["treatment", outcome]].isna().any().any():
        raise ValueError("treatment and outcome values must be complete")
    if not set(frame["treatment"].unique()).issubset({0, 1}):
        raise ValueError("treatment must contain only zero and one")

    treatment = frame.loc[frame["treatment"] == 1, outcome].astype(float)
    control = frame.loc[frame["treatment"] == 0, outcome].astype(float)
    if len(treatment) < 2 or len(control) < 2:
        raise ValueError("both treatment groups must contain at least two rows")
    effect = float(treatment.mean() - control.mean())
    standard_error = float(
        np.sqrt(
            treatment.var(ddof=1) / len(treatment)
            + control.var(ddof=1) / len(control)
        )
    )
    critical_value = float(stats.norm.ppf(1 - alpha / 2))
    z_score = effect / standard_error if standard_error > 0 else 0.0
    p_value = float(2 * stats.norm.sf(abs(z_score)))
    control_mean = float(control.mean())
    relative_lift = effect / control_mean if control_mean != 0 else math.nan
    return {
        "outcome": outcome,
        "method": "Unadjusted difference in means",
        "n_control": int(len(control)),
        "n_treatment": int(len(treatment)),
        "control_mean": control_mean,
        "treatment_mean": float(treatment.mean()),
        "absolute_effect": effect,
        "relative_lift": float(relative_lift),
        "standard_error": standard_error,
        "ci_lower": effect - critical_value * standard_error,
        "ci_upper": effect + critical_value * standard_error,
        "p_value": p_value,
    }


def cuped_estimate(
    frame: pd.DataFrame,
    outcome: str,
    covariate: str,
    alpha: float = 0.05,
) -> dict[str, float | int | str]:
    """Apply CUPED using a pre-treatment covariate and a control-fitted theta."""

    if covariate not in frame:
        raise ValueError("frame must contain the requested CUPED covariate")
    if frame[covariate].isna().any():
        raise ValueError("the CUPED covariate must be complete")

    adjusted = frame.copy()
    control = adjusted.loc[adjusted["treatment"] == 0, [outcome, covariate]].astype(
        float
    )
    covariate_variance = float(control[covariate].var(ddof=1))
    theta = (
        float(control[[outcome, covariate]].cov().iloc[0, 1]) / covariate_variance
        if covariate_variance > 0
        else 0.0
    )
    covariate_mean = float(adjusted[covariate].mean())
    adjusted_outcome = f"{outcome}_cuped"
    adjusted[adjusted_outcome] = adjusted[outcome] - theta * (
        adjusted[covariate] - covariate_mean
    )

    raw = difference_in_means(frame, outcome, alpha)
    result = difference_in_means(adjusted, adjusted_outcome, alpha)
    raw_variance = float(raw["standard_error"]) ** 2
    adjusted_variance = float(result["standard_error"]) ** 2
    variance_reduction = (
        1 - adjusted_variance / raw_variance if raw_variance > 0 else 0.0
    )
    sample_multiplier = (
        raw_variance / adjusted_variance if adjusted_variance > 0 else 1.0
    )
    result.update(
        {
            "outcome": outcome,
            "method": "CUPED",
            "covariate": covariate,
            "theta": theta,
            "variance_reduction": variance_reduction,
            "effective_sample_multiplier": sample_multiplier,
            "raw_standard_error": float(raw["standard_error"]),
        }
    )
    return result


def holm_adjust(p_values: list[float]) -> list[float]:
    """Return Holm-adjusted p-values while preserving input order."""

    if not p_values:
        return []
    values = np.asarray(p_values, dtype=float)
    order = np.argsort(values)
    adjusted_sorted = np.empty(len(values), dtype=float)
    running_max = 0.0
    for rank, index in enumerate(order):
        candidate = (len(values) - rank) * values[index]
        running_max = max(running_max, candidate)
        adjusted_sorted[rank] = min(running_max, 1.0)
    adjusted = np.empty(len(values), dtype=float)
    adjusted[order] = adjusted_sorted
    return adjusted.tolist()


def estimate_segment_effects(
    frame: pd.DataFrame,
    outcome: str = "post_orders",
    covariate: str = "pre_orders",
    alpha: float = 0.05,
) -> pd.DataFrame:
    """Estimate pre-specified segment effects and adjust for multiple testing."""

    rows: list[dict[str, object]] = []
    for segment, segment_frame in frame.groupby("segment", sort=True):
        estimate = cuped_estimate(segment_frame, outcome, covariate, alpha)
        rows.append({"segment": segment, **estimate})
    result = pd.DataFrame(rows)
    result["adjusted_p_value"] = holm_adjust(result["p_value"].tolist())
    result["significant_after_holm"] = result["adjusted_p_value"] < alpha
    return result.sort_values("segment").reset_index(drop=True)
