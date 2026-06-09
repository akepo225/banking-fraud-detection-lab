"""Tests for foundation-level Progressive data views."""

from pathlib import Path

import pandas as pd

from banking_fraud_lab import generate_minimal_banking_world
from banking_fraud_lab.progressive_views import (
    FOUNDATION_PROGRESSIVE_VIEW_SPECS,
    PB_RELATIONSHIP_CONTEXT,
    build_foundation_progressive_views,
)
from banking_fraud_lab.schema import (
    ALERTS,
    BANKING_RELATIONSHIPS,
    CASE_OUTCOMES,
    CASES,
    COLUMN_NAMES,
    PROTECTED_SCENARIO_ANSWER_KEYS,
    RELATIONSHIP_MANAGER_HISTORY,
    SUSPICIOUS_ACTIVITIES,
    TABLE_NAMES,
)


FOUNDATION_PROGRESSIVE_VIEW_SPECS_BY_NAME = {
    spec.name: spec for spec in FOUNDATION_PROGRESSIVE_VIEW_SPECS
}
PROTECTED_ANSWER_KEY_COLUMNS = set(COLUMN_NAMES[PROTECTED_SCENARIO_ANSWER_KEYS])


def test_foundation_client_relationships_view_is_stable_and_traceable() -> None:
    """The foundation Client relationship view must join back to canonical tables."""
    tables = generate_minimal_banking_world(seed=42)

    spec = FOUNDATION_PROGRESSIVE_VIEW_SPECS_BY_NAME["foundation_client_relationships"]
    assert spec.source_tables == ("clients", "partners", "banking_relationships")
    assert spec.stable_for_case_references
    assert spec.columns == (
        "client_id",
        "partner_id",
        "institution_name",
        "client_segment",
        "client_status",
        "partner_type",
        "partner_country",
        "risk_rating",
        "kyc_risk_effective_from",
        "kyc_risk_reviewed_at",
        "banking_relationship_id",
        "relationship_name",
        "relationship_status",
        "relationship_opened_at",
        "relationship_manager_code",
        "relationship_manager_assigned_at",
    )

    view = build_foundation_progressive_views(tables)[spec.name]

    assert tuple(view.columns) == spec.columns
    assert len(view) == len(tables["banking_relationships"])
    assert set(view["client_id"]) <= set(tables["clients"]["client_id"])
    assert set(view["partner_id"]) <= set(tables["partners"]["partner_id"])
    assert set(view["banking_relationship_id"]) == set(
        tables["banking_relationships"]["banking_relationship_id"]
    )


def test_foundation_alert_lifecycle_view_excludes_protected_answer_keys() -> None:
    """The foundation Alert lifecycle view must expose lifecycle rows, not answer keys."""
    tables = generate_minimal_banking_world(seed=42)

    spec = FOUNDATION_PROGRESSIVE_VIEW_SPECS_BY_NAME["foundation_alert_lifecycle"]
    assert spec.source_tables == (
        "suspicious_activities",
        "alerts",
        "cases",
        "case_outcomes",
    )
    assert PROTECTED_SCENARIO_ANSWER_KEYS not in spec.source_tables
    assert not (set(spec.columns) & PROTECTED_ANSWER_KEY_COLUMNS)

    view = build_foundation_progressive_views(tables)[spec.name]

    assert tuple(view.columns) == spec.columns
    assert len(view) == len(tables["suspicious_activities"])
    assert set(view["suspicious_activity_id"]) == set(
        tables["suspicious_activities"]["suspicious_activity_id"]
    )
    assert set(view["alert_id"].dropna()) == set(tables["alerts"]["alert_id"])
    assert set(view["case_id"].dropna()) <= set(tables["cases"]["case_id"])
    assert set(view["case_outcome_id"].dropna()) <= set(
        tables["case_outcomes"]["case_outcome_id"]
    )


def test_pb_relationship_context_view_uses_current_rm_history() -> None:
    """The private-banking relationship view must expose current RM history."""
    tables = generate_minimal_banking_world(seed=42)

    spec = FOUNDATION_PROGRESSIVE_VIEW_SPECS_BY_NAME["pb_relationship_context"]
    assert spec is PB_RELATIONSHIP_CONTEXT
    assert spec.source_tables == (
        "banking_relationships",
        "relationship_manager_history",
    )
    assert not spec.stable_for_case_references
    assert spec.columns == (
        "banking_relationship_id",
        "primary_client_id",
        "institution_name",
        "relationship_name",
        "relationship_opened_at",
        "relationship_status",
        "relationship_manager_code",
        "rm_effective_from",
        "rm_effective_to",
    )

    view = build_foundation_progressive_views(tables)[spec.name]
    current_rm_history = tables[RELATIONSHIP_MANAGER_HISTORY][
        tables[RELATIONSHIP_MANAGER_HISTORY]["effective_to"].isna()
    ]
    view_context = view.merge(
        current_rm_history[
            [
                "banking_relationship_id",
                "relationship_manager_code",
                "effective_from",
            ]
        ],
        on="banking_relationship_id",
        how="left",
        validate="one_to_one",
        suffixes=("_view", "_history"),
    )

    assert tuple(view.columns) == spec.columns
    assert len(view) == len(tables[BANKING_RELATIONSHIPS])
    assert set(view["banking_relationship_id"]) == set(
        tables[BANKING_RELATIONSHIPS]["banking_relationship_id"]
    )
    assert (
        view_context["relationship_manager_code_view"]
        == view_context["relationship_manager_code_history"]
    ).all()
    assert (view_context["rm_effective_from"] == view_context["effective_from"]).all()
    assert view["rm_effective_to"].isna().all()


