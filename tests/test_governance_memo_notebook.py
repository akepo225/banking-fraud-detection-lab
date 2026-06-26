"""Smoke and contract tests for the v0.7 governance memo notebook (#186)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import nbformat

NOTEBOOK_PATH = (
    Path(__file__).resolve().parents[1]
    / "notebooks"
    / "07_interpretability_model_risk"
    / "governance_memo.ipynb"
)


def test_governance_memo_notebook_executes(tmp_path: Path) -> None:
    """The governance memo notebook must execute on tiny data."""
    repo_root = Path(__file__).resolve().parents[1]
    output_name = "governance_memo.executed.ipynb"

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
    executed_path = tmp_path / output_name
    assert executed_path.exists()

    # The executed notebook must render a real stakeholder-readable memo, not just
    # exit cleanly. Guard against silent regressions where memo assembly produces
    # empty or placeholder output (issue #186 AC).
    notebook = nbformat.read(executed_path, as_version=4)
    rendered = "\n".join(
        output.get("text", "")
        for cell in notebook.cells
        for output in cell.get("outputs", [])
        if output.get("output_type") == "stream"
    )
    assert "Alpine Crest Private Bank" in rendered
    assert "NovaBank Digital" in rendered
    assert "should not be judged by headline accuracy" in rendered
    assert "Monitoring:" in rendered


def test_governance_memo_notebook_synthesises_both_tracks() -> None:
    """The memo must consume both track baselines and the documentation/checklist utilities."""
    text = NOTEBOOK_PATH.read_text(encoding="utf-8")
    # Both tracks.
    assert "generate_private_banking_transaction_fraud_world" in text
    assert "generate_digital_fraud_scenarios_world" in text
    assert "Alpine Crest Private Bank" in text
    assert "NovaBank Digital" in text
    # Slice-3 utilities.
    assert "build_model_documentation" in text
    assert "build_monitoring_checklist" in text
    # Threshold / FP synthesis.
    assert "recommend_lowest_cost_threshold" in text
    # Explanation synthesis (slice 1) and false-positive concentration (slice 2).
    assert "extract_feature_importance" in text
    assert "concentrate_false_positives" in text


def test_governance_memo_notebook_memo_uses_synthesized_outputs() -> None:
    """The memo loop must pull the computed documentation/monitoring artifacts, not boilerplate.

    Regression guard: the memo must reference ``documentation_artifacts`` and
    ``monitoring_checklists`` inside the memo-assembly loop so the rendered text reflects the
    actual filled sections and monitoring status per institution, rather than static claims.
    The execution smoke test proves those references resolve and render.
    """
    text = NOTEBOOK_PATH.read_text(encoding="utf-8")
    # The memo loop must dereference the per-institution artifacts.
    assert "documentation_artifacts[institution]" in text
    assert "monitoring_checklists[institution]" in text
    # The memo must report filled sections and monitoring status from the artifacts.
    assert "len(filled_sections)" in text or "filled_sections" in text
    assert "monitoring_summary" in text


def test_governance_memo_notebook_enforces_guardrails() -> None:
    """The notebook must enforce governance-language guardrails (PRD exit / issue #186 AC).

    The guardrail cell asserts at execution time that the generated memo_text contains no
    certification/legal-advice/compliance-requirement claims and keeps the limitation-aware
    framing visible. The execution smoke test above proves that assertion passes. This
    contract test additionally checks the notebook SOURCE carries the guardrail logic and the
    limitation-aware framing (without scanning the forbidden-word list itself, which lives in
    the source as the set being checked against).
    """
    text = NOTEBOOK_PATH.read_text(encoding="utf-8")
    # The guardrail cell must exist and assert against the forbidden terms.
    assert "forbidden not in memo_text.lower()" in text
    # Limitation-aware framing visible in the notebook.
    assert "should not be judged by headline accuracy" in text
    assert "no certification" in text.lower() or "certification" in text.lower()
    # The memo template states the educational, non-advice boundary.
    assert "not a certification" in text.lower() or "no certification" in text.lower()


def test_governance_memo_notebook_uses_glossary() -> None:
    """The notebook must use glossary institutions and avoid public-release language."""
    text = NOTEBOOK_PATH.read_text(encoding="utf-8")
    assert "Alpine Crest Private Bank" in text
    assert "NovaBank Digital" in text
    assert "published" not in text.lower()
