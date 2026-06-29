"""v1.0 acceptance-review and cross-version regression tests (issue #250).

Mirrors the v0.9 acceptance-review pattern (tests/test_v09_acceptance_review.py):
asserts every frozen v1.0 core module is present and individually runnable, the
v1.0 acceptance review carries the HITL boundary and hardening-only posture, and
re-executes the v0.3-v0.9 notebook smoke-test modules end-to-end via isolated
``uv run pytest`` subprocesses to prove the frozen core still runs. v1.0 adds no
notebooks and no feature scope (ADR-0002, ADR-0004, docs/release/v1.0-scope.md).
"""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
REVIEW_PATH = ROOT / "docs" / "release" / "v1.0-complete-public-core-curriculum-acceptance-review.md"
CHECKLIST_PATH = ROOT / "docs" / "release" / "v1.0-release-checklist.md"

# Frozen v1.0 core modules (matches docs/release/v1.0-scope.md and docs/ROADMAP.md
# § "v1.0: Complete Public Core Curriculum → Required modules"). v1.0 adds no modules.
FROZEN_CORE_MODULES = (
    "00_foundations",
    "01_private_banking_transaction_fraud",
    "02_digital_scam_to_mule",
    "03_alert_governance",
    "04_private_banking_feature_engineering",
    "05_digital_session_and_payment_fraud",
    "06_graph_network_fraud",
    "07_interpretability_model_risk",
    "08_production_monitoring_patterns",
    "09_capstone",
)

# Each frozen core module → the notebook smoke-test modules that prove it runs. v1.0
# adds no notebooks, so this is the existing surface; the cross-version regression
# loop below re-executes the v0.9 subset end-to-end.
MODULE_SMOKE_TESTS = {
    "00_foundations": ("test_foundations_notebook",),
    "01_private_banking_transaction_fraud": (
        "test_private_banking_notebook",
        "test_alpine_crest_case_narrative_notebook",
    ),
    "02_digital_scam_to_mule": ("test_digital_scam_to_mule_notebook",),
    "03_alert_governance": ("test_alert_governance_notebook",),
    "04_private_banking_feature_engineering": (
        "test_private_banking_feature_engineering_notebook",
        "test_private_banking_supervised_baseline_notebook",
    ),
    "05_digital_session_and_payment_fraud": (
        "test_digital_feature_engineering_notebook",
        "test_digital_supervised_baseline_notebook",
        "test_digital_alert_triage_notebook",
        "test_novabank_case_narrative_notebook",
    ),
    "06_graph_network_fraud": (
        "test_alpine_crest_graph_notebook",
        "test_novabank_graph_notebook",
    ),
    "07_interpretability_model_risk": (
        "test_alpine_crest_interpretability_notebook",
        "test_novabank_interpretability_notebook",
        "test_governance_memo_notebook",
    ),
    "08_production_monitoring_patterns": (
        "test_alpine_crest_monitoring_notebook",
        "test_novabank_monitoring_notebook",
        "test_alert_review_governance_notebook",
    ),
    "09_capstone": (
        "test_capstone_scoring_notebook",
        "test_capstone_synthesis_notebook",
    ),
}

# v1.0 deliverables that must be present on disk for the gate to hold. v1.0 adds no
# features, so this is the frozen core documentation + the scope/review artifacts,
# not new code. Each frozen module README proves the module is documented.
V10_DELIVERABLE_PATHS = {
    "scope_doc": "docs/release/v1.0-scope.md",
    "review_doc": "docs/release/v1.0-complete-public-core-curriculum-acceptance-review.md",
    "prd": "docs/prds/v1.0-complete-public-core-curriculum.md",
    **{
        f"core_module_readme_{module}": f"notebooks/{module}/README.md"
        for module in FROZEN_CORE_MODULES
    },
}

# v1.0 test modules that must exist (each enforces a v1.0 gate). Extended in #255
# to include the #252 data/schema gate module now that it has landed.
V10_TEST_MODULES = (
    "test_v10_acceptance_review",
    "test_v10_data_schema_gate",
)

