"""Smoke tests for the v0.9 capstone scoring notebooks (issue #227).

Mirrors the v0.6–v0.8 notebook smoke-test convention: each notebook executes
end-to-end via nbconvert on the seed-42 capstone dataset, and contract
assertions verify the reused v0.3–v0.7 surface, the glossary, and the
limitation-aware framing.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ALPINE_CREST_NOTEBOOK = ROOT / "notebooks" / "09_capstone" / "alpine_crest_capstone_scoring.ipynb"
NOVABANK_NOTEBOOK = ROOT / "notebooks" / "09_capstone" / "novabank_capstone_scoring.ipynb"


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
            "--ExecutePreprocessor.timeout=180",
            "--output-dir",
            str(tmp_path),
            "--output",
            output_name,
            str(notebook_path),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )


def test_alpine_crest_capstone_notebook_executes(tmp_path: Path) -> None:
    """The Alpine Crest capstone notebook runs end-to-end on capstone tiny data."""
    output_name = "alpine_crest_capstone_scoring.executed.ipynb"
    result = _execute(ALPINE_CREST_NOTEBOOK, tmp_path, output_name)
    assert result.returncode == 0, result.stdout + result.stderr
    assert (tmp_path / output_name).exists()


def test_novabank_capstone_notebook_executes(tmp_path: Path) -> None:
    """The NovaBank capstone notebook runs end-to-end on capstone tiny data."""
    output_name = "novabank_capstone_scoring.executed.ipynb"
    result = _execute(NOVABANK_NOTEBOOK, tmp_path, output_name)
    assert result.returncode == 0, result.stdout + result.stderr
    assert (tmp_path / output_name).exists()


def test_alpine_crest_capstone_notebook_reuses_v03_v07_surface() -> None:
    """The Alpine Crest notebook reuses the feature library, evaluation, threshold, explain."""
    text = ALPINE_CREST_NOTEBOOK.read_text(encoding="utf-8")
    for symbol in (
        "generate_capstone_private_banking_world",
        "build_private_banking_features",
        "evaluate_alert_scores",
        "recommend_lowest_cost_threshold",
        "extract_feature_importance",
        "concentrate_false_positives",
        "PRIVATE_BANKING_FEATURE_FAMILIES",
        "pb_high_value_movement",
        "pb_transaction_fraud",
    ):
        assert symbol in text, f"Alpine Crest capstone notebook missing {symbol}"


def test_novabank_capstone_notebook_reuses_v04_v07_surface() -> None:
    """The NovaBank notebook reuses the feature library, evaluation, threshold, explain."""
    text = NOVABANK_NOTEBOOK.read_text(encoding="utf-8")
    for symbol in (
        "generate_capstone_digital_banking_world",
        "build_digital_banking_features",
        "evaluate_alert_scores",
        "recommend_lowest_cost_threshold",
        "extract_feature_importance",
        "concentrate_false_positives",
        "DIGITAL_BANKING_FEATURE_FAMILIES",
        "digital_scam_to_mule",
        "new_beneficiary_payment",
    ):
        assert symbol in text, f"NovaBank capstone notebook missing {symbol}"


def test_capstone_notebooks_avoid_headline_accuracy_and_keep_glossary() -> None:
    """Both notebooks keep the limitation-aware framing and the fixed glossary."""
    for notebook_path, institution in (
        (ALPINE_CREST_NOTEBOOK, "Alpine Crest Private Bank"),
        (NOVABANK_NOTEBOOK, "NovaBank Digital"),
    ):
        text = notebook_path.read_text(encoding="utf-8")
        assert "should not be judged by headline accuracy" in text
        assert "accuracy is out of scope" in text
        assert institution in text
        assert "Banking relationship" in text or "Client" in text
        for banned in ("published", "is certified", "production-ready", "customer"):
            assert banned not in text.lower(), f"{notebook_path.name} contains banned {banned!r}"
