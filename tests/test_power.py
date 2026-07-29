from marketing_incrementality.power import minimum_detectable_effect


def test_mde_decreases_with_larger_sample() -> None:
    small = minimum_detectable_effect(1.0, 2_500, 2_500)
    large = minimum_detectable_effect(1.0, 10_000, 10_000)
    assert large < small