# Prior-version notebook smoke-test modules re-executed for cross-version regression.
# UNCHANGED from v0.9 (tests/test_v09_acceptance_review.py): v1.0 adds no notebooks.
# TODO(#264): extend this set with the v0.5 case-narrative + alert-triage smoke tests
# (currently covered structurally by the per-module runnability test above, not
# re-executed in this subprocess loop).
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


@pytest.mark.parametrize("module", FROZEN_CORE_MODULES)
def test_v10_frozen_core_module_present(module: str) -> None:
    """Every frozen v1.0 core module directory must exist on disk."""
    module_dir = ROOT / "notebooks" / module
    assert module_dir.is_dir(), f"frozen v1.0 core module missing: {module}"


@pytest.mark.parametrize("module", FROZEN_CORE_MODULES)
def test_v10_frozen_core_module_is_runnable(module: str) -> None:
    """Each frozen core module has a README, >=1 featured notebook, and a smoke test.

    The cross-version regression loop below re-executes the v0.9 smoke-test subset
    end-to-end; this parametrized check guarantees every frozen module is individually
    covered by at least one notebook smoke-test module on disk, so no module silently
    loses its runnable path.
    """
    module_dir = ROOT / "notebooks" / module
    assert (module_dir / "README.md").is_file(), f"{module} missing README.md"
    notebooks = sorted(module_dir.glob("*.ipynb"))
    assert notebooks, f"{module} has no featured notebook"
    for smoke_test in MODULE_SMOKE_TESTS[module]:
        smoke_path = ROOT / "tests" / f"{smoke_test}.py"
        assert smoke_path.is_file(), f"{module} covering smoke test missing: {smoke_test}"


@pytest.mark.parametrize("key", sorted(V10_DELIVERABLE_PATHS))
def test_v10_deliverable_present(key: str) -> None:
    """Every v1.0 deliverable must exist on disk."""
    path = ROOT / V10_DELIVERABLE_PATHS[key]
    assert path.is_file(), f"v1.0 deliverable missing: {key} -> {path}"


@pytest.mark.parametrize("module_name", V10_TEST_MODULES)
def test_v10_test_module_present(module_name: str) -> None:
    """Each v1.0 enforcement test module must be present and collectable."""
    module_path = ROOT / "tests" / f"{module_name}.py"
    assert module_path.is_file(), f"v1.0 test module missing: {module_path}"
    assert importlib.util.find_spec(module_name) is not None, (
        f"v1.0 test module not collectable: {module_name}"
    )


@pytest.mark.parametrize("module_name", PRIOR_NOTEBOOK_TEST_MODULES)
def test_prior_notebook_regression_modules_exist(module_name: str) -> None:
    """Each prior-version notebook smoke test must still be present."""
    module_path = ROOT / "tests" / f"{module_name}.py"
    assert module_path.is_file(), f"prior notebook regression module missing: {module_path}"


