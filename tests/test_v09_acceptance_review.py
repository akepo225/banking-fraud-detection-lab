"""v0.9 acceptance-review and cross-version regression tests (issue #234).

Mirrors the v0.8 acceptance-review pattern (tests/test_v08_acceptance_review.py):
asserts every v0.9 deliverable is present, both PRD exit criteria are enforced,
the acceptance review carries the HITL boundary and evidence, and re-executes
the v0.3-v0.9 notebook smoke-test modules end-to-end via isolated
``uv run pytest`` subprocesses to prove the capstone integration introduced no
notebook-execution regression.
"""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
REVIEW_PATH = ROOT / "docs" / "release" / "v0.9-capstone-beta-acceptance-review.md"

# Every v0.9 deliverable that must be present on disk for the beta to be complete.
V09_DELIVERABLE_PATHS = {
    "capstone_datasets_module": "src/banking_fraud_lab/capstone.py",
    "capstone_brief_alpine_crest": "docs/capstone/alpine_crest_brief.md",
    "capstone_brief_novabank": "docs/capstone/novabank_brief.md",
    "capstone_sql_private_banking": "sql/examples/12_capstone_private_banking.sql",
    "capstone_sql_digital_banking": "sql/examples/13_capstone_digital_banking.sql",
    "capstone_scoring_notebook_alpine": "notebooks/09_capstone/alpine_crest_capstone_scoring.ipynb",
    "capstone_scoring_notebook_novabank": "notebooks/09_capstone/novabank_capstone_scoring.ipynb",
    "capstone_synthesis_notebook": "notebooks/09_capstone/capstone_synthesis.ipynb",
    "capstone_module_readme": "notebooks/09_capstone/README.md",
    "capstone_rubric": "docs/capstone/rubric.md",
    "capstone_presentation_template": "docs/capstone/presentation_template.md",
    "troubleshooting": "docs/capstone/troubleshooting.md",
    "beta_checklist": "docs/release/v0.9-beta-checklist.md",
    "issue_template_bug": ".github/ISSUE_TEMPLATE/bug_report.yml",
    "issue_template_enhancement": ".github/ISSUE_TEMPLATE/enhancement.yml",
}

# v0.9 test modules that must exist (each enforces a v0.9 deliverable).
V09_TEST_MODULES = (
    "test_capstone_datasets",
    "test_capstone_docs",
    "test_capstone_sql",
    "test_capstone_scoring_notebook",
    "test_capstone_synthesis_notebook",
    "test_v09_clean_setup_commands",
    "test_issue_templates",
)

# Prior-version notebook smoke-test modules re-executed for cross-version
# regression. Extends the v0.8 set (tests/test_v08_acceptance_review.py) by
# adding the v0.8 monitoring notebooks + the v0.9 capstone notebooks.
PRIOR_NOTEBOOK_TEST_MODULES = (
    "test_foundations_notebook",  # v0.1
    "test_private_banking_notebook",  # v0.3
    "test_digital_scam_to_mule_notebook",  # v0.4
    "test_alert_governance_notebook",  # v0.1/v0.7
    "test_private_banking_feature_engineering_notebook",  # v0.3/v0.4
    "test_private_banking_supervised_baseline_notebook",  # v0.3/v0.4
    "test_digital_feature_engineering_notebook",
    "test_digital_supervised_baseline_notebook",
    "test_alpine_crest_graph_notebook",  # v0.6
    "test_novabank_graph_notebook",  # v0.6
    "test_alpine_crest_interpretability_notebook",  # v0.7
    "test_novabank_interpretability_notebook",  # v0.7
    "test_governance_memo_notebook",  # v0.7
    "test_alpine_crest_monitoring_notebook",  # v0.8
    "test_novabank_monitoring_notebook",  # v0.8
    "test_alert_review_governance_notebook",  # v0.8
    "test_capstone_scoring_notebook",  # v0.9
    "test_capstone_synthesis_notebook",  # v0.9
)


@pytest.mark.parametrize("key", sorted(V09_DELIVERABLE_PATHS))
def test_v09_deliverable_present(key: str) -> None:
    """Every v0.9 deliverable must exist on disk (PRD exit criterion 1)."""
    path = ROOT / V09_DELIVERABLE_PATHS[key]
    assert path.is_file(), f"v0.9 deliverable missing: {key} -> {path}"


