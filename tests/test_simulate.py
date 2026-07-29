from pandas.testing import assert_frame_equal

from marketing_incrementality.config import SimulationConfig
from marketing_incrementality.simulate import simulate_experiment


def test_simulation_is_reproducible_and_valid() -> None:
    config = SimulationConfig(n_customers=500, seed=8)
    first, first_truth = simulate_experiment(config)
    second, second_truth = simulate_experiment(config)
    assert_frame_equal(first, second)
    assert first_truth == second_truth
    assert set(first["treatment"].unique()) == {0, 1}
    assert (first[["pre_orders", "post_orders"]] >= 0).all().all()
    assert (first.loc[first["post_orders"] == 0, "post_revenue"] == 0).all()
    assert first["customer_id"].is_unique
