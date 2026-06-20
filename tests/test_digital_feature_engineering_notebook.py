"""Smoke test for the NovaBank Digital feature-engineering notebook."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_digital_feature_engineering_notebook_executes(tmp_path: Path) -> None:
    """The NovaBank Digital feature notebook must execute on tiny generated data."""
    repo_root = Path(__file__).resolve().parents[1]
    notebook_path = (
        repo_root
        / "notebooks"
        / "05_digital_session_and_payment_fraud"
        / "novabank_feature_engineering.ipynb"
    )
    output_name = "novabank_feature_engineering.executed.ipynb"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "jupyter",
            "nbconvert",
            "--execute",
            "--to",
            "notebook",
            "--ExecutePreprocessor.timeout=120",
            "--output-dir",
            str(tmp_path),
            "--output",
            output_name,
            str(notebook_path),
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert (tmp_path / output_name).exists()
