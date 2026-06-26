"""v0.7 acceptance-review and cross-version regression tests.

Mirrors the v0.6 acceptance-review test convention
(:mod:`tests.test_v06_acceptance_review`): asserts the v0.7 module presence,
both PRD exit criteria, the SHAP dependency-cost decision (slice #187), and
cross-version regression over prior notebooks feeding model outputs into v0.7.
"""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
REVIEW_PATH = ROOT / "docs" / "release" / "v0.7-interpretability-model-risk-acceptance-review.md"
PYPROJECT_PATH = ROOT / "pyproject.toml"
NOTEBOOKS_README = ROOT / "notebooks" / "README.md"


def _parse_pyproject() -> dict:
    """Parse pyproject.toml with tomllib (Python 3.11+) for robust dep inspection."""
    import tomllib

    with PYPROJECT_PATH.open("rb") as handle:
        return tomllib.load(handle)


# --- Core v0.7 module presence --------------------------------------------


def test_interpretability_module_is_importable() -> None:
    """The v0.7 interpretability module must be importable from the package root."""
    from banking_fraud_lab import EXPLANATION_FAMILY_SPECS  # noqa: F401

    assert EXPLANATION_FAMILY_SPECS, "EXPLANATION_FAMILY_SPECS catalog must be non-empty"


def test_governance_module_is_importable() -> None:
    """The v0.7 governance module must be importable from the package root."""
    from banking_fraud_lab import MODEL_DOCUMENTATION_SECTIONS, MONITORING_CHECKLIST_DIMENSIONS

    assert MODEL_DOCUMENTATION_SECTIONS
    assert MONITORING_CHECKLIST_DIMENSIONS


def test_v07_evaluation_utilities_are_additive() -> None:
    """The v0.7 FP/threshold utilities must be additive to evaluate_alert_scores."""
    from banking_fraud_lab import (
        concentrate_false_positives,
        evaluate_alert_scores,
        recommend_lowest_cost_threshold,
    )

    assert callable(evaluate_alert_scores)
    assert callable(concentrate_false_positives)
    assert callable(recommend_lowest_cost_threshold)


# --- SHAP dependency-cost decision (slice #187, HITL) ---------------------


def test_shap_is_optional_and_outside_core_and_dev() -> None:
    """shap must live only behind an optional extra, not in core or dev (cost decision).

    Per the accepted HITL decision on slice #187: SHAP stays optional and out of CI.
    The ``shap`` extra exists; it is NOT a core or dev dependency.
    """
    config = _parse_pyproject()
    optional_extras = config.get("project", {}).get("optional-dependencies", {})
    assert "shap" in optional_extras, "optional shap extra missing"
    core_deps = config.get("project", {}).get("dependencies", [])
    dev_deps = optional_extras.get("dev", [])
    assert not any("shap" in dep for dep in core_deps), "shap must not be a core dependency"
    assert not any("shap" in dep for dep in dev_deps), "shap must not be a dev dependency"


def test_shap_not_importable_in_ci_environment() -> None:
    """In the CI/default dev environment shap must not be installed (cost decision).

    ``uv sync --extra dev`` does NOT install the shap extra, so the package must not be
    importable in the CI profile. (Skipped only when a developer has the shap extra
    installed locally.)
    """
    from banking_fraud_lab import SHAP_AVAILABLE

    if SHAP_AVAILABLE:
        pytest.skip("shap extra installed; CI-profile guard not applicable")
    assert importlib.util.find_spec("shap") is None, (
        "shap is installed but must remain optional and outside `uv sync --extra dev` / CI"
    )


# --- Exit criterion 1: model notebooks link to interpretability/governance -


def test_featured_model_notebooks_link_to_interpretability_or_governance() -> None:
    """Every featured model notebook must link to an interpretability/governance exercise.

    The v0.3/v0.4 supervised baselines are extended by the v0.7 07 module, and
    03_alert_governance bidirectionally links to 07.
    """
    # The v0.7 module exists and is linked from the notebooks README.
    notebooks_readme = NOTEBOOKS_README.read_text(encoding="utf-8")
    assert "07_interpretability_model_risk" in notebooks_readme

    # 03_alert_governance links outbound to the 07 module.
    notebook_03 = (
        ROOT / "notebooks" / "03_alert_governance" / "alert_governance_memo.ipynb"
    ).read_text(encoding="utf-8")
    assert "07_interpretability_model_risk" in notebook_03

    # The 07 module README links back to 03 (bidirectional).
    readme_07 = (
        ROOT / "notebooks" / "07_interpretability_model_risk" / "README.md"
    ).read_text(encoding="utf-8")
    assert "03_alert_governance" in readme_07


