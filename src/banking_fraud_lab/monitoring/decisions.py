"""Alert-decision, reviewer-action, and audit-event monitoring builders.

These builders materialize ``alert_decision`` + ``reviewer_action`` +
``audit_event`` monitoring rows from score rows, carrying Client / User / Banking
relationship / Detection-pattern lineage through the whole chain and emitting an
immutable audit event per state transition. They reuse the #200 frozen table
vocabulary (:mod:`banking_fraud_lab.monitoring.spec`) and the v0.7
interpretability summaries (:mod:`banking_fraud_lab.interpretability.explanations`)
for reviewer-action evidence.

Glossary terms are used verbatim where natural: each decision / action is scoped
to a Banking relationship and carries Client / User lineage; the Detection
pattern and Alert lifecycle vocabulary are reused unchanged.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from banking_fraud_lab.monitoring.spec import (
    ALERT_DECISION,
    AUDIT_ALERT_DECISION_MADE,
    AUDIT_EVENT,
    AUDIT_REVIEWER_ACTION_RECORDED,
    REVIEWER_ACTION,
)
from banking_fraud_lab.schema import PATTERN_IDS

_OPTIONAL_LINEAGE_COLUMNS: tuple[str, ...] = (
    "client_id",
    "user_id",
    "account_id",
    "transaction_id",
    "alert_id",
)

_DEFAULT_TIMESTAMP_BASE = pd.Timestamp("2024-01-01")


@dataclass(frozen=True)
class AlertDecisionResult:
    """Alert-decision builder output: alert_decision rows + their audit events."""

    alert_decision_rows: "pd.DataFrame"
    audit_rows: "pd.DataFrame"


@dataclass(frozen=True)
class ReviewerActionResult:
    """Reviewer-action builder output: reviewer_action rows + their audit events."""

    reviewer_action_rows: "pd.DataFrame"
    audit_rows: "pd.DataFrame"


def decide_alerts(
    score_rows: "pd.DataFrame",
    *,
    threshold: float,
    threshold_id: str,
    seed: int = 42,
    decided_at: "pd.Timestamp | None" = None,
) -> AlertDecisionResult:
    """Apply a threshold to score rows, writing alert_decision rows + audit events.

    For each score row: ``decision = 'alert'`` when ``score >= threshold`` else
    ``'suppress'``. Each alert_decision row carries forward the score row's
    lineage (banking_relationship_id, client_id, user_id, account_id,
    transaction_id, alert_id) and detection_pattern_id, records the score_id +
    threshold_id + score_at_decision, and gets a deterministic
    alert_decision_id. One audit_event row (type
    :data:`~banking_fraud_lab.monitoring.spec.AUDIT_ALERT_DECISION_MADE`) is
    emitted per decision, referencing the score_id + alert_decision_id +
    threshold_id + lineage, with occurred_at strictly increasing across the
    batch.

    Args:
        score_rows: Score monitoring rows (one per scored entity). REQUIRED
            columns: ``score_id``, ``score``, ``banking_relationship_id``,
            ``detection_pattern_id``. OPTIONAL lineage columns carried through
            when present: ``client_id``, ``user_id``, ``account_id``,
            ``transaction_id``, ``alert_id``.
        threshold: Score value at or above which an alert decision is raised.
            Must be in ``(0.0, 1.0]``.
        threshold_id: Stable identifier of the threshold being applied; must be
            non-empty.
        seed: Drives the deterministic ids and the default decided_at timestamp.
        decided_at: Decision timestamp. If ``None``, defaults to a seed-derived
            deterministic timestamp (each row gets a strictly increasing offset).

    Returns:
        An :class:`AlertDecisionResult` whose ``alert_decision_rows`` conform
        exactly to :data:`banking_fraud_lab.monitoring.ALERT_DECISION` and whose
        ``audit_rows`` conform exactly to
        :data:`banking_fraud_lab.monitoring.AUDIT_EVENT`.

    Raises:
        ValueError: If ``threshold`` is outside ``(0.0, 1.0]``; if ``score_rows``
            is missing a required column; if any ``detection_pattern_id`` value is
            not in :data:`banking_fraud_lab.schema.PATTERN_IDS`; or if
            ``threshold_id`` is empty.
    """
    threshold = _validate_threshold(threshold)
    _validate_threshold_id(threshold_id)
    _validate_score_rows(score_rows)

    resolved_decided_at = _resolve_timestamp(decided_at, seed)

    decisions = _build_alert_decision_rows(
        score_rows,
        threshold=threshold,
        threshold_id=threshold_id,
        decided_at=resolved_decided_at,
        seed=seed,
    )
    audit_rows = _build_decision_audit_rows(
        decisions,
        threshold_id=threshold_id,
        seed=seed,
    )
    return AlertDecisionResult(alert_decision_rows=decisions, audit_rows=audit_rows)


def record_reviewer_action(
    alert_decision_rows: "pd.DataFrame",
    *,
    reviewer: str,
    action: str,
    rationale: str,
    evidence: "dict[str, Any] | str | None" = None,
    seed: int = 42,
    reviewed_at: "pd.Timestamp | None" = None,
) -> ReviewerActionResult:
    """Record a reviewer action per alert_decision row + emit audit events.

    One reviewer_action row per alert_decision row, carrying forward lineage +
    detection_pattern_id + alert_decision_id (+ score_id when present on the
    decision row), with a deterministic reviewer_action_id, reviewer,
    reviewed_at, action, rationale, and evidence. ``evidence`` embeds a v0.7
    interpretability summary: when a dict is passed it is JSON-serialized with
    ``sort_keys=True`` (stable); a str is stored verbatim; ``None`` stays null.
    One audit_event row (type
    :data:`~banking_fraud_lab.monitoring.spec.AUDIT_REVIEWER_ACTION_RECORDED`) is
    emitted per action, referencing reviewer_action_id + alert_decision_id +
    score_id + lineage, occurred_at strictly increasing.

    Args:
        alert_decision_rows: alert_decision monitoring rows to act on. REQUIRED
            columns: ``alert_decision_id``, ``banking_relationship_id``,
            ``detection_pattern_id``. The remaining lineage columns plus
            ``score_id`` are carried through when present.
        reviewer: Identifier of the reviewer, recorded on every reviewer_action row.
        action: Reviewer action such as confirm, dismiss, or escalate.
        rationale: Learner-readable reason for the reviewer action.
        evidence: v0.7 interpretability summary supporting the action. A dict is
            JSON-serialized with ``sort_keys=True``; a str is stored verbatim;
            ``None`` is recorded as null.
        seed: Drives the deterministic ids and the default reviewed_at timestamp.
        reviewed_at: Review timestamp. If ``None``, defaults to a seed-derived
            deterministic timestamp (each row gets a strictly increasing offset).

    Returns:
        A :class:`ReviewerActionResult` whose ``reviewer_action_rows`` conform
        exactly to :data:`banking_fraud_lab.monitoring.REVIEWER_ACTION` and whose
        ``audit_rows`` conform exactly to
        :data:`banking_fraud_lab.monitoring.AUDIT_EVENT`.

    Raises:
        ValueError: If ``alert_decision_rows`` is missing a required column.
    """
    _validate_alert_decision_rows(alert_decision_rows)

    resolved_reviewed_at = _resolve_timestamp(reviewed_at, seed)
    serialized_evidence = _serialize_evidence(evidence)

    actions = _build_reviewer_action_rows(
        alert_decision_rows,
        reviewer=reviewer,
        action=action,
        rationale=rationale,
        evidence=serialized_evidence,
        reviewed_at=resolved_reviewed_at,
        seed=seed,
    )
    audit_rows = _build_reviewer_audit_rows(actions, alert_decision_rows, seed=seed)
    return ReviewerActionResult(reviewer_action_rows=actions, audit_rows=audit_rows)


# --- Internal helpers ------------------------------------------------------


def _validate_threshold(threshold: float) -> float:
    """Return the threshold coerced to float, raising ValueError outside (0, 1]."""
    try:
        numeric = float(threshold)
    except (TypeError, ValueError) as exc:
        raise ValueError("threshold must be a finite number in (0.0, 1.0]") from exc
    if not math.isfinite(numeric) or numeric <= 0.0 or numeric > 1.0:
        raise ValueError("threshold must be in (0.0, 1.0]")
    return numeric


def _validate_threshold_id(threshold_id: str) -> None:
    """Raise ValueError when the threshold id is empty."""
    if not isinstance(threshold_id, str) or not threshold_id.strip():
        raise ValueError("threshold_id must be a non-empty string")


def _validate_score_rows(score_rows: "pd.DataFrame") -> None:
    """Raise ValueError when required columns are missing or patterns are unknown."""
    required = {"score_id", "score", "banking_relationship_id", "detection_pattern_id"}
    missing = sorted(required - set(score_rows.columns))
    if missing:
        raise ValueError(f"score_rows is missing required columns: {missing}")
    if score_rows.empty:
        raise ValueError("score_rows must contain at least one scored row")
    null_lineage = sorted(
        column
        for column in ("score_id", "banking_relationship_id", "detection_pattern_id")
        if score_rows[column].isna().any()
    )
    if null_lineage:
        raise ValueError(
            f"score_rows lineage columns must be non-null: {null_lineage}"
        )
    unknown = sorted(
        value
        for value in score_rows["detection_pattern_id"].unique()
        if value not in PATTERN_IDS
    )
    if unknown:
        raise ValueError(
            f"score_rows.detection_pattern_id values are not known Detection patterns: {unknown}"
        )


def _validate_alert_decision_rows(alert_decision_rows: "pd.DataFrame") -> None:
    """Raise ValueError when required alert_decision columns are missing."""
    required = {"alert_decision_id", "banking_relationship_id", "detection_pattern_id"}
    missing = sorted(required - set(alert_decision_rows.columns))
    if missing:
        raise ValueError(f"alert_decision_rows is missing required columns: {missing}")
    if alert_decision_rows.empty:
        raise ValueError("alert_decision_rows must contain at least one decision row")


def _resolve_timestamp(value: "pd.Timestamp | None", seed: int) -> "pd.Timestamp":
    """Return the supplied timestamp or a seed-derived deterministic default."""
    if value is not None:
        return pd.Timestamp(value)
    return _DEFAULT_TIMESTAMP_BASE + pd.Timedelta(seconds=int(seed))


def _stable_id(*parts: object) -> str:
    """Return a deterministic 16-hex-char digest of the joined string parts."""
    fingerprint = "|".join(str(part) for part in parts)
    return hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()[:16]


def _monotonic_timestamps(base: "pd.Timestamp", count: int) -> pd.Series:
    """Return a strictly increasing timestamp series of length ``count`` from ``base``."""
    offsets = pd.to_timedelta(np.arange(count, dtype="int64"), unit="s")
    return pd.Series([pd.Timestamp(base)] * count) + offsets


def _serialize_evidence(evidence: "dict[str, Any] | str | None") -> str | None:
    """Serialize evidence into a stable storage form (dict -> sorted-key JSON)."""
    if evidence is None:
        return None
    if isinstance(evidence, str):
        return evidence
    return json.dumps(evidence, sort_keys=True)


def _build_alert_decision_rows(
    score_rows: "pd.DataFrame",
    *,
    threshold: float,
    threshold_id: str,
    decided_at: "pd.Timestamp",
    seed: int,
) -> "pd.DataFrame":
    """Build alert_decision rows conforming exactly to the ALERT_DECISION spec."""
    count = len(score_rows)
    decisions = ["alert" if score >= threshold else "suppress" for score in score_rows["score"]]
    alert_decision_ids = [
        f"ad-{_stable_id(seed, threshold_id, threshold, score_id)}"
        for score_id in score_rows["score_id"]
    ]
    timestamps = _monotonic_timestamps(decided_at, count)

    column_sources: dict[str, pd.Series | list] = {
        "alert_decision_id": alert_decision_ids,
        "score_id": score_rows["score_id"].to_numpy(),
        "threshold_id": [threshold_id] * count,
        "detection_pattern_id": score_rows["detection_pattern_id"].to_numpy(),
        "banking_relationship_id": score_rows["banking_relationship_id"].to_numpy(),
        "decided_at": timestamps.to_numpy(),
        "decision": decisions,
        "score_at_decision": pd.to_numeric(score_rows["score"], errors="raise").to_numpy(),
    }
    for column in _OPTIONAL_LINEAGE_COLUMNS:
        if column in score_rows.columns:
            column_sources[column] = score_rows[column].to_numpy()
        else:
            column_sources[column] = [None] * count
    column_order = [column.name for column in ALERT_DECISION.columns]
    return pd.DataFrame(column_sources)[column_order]


def _build_decision_audit_rows(
    decisions: "pd.DataFrame",
    *,
    threshold_id: str,
    seed: int,
) -> "pd.DataFrame":
    """Build one AUDIT_ALERT_DECISION_MADE audit_event row per alert_decision row."""
    count = len(decisions)
    audit_event_ids = [
        f"ae-{_stable_id(seed, AUDIT_ALERT_DECISION_MADE, decision_id)}"
        for decision_id in decisions["alert_decision_id"]
    ]
    details = [
        f"alert_decision {decision} at score {score_at_decision}"
        for decision, score_at_decision in zip(
            decisions["decision"], decisions["score_at_decision"], strict=True
        )
    ]
    timestamps = _monotonic_timestamps(pd.Timestamp(decisions["decided_at"].iloc[0]), count)

    column_sources: dict[str, pd.Series | list] = {
        "audit_event_id": audit_event_ids,
        "audit_event_type": [AUDIT_ALERT_DECISION_MADE] * count,
        "score_id": decisions["score_id"].to_numpy(),
        "alert_decision_id": decisions["alert_decision_id"].to_numpy(),
        "reviewer_action_id": [None] * count,
        "threshold_id": [threshold_id] * count,
        "detection_pattern_id": decisions["detection_pattern_id"].to_numpy(),
        "banking_relationship_id": decisions["banking_relationship_id"].to_numpy(),
        "occurred_at": timestamps.to_numpy(),
        "detail": details,
    }
    for column in _OPTIONAL_LINEAGE_COLUMNS:
        if column in decisions.columns:
            column_sources[column] = decisions[column].to_numpy()
        else:
            column_sources[column] = [None] * count
    column_order = [column.name for column in AUDIT_EVENT.columns]
    return pd.DataFrame(column_sources)[column_order]


def _build_reviewer_action_rows(
    alert_decision_rows: "pd.DataFrame",
    *,
    reviewer: str,
    action: str,
    rationale: str,
    evidence: "str | None",
    reviewed_at: "pd.Timestamp",
    seed: int,
) -> "pd.DataFrame":
    """Build reviewer_action rows conforming exactly to the REVIEWER_ACTION spec.

    The REVIEWER_ACTION spec carries alert_decision_id + alert_id + banking /
    client / user / account / transaction lineage (no score_id); score_id lives
    only on the linked audit event, sourced separately.
    """
    count = len(alert_decision_rows)
    reviewer_action_ids = [
        f"ra-{_stable_id(seed, reviewer, action, decision_id)}"
        for decision_id in alert_decision_rows["alert_decision_id"]
    ]
    timestamps = _monotonic_timestamps(reviewed_at, count)

    column_sources: dict[str, pd.Series | list] = {
        "reviewer_action_id": reviewer_action_ids,
        "alert_decision_id": alert_decision_rows["alert_decision_id"].to_numpy(),
        "banking_relationship_id": alert_decision_rows["banking_relationship_id"].to_numpy(),
        "reviewer": [reviewer] * count,
        "reviewed_at": timestamps.to_numpy(),
        "action": [action] * count,
        "rationale": [rationale] * count,
        "evidence": [evidence] * count,
    }
    for column in _OPTIONAL_LINEAGE_COLUMNS:
        if column in alert_decision_rows.columns:
            column_sources[column] = alert_decision_rows[column].to_numpy()
        else:
            column_sources[column] = [None] * count
    column_order = [column.name for column in REVIEWER_ACTION.columns]
    return pd.DataFrame(column_sources)[column_order]


def _build_reviewer_audit_rows(
    actions: "pd.DataFrame",
    alert_decision_rows: "pd.DataFrame",
    *,
    seed: int,
) -> "pd.DataFrame":
    """Build one AUDIT_REVIEWER_ACTION_RECORDED audit_event row per reviewer_action.

    score_id + detection_pattern_id are NOT on reviewer_action rows, so they are
    looked up from the linked alert_decision rows via alert_decision_id.
    """
    count = len(actions)
    audit_event_ids = [
        f"ae-{_stable_id(seed, AUDIT_REVIEWER_ACTION_RECORDED, action_id)}"
        for action_id in actions["reviewer_action_id"]
    ]
    reviewer = actions["reviewer"].iloc[0] if count else ""
    action_value = actions["action"].iloc[0] if count else ""
    details = [f"reviewer {reviewer} {action_value}"] * count
    timestamps = _monotonic_timestamps(pd.Timestamp(actions["reviewed_at"].iloc[0]), count)

    decision_lookup = alert_decision_rows.set_index("alert_decision_id")

    def _from_decision(column: str) -> list:
        if column not in decision_lookup.columns:
            return [None] * count
        return decision_lookup.reindex(actions["alert_decision_id"])[column].tolist()

    column_sources: dict[str, pd.Series | list] = {
        "audit_event_id": audit_event_ids,
        "audit_event_type": [AUDIT_REVIEWER_ACTION_RECORDED] * count,
        "score_id": _from_decision("score_id"),
        "alert_decision_id": actions["alert_decision_id"].to_numpy(),
        "reviewer_action_id": actions["reviewer_action_id"].to_numpy(),
        "threshold_id": _from_decision("threshold_id"),
        "detection_pattern_id": _from_decision("detection_pattern_id"),
        "banking_relationship_id": actions["banking_relationship_id"].to_numpy(),
        "occurred_at": timestamps.to_numpy(),
        "detail": details,
    }
    for column in _OPTIONAL_LINEAGE_COLUMNS:
        if column in actions.columns:
            column_sources[column] = actions[column].to_numpy()
        else:
            column_sources[column] = [None] * count
    column_order = [column.name for column in AUDIT_EVENT.columns]
    return pd.DataFrame(column_sources)[column_order]


__all__ = [
    "AlertDecisionResult",
    "ReviewerActionResult",
    "decide_alerts",
    "record_reviewer_action",
]
