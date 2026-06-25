"""Smoke test for the NovaBank Digital graph-investigation notebook."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_novabank_graph_notebook_executes(tmp_path: Path) -> None:
    """The NovaBank Digital graph-investigation notebook must execute on tiny data."""
    repo_root = Path(__file__).resolve().parents[1]
    notebook_path = (
        repo_root
        / "notebooks"
        / "06_graph_network_fraud"
        / "novabank_graph_investigation.ipynb"
    )
    output_name = "novabank_graph_investigation.executed.ipynb"
    output_path = tmp_path / output_name

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
            "--output",
            output_name,
            "--output-dir",
            str(tmp_path),
            str(notebook_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"Notebook execution failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )
    assert output_path.exists(), f"Expected executed notebook at {output_path}"
