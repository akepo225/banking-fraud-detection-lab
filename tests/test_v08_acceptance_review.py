"""v0.8 acceptance-review and cross-version regression tests.

Mirrors the v0.7 acceptance-review test convention
(:mod:`tests.test_v07_acceptance_review`): asserts the v0.8 module presence,
both PRD exit criteria, the real-time-infrastructure dependency-cost decision
(slice #206, mirroring the v0.7 SHAP decision), and cross-version regression
over prior notebooks whose outputs feed v0.8 monitoring.
"""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
REVIEW_PATH = ROOT / "docs" / "release" / "v0.8-production-monitoring-acceptance-review.md"
PYPROJECT_PATH = ROOT / "pyproject.toml"
NOTEBOOKS_README = ROOT / "notebooks" / "README.md"
NOTEBOOK_08_DIR = ROOT / "notebooks" / "08_production_monitoring_patterns"

HEAVY_INFRA_PACKAGES = frozenset(
    {
        "kafka",
        "spark",
        "pyspark",
        "redis",
        "dash",
        "streamlit",
        "flink",
        "cassandra",
        "elasticsearch",
    }
)


def _parse_pyproject() -> dict:
    """Parse pyproject.toml with tomllib (Python 3.11+) for robust dep inspection."""
    import tomllib

    with PYPROJECT_PATH.open("rb") as handle:
        return tomllib.load(handle)


def _dep_names(section: list[str]) -> set[str]:
    """Extract lowercased package names (with optional extras stripped) from a dep list."""
    names: set[str] = set()
    for entry in section:
        token = entry.split("[", 1)[0].strip()
        for sep in ("=", "<", ">", "!", "~", ";"):
            token = token.split(sep, 1)[0]
        token = token.strip().lower()
        if token:
            names.add(token)
    return names


# --- Core v0.8 module presence --------------------------------------------


def test_monitoring_module_is_importable() -> None:
    """The v0.8 monitoring module must be importable from the package root."""
    import banking_fraud_lab.monitoring as monitoring

    assert hasattr(monitoring, "run_batch_scoring")


def test_monitoring_public_builders_are_present() -> None:
    """The v0.8 monitoring public builders must all exist on the package facade."""
    from banking_fraud_lab.monitoring import (
        check_feature_drift,
        check_monitoring_data_quality,
        check_score_drift,
        decide_alerts,
        inspect_alert_queue,
        record_reviewer_action,
        run_batch_scoring,
        summarise_alert_operations,
    )

    for builder in (
        run_batch_scoring,
        decide_alerts,
        record_reviewer_action,
        inspect_alert_queue,
        summarise_alert_operations,
        check_score_drift,
        check_feature_drift,
        check_monitoring_data_quality,
    ):
        assert callable(builder), f"monitoring builder not callable: {builder!r}"


def test_frozen_monitoring_table_contract_is_present() -> None:
    """The five frozen monitoring tables + audit-event vocab must be exposed."""
    from banking_fraud_lab.monitoring import AUDIT_EVENT_TYPES, MONITORING_TABLE_IDS

    assert MONITORING_TABLE_IDS == (
        "score",
        "threshold",
        "alert_decision",
        "reviewer_action",
        "audit_event",
    ), "frozen monitoring-table ids drifted from the #200 contract"
    assert set(AUDIT_EVENT_TYPES) == {
        "score_assigned",
        "alert_decision_made",
        "reviewer_action_recorded",
        "threshold_reviewed",
    }, "audit-event type vocabulary drifted"


# --- Exit criterion 1: production-pattern notebooks runnable ---------------


@pytest.mark.parametrize(
    "notebook_name",
    (
        "alpine_crest_monitoring.ipynb",
        "novabank_monitoring.ipynb",
        "alert_review_governance.ipynb",
    ),
)
def test_v08_production_monitoring_notebooks_present(notebook_name: str) -> None:
    """The three 08 production-monitoring notebooks must exist on disk as valid nbformat.

    Full end-to-end nbconvert execution is already covered by each notebook's own
    smoke test; here we assert presence + valid nbformat (JSON with nbformat magic)
    so the acceptance gate is fast.
    """
    import json

    notebook_path = NOTEBOOK_08_DIR / notebook_name
    assert notebook_path.is_file(), f"v0.8 notebook missing: {notebook_path}"
    with notebook_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    assert payload.get("nbformat") in (3, 4), f"{notebook_name} is not valid nbformat"


