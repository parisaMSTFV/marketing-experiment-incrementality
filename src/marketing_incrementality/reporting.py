from __future__ import annotations

from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

COLORS = {
    "navy": "#17324D",
    "blue": "#2F6690",
    "orange": "#F28E2B",
    "green": "#4E8B57",
    "red": "#C44E52",
    "gray": "#9AA5B1",
}


def _save(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def plot_before_after_vs_experiment(frame: pd.DataFrame, path: Path) -> None:
    treatment = frame.loc[frame["treatment"] == 1]
    control = frame.loc[frame["treatment"] == 0]
    treatment_change = treatment["post_orders"].mean() - treatment["pre_orders"].mean()
    control_change = control["post_orders"].mean() - control["pre_orders"].mean()
    randomized_effect = (
        treatment["post_orders"].mean() - control["post_orders"].mean()
    )
    values = [treatment_change, control_change, randomized_effect]
    labels = [
        "Treated\nbefore-after",
        "Control\nbefore-after",
        "Randomized\nestimate",
    ]
    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    bars = ax.bar(
        labels,
        values,
        color=[COLORS["gray"], COLORS["blue"], COLORS["orange"]],
    )
    ax.axhline(0, color=COLORS["navy"], linewidth=0.8)
    ax.set_ylabel("Change in orders per customer")
    ax.set_title("Market growth makes before-after attribution misleading")
    ax.spines[["top", "right"]].set_visible(False)
    for bar, value in zip(bars, values, strict=True):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value,
            f"{value:.3f}",
            ha="center",
            va="bottom",
        )
    _save(fig, path)


def plot_effect_estimates(estimates: pd.DataFrame, path: Path) -> None:
    frame = estimates.loc[estimates["outcome"] == "post_orders"].copy()
    labels = frame["method"].replace(
        {"Unadjusted difference in means": "Unadjusted"}
    )
    positions = np.arange(len(frame))
    effects = frame["absolute_effect"].to_numpy()
    lower = effects - frame["ci_lower"].to_numpy()
    upper = frame["ci_upper"].to_numpy() - effects
    fig, ax = plt.subplots(figsize=(7.0, 4.5))
    ax.errorbar(
        positions,
        effects,
        yerr=np.vstack([lower, upper]),
        fmt="o",
        color=COLORS["orange"],
        ecolor=COLORS["navy"],
        capsize=5,
        markersize=8,
    )
    ax.axhline(0, color=COLORS["gray"], linestyle="--")
    ax.set_xticks(positions, labels)
    ax.set_ylabel("Incremental orders per customer")
    ax.set_title("Intent-to-treat effect with 95% confidence intervals")
    ax.spines[["top", "right"]].set_visible(False)
    _save(fig, path)


def plot_precision_comparison(estimates: pd.DataFrame, path: Path) -> None:
    frame = estimates.loc[estimates["outcome"] == "post_orders"].copy()
    labels = frame["method"].replace(
        {"Unadjusted difference in means": "Unadjusted"}
    )
    fig, ax = plt.subplots(figsize=(6.6, 4.5))
    bars = ax.bar(
        labels,
        frame["standard_error"],
        color=[COLORS["blue"], COLORS["orange"]],
    )
    ax.set_ylabel("Standard error")
    ax.set_title("CUPED uses pre-period behavior to improve precision")
    ax.spines[["top", "right"]].set_visible(False)
    for bar, value in zip(bars, frame["standard_error"], strict=True):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value,
            f"{value:.4f}",
            ha="center",
            va="bottom",
        )
    _save(fig, path)


def plot_segment_effects(segment_effects: pd.DataFrame, path: Path) -> None:
    frame = segment_effects.sort_values("absolute_effect").reset_index(drop=True)
    positions = np.arange(len(frame))
    effects = frame["absolute_effect"].to_numpy()
    lower = effects - frame["ci_lower"].to_numpy()
    upper = frame["ci_upper"].to_numpy() - effects
    colors = [
        COLORS["orange"] if significant else COLORS["blue"]
        for significant in frame["significant_after_holm"]
    ]
    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    ax.errorbar(
        effects,
        positions,
        xerr=np.vstack([lower, upper]),
        fmt="none",
        ecolor=COLORS["navy"],
        capsize=4,
    )
    ax.scatter(effects, positions, color=colors, s=65, zorder=3)
    ax.axvline(0, color=COLORS["gray"], linestyle="--")
    ax.set_yticks(positions, frame["segment"])
    ax.set_xlabel("Incremental orders per customer")
    ax.set_title("Pre-specified segment effects with 95% confidence intervals")
    ax.spines[["top", "right"]].set_visible(False)
    _save(fig, path)


def plot_segment_profitability(economics: pd.DataFrame, path: Path) -> None:
    frame = economics.loc[economics["audience"] != "All customers"].copy()
    frame = frame.sort_values("net_incremental_profit")
    colors = [
        COLORS["green"] if value > 0 else COLORS["red"]
        for value in frame["net_incremental_profit"]
    ]
    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    ax.barh(frame["audience"], frame["net_incremental_profit"], color=colors)
    ax.axvline(0, color=COLORS["navy"], linewidth=0.9)
    ax.set_xlabel("Estimated net incremental profit")
    ax.set_title("Positive response does not guarantee profitable targeting")
    ax.spines[["top", "right"]].set_visible(False)
    _save(fig, path)


def plot_power_curve(power_curve: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    for method, color in [("Unadjusted", COLORS["blue"]), ("CUPED", COLORS["orange"])]:
        subset = power_curve.loc[power_curve["method"] == method]
        ax.plot(
            subset["total_sample_size"],
            subset["minimum_detectable_order_effect"],
            marker="o",
            label=method,
            color=color,
        )
    ax.set_xlabel("Total experiment sample size")
    ax.set_ylabel("Minimum detectable orders per customer")
    ax.set_title("Larger samples and CUPED detect smaller effects")
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    _save(fig, path)