@pytest.mark.parametrize("module_name", V09_TEST_MODULES)
def test_v09_test_module_present(module_name: str) -> None:
    """Each v0.9 enforcement test module must be present and collectable."""
    module_path = ROOT / "tests" / f"{module_name}.py"
    assert module_path.is_file(), f"v0.9 test module missing: {module_path}"
    assert importlib.util.find_spec(module_name) is not None, (
        f"v0.9 test module not collectable: {module_name}"
    )


@pytest.mark.parametrize("module_name", PRIOR_NOTEBOOK_TEST_MODULES)
def test_prior_notebook_regression_modules_exist(module_name: str) -> None:
    """Each prior-version notebook smoke test must still be present."""
    module_path = ROOT / "tests" / f"{module_name}.py"
    assert module_path.is_file(), f"prior notebook regression module missing: {module_path}"


@pytest.mark.regression_execution
def test_prior_notebooks_execute_end_to_end() -> None:
    """Re-execute v0.3-v0.9 notebook smoke tests via isolated uv run pytest subprocesses.

    Each prior notebook smoke-test module runs in its own subprocess (the
    canonical ``uv run pytest`` invocation CI uses) so a per-module regression
    is caught on its own. Extends the v0.8 cross-version regression one version
    further (adds the v0.8 monitoring notebooks + the v0.9 capstone notebooks).
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


def test_v09_acceptance_review_has_hitl_boundary_and_evidence() -> None:
    """The v0.9 review must state HITL status, command evidence, and PRD linkage."""
    review = REVIEW_PATH.read_text(encoding="utf-8")
    required_terms = [
        "Status: draft for human review.",
        "<!-- HITL-REVIEW-REQUIRED:",
        "uv sync --extra dev",
        "uv run ruff check .",
        "uv run pytest",
        "#52",
        "#229",
        "#233",
        "#234",
        "Alpine Crest Private Bank",
        "NovaBank Digital",
        "Hold pending final human beta decision",
        "recommend_lowest_cost_threshold",
        "evaluate_alert_scores",
        "v1.0 hardens",
    ]
    for term in required_terms:
        assert term in review, f"v0.9 acceptance review missing {term!r}"


def test_v09_acceptance_review_preserves_private_beta_framing() -> None:
    """The review keeps the repository-still-private / beta-not-public framing.

    Negated beta-honesty phrasing ("not a shipped release") is correct and must
    not be banned; only ASSERTIVE public-release claims violate the framing. The
    review also legitimately names banned phrases inside its prohibited-content
    search command, so a flat substring ban would create false positives.
    """
    review = REVIEW_PATH.read_text(encoding="utf-8").lower()
    assert "private" in review
    assert "beta" in review
    assert "not a shipped release" in review  # correct beta-honesty framing
    # Assertive public-release claims are banned. These are checked sentence-by-
    # sentence so the negated disclaimer and the search-command listing do not
    # trip a flat substring check.
    assertive_claims = (
        "is now published",
        "has been published",
        "publicly released",
        "is production-ready",
        "is certified",
    )
    for line in review.splitlines():
        stripped = line.strip()
        # Skip the prohibited-content search command line and code fences.
        if stripped.startswith("rg ") or stripped.startswith("```"):
            continue
        for claim in assertive_claims:
            assert claim not in line, f"v0.9 review makes assertive claim {claim!r}: {stripped!r}"


def test_v09_enforces_both_prd_exit_criteria() -> None:
    """PRD exit criterion 1 (capstone path) and 2 (beta-readiness) are both enforced.

    The enforcement is structural: exit criterion 1 is covered by the capstone
    deliverables + their test modules (parametrized presence checks above); exit
    criterion 2 is covered by the beta checklist, clean-setup test, terminology
    guardrails, and issue templates (all asserted present above). This test
    documents the mapping explicitly so a future change cannot silently drop one.
    """
    review = REVIEW_PATH.read_text(encoding="utf-8")
    assert "Exit criterion 1" in review
    assert "Exit criterion 2" in review
    assert "v0.9-beta-checklist" in review
    assert "terminology" in review.lower()
