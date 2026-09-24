import sys

from marketing_incrementality.cli import main


def test_run_command_executes_pipeline_outside_default_path(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    output = tmp_path / "run"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "incrementality-case",
            "run",
            "--customers",
            "500",
            "--seed",
            "4",
            "--project-root",
            str(output),
        ],
    )
    main()
    assert "Economic decision:" in capsys.readouterr().out
    assert (output / "reports" / "metrics.json").exists()


def test_stability_command_writes_requested_table(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    output = tmp_path / "stability.csv"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "incrementality-case",
            "stability",
            "--customers",
            "500",
            "--seeds",
            "2",
            "--output",
            str(output),
        ],
    )
    main()
    assert "Decision counts:" in capsys.readouterr().out
    assert output.exists()
