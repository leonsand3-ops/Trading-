from pathlib import Path

import pytest
from typer.testing import CliRunner

from swing import __version__
from swing.cli import app


def test_version_command_prints_version() -> None:
    result = CliRunner().invoke(app, ["version"])
    assert result.exit_code == 0
    assert result.stdout.strip() == __version__


def _write_csv(directory: Path, symbol: str, closes: list[float]) -> None:
    lines = ["date,open,high,low,close,volume"]
    for i, c in enumerate(closes):
        lines.append(f"2024-01-{i + 2:02d},{c},{c + 1},{c - 1},{c},1000")
    (directory / f"{symbol}.csv").write_text("\n".join(lines) + "\n")


def test_data_update_check_and_show(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SWING_DATA_DIR", str(tmp_path / "lake"))
    csv_dir = tmp_path / "csv"
    csv_dir.mkdir()
    _write_csv(csv_dir, "AAA", [10.0, 11.0, 12.0, 13.0])  # Jan 2-5 2024
    runner = CliRunner()

    update = runner.invoke(
        app,
        [
            "data",
            "update",
            "--source",
            "csv",
            "--csv-dir",
            str(csv_dir),
            "--symbols",
            "AAA,BBB",
            "--start",
            "2024-01-01",
            "--end",
            "2024-01-31",
        ],
    )
    assert update.exit_code == 0, update.output
    assert "Sparade 4 rader för 1 symboler" in update.stdout
    assert "MISSLYCKADES BBB" in update.output

    check = runner.invoke(app, ["data", "check"])
    assert check.exit_code == 0, check.output
    assert "Inga problem" in check.stdout

    show = runner.invoke(app, ["data", "show", "AAA", "--as-of", "2024-01-03"])
    assert show.exit_code == 0, show.output
    assert "2024-01-03" in show.stdout
    assert "2024-01-04" not in show.stdout
