import pandas as pd

from marketing_incrementality.diagnostics import balance_table, sample_ratio_check


def test_sample_ratio_check_detects_large_mismatch() -> None:
    frame = pd.DataFrame({"treatment": [0] * 100 + [1] * 900})
    result = sample_ratio_check(frame)
    assert result["passed"] is False
    assert result["p_value"] < 0.001


def test_balance_table_flags_material_difference() -> None:
    frame = pd.DataFrame(
        {
            "treatment": [0] * 10 + [1] * 10,
            "pre_orders": [0.0] * 10 + [5.0] * 10,
            "segment": ["A"] * 20,
        }
    )
    result = balance_table(frame, ["pre_orders"])
    pre_orders = result.set_index("covariate").loc["pre_orders"]
    assert not bool(pre_orders["passed"])
