"""Smoke test for the alert-governance notebook."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

NOTEBOOK_PATH = (
    Path(__file__).resolve().parents[1]
    / "notebooks"
    / "03_alert_governance"
    / "alert_governance_memo.ipynb"
)
MODULE_07_README = (
    Path(__file__).resolve().parents[1]
    / "notebooks"
    / "07_interpretability_model_risk"
    / "README.md"
)


def test_alert_governance_notebook_executes(tmp_path: Path) -> None:
    """The governance notebook must execute end-to-end on tiny generated data."""
    repo_root = Path(__file__).resolve().parents[1]
    output_name = "alert_governance_memo.executed.ipynb"

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


def test_alert_governance_notebook_reflects_v07_depth() -> None:
    """The notebook must reference v0.5/v0.6/v0.7 layers (issue #188 AC)."""
    text = NOTEBOOK_PATH.read_text(encoding="utf-8")
    # v0.5 case layer.
    assert "case narrative" in text.lower() or "v0.5" in text.lower()
    # v0.6 graph layer — both graph-native pattern ids must be referenced.
    assert "mule_ring" in text
    assert "circular_funds_movement" in text
    # v0.7 model-risk templates.
    assert "07_interpretability_model_risk" in text


def test_alert_governance_notebook_bidirectionally_links_07_module() -> None:
    """Cross-references between 03 and the 07 module must be bidirectional (AC).

    Outbound: this notebook points to the 07 module; inbound: the 07 module README
    points back to 03_alert_governance.
    """
    text = NOTEBOOK_PATH.read_text(encoding="utf-8")
    # Outbound: 03 points to the 07 module.
    assert "notebooks/07_interpretability_model_risk/" in text
    # The notebook stays the first governance bridge (depth added, not replaced).
    assert "first governance bridge" in text.lower()
    # Inbound (reciprocal): the 07 module README references 03_alert_governance.
    readme_07 = MODULE_07_README.read_text(encoding="utf-8")
    assert "03_alert_governance" in readme_07


def test_alert_governance_notebook_keeps_limitation_framing() -> None:
    """The notebook must keep the limitation-aware framing visible."""
    text = NOTEBOOK_PATH.read_text(encoding="utf-8")
    assert "headline accuracy" in text.lower()
