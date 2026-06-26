"""Tests for the v0.8 frozen production-monitoring table vocabulary.

Covers the five monitoring tables (score, threshold, alert_decision,
reviewer_action, audit_event), their lineage into the physical schema, the
Detection-pattern coverage, the audit-event type vocabulary, and the
module-load integrity guard.
"""

from __future__ import annotations

import dataclasses
from dataclasses import FrozenInstanceError

import pytest

import banking_fraud_lab.monitoring as m
from banking_fraud_lab.governance import MONITORING_CHECKLIST_DIMENSION_IDS
from banking_fraud_lab.monitoring import (
    ALERT_DECISION,
    AUDIT_EVENT,
    AUDIT_EVENT_TYPES,
    MONITORING_TABLES,
    MONITORING_TABLE_IDS,
    REVIEWER_ACTION,
    SCORE,
    THRESHOLD,
    MonitoringTableSpec,
)
from banking_fraud_lab.monitoring.spec import _validate_monitoring_tables
from banking_fraud_lab.schema import COLUMN_NAMES, PATTERN_IDS


def test_five_monitoring_tables_exist() -> None:
    """The five v0.8 monitoring tables must be present in order."""
    assert MONITORING_TABLE_IDS == (
        "score",
        "threshold",
        "alert_decision",
        "reviewer_action",
        "audit_event",
    )


def test_table_specs_are_frozen() -> None:
    """Each monitoring table spec must be a frozen dataclass."""
    for table in MONITORING_TABLES:
        assert dataclasses.is_dataclass(table)
        assert dataclasses.is_dataclass(type(table))
        assert getattr(table.__dataclass_params__, "frozen", False) is True
        with pytest.raises(FrozenInstanceError):
            table.table_id = "mutated"  # type: ignore[misc]


def test_lineage_keys_resolve_to_real_schema_columns() -> None:
    """Every lineage key must be a real physical schema column name."""
    physical_columns: set[str] = set()
    for cols in COLUMN_NAMES.values():
        physical_columns.update(cols)
    for table in MONITORING_TABLES:
        for key in table.lineage_keys:
            assert key in physical_columns, f"{table.table_id}: {key!r} not a schema column"


def test_relationship_tables_carry_client_and_user_lineage() -> None:
    """Relationship-bearing tables must trace directly to Client and User.

    A Banking relationship alone cannot reach a digital User, so the score,
    alert_decision, reviewer_action, and audit_event tables must each carry
    ``client_id`` and ``user_id`` lineage keys (PRD user story 7 and the #202
    score-to-audit walk-back both require it).
    """
    for table in (SCORE, ALERT_DECISION, REVIEWER_ACTION, AUDIT_EVENT):
        assert "client_id" in table.lineage_keys, f"{table.table_id} missing client_id lineage"
        assert "user_id" in table.lineage_keys, f"{table.table_id} missing user_id lineage"
    assert "client_id" not in THRESHOLD.lineage_keys
    assert "user_id" not in THRESHOLD.lineage_keys


def test_detection_pattern_coverage_is_valid() -> None:
    """Every declared Detection-pattern id must be a known PATTERN_IDS entry."""
    for table in MONITORING_TABLES:
        assert table.detection_pattern_ids
        for pattern_id in table.detection_pattern_ids:
            assert pattern_id in PATTERN_IDS, (
                f"{table.table_id}: {pattern_id!r} not in PATTERN_IDS"
            )


def test_score_table_carries_drift_and_data_quality_dimensions() -> None:
    """The score table must carry score_drift and data_quality dimensions."""
    assert SCORE.monitoring_dimension_ids == ("score_drift", "data_quality")
    for dimension_id in SCORE.monitoring_dimension_ids:
        assert dimension_id in MONITORING_CHECKLIST_DIMENSION_IDS


def test_guard_rejects_unknown_lineage_key() -> None:
    """The guard must reject a lineage key that is not a real schema column."""
    bad = MonitoringTableSpec(
        table_id="bad",
        display_name="Bad",
        description="Bad spec.",
        columns=(),
        lineage_keys=("not_a_real_column",),
        detection_pattern_ids=(),
        monitoring_dimension_ids=(),
    )
    with pytest.raises(ValueError, match="lineage keys"):
        _validate_monitoring_tables((bad,))


def test_guard_rejects_unknown_pattern_id() -> None:
    """The guard must reject an unknown Detection-pattern id."""
    bad = MonitoringTableSpec(
        table_id="bad",
        display_name="Bad",
        description="Bad spec.",
        columns=(),
        lineage_keys=(),
        detection_pattern_ids=("not_a_pattern",),
        monitoring_dimension_ids=(),
    )
    with pytest.raises(ValueError, match="Detection pattern"):
        _validate_monitoring_tables((bad,))


def test_guard_rejects_unknown_dimension_id() -> None:
    """The guard must reject an unknown monitoring-checklist dimension id."""
    bad = MonitoringTableSpec(
        table_id="bad",
        display_name="Bad",
        description="Bad spec.",
        columns=(),
        lineage_keys=(),
        detection_pattern_ids=(),
        monitoring_dimension_ids=("not_a_dimension",),
    )
    with pytest.raises(ValueError, match="dimension"):
        _validate_monitoring_tables((bad,))


def test_guard_accepts_valid_tables() -> None:
    """The guard must accept the shipped MONITORING_TABLES tuple."""
    assert _validate_monitoring_tables(MONITORING_TABLES) is None


def test_relationship_bearing_tables_use_glossary_terms() -> None:
    """Relationship-bearing tables must use the Client/User/Banking relationship glossary."""
    for table in (SCORE, ALERT_DECISION, REVIEWER_ACTION, AUDIT_EVENT):
        assert "Client" in table.description, f"{table.table_id} missing 'Client'"
        assert "User" in table.description, f"{table.table_id} missing 'User'"
        assert "Banking relationship" in table.description, (
            f"{table.table_id} missing 'Banking relationship'"
        )


def test_audit_event_vocabulary() -> None:
    """The audit-event type vocabulary must be the four expected types in order."""
    assert AUDIT_EVENT_TYPES == (
        "score_assigned",
        "alert_decision_made",
        "reviewer_action_recorded",
        "threshold_reviewed",
    )
    assert isinstance(m.AUDIT_EVENT_TYPE_IDS, frozenset)
    assert m.AUDIT_EVENT_TYPE_IDS == set(AUDIT_EVENT_TYPES)


def test_public_facade_reexports() -> None:
    """The package facade must re-export every public monitoring symbol."""
    expected = {
        "ALERT_DECISION",
        "AUDIT_ALERT_DECISION_MADE",
        "AUDIT_EVENT",
        "AUDIT_EVENT_TYPE_IDS",
        "AUDIT_EVENT_TYPES",
        "AUDIT_REVIEWER_ACTION_RECORDED",
        "AUDIT_SCORE_ASSIGNED",
        "AUDIT_THRESHOLD_REVIEWED",
        "MonitoringTableSpec",
        "MONITORING_TABLES",
        "MONITORING_TABLE_IDS",
        "REVIEWER_ACTION",
        "SCORE",
        "THRESHOLD",
    }
    for name in expected:
        assert hasattr(m, name), f"banking_fraud_lab.monitoring missing {name!r}"
    assert ALERT_DECISION is m.ALERT_DECISION
    assert AUDIT_EVENT is m.AUDIT_EVENT
    assert REVIEWER_ACTION is m.REVIEWER_ACTION
    assert SCORE is m.SCORE
    assert THRESHOLD is m.THRESHOLD
