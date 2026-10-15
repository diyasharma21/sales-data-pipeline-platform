"""Integration tests for the Main CLI Pipeline Orchestrator (main.py)."""

from pathlib import Path
import pytest
from sqlalchemy import Engine

from main import run_pipeline


def test_run_pipeline_success_end_to_end(
    valid_csv_file: Path,
    tmp_path: Path,
) -> None:
    """Test full end-to-end execution of run_pipeline returning exit code 0."""
    db_file = tmp_path / "test_main_db.db"
    db_url = f"sqlite:///{db_file.as_posix()}"

    exit_code = run_pipeline(
        input_file=valid_csv_file,
        db_url=db_url,
        export_csv=True,
    )

    assert exit_code == 0
    assert db_file.exists()


def test_run_pipeline_missing_file_failure(tmp_path: Path) -> None:
    """Test run_pipeline returns non-zero exit code 1 when input file is missing."""
    fake_file = tmp_path / "does_not_exist.csv"
    db_file = tmp_path / "test_fail_db.db"
    db_url = f"sqlite:///{db_file.as_posix()}"

    exit_code = run_pipeline(
        input_file=fake_file,
        db_url=db_url,
        export_csv=False,
    )

    assert exit_code == 1