def test_pb_relationship_context_view_selects_latest_current_rm_history() -> None:
    """Duplicate current RM-history rows should collapse to the latest assignment."""
    tables = generate_minimal_banking_world(seed=42)
    first_history = tables[RELATIONSHIP_MANAGER_HISTORY].iloc[[0]].copy()
    first_relationship_id = str(first_history.iloc[0]["banking_relationship_id"])
    latest_effective_from = pd.Timestamp(first_history.iloc[0]["effective_from"]) + pd.Timedelta(
        minutes=30
    )
    first_history.loc[:, "rm_history_id"] = "RMH-9999"
    first_history.loc[:, "relationship_manager_code"] = "RM-999"
    first_history.loc[:, "effective_from"] = latest_effective_from
    tables[RELATIONSHIP_MANAGER_HISTORY] = pd.concat(
        [tables[RELATIONSHIP_MANAGER_HISTORY], first_history],
        ignore_index=True,
    )

    view = build_foundation_progressive_views(tables)["pb_relationship_context"]
    selected_row = view[view["banking_relationship_id"] == first_relationship_id].iloc[0]

    assert len(view) == len(tables[BANKING_RELATIONSHIPS])
    assert selected_row["relationship_manager_code"] == "RM-999"
    assert selected_row["rm_effective_from"] == latest_effective_from


def test_foundation_alert_lifecycle_allows_schema_valid_child_multiplicity() -> None:
    """The Python view builder must match SQLite joins for schema-valid child rows."""
    tables = generate_minimal_banking_world(seed=42)
    original_view = build_foundation_progressive_views(tables)["foundation_alert_lifecycle"]

    extra_alert = tables[ALERTS].iloc[[0]].copy()
    extra_alert.loc[:, "alert_id"] = "alert_extra_multi_001"
    tables[ALERTS] = pd.concat([tables[ALERTS], extra_alert], ignore_index=True)

    extra_case = tables[CASES].iloc[[0]].copy()
    extra_case.loc[:, "case_id"] = "case_extra_multi_001"
    extra_case.loc[:, "alert_id"] = "alert_extra_multi_001"
    second_extra_case = extra_case.copy()
    second_extra_case.loc[:, "case_id"] = "case_extra_multi_002"
    tables[CASES] = pd.concat(
        [tables[CASES], extra_case, second_extra_case],
        ignore_index=True,
    )

    extra_outcome = tables[CASE_OUTCOMES].iloc[[0]].copy()
    extra_outcome.loc[:, "case_outcome_id"] = "outcome_extra_multi_001"
    extra_outcome.loc[:, "case_id"] = "case_extra_multi_001"
    second_extra_outcome = extra_outcome.copy()
    second_extra_outcome.loc[:, "case_outcome_id"] = "outcome_extra_multi_002"
    tables[CASE_OUTCOMES] = pd.concat(
        [tables[CASE_OUTCOMES], extra_outcome, second_extra_outcome],
        ignore_index=True,
    )

    view = build_foundation_progressive_views(tables)["foundation_alert_lifecycle"]

    assert len(view) == len(original_view) + 3
    assert set(view["suspicious_activity_id"]) == set(
        tables[SUSPICIOUS_ACTIVITIES]["suspicious_activity_id"]
    )
    assert "alert_extra_multi_001" in set(view["alert_id"])
    assert "case_extra_multi_001" in set(view["case_id"])
    assert "case_extra_multi_002" in set(view["case_id"])
    assert "outcome_extra_multi_001" in set(view["case_outcome_id"])
    assert "outcome_extra_multi_002" in set(view["case_outcome_id"])


def test_foundation_progressive_view_specs_use_canonical_unprotected_sources() -> None:
    """Foundation Progressive views must be traceable to canonical unprotected tables."""
    for spec in FOUNDATION_PROGRESSIVE_VIEW_SPECS:
        assert set(spec.source_tables) <= set(TABLE_NAMES)
        assert PROTECTED_SCENARIO_ANSWER_KEYS not in spec.source_tables
        assert not (set(spec.columns) & PROTECTED_ANSWER_KEY_COLUMNS)
        assert spec.purpose


def test_foundation_progressive_views_are_documented() -> None:
    """Progressive view docs must describe purpose, sources, and stable references."""
    docs = Path("docs/schema/progressive_views.md").read_text(encoding="utf-8")
    normalized_docs = _normalize(docs)
    schema_readme = Path("docs/schema/README.md").read_text(encoding="utf-8")

    assert "progressive_views.md" in schema_readme
    assert "stable for future v0.5 case-pack cross-references" in docs

    for spec in FOUNDATION_PROGRESSIVE_VIEW_SPECS:
        assert f"## `{spec.name}`" in docs
        assert spec.purpose in normalized_docs
        for source_table in spec.source_tables:
            assert f"`{source_table}`" in docs
        for column_name in spec.columns:
            assert f"`{column_name}`" in docs


def _normalize(markdown: str) -> str:
    """Collapse Markdown whitespace for resilient documentation assertions."""
    return " ".join(markdown.split())
