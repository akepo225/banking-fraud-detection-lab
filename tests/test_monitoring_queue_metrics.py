"""Tests for the alert-queue inspection and operational-metrics builders (v0.8 Wave 4).

Covers :func:`banking_fraud_lab.monitoring.inspect_alert_queue` (mirrors the
``04_progressive_alert_queue.sql`` severity -> generated_at -> alert_id ranking)
and :func:`banking_fraud_lab.monitoring.summarise_alert_operations` (which REUSES
the v0.7 ``evaluate_alert_scores`` precision/recall and the v0.1 ``alert_capacity``
convention rather than recomputing them).
"""

from __future__ import annotations

import pandas as pd

from banking_fraud_lab.evaluation import evaluate_alert_scores
from banking_fraud_lab.monitoring import inspect_alert_queue, summarise_alert_operations

_DEFAULT_NOW = pd.Timestamp("2024-01-02T06:00:00")


def _queue_decision_rows() -> pd.DataFrame:
    """Return decision rows enriched with alert-lifecycle columns, mixed severities."""
    return pd.DataFrame(
        {
            "alert_id": ["AL-1", "AL-2", "AL-3", "AL-4", "AL-5"],
            "institution_name": [
                "Alpine Crest Private Bank",
                "Alpine Crest Private Bank",
                "Alpine Crest Private Bank",
                "NovaBank Digital",
                "Alpine Crest Private Bank",
            ],
            "banking_relationship_id": ["BR-1", "BR-1", "BR-2", "BR-9", "BR-3"],
            "client_id": ["CL-1", "CL-2", None, "CL-9", "CL-4"],
            "user_id": [None, "U-2", None, "U-9", None],
            "account_id": ["AC-1", "AC-2", "AC-3", "AC-9", "AC-5"],
            "transaction_id": ["TX-1", "TX-2", "TX-3", "TX-9", "TX-5"],
            "detection_pattern_id": [
                "pb_high_value_movement",
                "pb_high_value_movement",
                "pb_structuring_indicator",
                "nb_session_anomaly",
                "pb_high_value_movement",
            ],
            "severity": ["low", "medium", "high", "high", "high"],
            "alert_status": ["open", "open", "open", "closed", "escalated"],
            "generated_at": pd.to_datetime(
                [
                    "2024-01-01T00:00:00",
                    "2024-01-01T01:00:00",
                    "2024-01-01T02:00:00",
                    "2024-01-01T03:00:00",
                    "2024-01-01T02:00:00",
                ]
            ),
        }
    )


def test_inspect_alert_queue_ranks_severity_then_age() -> None:
    """Queue rank is severity -> generated_at -> alert_id, mirroring the SQL example."""
    queue = inspect_alert_queue(
        _queue_decision_rows(),
        institution="Alpine Crest Private Bank",
        now=_DEFAULT_NOW,
    )

    # High severity first (AL-3 and AL-5 share severity + generated_at -> alert_id breaks tie).
    assert queue["alert_queue_rank"].tolist() == [1, 2, 3, 4]
    assert queue["alert_id"].tolist() == ["AL-3", "AL-5", "AL-2", "AL-1"]

    # alert_age_hours computed from now - generated_at, rounded to 2 decimals.
    assert queue.loc[queue["alert_id"] == "AL-1", "alert_age_hours"].iloc[0] == 30.0
    assert queue.loc[queue["alert_id"] == "AL-3", "alert_age_hours"].iloc[0] == 28.0

    # Lineage columns carried through (banking_relationship_id always, client/user when present).
    assert queue["banking_relationship_id"].tolist() == ["BR-2", "BR-3", "BR-1", "BR-1"]
    assert queue["detection_pattern_id"].tolist() == [
        "pb_structuring_indicator",
        "pb_high_value_movement",
        "pb_high_value_movement",
        "pb_high_value_movement",
    ]
    assert queue.loc[queue["alert_id"] == "AL-2", "client_id"].iloc[0] == "CL-2"
    assert queue.loc[queue["alert_id"] == "AL-2", "user_id"].iloc[0] == "U-2"
    assert pd.isna(queue.loc[queue["alert_id"] == "AL-3", "client_id"].iloc[0])


