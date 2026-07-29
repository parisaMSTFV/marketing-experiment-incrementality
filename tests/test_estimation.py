import numpy as np
import pandas as pd

from marketing_incrementality.estimation import cuped_estimate, holm_adjust


def test_cuped_reduces_standard_error_for_correlated_covariate() -> None:
    rng = np.random.default_rng(12)
    size = 8_000
    treatment = rng.binomial(1, 0.5, size)
    pre = rng.normal(4, 1.5, size)
    post = 0.9 * pre + 0.25 * treatment + rng.normal(0, 0.5, size)
    frame = pd.DataFrame(
        {"treatment": treatment, "pre_orders": pre, "post_orders": post}
    )
    result = cuped_estimate(frame, "post_orders", "pre_orders")
    assert result["standard_error"] < result["raw_standard_error"]
    assert abs(result["absolute_effect"] - 0.25) < 0.05


def test_holm_adjustment_preserves_order_and_monotonic_control() -> None:
    adjusted = holm_adjust([0.01, 0.04, 0.20])
    assert adjusted == [0.03, 0.08, 0.20]
