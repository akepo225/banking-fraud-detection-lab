"""Smoke test for the NovaBank Digital supervised-baseline notebook."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_digital_supervised_baseline_notebook_executes(tmp_path: Path) -> None:
    """The NovaBank Digital supervised baseline notebook must execute on small data."""
    repo_root = Path(__file__).resolve().parents[1]
    notebook_path = (
        repo_root
        / "notebooks"
        / "05_digital_session_and_payment_fraud"
        / "novabank_supervised_baseline.ipynb"
    )
    output_name = "novabank_supervised_baseline.executed.ipynb"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "jupyter",
            "nbconvert",
            "--execute",
            "--to",
            "notebook",
            "--ExecutePreprocessor.timeout=180",
            "--output-dir",
            str(tmp_path),
            "--output",
            output_name,
            str(notebook_path),
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=240,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert (tmp_path / output_name).exists()
