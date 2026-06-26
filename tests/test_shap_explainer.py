"""Tests for the optional SHAP explainability path (availability-guarded).

Mirrors the v0.6 Neo4j optional-extra test precedent
(:mod:`tests.test_neo4j_export`) and the v0.6 acceptance-review optional-extra
assertions: SHAP must live only behind an optional extra, never in core or dev,
and importing the package must succeed without it.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from banking_fraud_lab import SHAP_AVAILABLE, explain_with_shap

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT_PATH = ROOT / "pyproject.toml"


def _pyproject_text() -> str:
    return PYPROJECT_PATH.read_text(encoding="utf-8")


def test_shap_availability_flag_exists() -> None:
    """The SHAP_AVAILABLE flag must exist and be a boolean."""
    assert isinstance(SHAP_AVAILABLE, bool)


def test_import_succeeds_without_shap() -> None:
    """Importing the package must never require the optional shap package.

    If this test module imported at all, banking_fraud_lab imported cleanly
    regardless of whether the optional shap package is present. SHAP_AVAILABLE
    reflects the optional state; the CI/default-dev environment has shap absent,
    but the import contract holds either way.
    """
    assert isinstance(SHAP_AVAILABLE, bool)


def test_explain_with_shap_raises_when_shap_absent() -> None:
    """explain_with_shap must raise a clear RuntimeError with install guidance when shap absent."""
    if SHAP_AVAILABLE:
        pytest.skip("shap is installed in this environment; skipping the absent-path test")
    frame = pd.DataFrame({"a": [1.0, 2.0], "b": [3.0, 4.0]})
    with pytest.raises(RuntimeError, match="optional extra is not installed"):
        explain_with_shap(model=None, feature_frame=frame, feature_columns=["a", "b"])


def test_shap_is_optional_and_outside_core_and_dev() -> None:
    """shap must live only behind an optional extra, not in core or dev dependencies."""
    text = _pyproject_text()
    # The optional shap extra exists.
    assert "shap = [" in text, "optional shap extra missing"
    # shap is NOT in the core dependencies block.
    dependencies_start = text.index("dependencies = [")
    dependencies_end = text.index("]", dependencies_start)
    dependencies_block = text[dependencies_start:dependencies_end]
    assert "shap" not in dependencies_block, "shap must not be a core dependency"
    # shap is NOT in the dev block.
    dev_start = text.index("dev = [")
    dev_end = text.index("]", dev_start)
    dev_block = text[dev_start:dev_end]
    assert "shap" not in dev_block, "shap must not be a dev dependency"


def test_shap_not_importable_in_ci_environment() -> None:
    """In the CI/default dev environment, the shap package must not be importable.

    Guards the dependency-cost decision: shap stays optional and out of CI, so a
    plain ``uv sync --extra dev`` must not install it. Skipped when the shap extra
    is intentionally installed locally.
    """
    if SHAP_AVAILABLE:
        pytest.skip("shap extra installed; CI-profile guard not applicable")
    import importlib.util

    assert importlib.util.find_spec("shap") is None, (
        "shap is installed but must remain optional and outside `uv sync --extra dev` / CI"
    )
