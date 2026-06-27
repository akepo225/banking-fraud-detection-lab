"""Smoke and contract tests for the alert-review governance notebook (v0.8 #209)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

NOTEBOOK_PATH = (
    Path(__file__).resolve().parents[1]
    / "notebooks"
    / "08_production_monitoring_patterns"
    / "alert_review_governance.ipynb"
)


def test_alert_review_governance_notebook_executes(tmp_path: Path) -> None:
    """The alert-review governance notebook must execute on tiny data."""
    repo_root = Path(__file__).resolve().parents[1]
    output_name = "alert_review_governance.executed.ipynb"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "jupyter",
            "nbconvert",
            "--execute",
            "--to",
            "notebook",
            "--ExecutePreprocessor.timeout=240",
            "--output-dir",
            str(tmp_path),
            "--output",
            output_name,
            str(NOTEBOOK_PATH),
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert (tmp_path / output_name).exists()


def test_alert_review_governance_notebook_runs_both_tracks() -> None:
    """The notebook must run BOTH tracks' monitoring flow side by side."""
    notebook_text = NOTEBOOK_PATH.read_text(encoding="utf-8")

    # Both tracks' data + feature builders consumed.
    assert "generate_private_banking_transaction_fraud_world" in notebook_text
    assert "generate_digital_fraud_scenarios_world" in notebook_text
    assert "build_private_banking_features" in notebook_text
    assert "build_digital_banking_features" in notebook_text

    # Both detection patterns in scope.
    assert "pb_high_value_movement" in notebook_text
    assert "digital_scam_to_mule" in notebook_text

    # Core v0.8 monitoring builders reused for both tracks.
    assert "run_batch_scoring" in notebook_text
    assert "decide_alerts" in notebook_text
    assert "summarise_alert_operations" in notebook_text
    assert "check_score_drift" in notebook_text


def test_alert_review_governance_notebook_runs_alert_review_exercise() -> None:
    """The notebook must reuse a v0.7 explanation as reviewer-action evidence."""
    notebook_text = NOTEBOOK_PATH.read_text(encoding="utf-8")

    # v0.7 explanation reused as reviewer-action evidence.
    assert "explain_feature_family" in notebook_text
    assert "PB_HIGH_VALUE_EXPLANATION" in notebook_text
    assert "record_reviewer_action" in notebook_text

    # Lineage walk back through the monitoring chain.
    assert "alert_decision_id" in notebook_text
    assert "score_id" in notebook_text
    assert "banking_relationship_id" in notebook_text


def test_alert_review_governance_notebook_produces_governance_summary() -> None:
    """The notebook must tie monitoring back to the v0.7 governance framing."""
    notebook_text = NOTEBOOK_PATH.read_text(encoding="utf-8")

    # v0.7 governance framing reused.
    assert "build_model_documentation" in notebook_text
    assert "build_monitoring_checklist" in notebook_text

    # Alert lifecycle tie-back.
    assert "Alert lifecycle" in notebook_text

    # Governance-language guardrail cell present.
    assert "should not be judged by headline accuracy" in notebook_text


def test_alert_review_governance_notebook_uses_glossary() -> None:
    """The notebook must name both institutions and avoid public-release language."""
    notebook_text = NOTEBOOK_PATH.read_text(encoding="utf-8")
    assert "Alpine Crest Private Bank" in notebook_text
    assert "NovaBank Digital" in notebook_text
    # No public-release / production-readiness / certification claims.
    assert "is certified" not in notebook_text.lower()
    assert "production-ready" not in notebook_text.lower()
    assert "published" not in notebook_text.lower()