def test_v08_notebooks_linked_from_notebooks_readme() -> None:
    """The v0.8 module must be placed in the learner path (notebooks README)."""
    text = NOTEBOOKS_README.read_text(encoding="utf-8")
    assert "08_production_monitoring_patterns" in text
    assert "alpine_crest_monitoring.ipynb" in text
    assert "novabank_monitoring.ipynb" in text
    assert "alert_review_governance.ipynb" in text


# --- Exit criterion 2: monitoring tied to Alert lifecycle + reusing v0.7 ---


def test_drift_checks_reference_governance_dimension_ids() -> None:
    """check_score_drift / check_monitoring_data_quality emit governance dimension ids.

    The v0.8 monitoring module reuses the v0.7 governance
    ``MONITORING_CHECKLIST_DIMENSIONS`` vocabulary rather than inventing its own:
    score drift maps to ``score_drift`` and data quality to ``data_quality``.
    """
    import pandas as pd

    from banking_fraud_lab import MONITORING_CHECKLIST_DIMENSION_IDS
    from banking_fraud_lab.monitoring import (
        check_monitoring_data_quality,
        check_score_drift,
    )

    assert "score_drift" in MONITORING_CHECKLIST_DIMENSION_IDS
    assert "data_quality" in MONITORING_CHECKLIST_DIMENSION_IDS

    drift_result = check_score_drift([0.1, 0.2, 0.3], [0.4, 0.5, 0.6], tolerance=0.01)
    assert drift_result.dimension_id == "score_drift", (
        "check_score_drift must emit the governance 'score_drift' dimension id"
    )

    frame = pd.DataFrame({"amount": [1.0, 2.0], "channel": ["online", "branch"]})
    dq_result = check_monitoring_data_quality(frame, required_columns=["amount"])
    assert dq_result.dimension_id == "data_quality", (
        "check_monitoring_data_quality must emit the governance 'data_quality' dimension id"
    )


def test_alert_lifecycle_audit_chain_uses_frozen_vocabulary() -> None:
    """run_batch_scoring -> decide_alerts -> record_reviewer_action audit chain.

    A tiny functional chain asserts that the audit_event rows emitted along the
    Alert lifecycle use ``audit_event_type`` values drawn from the frozen
    ``AUDIT_EVENT_TYPES`` vocabulary (PRD exit criterion 2: monitoring tied to
    the Alert lifecycle).
    """
    import pandas as pd

    from banking_fraud_lab.monitoring import (
        AUDIT_EVENT_TYPES,
        decide_alerts,
        record_reviewer_action,
        run_batch_scoring,
    )

    scored_frame = pd.DataFrame(
        {
            "score": [0.9, 0.2],
            "banking_relationship_id": ["br_1", "br_2"],
            "client_id": ["cli_1", None],
            "user_id": [None, "usr_2"],
        }
    )
    batch = run_batch_scoring(
        scored_frame,
        detection_pattern_id="session_payment_velocity",
        threshold=0.5,
        scorer="tiny_scorer",
        score_version="0",
    )
    decisions = decide_alerts(
        batch.score_rows, threshold=0.5, threshold_id="th_test_0"
    )
    actions = record_reviewer_action(
        decisions.alert_decision_rows,
        reviewer="reviewer_a",
        action="confirm",
        rationale="acceptance-test chain",
    )

    decision_types = set(decisions.audit_rows["audit_event_type"].tolist())
    reviewer_types = set(actions.audit_rows["audit_event_type"].tolist())
    assert decision_types, "decide_alerts must emit at least one audit_event row"
    assert reviewer_types, "record_reviewer_action must emit at least one audit_event row"
    assert decision_types.issubset(AUDIT_EVENT_TYPES), (
        f"decision audit types outside frozen vocabulary: {decision_types - set(AUDIT_EVENT_TYPES)}"
    )
    assert reviewer_types.issubset(AUDIT_EVENT_TYPES), (
        f"reviewer audit types outside frozen vocabulary: {reviewer_types - set(AUDIT_EVENT_TYPES)}"
    )


