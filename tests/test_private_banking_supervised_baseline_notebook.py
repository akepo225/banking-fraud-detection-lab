"""Smoke and contract tests for the Alpine Crest supervised baseline notebook."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

NOTEBOOK_PATH = (
    Path(__file__).resolve().parents[1]
    / "notebooks"
    / "04_private_banking_feature_engineering"
    / "alpine_crest_supervised_baseline.ipynb"
)


def test_private_banking_supervised_baseline_notebook_executes(
    tmp_path: Path,
) -> None:
    """The supervised baseline notebook must execute on tiny generated data."""
    repo_root = Path(__file__).resolve().parents[1]
    output_name = "alpine_crest_supervised_baseline.executed.ipynb"

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
            str(NOTEBOOK_PATH),
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert (tmp_path / output_name).exists()


def test_private_banking_supervised_baseline_notebook_uses_evaluation_contract() -> None:
    """The notebook should use shared feature and evaluation contracts."""
    notebook_text = NOTEBOOK_PATH.read_text(encoding="utf-8")

    assert "build_private_banking_features" in notebook_text
    assert "PRIVATE_BANKING_FEATURE_FAMILIES" in notebook_text
    assert "PATTERN_IDS" in notebook_text
    assert "evaluate_alert_scores" in notebook_text
    assert "threshold_summaries" in notebook_text
    assert "cost_curve" in notebook_text
    assert "lowest_cost_threshold" in notebook_text
    assert "limitation_summary" in notebook_text
    assert "alert_capacity=2" in notebook_text
    assert "investigation_cost_chf" in notebook_text
    assert "false_positive_cost_chf" in notebook_text
    assert "missed_fraud_cost_chf" in notebook_text
    assert "PRIVATE_BANKING_FALSE_POSITIVE_TYPE" in notebook_text
    assert "PROTECTED_SCENARIO_ANSWER_KEYS not in learner_tables" in notebook_text
    assert "accuracy_score" not in notebook_text
