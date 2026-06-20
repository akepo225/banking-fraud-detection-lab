"""Smoke test for the NovaBank Digital feature-engineering notebook."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_NOTEBOOK_PATH = (
    Path(__file__).resolve().parents[1]
    / "notebooks"
    / "05_digital_session_and_payment_fraud"
    / "novabank_feature_engineering.ipynb"
)


def test_digital_feature_engineering_notebook_executes(tmp_path: Path) -> None:
    """The NovaBank Digital feature notebook must execute on tiny generated data."""
    repo_root = Path(__file__).resolve().parents[1]
    output_name = "novabank_feature_engineering.executed.ipynb"

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
            str(_NOTEBOOK_PATH),
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert (tmp_path / output_name).exists()


def test_digital_feature_engineering_notebook_exists_at_canonical_path() -> None:
    """The notebook must exist at the path declared in the README and CI test."""
    assert _NOTEBOOK_PATH.exists(), (
        f"Notebook not found at expected path: {_NOTEBOOK_PATH}"
    )
    assert _NOTEBOOK_PATH.suffix == ".ipynb"


def test_digital_feature_engineering_notebook_is_valid_json() -> None:
    """The notebook file must be parseable as valid JSON (nbformat contract)."""
    raw = _NOTEBOOK_PATH.read_text(encoding="utf-8")
    notebook = json.loads(raw)
    assert notebook.get("nbformat") == 4
    assert "cells" in notebook
    assert len(notebook["cells"]) > 0


def test_digital_feature_engineering_notebook_has_required_imports() -> None:
    """The notebook setup cell must import the required banking_fraud_lab symbols."""
    notebook = json.loads(_NOTEBOOK_PATH.read_text(encoding="utf-8"))
    all_source = "\n".join(
        "".join(cell["source"])
        for cell in notebook["cells"]
        if cell["cell_type"] == "code"
    )
    required_symbols = [
        "build_digital_banking_features",
        "build_foundation_progressive_views",
        "build_learner_facing_views",
        "generate_digital_fraud_scenarios_world",
        "load_tables_to_sqlite",
        "DIGITAL_BANKING_FEATURE_FAMILIES",
        "NB_USER_SESSION_CONTEXT",
        "PATTERN_IDS",
        "PROTECTED_SCENARIO_ANSWER_KEYS",
    ]
    for symbol in required_symbols:
        assert symbol in all_source, (
            f"Required symbol '{symbol}' not found in notebook code cells."
        )


def test_digital_feature_engineering_notebook_asserts_protected_key_exclusion() -> None:
    """The notebook must assert that PROTECTED_SCENARIO_ANSWER_KEYS is excluded.

    The learner-facing views must never expose the ground-truth fraud label.
    The notebook is required to validate this with an explicit assert.
    """
    notebook = json.loads(_NOTEBOOK_PATH.read_text(encoding="utf-8"))
    all_source = "\n".join(
        "".join(cell["source"])
        for cell in notebook["cells"]
        if cell["cell_type"] == "code"
    )
    # Both the positive check (key present in full tables) and the
    # negative check (key absent from learner tables) must be present.
    assert "PROTECTED_SCENARIO_ANSWER_KEYS" in all_source
    assert "not in learner_tables" in all_source or (
        "PROTECTED_SCENARIO_ANSWER_KEYS not in" in all_source
    )


def test_digital_feature_engineering_notebook_references_all_three_sql_exercises() -> None:
    """The notebook must reference all three digital SQL exercise files."""
    notebook = json.loads(_NOTEBOOK_PATH.read_text(encoding="utf-8"))
    all_source = "\n".join(
        "".join(cell["source"])
        for cell in notebook["cells"]
        if cell["cell_type"] == "code"
    )
    expected_sql_files = [
        "09_digital_session_channel_features.sql",
        "10_digital_beneficiary_passthrough_features.sql",
        "11_digital_velocity_account_features.sql",
    ]
    for sql_file in expected_sql_files:
        assert sql_file in all_source, (
            f"Notebook does not reference SQL exercise '{sql_file}'."
        )


def test_digital_feature_engineering_notebook_validates_detection_pattern_ids() -> None:
    """The notebook must assert that feature families map only to digital pattern IDs."""
    notebook = json.loads(_NOTEBOOK_PATH.read_text(encoding="utf-8"))
    all_source = "\n".join(
        "".join(cell["source"])
        for cell in notebook["cells"]
        if cell["cell_type"] == "code"
    )
    digital_pattern_ids = [
        "digital_scam_to_mule",
        "new_beneficiary_payment",
        "session_payment_velocity",
    ]
    for pattern_id in digital_pattern_ids:
        assert pattern_id in all_source, (
            f"Notebook does not reference digital pattern ID '{pattern_id}'."
        )


def test_digital_feature_engineering_notebook_has_markdown_documentation() -> None:
    """The notebook must contain markdown cells documenting the key sections."""
    notebook = json.loads(_NOTEBOOK_PATH.read_text(encoding="utf-8"))
    markdown_text = "\n".join(
        "".join(cell["source"])
        for cell in notebook["cells"]
        if cell["cell_type"] == "markdown"
    )
    required_headings = [
        "NovaBank Digital Feature Engineering",
        "Generate Learner-Facing Data",
        "Explore The Digital Session Context View",
        "Map Feature Families To Detection Patterns",
        "Build The Python Feature Frame",
        "Run The SQLite Feature Exercises",
        "Compare Python And SQL Outputs",
    ]
    for heading in required_headings:
        assert heading in markdown_text, (
            f"Required notebook section heading not found: '{heading}'"
        )


def test_notebooks_readme_references_digital_feature_engineering_notebook() -> None:
    """notebooks/README.md must document the new 05_digital_session_and_payment_fraud track.

    This validates the README.md change added in this PR which registers the new
    notebook under the numbered track convention.
    """
    readme_path = Path(__file__).resolve().parents[1] / "notebooks" / "README.md"
    readme = readme_path.read_text(encoding="utf-8")

    assert "05_digital_session_and_payment_fraud" in readme, (
        "notebooks/README.md does not reference the '05_digital_session_and_payment_fraud' "
        "directory."
    )
    assert "novabank_feature_engineering.ipynb" in readme, (
        "notebooks/README.md does not mention 'novabank_feature_engineering.ipynb'."
    )
    assert "NovaBank Digital" in readme


def test_notebooks_readme_smoke_test_command_includes_digital_feature_engineering() -> None:
    """notebooks/README.md smoke-test command must include the new notebook test.

    The README.md change updated the pytest command listed in the README to include
    test_digital_feature_engineering_notebook.py.
    """
    readme_path = Path(__file__).resolve().parents[1] / "notebooks" / "README.md"
    readme = readme_path.read_text(encoding="utf-8")

    assert "test_digital_feature_engineering_notebook.py" in readme, (
        "notebooks/README.md smoke-test command does not include "
        "'test_digital_feature_engineering_notebook.py'."
    )