def test_monitoring_reuses_v07_symbols() -> None:
    """The v0.7 symbols the monitoring module consumes must still be importable.

    Cited reuse (PRD exit criterion 2): ``recommend_lowest_cost_threshold`` and
    ``evaluate_alert_scores`` (threshold source for batch scoring),
    ``explain_feature_family`` (reviewer_action.evidence), and the governance
    ``MONITORING_CHECKLIST_DIMENSIONS`` (drift / data-quality dimension ids).
    """
    from banking_fraud_lab import (
        MONITORING_CHECKLIST_DIMENSIONS,
        evaluate_alert_scores,
        explain_feature_family,
        recommend_lowest_cost_threshold,
    )

    assert callable(evaluate_alert_scores)
    assert callable(recommend_lowest_cost_threshold)
    assert callable(explain_feature_family)
    assert MONITORING_CHECKLIST_DIMENSIONS, "governance dimensions must be non-empty"


# --- Real-time-infra dependency-cost decision (slice #206, HITL) -----------


def test_heavy_realtime_infra_is_outside_core_and_dev() -> None:
    """Kafka/Spark/Redis/dashboards must not be core or dev dependencies (cost decision).

    Per the accepted HITL decision on slice #206: heavy real-time infrastructure
    stays optional and out of CI, mirroring the v0.7 SHAP decision (#187) and the
    v0.6 Neo4j decision (#154). None of the listed packages may appear in
    ``[project].dependencies`` or the ``dev`` extra.
    """
    config = _parse_pyproject()
    optional_extras = config.get("project", {}).get("optional-dependencies", {})
    core_deps = _dep_names(config.get("project", {}).get("dependencies", []))
    dev_deps = _dep_names(optional_extras.get("dev", []))

    in_core = HEAVY_INFRA_PACKAGES & core_deps
    in_dev = HEAVY_INFRA_PACKAGES & dev_deps
    assert not in_core, f"heavy infra must not be a core dependency: {sorted(in_core)}"
    assert not in_dev, f"heavy infra must not be a dev dependency: {sorted(in_dev)}"


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
    "test_alpine_crest_interpretability_notebook",  # v0.7
    "test_novabank_interpretability_notebook",  # v0.7
    "test_governance_memo_notebook",  # v0.7
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
    """The gate must prove prior-version notebooks feeding v0.8 still execute.

    Runs each prior notebook smoke-test module directly via an isolated
    ``uv run pytest`` subprocess -- the same canonical invocation CI uses -- so
    the Jupyter kernel environment matches CI exactly. Each module runs in its
    own subprocess so a per-module regression is caught on its own. This extends
    the v0.7 cross-version regression one version further (adds the v0.7
    interpretability + governance-memo notebook modules).
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


def test_v08_acceptance_review_has_hitl_boundary_and_evidence() -> None:
    """The v0.8 review must state HITL status and link PRD deliverable evidence."""
    review = REVIEW_PATH.read_text(encoding="utf-8")

    required_terms = [
        "Status: draft for human review.",
        "<!-- HITL-REVIEW-REQUIRED:",
        "uv sync --extra dev",
        "uv run ruff check .",
        "uv run pytest",
        "#200",
        "#206",
        "#210",
        "Kafka",
        "Spark",
        "Redis",
        "recommend_lowest_cost_threshold",
        "evaluate_alert_scores",
        "explain_feature_family",
        "MONITORING_CHECKLIST_DIMENSIONS",
        "audit_event",
        "alert_decision",
        "reviewer_action",
    ]
    for term in required_terms:
        assert term in review, f"v0.8 acceptance review missing term: {term!r}"


def test_v08_acceptance_review_has_no_public_release_language() -> None:
    """The repo stays private; the v0.8 review must not claim publication/readiness."""
    review = REVIEW_PATH.read_text(encoding="utf-8")
    forbidden = (
        "now public",
        "publicly released",
        "v1.0 is published",
        "is now published",
        "production-ready",
        "production readiness",
    )
    for term in forbidden:
        assert term.lower() not in review.lower(), (
            f"v0.8 review must not include public-release language: {term!r}"
        )
