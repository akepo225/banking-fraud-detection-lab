"""Smoke and contract tests for the NovaBank interpretability notebook (v0.7)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

NOTEBOOK_PATH = (
    Path(__file__).resolve().parents[1]
    / "notebooks"
    / "07_interpretability_model_risk"
    / "novabank_interpretability.ipynb"
)


def test_novabank_interpretability_notebook_executes(tmp_path: Path) -> None:
    """The NovaBank interpretability notebook must execute on small data."""
    repo_root = Path(__file__).resolve().parents[1]
    output_name = "novabank_interpretability.executed.ipynb"

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
            str(NOTEBOOK_PATH),
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=240,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert (tmp_path / output_name).exists()


def test_novabank_interpretability_notebook_uses_v07_contracts() -> None:
    """The notebook must consume the v0.7 explanation/threshold/doc contracts."""
    notebook_text = NOTEBOOK_PATH.read_text(encoding="utf-8")

    assert "extract_feature_importance" in notebook_text
    assert "build_partial_dependence_grid" in notebook_text
    assert "PATTERN_TO_EXPLANATION_FAMILY" in notebook_text
    assert "recommend_lowest_cost_threshold" in notebook_text
    assert "concentrate_false_positives" in notebook_text
    assert "build_model_documentation" in notebook_text

    # Digital Detection-pattern linkage.
    assert "digital_scam_to_mule" in notebook_text


def test_novabank_interpretability_notebook_compares_signal_types() -> None:
    """The notebook must compare rule/model/graph/case evidence (issue #185 AC)."""
    notebook_text = NOTEBOOK_PATH.read_text(encoding="utf-8")
    assert "Compare Rule, Model, Graph, And Case Evidence" in notebook_text
    assert "rule_triggered" in notebook_text
    assert "graph_pattern" in notebook_text
    assert "mule_ring" in notebook_text


def test_novabank_interpretability_notebook_keeps_limitations_visible() -> None:
    """The notebook must keep the 'not judged by headline accuracy' framing visible (PRD exit 2)."""
    notebook_text = NOTEBOOK_PATH.read_text(encoding="utf-8")
    assert "accuracy is out of scope" in notebook_text
    assert "should not be judged by headline accuracy" in notebook_text


def test_novabank_interpretability_notebook_uses_glossary() -> None:
    """The notebook must use the glossary institution and User/Client distinction."""
    notebook_text = NOTEBOOK_PATH.read_text(encoding="utf-8")
    assert "NovaBank Digital" in notebook_text
    assert "User" in notebook_text
    assert "Client" in notebook_text
    assert "published" not in notebook_text.lower()
