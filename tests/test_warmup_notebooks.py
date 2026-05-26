"""Smoke tests for optional canonical-data warm-up notebooks."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
WARMUP_DIR = REPO_ROOT / "notebooks" / "00_foundations" / "warmups"
WARMUP_NOTEBOOKS = (
    "python_canonical_data_warmup.ipynb",
    "pandas_progressive_views_warmup.ipynb",
    "sql_progressive_views_warmup.ipynb",
    "sklearn_alert_scoring_warmup.ipynb",
)


@pytest.mark.parametrize("notebook_name", WARMUP_NOTEBOOKS)
def test_optional_warmup_notebook_executes(
    notebook_name: str,
    tmp_path: Path,
) -> None:
    """Every optional warm-up notebook must execute on tiny canonical data."""
    notebook_path = WARMUP_DIR / notebook_name
    output_name = notebook_name.replace(".ipynb", ".executed.ipynb")

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
            str(notebook_path),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert (tmp_path / output_name).exists()


def test_warmup_guide_marks_notebooks_optional_and_canonical() -> None:
    """Notebook guides must link real optional warm-ups without making them required."""
    notebook_guide = (REPO_ROOT / "notebooks" / "README.md").read_text(
        encoding="utf-8"
    )
    warmup_guide = (WARMUP_DIR / "README.md").read_text(encoding="utf-8")
    normalized_notebook_guide = " ".join(notebook_guide.split())

    assert "Optional Warm-Ups" in notebook_guide
    assert "outside the required core module sequence" in normalized_notebook_guide
    assert "not a separate beginner curriculum" in warmup_guide
    assert "Realistic synthetic data model" in warmup_guide
    assert "Progressive data views" in warmup_guide
    assert "SQLite" in warmup_guide
    assert "sklearn" in warmup_guide.lower()

    for notebook_name in WARMUP_NOTEBOOKS:
        assert (WARMUP_DIR / notebook_name).exists()
        assert notebook_name in notebook_guide
        assert notebook_name in warmup_guide


def test_warmups_use_canonical_data_surfaces() -> None:
    """Warm-ups must exercise canonical generated data, Progressive views, and SQLite."""
    notebook_text_by_name = {
        notebook_name: (WARMUP_DIR / notebook_name).read_text(encoding="utf-8")
        for notebook_name in WARMUP_NOTEBOOKS
    }

    assert "generate_minimal_banking_world(seed=42)" in "\n".join(
        notebook_text_by_name.values()
    )
    assert "build_learner_facing_views" in notebook_text_by_name[
        "python_canonical_data_warmup.ipynb"
    ]
    assert "build_foundation_progressive_views" in notebook_text_by_name[
        "pandas_progressive_views_warmup.ipynb"
    ]
    assert "create_minimal_banking_world_sqlite" in notebook_text_by_name[
        "sql_progressive_views_warmup.ipynb"
    ]
    assert "foundation_alert_lifecycle" in notebook_text_by_name[
        "sklearn_alert_scoring_warmup.ipynb"
    ]
    assert "evaluate_alert_scores" in notebook_text_by_name[
        "sklearn_alert_scoring_warmup.ipynb"
    ]