@pytest.mark.regression_execution
def test_prior_notebooks_execute_end_to_end() -> None:
    """Re-execute v0.3-v0.9 notebook smoke tests via isolated uv run pytest subprocesses.

    Each prior notebook smoke-test module runs in its own subprocess (the canonical
    ``uv run pytest`` invocation CI uses) so a per-module regression is caught on its
    own. UNCHANGED from v0.9 (tests/test_v09_acceptance_review.py): v1.0 adds no
    notebooks, so the re-executed set is identical and proves the frozen core still
    runs end-to-end after the v1.0 hardening slices.
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


def test_v10_acceptance_review_has_hitl_boundary_and_evidence() -> None:
    """The v1.0 review states HITL status, command evidence, scope linkage, and posture."""
    review = REVIEW_PATH.read_text(encoding="utf-8")
    required_terms = [
        "uv sync --extra dev",
        "uv run ruff check .",
        "uv run pytest",
        "#53",
        "#249",
        "#250",
        "#251",
        "#252",
        "#253",
        "#254",
        "#255",
        "Alpine Crest Private Bank",
        "NovaBank Digital",
        "v1.0 hardens",
        "hardening only",
        "Fraud detection tracks",
        "Detection patterns",
        "Realistic synthetic data model",
        "Progressive data views",
        "docs/release/v1.0-scope.md",
        "docs/prds/v1.0-complete-public-core-curriculum.md",
        "docs/release/v0.1-publication-checklist.md",
    ]
    for term in required_terms:
        assert term in review, f"v1.0 acceptance review missing {term!r}"
    # HITL marker: COMPLETE once signed, REQUIRED until then. #250 lands the draft
    # (REQUIRED); the marker flips to COMPLETE under #255 HITL sign-off.
    assert "<!-- HITL-REVIEW-COMPLETE:" in review or "<!-- HITL-REVIEW-REQUIRED:" in review, (
        "v1.0 acceptance review missing HITL boundary marker"
    )


def test_v10_acceptance_review_preserves_private_pre_publication_framing() -> None:
    """The review keeps the repository-still-private / hardening-not-publication framing.

    v1.0 is hardening only and does not publish the repo; assertive public-release
    claims are banned. Checked sentence-by-sentence so a negated disclaimer (or the
    prohibited-content search command landing later under #255) does not trip a flat
    substring check.
    """
    review = REVIEW_PATH.read_text(encoding="utf-8").lower()
    assert "private" in review
    assert "hardening only" in review
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
            assert claim not in line, f"v1.0 review makes assertive claim {claim!r}: {stripped!r}"


def test_v10_acceptance_review_maps_every_prd_user_story() -> None:
    """Every parent PRD (#53) user story maps to issue/PR, files, tests, and HITL evidence."""
    review = REVIEW_PATH.read_text(encoding="utf-8")
    assert "PRD User Story Acceptance Matrix" in review
    for heading in ("Child issue / PR", "Evidence files", "Automated tests", "Manual / HITL evidence"):
        assert heading in review, f"acceptance matrix missing column {heading!r}"
    for story_number in range(1, 12):  # PRD #53 has 11 user stories
        assert f"User story {story_number}:" in review, (
            f"acceptance matrix missing user story {story_number}"
        )
    for child_issue in (250, 251, 252, 253, 254, 255):
        assert f"#{child_issue}" in review, f"acceptance review missing issue #{child_issue}"


def test_v10_acceptance_review_traces_the_learner_path() -> None:
    """The end-to-end learner path evidence must cover the full frozen core sequence."""
    review = REVIEW_PATH.read_text(encoding="utf-8")
    assert "End-To-End Learner Path Evidence" in review
    required_steps = (
        "Foundations",
        "Private-banking transaction baseline",
        "Digital scam-to-mule baseline",
        "Alert governance",
        "Private-banking feature engineering",
        "Digital session and payment fraud",
        "Graph and network fraud",
        "Interpretability and model risk",
        "Production monitoring patterns",
        "Capstone",
    )
    for step in required_steps:
        assert step in review, f"end-to-end learner path missing step {step!r}"


def test_v10_acceptance_review_documents_exit_criteria() -> None:
    """The review documents the v1.0 acceptance criteria and maps each to a gate."""
    review = REVIEW_PATH.read_text(encoding="utf-8")
    assert "Exit Criteria" in review
    for phrase in (
        "runnable featured notebooks",
        "Progressive data views",
        "SQLite exercises",
        "Case library covers",
        "CI passes on a clean checkout",
    ):
        assert phrase in review, f"exit criteria missing {phrase!r}"


def test_v10_release_checklist_present_and_gated() -> None:
    """The v1.0 release checklist exists, carries the HITL boundary, and references CI."""
    assert CHECKLIST_PATH.is_file(), f"v1.0 release checklist missing: {CHECKLIST_PATH}"
    checklist = CHECKLIST_PATH.read_text(encoding="utf-8")
    assert (
        "<!-- HITL-REVIEW-COMPLETE:" in checklist
        or "<!-- HITL-REVIEW-REQUIRED:" in checklist
    ), "v1.0 release checklist missing HITL boundary marker"
    for cmd in ("uv sync --extra dev", "uv run ruff check .", "uv run pytest"):
        assert cmd in checklist, f"checklist missing CI command {cmd!r}"
    assert "hardening only" in checklist.lower()
    assert "Release-Blocking Gates" in checklist
    for issue in (53, 249):
        assert f"#{issue}" in checklist, f"checklist missing issue #{issue}"
