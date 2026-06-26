"""Smoke and contract tests for the Alpine Crest interpretability notebook (v0.7)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

NOTEBOOK_PATH = (
    Path(__file__).resolve().parents[1]
    / "notebooks"
    / "07_interpretability_model_risk"
    / "alpine_crest_interpretability.ipynb"
)


def test_alpine_crest_interpretability_notebook_executes(tmp_path: Path) -> None:
    """The Alpine Crest interpretability notebook must execute on tiny data."""
    repo_root = Path(__file__).resolve().parents[1]
    output_name = "alpine_crest_interpretability.executed.ipynb"

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


def test_alpine_crest_interpretability_notebook_uses_v07_contracts() -> None:
    """The notebook must consume the v0.7 explanation/threshold/doc contracts."""
    notebook_text = NOTEBOOK_PATH.read_text(encoding="utf-8")

    # Explanation utilities (slice 1).
    assert "extract_feature_importance" in notebook_text
    assert "build_partial_dependence_grid" in notebook_text
    assert "EXPLANATION_FAMILY_SPECS" in notebook_text or "PATTERN_TO_EXPLANATION_FAMILY" in notebook_text

    # Threshold / FP utilities (slice 2).
    assert "recommend_lowest_cost_threshold" in notebook_text
    assert "concentrate_false_positives" in notebook_text

    # Model-documentation template (slice 3).
    assert "build_model_documentation" in notebook_text

    # Detection-pattern linkage.
    assert "pb_high_value_movement" in notebook_text or "pb_transaction_fraud" in notebook_text


def test_alpine_crest_interpretability_notebook_keeps_limitations_visible() -> None:
    """The notebook must keep the 'not judged by headline accuracy' framing visible (PRD exit 2)."""
    notebook_text = NOTEBOOK_PATH.read_text(encoding="utf-8")
    assert "accuracy is out of scope" in notebook_text
    assert "should not be judged by headline accuracy" in notebook_text


def test_alpine_crest_interpretability_notebook_uses_glossary() -> None:
    """The notebook must use the glossary institution and avoid public-release language."""
    notebook_text = NOTEBOOK_PATH.read_text(encoding="utf-8")
    assert "Alpine Crest Private Bank" in notebook_text
    # No public-release / certification claims.
    assert "published" not in notebook_text.lower()
    assert "is certified" not in notebook_text.lower()