# --- Exit criterion 2: "not judged by headline accuracy" framing visible --


@pytest.mark.parametrize(
    "notebook_rel",
    (
        "notebooks/07_interpretability_model_risk/alpine_crest_interpretability.ipynb",
        "notebooks/07_interpretability_model_risk/novabank_interpretability.ipynb",
    ),
)
def test_interpretability_notebooks_surface_headline_accuracy_limit(notebook_rel: str) -> None:
    """The interpretability notebooks must surface the headline-accuracy limitation (PRD exit 2)."""
    text = (ROOT / notebook_rel).read_text(encoding="utf-8")
    assert "should not be judged by headline accuracy" in text, (
        f"{notebook_rel} must surface the headline-accuracy limitation framing"
    )
    assert "accuracy is out of scope" in text


# --- v0.7 notebooks linked from notebooks README --------------------------


def test_v07_notebooks_linked_from_notebooks_readme() -> None:
    """The v0.7 module must be placed in the learner path."""
    text = NOTEBOOKS_README.read_text(encoding="utf-8")
    assert "07_interpretability_model_risk" in text
    assert "alpine_crest_interpretability.ipynb" in text
    assert "novabank_interpretability.ipynb" in text


# --- Cross-version regression: prior notebooks still covered --------------


PRIOR_NOTEBOOK_TEST_MODULES = (
    "test_private_banking_notebook",  # v0.3 private-banking baseline
    "test_digital_scam_to_mule_notebook",  # v0.4 digital-banking baseline
    "test_alert_governance_notebook",  # v0.1/v0.7 alert governance
    "test_private_banking_feature_engineering_notebook",  # v0.3/v0.4 feature engineering
    "test_private_banking_supervised_baseline_notebook",  # v0.3/v0.4 supervised baseline
    "test_digital_feature_engineering_notebook",
    "test_digital_supervised_baseline_notebook",
    "test_alpine_crest_graph_notebook",  # v0.6
    "test_novabank_graph_notebook",  # v0.6
)


@pytest.mark.parametrize("module_name", PRIOR_NOTEBOOK_TEST_MODULES)
def test_prior_notebook_regression_modules_exist(module_name: str) -> None:
    """Each prior-version notebook smoke test must still be present."""
    module_path = ROOT / "tests" / f"{module_name}.py"
    assert module_path.is_file(), f"prior notebook regression module missing: {module_path}"


def test_prior_notebook_test_modules_are_collectable() -> None:
    """The prior notebook test modules must be importable (collectable)."""
    for module_name in PRIOR_NOTEBOOK_TEST_MODULES:
        assert importlib.util.find_spec(module_name) is not None, (
            f"notebook regression module not collectable: {module_name}"
        )


@pytest.mark.regression_execution
def test_prior_notebooks_execute_end_to_end() -> None:
    """The gate must prove prior-version notebooks feeding v0.7 still execute.

    Runs each prior notebook smoke-test module directly via an isolated
    ``uv run pytest`` subprocess — the same canonical invocation CI uses — so the
    Jupyter kernel environment matches CI exactly. Each module runs in its own
    subprocess so a per-module regression is caught on its own.
    """
    failures: list[str] = []
    for name in PRIOR_NOTEBOOK_TEST_MODULES:
        module_path = ROOT / "tests" / f"{name}.py"
        try:
            result = subprocess.run(  # noqa: S603 - "uv" is the project-mandated runner; argv is controlled.
                ["uv", "run", "pytest", str(module_path), "-q"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
                timeout=300,
            )
        except subprocess.TimeoutExpired as exc:
            failures.append(f"{name} (timed out after 300s): {exc}")
            continue
        if result.returncode != 0:
            failures.append(
                f"{name} (exit {result.returncode}):\n" + result.stdout + result.stderr
            )

    assert not failures, "prior notebook execution failed:\n" + "\n".join(failures)


# --- Acceptance review artifact -------------------------------------------


def test_v07_acceptance_review_has_hitl_boundary_and_evidence() -> None:
    """The v0.7 review must state HITL status and link PRD deliverable evidence."""
    review = REVIEW_PATH.read_text(encoding="utf-8")

    required_terms = [
        "Status: draft for human review.",
        "<!-- HITL-REVIEW-REQUIRED:",
        "uv sync --extra dev",
        "uv run ruff check .",
        "uv run pytest",
        "should not be judged by headline accuracy",
        "mule_ring",
        "circular_funds_movement",
        "#187",
        "shap",
    ]
    for term in required_terms:
        assert term in review, f"v0.7 acceptance review missing term: {term!r}"
