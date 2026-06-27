"""Smoke tests for the v0.9 capstone synthesis notebook (issue #228).

Mirrors the v0.8 synthesis-notebook smoke-test convention: the notebook
executes end-to-end via nbconvert on the seed-42 capstone dataset, and contract
assertions verify the reused v0.6 graph layer, v0.8 monitoring builders, v0.7
governance surface, the glossary, and the limitation-aware framing.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SYNTHESIS_NOTEBOOK = ROOT / "notebooks" / "09_capstone" / "capstone_synthesis.ipynb"


def _execute(notebook_path: Path, tmp_path: Path, output_name: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "jupyter",
            "nbconvert",
            "--execute",
            "--to",
            "notebook",
            "--ExecutePreprocessor.timeout=300",
            "--output-dir",
            str(tmp_path),
            "--output",
            output_name,
            str(notebook_path),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=420,
        check=False,
    )


def test_capstone_synthesis_notebook_executes(tmp_path: Path) -> None:
    """The capstone synthesis notebook runs end-to-end on capstone tiny data."""
    output_name = "capstone_synthesis.executed.ipynb"
    result = _execute(SYNTHESIS_NOTEBOOK, tmp_path, output_name)
    assert result.returncode == 0, result.stdout + result.stderr
    assert (tmp_path / output_name).exists()


def test_capstone_synthesis_reuses_graph_and_capstone_surface() -> None:
    """The synthesis notebook reuses the v0.6 graph layer and capstone generators."""
    text = SYNTHESIS_NOTEBOOK.read_text(encoding="utf-8")
    for symbol in (
        "build_banking_graph",
        "build_all_graph_features",
        "join_graph_features_to_view",
        "generate_capstone_private_banking_world",
        "generate_capstone_digital_banking_world",
        "circular_funds_movement",
        "mule_ring",
    ):
        assert symbol in text, f"capstone synthesis notebook missing {symbol}"


def test_capstone_synthesis_reuses_v08_monitoring_surface() -> None:
    """The synthesis notebook reuses the v0.8 monitoring builders."""
    text = SYNTHESIS_NOTEBOOK.read_text(encoding="utf-8")
    for symbol in (
        "run_batch_scoring",
        "decide_alerts",
        "record_reviewer_action",
        "inspect_alert_queue",
        "check_score_drift",
        "summarise_alert_operations",
    ):
        assert symbol in text, f"capstone synthesis notebook missing {symbol}"


def test_capstone_synthesis_reuses_v07_governance_surface() -> None:
    """The synthesis notebook reuses the v0.7 governance template and renders a memo."""
    text = SYNTHESIS_NOTEBOOK.read_text(encoding="utf-8")
    for symbol in (
        "build_model_documentation",
        "build_monitoring_checklist",
        "recommend_lowest_cost_threshold",
        "evaluate_alert_scores",
        "Alert lifecycle",
        "governance memo",
    ):
        assert symbol in text, f"capstone synthesis notebook missing {symbol}"


def test_capstone_synthesis_uses_glossary_and_keeps_limits() -> None:
    """The synthesis notebook keeps the glossary and the limitation-aware framing."""
    text = SYNTHESIS_NOTEBOOK.read_text(encoding="utf-8")
    assert "Alpine Crest Private Bank" in text
    assert "NovaBank Digital" in text
    assert "should not be judged by headline accuracy" in text
    assert "investigative support" in text.lower()
    for banned in ("published", "is certified", "production-ready", "customer"):
        assert banned not in text.lower(), f"notebook contains banned {banned!r}"
