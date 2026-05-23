"""Smoke test for the Alpine Crest private-banking notebook."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_private_banking_notebook_executes(tmp_path: Path) -> None:
    """The private-banking baseline notebook must execute on tiny generated data."""
    repo_root = Path(__file__).resolve().parents[1]
    notebook_path = (
        repo_root
        / "notebooks"
        / "01_private_banking_transaction_fraud"
        / "alpine_crest_baseline.ipynb"
    )
    output_name = "alpine_crest_baseline.executed.ipynb"

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
