"""Tests for foundation-level Progressive data views."""

from pathlib import Path

from banking_fraud_lab import generate_minimal_banking_world
from banking_fraud_lab.progressive_views import (
    FOUNDATION_PROGRESSIVE_VIEW_SPECS,
    build_foundation_progressive_views,
)
from banking_fraud_lab.schema import COLUMN_NAMES, PROTECTED_SCENARIO_ANSWER_KEYS, TABLE_NAMES


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
