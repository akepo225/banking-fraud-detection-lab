"""Frozen production-monitoring table vocabulary for the v0.8 tracer bullet.

Mirrors the frozen-spec precedent set by :mod:`banking_fraud_lab.schema`
(``PatternSpec`` / ``PATTERN_IDS``), :mod:`banking_fraud_lab.graph.features_spec`
(``GraphFeatureFamilySpec``), :mod:`banking_fraud_lab.governance.spec`
(``ModelDocumentationSectionSpec``), and :mod:`banking_fraud_lab.interpretability.spec`.

This module defines the five production-monitoring tables that record how a
fraud-detection model behaves after deployment: ``score`` (the per-entity model
score that feeds an alert decision for a Detection pattern, scoped to a Banking
relationship / Client / User), ``threshold`` (the score threshold applied to
produce alert decisions), ``alert_decision`` (applying a threshold to a score
yields the alert decision in the Alert lifecycle), ``reviewer_action`` (a human
reviewer's action on an alert decision in the Alert lifecycle), and
``audit_event`` (the immutable audit trail that ties scores, decisions, reviewer
actions, and thresholds back to Client / User / Banking relationship / Detection
pattern lineage).

Each table is declared as a frozen :class:`MonitoringTableSpec` whose lineage
keys are physical schema columns only, whose Detection-pattern coverage is a
subset of the schema's ``PATTERN_IDS``, and whose monitoring-checklist
dimensions are a subset of the governance ``MONITORING_CHECKLIST_DIMENSION_IDS``.
A module-load integrity guard re-validates those references so the vocabulary
cannot drift from its upstream dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass

from banking_fraud_lab.governance import MONITORING_CHECKLIST_DIMENSION_IDS
from banking_fraud_lab.schema import COLUMN_NAMES, PATTERN_IDS, ColumnSpec


@dataclass(frozen=True)
class MonitoringTableSpec:
    """Structured metadata for one frozen production-monitoring table."""

    table_id: str
    display_name: str
    description: str
    columns: tuple[ColumnSpec, ...]
    lineage_keys: tuple[str, ...]
    detection_pattern_ids: tuple[str, ...]
    monitoring_dimension_ids: tuple[str, ...] = ()


SCORE = MonitoringTableSpec(
    table_id="score",
    display_name="Alert score",
    description=(
        "Holds the per-entity model score that feeds an alert decision for a "
        "Detection pattern, scoped to a Banking relationship / Client / User. "
        "Score drift and data quality are watched against this table."
    ),
    columns=(
        ColumnSpec("score_id", "string", False, "Stable monitoring score identifier."),
        ColumnSpec(
            "detection_pattern_id",
            "string",
            False,
            "Detection pattern the score is computed for.",
        ),
        ColumnSpec(
            "banking_relationship_id",
            "string",
            False,
            "Banking relationship the scored entity belongs to.",
            references="banking_relationships.banking_relationship_id",
        ),
        ColumnSpec(
            "client_id",
            "string",
            True,
            "Client linked to the score, where applicable.",
            references="clients.client_id",
        ),
        ColumnSpec(
            "user_id",
            "string",
            True,
            "Digital login User linked to the score, where applicable.",
            references="users.user_id",
        ),
        ColumnSpec(
            "account_id",
            "string",
            True,
            "Account the score is anchored to, where applicable.",
            references="accounts.account_id",
        ),
        ColumnSpec(
            "transaction_id",
            "string",
            True,
            "Transaction the score is anchored to, where applicable.",
            references="transactions.transaction_id",
        ),
        ColumnSpec(
            "alert_id",
            "string",
            True,
            "Alert raised from this score, where applicable.",
            references="alerts.alert_id",
        ),
        ColumnSpec("scored_at", "datetime64[ns]", False, "Timestamp the score was produced."),
        ColumnSpec("score", "float64", False, "Model fraud-propensity score."),
        ColumnSpec("scorer", "string", False, "Identifier of the scorer that produced the score."),
        ColumnSpec(
            "score_version",
            "string",
            False,
            "Version of the scorer/model that produced the score.",
        ),
    ),
    lineage_keys=(
        "banking_relationship_id",
        "client_id",
        "user_id",
        "account_id",
        "transaction_id",
        "alert_id",
    ),
    detection_pattern_ids=PATTERN_IDS,
    monitoring_dimension_ids=("score_drift", "data_quality"),
)


THRESHOLD = MonitoringTableSpec(
    table_id="threshold",
    display_name="Score threshold",
    description=(
        "Holds the score threshold applied to produce alert decisions. Each "
        "threshold records its selection/review provenance, tying it to the v0.7 "
        "threshold recommender and evaluate_alert_scores so a reviewer can see "
        "how a value was chosen and when it was superseded."
    ),
    columns=(
        ColumnSpec("threshold_id", "string", False, "Stable monitoring threshold identifier."),
        ColumnSpec(
            "detection_pattern_id",
            "string",
            False,
            "Detection pattern the threshold applies to.",
        ),
        ColumnSpec(
            "threshold_value",
            "float64",
            False,
            "Score value at or above which an alert decision is raised.",
        ),
        ColumnSpec("selected_at", "datetime64[ns]", False, "Timestamp the threshold was selected."),
        ColumnSpec(
            "selection_method",
            "string",
            False,
            "How the threshold was chosen (e.g. cost-optimal alert capacity).",
        ),
        ColumnSpec(
            "review_status",
            "string",
            False,
            "Lifecycle status such as active or superseded.",
        ),
        ColumnSpec(
            "evidence_ref",
            "string",
            False,
            "Pointer to the evaluation artifact supporting the threshold.",
        ),
    ),
    lineage_keys=(),
    detection_pattern_ids=PATTERN_IDS,
    monitoring_dimension_ids=(),
)


ALERT_DECISION = MonitoringTableSpec(
    table_id="alert_decision",
    display_name="Alert decision",
    description=(
        "Applying a threshold to a score yields the alert decision in the Alert "
        "lifecycle, scoped to a Banking relationship / Client / User. The "
        "decision records the score value at the moment the decision was made."
    ),
    columns=(
        ColumnSpec(
            "alert_decision_id",
            "string",
            False,
            "Stable monitoring alert-decision identifier.",
        ),
        ColumnSpec(
            "score_id",
            "string",
            False,
            "Score the decision was made from.",
            references="score.score_id",
        ),
        ColumnSpec(
            "threshold_id",
            "string",
            False,
            "Threshold applied to the score.",
            references="threshold.threshold_id",
        ),
        ColumnSpec(
            "detection_pattern_id",
            "string",
            False,
            "Detection pattern the decision concerns.",
        ),
        ColumnSpec(
            "banking_relationship_id",
            "string",
            False,
            "Banking relationship linked to the decision.",
            references="banking_relationships.banking_relationship_id",
        ),
        ColumnSpec(
            "client_id",
            "string",
            True,
            "Client linked to the decision, where applicable.",
            references="clients.client_id",
        ),
        ColumnSpec(
            "user_id",
            "string",
            True,
            "Digital login User linked to the decision, where applicable.",
            references="users.user_id",
        ),
        ColumnSpec(
            "account_id",
            "string",
            True,
            "Account linked to the decision.",
            references="accounts.account_id",
        ),
        ColumnSpec(
            "transaction_id",
            "string",
            True,
            "Transaction linked to the decision.",
            references="transactions.transaction_id",
        ),
        ColumnSpec(
            "alert_id",
            "string",
            True,
            "Alert raised by this decision, where applicable.",
            references="alerts.alert_id",
        ),
        ColumnSpec("decided_at", "datetime64[ns]", False, "Timestamp the decision was made."),
        ColumnSpec(
            "decision",
            "string",
            False,
            "Decision outcome such as alert or suppress.",
        ),
        ColumnSpec(
            "score_at_decision",
            "float64",
            False,
            "Score value at the moment the decision was made.",
        ),
    ),
    lineage_keys=(
        "banking_relationship_id",
        "client_id",
        "user_id",
        "account_id",
        "transaction_id",
        "alert_id",
    ),
    detection_pattern_ids=PATTERN_IDS,
    monitoring_dimension_ids=(),
)


REVIEWER_ACTION = MonitoringTableSpec(
    table_id="reviewer_action",
    display_name="Reviewer action",
    description=(
        "Records a human reviewer's action on an alert decision in the Alert "
        "lifecycle, scoped to a Banking relationship / Client / User. Each row "
        "carries a learner-readable rationale so the action can be audited."
    ),
    columns=(
        ColumnSpec(
            "reviewer_action_id",
            "string",
            False,
            "Stable monitoring reviewer-action identifier.",
        ),
        ColumnSpec(
            "alert_decision_id",
            "string",
            False,
            "Alert decision the reviewer acted on.",
            references="alert_decision.alert_decision_id",
        ),
        ColumnSpec(
            "alert_id",
            "string",
            True,
            "Alert the reviewer action concerns, where applicable.",
            references="alerts.alert_id",
        ),
        ColumnSpec(
            "banking_relationship_id",
            "string",
            False,
            "Banking relationship linked to the reviewer action.",
            references="banking_relationships.banking_relationship_id",
        ),
        ColumnSpec(
            "client_id",
            "string",
            True,
            "Client linked to the reviewer action, where applicable.",
            references="clients.client_id",
        ),
        ColumnSpec(
            "user_id",
            "string",
            True,
            "Digital login User linked to the reviewer action, where applicable.",
            references="users.user_id",
        ),
        ColumnSpec(
            "account_id",
            "string",
            True,
            "Account linked to the reviewer action.",
            references="accounts.account_id",
        ),
        ColumnSpec(
            "transaction_id",
            "string",
            True,
            "Transaction linked to the reviewer action.",
            references="transactions.transaction_id",
        ),
        ColumnSpec("reviewer", "string", False, "Identifier of the reviewer."),
        ColumnSpec(
            "reviewed_at",
            "datetime64[ns]",
            False,
            "Timestamp the reviewer action was recorded.",
        ),
        ColumnSpec(
            "action",
            "string",
            False,
            "Reviewer action such as confirm, dismiss, or escalate.",
        ),
        ColumnSpec(
            "rationale",
            "string",
            False,
            "Learner-readable reason for the reviewer action.",
        ),
        ColumnSpec(
            "evidence",
            "string",
            True,
            "v0.7 interpretability summary (e.g. explain_feature_family / "
            "extract_feature_importance output) supporting the action, where applicable.",
        ),
    ),
    lineage_keys=(
        "banking_relationship_id",
        "client_id",
        "user_id",
        "account_id",
        "transaction_id",
        "alert_id",
    ),
    detection_pattern_ids=PATTERN_IDS,
    monitoring_dimension_ids=(),
)


AUDIT_EVENT = MonitoringTableSpec(
    table_id="audit_event",
    display_name="Audit event",
    description=(
        "The immutable audit trail that ties scores, decisions, reviewer "
        "actions, and thresholds back to Client / User / Banking relationship / "
        "Detection pattern lineage so every operational step can be reconstructed."
    ),
    columns=(
        ColumnSpec(
            "audit_event_id",
            "string",
            False,
            "Stable monitoring audit-event identifier.",
        ),
        ColumnSpec(
            "audit_event_type",
            "string",
            False,
            "Type of audit event (one of AUDIT_EVENT_TYPES).",
        ),
        ColumnSpec(
            "score_id",
            "string",
            True,
            "Score referenced by the event, where applicable.",
            references="score.score_id",
        ),
        ColumnSpec(
            "alert_decision_id",
            "string",
            True,
            "Alert decision referenced by the event, where applicable.",
            references="alert_decision.alert_decision_id",
        ),
        ColumnSpec(
            "reviewer_action_id",
            "string",
            True,
            "Reviewer action referenced by the event, where applicable.",
            references="reviewer_action.reviewer_action_id",
        ),
        ColumnSpec(
            "threshold_id",
            "string",
            True,
            "Threshold referenced by the event, where applicable.",
            references="threshold.threshold_id",
        ),
        ColumnSpec(
            "detection_pattern_id",
            "string",
            False,
            "Detection pattern the event concerns.",
        ),
        ColumnSpec(
            "banking_relationship_id",
            "string",
            True,
            "Banking relationship linked to the event.",
            references="banking_relationships.banking_relationship_id",
        ),
        ColumnSpec(
            "client_id",
            "string",
            True,
            "Client linked to the event, where applicable.",
            references="clients.client_id",
        ),
        ColumnSpec(
            "user_id",
            "string",
            True,
            "Digital login User linked to the event, where applicable.",
            references="users.user_id",
        ),
        ColumnSpec(
            "account_id",
            "string",
            True,
            "Account linked to the event.",
            references="accounts.account_id",
        ),
        ColumnSpec(
            "transaction_id",
            "string",
            True,
            "Transaction linked to the event.",
            references="transactions.transaction_id",
        ),
        ColumnSpec(
            "alert_id",
            "string",
            True,
            "Alert linked to the event.",
            references="alerts.alert_id",
        ),
        ColumnSpec("occurred_at", "datetime64[ns]", False, "Timestamp the audit event occurred."),
        ColumnSpec("detail", "string", False, "Learner-readable audit detail."),
    ),
    lineage_keys=(
        "banking_relationship_id",
        "client_id",
        "user_id",
        "account_id",
        "transaction_id",
        "alert_id",
    ),
    detection_pattern_ids=PATTERN_IDS,
    monitoring_dimension_ids=(),
)


MONITORING_TABLES: tuple[MonitoringTableSpec, ...] = (
    SCORE,
    THRESHOLD,
    ALERT_DECISION,
    REVIEWER_ACTION,
    AUDIT_EVENT,
)

MONITORING_TABLE_IDS: tuple[str, ...] = tuple(t.table_id for t in MONITORING_TABLES)


# --- Audit-event type vocabulary -------------------------------------------
# The four audit-event types cover the operational steps the monitoring tables
# record: a score is assigned, a threshold is applied to make an alert decision,
# a reviewer acts on that decision, and a threshold is periodically reviewed.

AUDIT_SCORE_ASSIGNED = "score_assigned"
AUDIT_ALERT_DECISION_MADE = "alert_decision_made"
AUDIT_REVIEWER_ACTION_RECORDED = "reviewer_action_recorded"
AUDIT_THRESHOLD_REVIEWED = "threshold_reviewed"

AUDIT_EVENT_TYPES: tuple[str, ...] = (
    AUDIT_SCORE_ASSIGNED,
    AUDIT_ALERT_DECISION_MADE,
    AUDIT_REVIEWER_ACTION_RECORDED,
    AUDIT_THRESHOLD_REVIEWED,
)

#: Audit-event types as a set, for membership checks during audit building.
AUDIT_EVENT_TYPE_IDS: frozenset[str] = frozenset(AUDIT_EVENT_TYPES)


# --- Module-load integrity guard -------------------------------------------
# Reusable validator so tests can call it with a bad spec; mirrors the module-
# load guard in graph/features_spec.py but as a function.


def _validate_monitoring_tables(tables: tuple[MonitoringTableSpec, ...]) -> None:
    """Raise ValueError if any lineage key, pattern id, or dimension id is unknown."""
    physical_columns: set[str] = set()
    for cols in COLUMN_NAMES.values():
        physical_columns.update(cols)
    for table in tables:
        bad_keys = sorted(k for k in table.lineage_keys if k not in physical_columns)
        if bad_keys:
            raise ValueError(
                f"Monitoring table {table.table_id!r} lineage keys are not real schema "
                f"columns: {bad_keys}"
            )
        bad_patterns = sorted(p for p in table.detection_pattern_ids if p not in PATTERN_IDS)
        if bad_patterns:
            raise ValueError(
                f"Monitoring table {table.table_id!r} references unknown Detection pattern "
                f"ids: {bad_patterns}"
            )
        bad_dims = sorted(
            d
            for d in table.monitoring_dimension_ids
            if d not in MONITORING_CHECKLIST_DIMENSION_IDS
        )
        if bad_dims:
            raise ValueError(
                f"Monitoring table {table.table_id!r} references unknown monitoring "
                f"checklist dimension ids: {bad_dims}"
            )


_validate_monitoring_tables(MONITORING_TABLES)


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