def test_inspect_alert_queue_filters_by_institution_and_deterministic() -> None:
    """Only rows for the requested institution appear; repeated calls are identical."""
    rows = _queue_decision_rows()
    first = inspect_alert_queue(rows, institution="NovaBank Digital", now=_DEFAULT_NOW)
    second = inspect_alert_queue(rows, institution="NovaBank Digital", now=_DEFAULT_NOW)

    assert first["alert_id"].tolist() == ["AL-4"]
    pd.testing.assert_frame_equal(first, second)

    # Case-insensitive match works.
    mixed = inspect_alert_queue(rows, institution="novabank digital", now=_DEFAULT_NOW)
    pd.testing.assert_frame_equal(mixed, first)


def _tiny_evaluation_report() -> dict:
    """Build a tiny evaluate_alert_scores report over synthetic cases/outcomes/scores."""
    cases = pd.DataFrame(
        {
            "case_id": ["CASE-1", "CASE-2", "CASE-3", "CASE-4"],
            "alert_id": ["AL-1", "AL-2", "AL-3", "AL-4"],
        }
    )
    case_outcomes = pd.DataFrame(
        {
            "case_id": ["CASE-1", "CASE-2", "CASE-3", "CASE-4"],
            "confirmed_fraud": [True, False, True, False],
        }
    )
    alert_scores = pd.DataFrame(
        {
            "alert_id": ["AL-1", "AL-2", "AL-3", "AL-4"],
            "score": [0.9, 0.8, 0.4, 0.1],
        }
    )
    return evaluate_alert_scores(
        cases,
        case_outcomes,
        alert_scores,
        thresholds=(0.75,),
        alert_capacity=2,
    )


def test_summarise_alert_operations_reuses_evaluation() -> None:
    """precision/recall come verbatim from evaluation['lowest_cost_summary']; no recompute."""
    report = _tiny_evaluation_report()
    summary = report["lowest_cost_summary"]

    decision_rows = pd.DataFrame(
        {
            "alert_id": ["AL-1", "AL-2", "AL-3", "AL-4"],
            "institution_name": [
                "Alpine Crest Private Bank",
                "Alpine Crest Private Bank",
                "Alpine Crest Private Bank",
                "Alpine Crest Private Bank",
            ],
            "decision": ["alert", "alert", "suppress", "suppress"],
            "alert_status": ["open", "open", "closed", "closed"],
            "detection_pattern_id": [
                "pb_high_value_movement",
                "pb_high_value_movement",
                "pb_structuring_indicator",
                "pb_structuring_indicator",
            ],
        }
    )

    metrics = summarise_alert_operations(
        decision_rows,
        alert_capacity=2,
        evaluation=report,
    )

    assert metrics["precision"] == summary["precision"]
    assert metrics["recall"] == summary["recall"]
    assert metrics["alert_volume"] == 2
    assert metrics["alert_capacity"] == 2
    assert metrics["capacity_utilization"] == round(2 / 2, 4)
    assert metrics["closure_distribution"] == {"open": 2, "closed": 2}
    assert metrics["detection_pattern_ids"] == [
        "pb_high_value_movement",
        "pb_structuring_indicator",
    ]
    assert metrics["institution"] == "Alpine Crest Private Bank"


def test_summarise_alert_operations_precision_from_labels() -> None:
    """Without evaluation, precision/recall are computed from confirmed_fraud labels."""
    decision_rows = pd.DataFrame(
        {
            "alert_id": ["AL-1", "AL-2", "AL-3", "AL-4"],
            "decision": ["alert", "alert", "suppress", "suppress"],
            "confirmed_fraud": [True, False, True, False],
        }
    )

    metrics = summarise_alert_operations(decision_rows, alert_capacity=4)

    # alerted: AL-1 (TP), AL-2 (FP); missed: AL-3 (FN). precision = 1/2, recall = 1/2.
    assert metrics["precision"] == 0.5
    assert metrics["recall"] == 0.5
    assert metrics["alert_volume"] == 2


def test_capacity_utilization_against_v0_1_convention() -> None:
    """capacity_utilization == round(alert_volume / alert_capacity, 4), the v0.1 convention."""
    decision_rows = pd.DataFrame(
        {
            "decision": ["alert", "alert", "alert", "suppress"],
            "institution_name": ["NovaBank Digital"] * 4,
        }
    )
    metrics = summarise_alert_operations(decision_rows, alert_capacity=7)
    assert metrics["alert_volume"] == 3
    assert metrics["alert_capacity"] == 7
    assert metrics["capacity_utilization"] == round(3 / 7, 4)
