"""Alert-queue inspection and operational monitoring metric builders.

These builders give the Alert lifecycle operational meaning (PRD user stories 3
& 4) by turning ``alert_decision`` rows (enriched with the
``foundation_alert_lifecycle`` Progressive data view) into an inspectable queue
view and an operational-metrics summary. The queue ranking mirrors
``sql/examples/04_progressive_alert_queue.sql`` exactly: severity (high > medium
> low), then ``generated_at`` ascending, then ``alert_id`` ascending. The
operational summary reuses the v0.7 :func:`evaluate_alert_scores`
``lowest_cost_summary`` precision/recall and the v0.1 ``alert_capacity``
convention rather than recomputing them.

Three summary entry points are provided: :func:`summarise_alert_operations` (one
institution, the original contract), :func:`summarise_alert_operations_by_track`
(grouped by institution, preserving the original grouped shape), and
:func:`summarise_alert_operations_by_institution_track` (one row per institution
/ track pair for the PRD #203 path). All share the same per-group computation
and reuse evaluation precision/recall on the PRD path.

Glossary terms are used verbatim where natural: every queue row traces to a
Banking relationship (and Client / User lineage when present) and to a
Detection pattern; the Alert lifecycle and Detection pattern vocabulary are
reused unchanged. Output is deterministic for fixed inputs: no wall-clock
timestamps are introduced (the default ``now`` is a fixed timestamp, not
``datetime.now()``).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pandas as pd

_OPTIONAL_LINEAGE_COLUMNS: tuple[str, ...] = (
    "client_id",
    "user_id",
    "account_id",
    "transaction_id",
    "detection_pattern_id",
)

_SEVERITY_RANK: dict[str, int] = {"high": 1, "medium": 2, "low": 3}

_DEFAULT_NOW = pd.Timestamp("2024-01-01")


def inspect_alert_queue(
    decision_rows: "pd.DataFrame",
    *,
    institution: str,
    now: "pd.Timestamp | None" = None,
    stale_threshold_hours: "float | None" = None,
) -> "pd.DataFrame":
    """Build an inspectable Alert queue view for one institution.

    The queue ranking mirrors ``sql/examples/04_progressive_alert_queue.sql``
    exactly: within the selected institution, sort by severity (high=1,
    medium=2, low/other=3), then ``generated_at`` ascending, then ``alert_id``
    ascending, and emit a 1-based ``alert_queue_rank``.

    Args:
        decision_rows: Caller-built frame produced by joining ``alert_decision``
            rows with the ``foundation_alert_lifecycle`` Progressive data view,
            so it carries at least ``alert_id``, ``banking_relationship_id``,
            ``institution_name``, ``generated_at`` (datetime64), ``severity``
            (high/medium/low), and ``alert_status``. Optional lineage columns
            carried through when present: ``client_id``, ``user_id``,
            ``account_id``, ``transaction_id``, ``detection_pattern_id``.
        institution: Institution whose queue is inspected (matched
            case-insensitively against ``institution_name``), e.g. Alpine Crest
            Private Bank or NovaBank Digital.
        now: Reference timestamp used to compute ``alert_age_hours``. If
            ``None``, defaults to the deterministic
            :data:`_DEFAULT_NOW` (NOT ``datetime.now()``).
        stale_threshold_hours: When set, alerts whose ``alert_age_hours`` exceeds
            this value are flagged ``is_stale_alert=True`` so aged-out alerts
            surface in the queue (PRD user story 3). When ``None`` (the default)
            every row is ``is_stale_alert=False``, preserving prior behavior.

    Returns:
        A queue view (one row per alert) ordered by ``alert_queue_rank`` with
        columns ``alert_id``, ``institution_name``, ``banking_relationship_id``,
        ``client_id``/``user_id``/``account_id``/``transaction_id`` (when
        present), ``detection_pattern_id`` (when present), ``severity``,
        ``alert_status``, ``alert_age_hours`` (rounded to 2 decimals),
        ``alert_queue_rank``, and ``is_stale_alert``. Each row traces to a
        Banking relationship (and Client/User lineage when present) and to a
        Detection pattern.

    Raises:
        ValueError: If ``decision_rows`` is missing a required column, if
            ``generated_at`` is not a datetime column, if no rows match the
            requested institution, or if ``stale_threshold_hours`` is negative.
    """
    _validate_decision_rows(decision_rows)
    if stale_threshold_hours is not None and (
        not isinstance(stale_threshold_hours, int | float) or stale_threshold_hours < 0
    ):
        raise ValueError("stale_threshold_hours must be a non-negative number or None")

    resolved_now = _DEFAULT_NOW if now is None else pd.Timestamp(now)

    filtered = decision_rows[
        decision_rows["institution_name"].astype(str).str.strip().str.lower()
        == str(institution).strip().lower()
    ].copy()
    if filtered.empty:
        raise ValueError(f"No alert_decision rows match institution {institution!r}")

    filtered["alert_age_hours"] = (
        (resolved_now - pd.to_datetime(filtered["generated_at"])).dt.total_seconds()
        / 3600.0
    ).round(2)

    severity_rank = filtered["severity"].astype(str).str.lower().map(_SEVERITY_RANK).fillna(3)
    filtered["_severity_rank"] = severity_rank
    filtered = filtered.sort_values(
        by=["_severity_rank", "generated_at", "alert_id"],
        kind="stable",
    ).reset_index(drop=True)
    filtered["alert_queue_rank"] = range(1, len(filtered) + 1)

    if stale_threshold_hours is not None:
        filtered["is_stale_alert"] = filtered["alert_age_hours"] > float(stale_threshold_hours)
    else:
        filtered["is_stale_alert"] = False

    queue_columns = [
        "alert_id",
        "institution_name",
        "banking_relationship_id",
    ]
    for column in _OPTIONAL_LINEAGE_COLUMNS:
        if column in filtered.columns:
            queue_columns.append(column)
    queue_columns.extend(
        ["severity", "alert_status", "alert_age_hours", "alert_queue_rank", "is_stale_alert"]
    )
    return filtered[queue_columns]


def summarise_alert_operations(
    decision_rows: "pd.DataFrame",
    *,
    alert_capacity: int,
    evaluation: "dict[str, Any] | None" = None,
) -> "dict[str, Any]":
    """Summarise Alert operations into a deterministic operational-metrics dict.

    Precision/recall are REUSED from ``evaluate_alert_scores`` when an
    ``evaluation`` result is supplied (taken from
    ``evaluation['lowest_cost_summary']``); they are NOT recomputed. When no
    ``evaluation`` is supplied and ``decision_rows`` has a boolean
    ``confirmed_fraud`` column, precision/recall are computed over
    ``decision == 'alert'`` rows. Otherwise precision/recall are ``None``.

    Args:
        decision_rows: ``alert_decision`` rows (optionally enriched with
            ``alert_status``, ``confirmed_fraud``, ``institution_name``,
            ``detection_pattern_id``). When ``decision`` is present,
            ``alert_volume`` counts rows with ``decision == 'alert'``;
            otherwise it counts all rows.
        alert_capacity: Operational alert capacity (the v0.1 convention).
            Must be positive.
        evaluation: An :func:`evaluate_alert_scores` result dict. When supplied,
            precision/recall are read from
            ``evaluation['lowest_cost_summary']`` and reused verbatim.

    Returns:
        A dict with keys ``institution``, ``alert_volume``,
        ``alert_capacity``, ``capacity_utilization``, ``precision``, ``recall``,
        ``closure_distribution``, and ``detection_pattern_ids``. Deterministic
        for fixed inputs.

    Raises:
        ValueError: If ``alert_capacity`` is not positive, or if ``decision_rows``
            contains more than one institution (use
            :func:`summarise_alert_operations_by_track` for a mixed-bank frame).
    """
    institution = _resolve_institution(decision_rows)
    return _summarise_one_group(
        decision_rows,
        alert_capacity=alert_capacity,
        evaluation=evaluation,
        institution=institution,
    )


def summarise_alert_operations_by_track(
    decision_rows: "pd.DataFrame",
    *,
    alert_capacity: int,
    evaluation: "dict[str, Any] | None" = None,
) -> "dict[str, dict[str, Any]]":
    """Summarise Alert operations grouped by institution (legacy grouped shape).

    The grouped companion to :func:`summarise_alert_operations`: it splits the
    decision rows by ``institution_name`` (e.g. Alpine Crest Private Bank and
    NovaBank Digital) and runs the SAME per-group summary logic, so alert
    volume, precision, recall, capacity utilization, and closure outcomes are
    visible per institution rather than only in aggregate. Like the single-group
    function, precision/recall are REUSED from ``evaluate_alert_scores`` when an
    ``evaluation`` result is supplied rather than recomputed. Use
    :func:`summarise_alert_operations_by_institution_track` for the strict PRD
    #203 institution / track contract.

    Args:
        decision_rows: ``alert_decision`` rows carrying ``institution_name``
            plus the optional enrichment columns documented on
            :func:`summarise_alert_operations`. Must contain at least one row.
        alert_capacity: Operational alert capacity (the v0.1 convention), shared
            by every institution group. Must be positive.
        evaluation: An :func:`evaluate_alert_scores` result dict. When supplied,
            its ``lowest_cost_summary`` precision/recall are reused verbatim for
            every institution group.

    Returns:
        A dict keyed by the exact institution name (as it appears in the frame),
        each value the same operational-metrics dict shape
        :func:`summarise_alert_operations` returns. Tracks are deterministically
        ordered by institution name.

    Raises:
        ValueError: If ``alert_capacity`` is not positive, if
            ``institution_name`` is missing, if any ``institution_name`` is null,
            or if there are no rows to group.
    """
    if not isinstance(alert_capacity, int | float) or alert_capacity <= 0:
        raise ValueError("alert_capacity must be positive")
    if "institution_name" not in decision_rows.columns:
        raise ValueError("decision_rows is missing required column: ['institution_name']")
    if decision_rows.empty:
        raise ValueError("decision_rows must contain at least one row")
    if decision_rows["institution_name"].isna().any():
        raise ValueError("decision_rows['institution_name'] must be non-null for every row")

    grouped: "dict[str, dict[str, Any]]" = {}
    for institution in sorted(decision_rows["institution_name"].astype(str).unique()):
        group_rows = decision_rows[
            decision_rows["institution_name"].astype(str) == institution
        ]
        grouped[institution] = _summarise_one_group(
            group_rows,
            alert_capacity=alert_capacity,
            evaluation=evaluation,
            institution=institution,
        )
    return grouped


def summarise_alert_operations_by_institution_track(
    decision_rows: "pd.DataFrame",
    *,
    alert_capacity: int,
    evaluation_by_group: Mapping[tuple[str, str], dict[str, Any]] | None = None,
) -> "pd.DataFrame":
    """Summarise operations for each institution / track pair.

    This companion keeps :func:`summarise_alert_operations_by_track` backward
    compatible while providing the stricter PRD #203 grouping contract: one
    deterministic row per ``(institution_name, track)`` pair with alert volume,
    precision, recall, capacity utilization, and closure outcomes. When
    ``evaluation_by_group`` is supplied, each group's precision/recall are read
    from that group's full :func:`evaluate_alert_scores` result instead of being
    recomputed from labels.

    Args:
        decision_rows: ``alert_decision`` rows carrying non-null
            ``institution_name`` and ``track`` columns plus the optional
            enrichment columns documented on :func:`summarise_alert_operations`.
        alert_capacity: Operational alert capacity (the v0.1 convention), shared
            by every group. Must be positive.
        evaluation_by_group: Optional mapping keyed by
            ``(institution_name, track)``. If supplied, every observed group must
            have a matching :func:`evaluate_alert_scores` result; precision and
            recall are reused from its ``lowest_cost_summary``.

    Returns:
        A deterministic DataFrame ordered by ``institution_name`` then ``track``.

    Raises:
        ValueError: If required grouping columns are missing/null, if capacity is
            not positive, or if ``evaluation_by_group`` lacks an observed group.
    """
    if not isinstance(alert_capacity, int | float) or alert_capacity <= 0:
        raise ValueError("alert_capacity must be positive")
    required = {"institution_name", "track"}
    missing = sorted(required - set(decision_rows.columns))
    if missing:
        raise ValueError(f"decision_rows is missing required columns: {missing}")
    if decision_rows.empty:
        raise ValueError("decision_rows must contain at least one row")
    null_grouping = sorted(
        column for column in required if decision_rows[column].isna().any()
    )
    if null_grouping:
        raise ValueError(
            f"decision_rows grouping columns must be non-null: {null_grouping}"
        )

    rows: list[dict[str, Any]] = []
    for (institution, track), group_rows in decision_rows.groupby(
        ["institution_name", "track"], sort=True
    ):
        group_key = (str(institution), str(track))
        group_evaluation = None
        if evaluation_by_group is not None:
            if group_key not in evaluation_by_group:
                raise ValueError(
                    "evaluation_by_group is missing evaluate_alert_scores result "
                    f"for group {group_key!r}"
                )
            group_evaluation = evaluation_by_group[group_key]
        metrics = _summarise_one_group(
            group_rows,
            alert_capacity=alert_capacity,
            evaluation=group_evaluation,
            institution=str(institution),
        )
        rows.append(
            {
                "institution_name": str(institution),
                "track": str(track),
                "alert_volume": metrics["alert_volume"],
                "alert_capacity": metrics["alert_capacity"],
                "capacity_utilization": metrics["capacity_utilization"],
                "precision": metrics["precision"],
                "recall": metrics["recall"],
                "closure_distribution": metrics["closure_distribution"],
                "detection_pattern_ids": tuple(metrics["detection_pattern_ids"]),
            }
        )

    columns = [
        "institution_name",
        "track",
        "alert_volume",
        "alert_capacity",
        "capacity_utilization",
        "precision",
        "recall",
        "closure_distribution",
        "detection_pattern_ids",
    ]
    return pd.DataFrame(rows, columns=columns)


# --- Internal helpers ------------------------------------------------------


def _resolve_institution(decision_rows: "pd.DataFrame") -> "str | None":
    """Return the single institution name on the frame, else None.

    Raises ``ValueError`` when the frame mixes more than one institution. The
    single-institution summary (:func:`summarise_alert_operations`) must not
    silently aggregate a mixed-bank frame under one label; the caller should use
    :func:`summarise_alert_operations_by_track` for that.
    """
    if "institution_name" in decision_rows.columns and not decision_rows.empty:
        unique = sorted(
            decision_rows["institution_name"].dropna().astype(str).unique()
        )
        if len(unique) > 1:
            raise ValueError(
                "decision_rows contains multiple institutions ("
                + ", ".join(unique)
                + "); use summarise_alert_operations_by_track"
            )
        if unique:
            return unique[0]
    return None


def _summarise_one_group(
    decision_rows: "pd.DataFrame",
    *,
    alert_capacity: "int | float",
    evaluation: "dict[str, Any] | None",
    institution: "str | None",
) -> "dict[str, Any]":
    """Compute the operational-metrics dict for one (institution) group of decision rows.

    Shared by :func:`summarise_alert_operations` (whole frame as one group) and
    :func:`summarise_alert_operations_by_track` (one group per institution).
    Precision/recall reuse the ``evaluate_alert_scores`` summary when supplied.
    """
    if not isinstance(alert_capacity, int | float) or alert_capacity <= 0:
        raise ValueError("alert_capacity must be positive")

    if "decision" in decision_rows.columns:
        alert_volume = int((decision_rows["decision"] == "alert").sum())
    else:
        alert_volume = int(len(decision_rows))

    evaluation_summary = _evaluation_summary(evaluation)
    if evaluation_summary is not None:
        capacity_utilization = evaluation_summary["capacity_utilization"]
    else:
        capacity_utilization = round(alert_volume / float(alert_capacity), 4)

    closure_distribution = _closure_distribution(decision_rows)

    precision, recall = _resolve_precision_recall(decision_rows, evaluation)

    detection_pattern_ids: list[str] = []
    if "detection_pattern_id" in decision_rows.columns:
        detection_pattern_ids = sorted(
            str(value)
            for value in decision_rows["detection_pattern_id"].dropna().unique()
        )

    return {
        "institution": institution,
        "alert_volume": alert_volume,
        "alert_capacity": int(alert_capacity),
        "capacity_utilization": capacity_utilization,
        "precision": precision,
        "recall": recall,
        "closure_distribution": closure_distribution,
        "detection_pattern_ids": detection_pattern_ids,
    }


def _validate_decision_rows(decision_rows: "pd.DataFrame") -> None:
    """Raise ValueError when required queue columns are missing or generated_at is not datetime."""
    required = {
        "alert_id",
        "banking_relationship_id",
        "institution_name",
        "generated_at",
        "severity",
        "alert_status",
    }
    missing = sorted(required - set(decision_rows.columns))
    if missing:
        raise ValueError(f"decision_rows is missing required columns: {missing}")
    if decision_rows.empty:
        raise ValueError("decision_rows must contain at least one row")
    if not pd.api.types.is_datetime64_any_dtype(decision_rows["generated_at"]):
        raise ValueError("decision_rows.generated_at must be a datetime64 column")


def _resolve_precision_recall(
    decision_rows: "pd.DataFrame",
    evaluation: "dict[str, Any] | None",
) -> "tuple[float | None, float | None]":
    """Reuse precision/recall from evaluation when supplied, else compute from labels."""
    summary = _evaluation_summary(evaluation)
    if summary is not None:
        return summary["precision"], summary["recall"]

    if "confirmed_fraud" in decision_rows.columns and "decision" in decision_rows.columns:
        alerted = decision_rows[decision_rows["decision"] == "alert"]
        labels = alerted["confirmed_fraud"].astype(bool)
        true_positives = int(labels.sum())
        false_positives = int((~labels).sum())
        false_negatives = int(
            (
                decision_rows.loc[decision_rows["decision"] != "alert", "confirmed_fraud"]
                .astype(bool)
                .sum()
            )
        )
        precision = (
            round(true_positives / (true_positives + false_positives), 6)
            if (true_positives + false_positives) > 0
            else 0.0
        )
        recall = (
            round(true_positives / (true_positives + false_negatives), 6)
            if (true_positives + false_negatives) > 0
            else 0.0
        )
        return precision, recall

    return None, None


def _evaluation_summary(evaluation: "dict[str, Any] | None") -> "dict[str, Any] | None":
    """Return the evaluate_alert_scores lowest_cost_summary, validating shape."""
    if evaluation is None:
        return None
    summary = evaluation.get("lowest_cost_summary")
    if summary is None:
        raise ValueError(
            "evaluation is missing the 'lowest_cost_summary' key "
            "(pass a full evaluate_alert_scores result)"
        )
    required = {"precision", "recall", "capacity_utilization"}
    missing = sorted(required - set(summary))
    if missing:
        raise ValueError(
            "evaluation['lowest_cost_summary'] is missing required keys: "
            f"{missing}"
        )
    return summary


def _closure_distribution(decision_rows: "pd.DataFrame") -> "dict[str, int]":
    """Return closure/outcome counts from the richest available lifecycle column."""
    for column in ("outcome_type", "closure_outcome", "alert_status", "case_status"):
        if column in decision_rows.columns:
            return {
                str(status): int(count)
                for status, count in decision_rows[column].value_counts().items()
            }
    return {}


__all__ = [
    "inspect_alert_queue",
    "summarise_alert_operations",
    "summarise_alert_operations_by_institution_track",
    "summarise_alert_operations_by_track",
]
