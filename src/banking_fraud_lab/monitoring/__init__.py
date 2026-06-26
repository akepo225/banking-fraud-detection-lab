"""Frozen production-monitoring table vocabulary for the v0.8 tracer bullet.

Mirrors the frozen-spec facade precedent of :mod:`banking_fraud_lab.governance`.
The frozen table vocabulary (score, threshold, alert_decision, reviewer_action,
audit_event) and the audit-event type vocabulary live in :mod:`.spec`; future
deterministic builders (batch scoring, alert-decision/reviewer/audit rows,
drift and data-quality checks) will live in their own submodules.
"""

from __future__ import annotations

from banking_fraud_lab.monitoring.spec import (
    ALERT_DECISION,
    AUDIT_ALERT_DECISION_MADE,
    AUDIT_EVENT,
    AUDIT_EVENT_TYPE_IDS,
    AUDIT_EVENT_TYPES,
    AUDIT_REVIEWER_ACTION_RECORDED,
    AUDIT_SCORE_ASSIGNED,
    AUDIT_THRESHOLD_REVIEWED,
    MonitoringTableSpec,
    MONITORING_TABLES,
    MONITORING_TABLE_IDS,
    REVIEWER_ACTION,
    SCORE,
    THRESHOLD,
)

__all__ = [
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
]
