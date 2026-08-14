from marketing_incrementality.pipeline import run_pipeline


def test_pipeline_writes_auditable_outputs(tmp_path) -> None:
    metrics = run_pipeline(tmp_path, n_customers=1_000, seed=5)
    assert metrics["run"]["data_is_synthetic"] is True
    assert (tmp_path / "reports" / "metrics.json").exists()
    assert (tmp_path / "reports" / "effect_estimates.csv").exists()
    assert (tmp_path / "reports" / "campaign_economics.csv").exists()
    assert (tmp_path / "reports" / "economic_break_even.csv").exists()
    assert (tmp_path / "reports" / "decision_note.md").exists()
    assert (tmp_path / "reports" / "figures" / "effect_estimates.png").exists()
    assert (tmp_path / "reports" / "figures" / "economic_break_even.png").exists()
    assert metrics["economics"][0]["recommendation"] in {
        "Scale",
        "Redesign",
        "Stop",
    }
