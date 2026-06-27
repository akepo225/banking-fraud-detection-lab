"""Smoke and contract tests for the NovaBank Digital production-monitoring notebook (v0.8)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

NOTEBOOK_PATH = (
    Path(__file__).resolve().parents[1]
    / "notebooks"
    / "08_production_monitoring_patterns"
    / "novabank_monitoring.ipynb"
)


def test_novabank_monitoring_notebook_executes(tmp_path: Path) -> None:
    """The NovaBank monitoring notebook must execute on tiny data."""
    repo_root = Path(__file__).resolve().parents[1]
    output_name = "novabank_monitoring.executed.ipynb"

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


def test_novabank_monitoring_notebook_uses_v08_contracts() -> None:
    """The notebook must consume the v0.8 monitoring builders."""
    notebook_text = NOTEBOOK_PATH.read_text(encoding="utf-8")

    # Batch scoring + alert decisions + reviewer/audit (slices 1, 2, 3).
    assert "run_batch_scoring" in notebook_text
    assert "decide_alerts" in notebook_text
    assert "record_reviewer_action" in notebook_text

    # Queue + operational metrics (slice 4).
    assert "inspect_alert_queue" in notebook_text
    assert "summarise_alert_operations" in notebook_text

    # Drift + data-quality (slice 5).
    assert "check_score_drift" in notebook_text
    assert "check_feature_drift" in notebook_text
    assert "check_monitoring_data_quality" in notebook_text

    # Detection-pattern linkage.
    assert "digital_scam_to_mule" in notebook_text


def test_novabank_monitoring_notebook_keeps_limitations_visible() -> None:
    """The notebook must keep the 'not judged by headline accuracy' framing visible."""
    notebook_text = NOTEBOOK_PATH.read_text(encoding="utf-8")
    assert "should not be judged by headline accuracy" in notebook_text


def test_novabank_monitoring_notebook_uses_glossary() -> None:
    """The notebook must use the glossary institution and avoid public-release language."""
    notebook_text = NOTEBOOK_PATH.read_text(encoding="utf-8")
    assert "NovaBank Digital" in notebook_text
    # No public-release / production-readiness / certification claims.
    assert "is certified" not in notebook_text.lower()
    assert "production-ready" not in notebook_text.lower()
    assert "published" not in notebook_text.lower()
