"""Alert-aware evaluation utilities for generated fraud case outcomes."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import Any

import numpy as np
import pandas as pd

DEFAULT_THRESHOLDS = (0.25, 0.5, 0.75)
LIMITATION_SUMMARY = (
    "These metrics use generated case outcomes and model-like alert scores to discuss "
    "alert capacity, precision, recall, PR-AUC, and costs. Headline accuracy is out of "
    "scope because fraud labels are sparse, alert outcomes are operational decisions, "
    "and protected answer keys remain separate from learner-facing data."
)


def evaluate_alert_scores(
    cases: pd.DataFrame,
    case_outcomes: pd.DataFrame,
    alert_scores: pd.DataFrame,
    *,
    thresholds: Sequence[float] = DEFAULT_THRESHOLDS,
    alert_capacity: int = 10,
    investigation_cost_chf: float = 75.0,
    false_positive_cost_chf: float = 25.0,
    missed_fraud_cost_chf: float | None = None,
) -> dict[str, Any]:
    """Evaluate alert-level scores against generated case outcomes."""
    prepared = _prepare_scored_outcomes(cases, case_outcomes, alert_scores)
    normalized_thresholds = _normalize_thresholds(thresholds)
    if alert_capacity <= 0:
        raise ValueError("alert_capacity must be positive")
    _validate_non_negative_cost("investigation_cost_chf", investigation_cost_chf)
    _validate_non_negative_cost("false_positive_cost_chf", false_positive_cost_chf)
    if missed_fraud_cost_chf is not None:
        _validate_non_negative_cost("missed_fraud_cost_chf", missed_fraud_cost_chf)

    threshold_summaries = [
        _threshold_summary(
            prepared,
            threshold=threshold,
            alert_capacity=alert_capacity,
            investigation_cost_chf=investigation_cost_chf,
            false_positive_cost_chf=false_positive_cost_chf,
            missed_fraud_cost_chf=missed_fraud_cost_chf,
        )
        for threshold in normalized_thresholds
    ]
    cost_curve = [
        {
            "threshold": summary["threshold"],
            "investigation_cost_chf": summary["investigation_cost_chf"],
            "false_positive_cost_chf": summary["false_positive_cost_chf"],
            "missed_fraud_cost_chf": summary["missed_fraud_cost_chf"],
            "total_cost_chf": summary["total_cost_chf"],
        }
        for summary in threshold_summaries
    ]
    # lowest_cost_summary is selected from threshold_summaries by minimizing the
    # lambda key: total cost first, then maximizing recall to avoid missed fraud,
    # then minimizing alert volume to reduce review workload.
    lowest_cost_summary = min(
        threshold_summaries,
        key=lambda summary: (
            summary["total_cost_chf"],
            -summary["recall"],
            summary["alert_volume"],
        ),
    )

    return {
        "population": {
            "case_count": int(len(prepared)),
            "confirmed_fraud_count": int(prepared["_label"].sum()),
            "non_fraud_count": int((~prepared["_label"]).sum()),
        },
        "pr_auc": _average_precision(prepared["_label"], prepared["_score"]),
        "threshold_summaries": threshold_summaries,
        "cost_curve": cost_curve,
        "lowest_cost_threshold": lowest_cost_summary["threshold"],
        "lowest_cost_summary": lowest_cost_summary,
        "limitation_summary": LIMITATION_SUMMARY,
    }


def _prepare_scored_outcomes(
    cases: pd.DataFrame,
    case_outcomes: pd.DataFrame,
    alert_scores: pd.DataFrame,
) -> pd.DataFrame:
    """Join cases, outcomes, and alert scores into one evaluation frame."""
    _require_columns(cases, {"case_id", "alert_id"}, "cases")
    _require_columns(case_outcomes, {"case_id", "confirmed_fraud"}, "case_outcomes")
    _require_columns(alert_scores, {"alert_id", "score"}, "alert_scores")
    _require_unique(cases, "case_id", "cases")
    _require_unique(cases, "alert_id", "cases")
    _require_unique(case_outcomes, "case_id", "case_outcomes")
    _require_unique(alert_scores, "alert_id", "alert_scores")

    outcome_columns = ["case_id", "confirmed_fraud"]
    if "loss_amount_chf" in case_outcomes.columns:
        outcome_columns.append("loss_amount_chf")

    labels = cases[["case_id", "alert_id"]].merge(
        case_outcomes[outcome_columns],
        on="case_id",
        how="inner",
        validate="one_to_one",
    )
    if labels.empty:
        raise ValueError("cases and case_outcomes must contain at least one matched row")

    missing_scores = sorted(set(labels["alert_id"]) - set(alert_scores["alert_id"]))
    if missing_scores:
        raise ValueError(f"alert_scores is missing scores for alert_id values: {missing_scores}")

    scored = labels.merge(
        alert_scores[["alert_id", "score"]],
        on="alert_id",
        how="left",
        validate="one_to_one",
    )
    scored["_label"] = scored["confirmed_fraud"].map(_parse_confirmed_fraud_label).astype(bool)
    scored["_score"] = pd.to_numeric(scored["score"], errors="raise").astype(float)
    if not scored["_score"].between(0.0, 1.0).all():
        raise ValueError("alert_scores.score values must be between 0 and 1")

    if "loss_amount_chf" in scored.columns:
        scored["_loss_amount_chf"] = scored["loss_amount_chf"].map(_money_to_float)
    else:
        scored["_loss_amount_chf"] = 0.0
    scored.loc[~scored["_label"], "_loss_amount_chf"] = 0.0

    return scored


def _threshold_summary(
    scored: pd.DataFrame,
    *,
    threshold: float,
    alert_capacity: int,
    investigation_cost_chf: float,
    false_positive_cost_chf: float,
    missed_fraud_cost_chf: float | None,
) -> dict[str, Any]:
    """Calculate one threshold's confusion matrix, capacity, and cost summary."""
    selected = scored["_score"] >= threshold
    positives = scored["_label"]
    tp = int((selected & positives).sum())
    fp = int((selected & ~positives).sum())
    fn = int((~selected & positives).sum())
    tn = int((~selected & ~positives).sum())
    alert_volume = int(selected.sum())
    missed_cost = (
        fn * missed_fraud_cost_chf
        if missed_fraud_cost_chf is not None
        else float(scored.loc[~selected & positives, "_loss_amount_chf"].sum())
    )
    investigation_cost = alert_volume * investigation_cost_chf
    false_positive_cost = fp * false_positive_cost_chf

    return {
        "threshold": threshold,
        "precision": _safe_divide(tp, tp + fp),
        "recall": _safe_divide(tp, tp + fn),
        "true_positives": tp,
        "false_positives": fp,
        "true_negatives": tn,
        "false_negatives": fn,
        "alert_volume": alert_volume,
        "alert_capacity": alert_capacity,
        "capacity_utilization": _round_metric(alert_volume / alert_capacity),
        "over_capacity_alerts": max(0, alert_volume - alert_capacity),
        "investigation_cost_chf": _round_money(investigation_cost),
        "false_positive_cost_chf": _round_money(false_positive_cost),
        "missed_fraud_cost_chf": _round_money(missed_cost),
        "total_cost_chf": _round_money(
            investigation_cost + false_positive_cost + missed_cost
        ),
    }


def _average_precision(labels: pd.Series, scores: pd.Series) -> float:
    """Calculate average precision as the PR-AUC summary for sparse fraud labels."""
    pairs = sorted(
        zip(scores.astype(float), labels.astype(bool), strict=True),
        key=lambda pair: pair[0],
        reverse=True,
    )
    positive_count = sum(1 for _, label in pairs if label)
    if positive_count == 0:
        return 0.0

    area = 0.0
    true_positives = 0
    false_positives = 0
    previous_recall = 0.0
    index = 0
    while index < len(pairs):
        score = pairs[index][0]
        while index < len(pairs) and pairs[index][0] == score:
            if pairs[index][1]:
                true_positives += 1
            else:
                false_positives += 1
            index += 1
        precision = true_positives / (true_positives + false_positives)
        recall = true_positives / positive_count
        area += (recall - previous_recall) * precision
        previous_recall = recall

    return _round_metric(area)


def _normalize_thresholds(thresholds: Sequence[float]) -> tuple[float, ...]:
    """Validate and sort threshold values from high to low."""
    try:
        normalized_values = {float(threshold) for threshold in thresholds}
    except (TypeError, ValueError) as exc:
        raise ValueError("thresholds must contain numeric values") from exc

    normalized = tuple(sorted(normalized_values, reverse=True))
    if not normalized:
        raise ValueError("thresholds must contain at least one threshold")
    if any(
        not math.isfinite(threshold) or threshold < 0.0 or threshold > 1.0
        for threshold in normalized
    ):
        raise ValueError("thresholds must be finite values between 0 and 1")
    return normalized


def _require_columns(frame: pd.DataFrame, columns: set[str], frame_name: str) -> None:
    """Raise a clear error when an input DataFrame is missing required columns."""
    missing_columns = columns - set(frame.columns)
    if missing_columns:
        raise ValueError(f"{frame_name} is missing required columns: {sorted(missing_columns)}")


def _require_unique(frame: pd.DataFrame, column_name: str, frame_name: str) -> None:
    """Raise a clear error when key columns contain duplicate values."""
    duplicated = frame[column_name][frame[column_name].duplicated()].unique()
    if len(duplicated):
        raise ValueError(
            f"{frame_name}.{column_name} must be unique; duplicates: {sorted(duplicated)}"
        )


def _validate_non_negative_cost(parameter_name: str, value: float) -> None:
    """Raise a clear error when a cost parameter is negative."""
    try:
        numeric_value = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{parameter_name} must be finite and non-negative") from exc
    if not math.isfinite(numeric_value) or numeric_value < 0:
        raise ValueError(f"{parameter_name} must be finite and non-negative")


def _parse_confirmed_fraud_label(value: object) -> bool:
    """Parse generated or exported confirmed-fraud labels without truthiness coercion."""
    if value is None or pd.isna(value):
        raise ValueError("case_outcomes.confirmed_fraud values must be non-null booleans")
    if isinstance(value, np.bool_ | bool):
        return bool(value)
    if isinstance(value, np.integer | int):
        if int(value) in {0, 1}:
            return bool(value)
    if isinstance(value, np.floating | float):
        numeric_value = float(value)
        if math.isfinite(numeric_value) and numeric_value in {0.0, 1.0}:
            return bool(numeric_value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "t", "yes", "y", "1"}:
            return True
        if normalized in {"false", "f", "no", "n", "0"}:
            return False
    raise ValueError(
        "case_outcomes.confirmed_fraud values must be booleans or recognized "
        f"boolean encodings; got {value!r}"
    )


def _money_to_float(value: object) -> float:
    """Convert Decimal, NumPy, pandas, or Python money-like values to float."""
    if value is None or pd.isna(value):
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, np.integer | np.floating):
        return float(value)
    return float(value)


def _safe_divide(numerator: int, denominator: int) -> float:
    """Divide and round, returning zero when the denominator is zero."""
    if denominator == 0:
        return 0.0
    return _round_metric(numerator / denominator)


def _round_metric(value: float) -> float:
    """Round metric values to stable notebook-friendly precision."""
    return round(float(value), 6)


def _round_money(value: float) -> float:
    """Round CHF cost values to cents."""
    return round(float(value), 2)


# --- v0.7: false-positive concentration + threshold recommender -----------
# These utilities are ADDITIVE to ``evaluate_alert_scores``: its signature and
# output are unchanged. They reuse the same scored-outcome join so a learner can
# hand in the same frames and see (a) where false positives burden specific
# segments/workflows and (b) a recommended threshold reflecting operational
# tradeoffs across alert capacity and cost parameters.

#: Segment columns recognised by default when measuring false-positive
#: concentration. Each maps a facet of the alert lifecycle a reviewer can slice
#: on: the Detection pattern that raised the alert (``alert_type``), the track it
#: belongs to (``track``), and the Banking relationship container
#: (``banking_relationship_id``).
DEFAULT_FP_SEGMENT_COLUMNS: tuple[str, ...] = (
    "alert_type",
    "track",
    "banking_relationship_id",
)


def concentrate_false_positives(
    cases: pd.DataFrame,
    case_outcomes: pd.DataFrame,
    alert_scores: pd.DataFrame,
    *,
    threshold: float,
    segment_columns: Sequence[str] = DEFAULT_FP_SEGMENT_COLUMNS,
    alerts: pd.DataFrame | None = None,
    activity_type_to_track: Mapping[str, str] | None = None,
) -> pd.DataFrame:
    """Measure where false positives concentrate by segment.

    Joins cases, outcomes, and alert scores exactly as
    :func:`evaluate_alert_scores` does, then selects the alerts whose score meets
    ``threshold`` and groups the false positives (scored above threshold but not
    confirmed fraud) by the requested ``segment_columns``. The result lets a
    learner see which ``alert_type``, track, or Banking relationship bears the
    heaviest review burden so investigation capacity can be planned.

    Args:
        cases: Cases frame with at least ``case_id`` and ``alert_id``.
        case_outcomes: Outcomes frame with ``case_id`` and ``confirmed_fraud``.
        alert_scores: Scores frame with ``alert_id`` and ``score`` in [0, 1].
        threshold: The score threshold defining an alerted case. Must be in
            [0, 1].
        segment_columns: The columns to group false positives by. Defaults to
            :data:`DEFAULT_FP_SEGMENT_COLUMNS`; only columns present in the joined
            frame (or enriched via ``alerts``) are used, so missing columns are
            skipped rather than raising.
        alerts: Optional alerts frame used to enrich the join with segment
            columns not present on ``cases`` (e.g. ``alert_type``). Joined on
            ``alert_id``.
        activity_type_to_track: Optional mapping from ``alert_type``/activity
            type to track label (e.g. ``"private_banking"`` /
            ``"digital_banking"``). When supplied, a ``track`` column is derived
            so concentration can be read by Detection track. When omitted, the
            ``track`` segment column is skipped if not already present.

    Returns:
        A DataFrame with one row per segment combination that produced at least
        one false positive, columns ``false_positive_count``, ``false_positive_share``
        (share of all false positives at this threshold), ``alerted_count``
        (total alerts above threshold in the segment, for precision context),
        and ``false_positive_rate`` (FPs / alerted in the segment), sorted by
        descending ``false_positive_count`` then the segment columns for
        deterministic ordering. Empty when no alerts clear the threshold.

    Raises:
        ValueError: If ``threshold`` is outside [0, 1] or no segment columns
            resolve to a present column.
    """
    if not math.isfinite(threshold) or threshold < 0.0 or threshold > 1.0:
        raise ValueError("threshold must be a finite value between 0 and 1")

    scored = _prepare_scored_outcomes(cases, case_outcomes, alert_scores)
    if alerts is not None:
        _require_columns(alerts, {"alert_id"}, "alerts")
        # Pull every requested segment column that lives on the alerts frame,
        # PLUS alert_type when a track mapping is supplied (the track column is
        # derived from alert_type below, so it must be present even if the caller
        # only asked for the derived ``track`` segment).
        wanted = set(segment_columns)
        if activity_type_to_track is not None:
            wanted.add("alert_type")
        enrich_columns = [
            column
            for column in wanted
            if column not in scored.columns and column in alerts.columns
        ]
        if enrich_columns:
            scored = scored.merge(
                alerts[["alert_id", *enrich_columns]],
                on="alert_id",
                how="left",
                validate="many_to_one",
            )

    if activity_type_to_track is not None and "alert_type" in scored.columns:
        scored = scored.assign(
            track=scored["alert_type"].map(activity_type_to_track)
        )

    resolved_segments = [column for column in segment_columns if column in scored.columns]
    if not resolved_segments:
        raise ValueError(
            "no segment_columns resolve to a column in the joined frame; pass "
            "an alerts frame or activity_type_to_track mapping to enrich it"
        )

    alerted = scored[scored["_score"] >= threshold]
    false_positives = alerted[~alerted["_label"]]
    if false_positives.empty:
        return pd.DataFrame(
            columns=[
                *resolved_segments,
                "false_positive_count",
                "false_positive_share",
                "alerted_count",
                "false_positive_rate",
            ]
        )

    total_fp = int(len(false_positives))
    grouped = (
        false_positives.groupby(list(resolved_segments), dropna=False, sort=False)
        .size()
        .rename("false_positive_count")
        .reset_index()
    )
    alerted_grouped = (
        alerted.groupby(list(resolved_segments), dropna=False, sort=False)
        .size()
        .rename("alerted_count")
        .reset_index()
    )
    result = grouped.merge(alerted_grouped, on=list(resolved_segments), how="left")
    result["false_positive_count"] = result["false_positive_count"].astype(int)
    result["alerted_count"] = result["alerted_count"].astype(int)
    result["false_positive_share"] = result["false_positive_count"].map(
        lambda count: _round_metric(count / total_fp)
    )
    result["false_positive_rate"] = result.apply(
        lambda row: _round_metric(row["false_positive_count"] / row["alerted_count"]),
        axis=1,
    )
    sort_keys = ["false_positive_count", *resolved_segments]
    ascending = [False] + [True] * len(resolved_segments)
    return result.sort_values(sort_keys, ascending=ascending, kind="stable").reset_index(
        drop=True
    )


def recommend_lowest_cost_threshold(
    cases: pd.DataFrame,
    case_outcomes: pd.DataFrame,
    alert_scores: pd.DataFrame,
    *,
    candidate_thresholds: Sequence[float] = DEFAULT_THRESHOLDS,
    alert_capacities: Sequence[int] = (5, 10, 25),
    investigation_cost_chf: float = 75.0,
    false_positive_cost_chf: float = 25.0,
    missed_fraud_cost_chf: float | None = None,
) -> dict[str, Any]:
    """Recommend the lowest-cost alert threshold across capacity and cost settings.

    Sweeps the cost surface across every combination of ``candidate_thresholds``
    and ``alert_capacities`` using the same cost model as
    :func:`evaluate_alert_scores`, then reports the threshold with the lowest
    total cost for each capacity (``per_capacity``) and the single global
    recommendation (``recommended_threshold``) plus its full summary. Lets a
    learner read a recommended threshold that reflects operational tradeoffs
    rather than eyeballing a single threshold.

    Args:
        cases: Cases frame with at least ``case_id`` and ``alert_id``.
        case_outcomes: Outcomes frame with ``case_id`` and ``confirmed_fraud``.
        alert_scores: Scores frame with ``alert_id`` and ``score`` in [0, 1].
        candidate_thresholds: Thresholds to evaluate. Must be non-empty, each in
            [0, 1]. Defaults to :data:`DEFAULT_THRESHOLDS`.
        alert_capacities: Alert-investigation capacities to sweep. Must be
            non-empty, each positive.
        investigation_cost_chf: Per-alert investigation cost (non-negative).
        false_positive_cost_chf: Per-false-positive cost (non-negative).
        missed_fraud_cost_chf: Per-missed-fraud cost (non-negative). When
            ``None``, missed cost is driven by the joined ``loss_amount_chf``
            exactly as in :func:`evaluate_alert_scores`.

    Returns:
        A dict with ``per_capacity`` (one entry per alert capacity, each carrying
        its lowest-cost threshold and summary), ``recommended_threshold`` (the
        global lowest-cost threshold), ``recommended_summary`` (its full
        threshold summary), ``recommended_alert_capacity`` (the capacity at which
        the global minimum occurs), and ``cost_surface`` (one row per
        threshold × capacity combination).

    Raises:
        ValueError: If thresholds/capacities are empty/invalid or costs are
            negative.
    """
    normalized_thresholds = _normalize_thresholds(candidate_thresholds)
    capacities = _normalize_capacities(alert_capacities)
    _validate_non_negative_cost("investigation_cost_chf", investigation_cost_chf)
    _validate_non_negative_cost("false_positive_cost_chf", false_positive_cost_chf)
    if missed_fraud_cost_chf is not None:
        _validate_non_negative_cost("missed_fraud_cost_chf", missed_fraud_cost_chf)

    scored = _prepare_scored_outcomes(cases, case_outcomes, alert_scores)

    cost_surface: list[dict[str, Any]] = []
    per_capacity: dict[int, dict[str, Any]] = {}
    global_best: tuple[float, int, dict[str, Any]] | None = None

    for capacity in capacities:
        capacity_summaries = [
            _capacity_aware_summary(
                scored,
                threshold=threshold,
                alert_capacity=capacity,
                investigation_cost_chf=investigation_cost_chf,
                false_positive_cost_chf=false_positive_cost_chf,
                missed_fraud_cost_chf=missed_fraud_cost_chf,
            )
            for threshold in normalized_thresholds
        ]
        # Same tie-break as evaluate_alert_scores: total cost, then recall
        # (maximised), then alert volume (minimised).
        best_summary = min(
            capacity_summaries,
            key=lambda summary: (
                summary["total_cost_chf"],
                -summary["recall"],
                summary["alert_volume"],
            ),
        )
        per_capacity[capacity] = {
            "alert_capacity": capacity,
            "lowest_cost_threshold": best_summary["threshold"],
            "lowest_cost_summary": best_summary,
        }
        for threshold, summary in zip(normalized_thresholds, capacity_summaries, strict=True):
            cost_surface.append(
                {
                    "alert_capacity": capacity,
                    "threshold": threshold,
                    "total_cost_chf": summary["total_cost_chf"],
                    "recall": summary["recall"],
                    "precision": summary["precision"],
                    "alert_volume": summary["alert_volume"],
                    "over_capacity_alerts": summary["over_capacity_alerts"],
                }
            )
            candidate = (summary["total_cost_chf"], capacity, summary)
            if global_best is None or _cost_key(candidate) < _cost_key(global_best):
                global_best = candidate

    assert global_best is not None  # capacities is guaranteed non-empty above
    _total_cost, best_capacity, recommended_summary = global_best
    return {
        "per_capacity": per_capacity,
        "recommended_threshold": recommended_summary["threshold"],
        "recommended_summary": recommended_summary,
        "recommended_alert_capacity": best_capacity,
        "cost_surface": cost_surface,
    }


def _capacity_aware_summary(
    scored: pd.DataFrame,
    *,
    threshold: float,
    alert_capacity: int,
    investigation_cost_chf: float,
    false_positive_cost_chf: float,
    missed_fraud_cost_chf: float | None,
) -> dict[str, Any]:
    """Build a threshold summary whose cost respects investigation capacity.

    Mirrors :func:`_threshold_summary` but makes ``alert_capacity`` drive the
    cost, not just the reporting fields: when more alerts clear ``threshold``
    than the team can investigate, only the top ``alert_capacity`` alerts (by
    score) are investigated. Any over-capacity TRUE positive is then effectively
    missed (it was alerted but never reviewed), so missed-fraud cost applies to
    it. This is the operational reality the recommender must reflect so that
    sweeping capacity actually changes the recommendation.
    """
    selected = scored["_score"] >= threshold
    positives = scored["_label"]
    alert_volume = int(selected.sum())
    over_capacity = max(0, alert_volume - alert_capacity)

    # Investigate only the highest-scoring alerts, up to capacity. Ties at the
    # capacity boundary are broken by score (descending) then label so the
    # investigated set is deterministic.
    if over_capacity == 0:
        investigated = selected
        overflow = pd.Series(False, index=scored.index)
    else:
        ranked = scored.loc[selected].sort_values(
            "_score", ascending=False, kind="stable"
        )
        investigated_ids = ranked.head(alert_capacity).index
        overflow_ids = ranked.tail(over_capacity).index
        investigated = pd.Series(False, index=scored.index)
        investigated.loc[investigated_ids] = True
        overflow = pd.Series(False, index=scored.index)
        overflow.loc[overflow_ids] = True

    tp = int((investigated & positives).sum())
    fp = int((investigated & ~positives).sum())
    # Over-capacity true positives were alerted but not investigated: they slip
    # through and count as missed fraud. Over-capacity false positives are
    # dropped (no investigation, no FP cost).
    missed_overflow_tp = int((overflow & positives).sum())
    fn = int((~selected & positives).sum()) + missed_overflow_tp
    tn = int((~investigated & ~positives & ~overflow).sum())

    missed_cost = (
        fn * missed_fraud_cost_chf
        if missed_fraud_cost_chf is not None
        else float(
            scored.loc[~selected & positives, "_loss_amount_chf"].sum()
            + scored.loc[overflow & positives, "_loss_amount_chf"].sum()
        )
    )
    investigation_cost = int(investigated.sum()) * investigation_cost_chf
    false_positive_cost = fp * false_positive_cost_chf

    return {
        "threshold": threshold,
        "precision": _safe_divide(tp, tp + fp),
        "recall": _safe_divide(tp, tp + fn),
        "true_positives": tp,
        "false_positives": fp,
        "true_negatives": tn,
        "false_negatives": fn,
        "alert_volume": alert_volume,
        "alert_capacity": alert_capacity,
        "capacity_utilization": _round_metric(alert_volume / alert_capacity),
        "over_capacity_alerts": over_capacity,
        "investigation_cost_chf": _round_money(investigation_cost),
        "false_positive_cost_chf": _round_money(false_positive_cost),
        "missed_fraud_cost_chf": _round_money(missed_cost),
        "total_cost_chf": _round_money(
            investigation_cost + false_positive_cost + missed_cost
        ),
    }


def _normalize_capacities(capacities: Sequence[int]) -> tuple[int, ...]:
    """Validate and de-duplicate alert capacities, returning them sorted ascending.

    Rejects booleans and non-integral values rather than silently coercing them,
    so an accidental float (e.g. ``1.5``) or ``True`` raises instead of being
    truncated.
    """
    values: set[int] = set()
    for capacity in capacities:
        if isinstance(capacity, bool):
            raise ValueError("alert_capacities must contain integer values")
        numeric = float(capacity)
        if not numeric.is_integer():
            raise ValueError("alert_capacities must contain integer values")
        values.add(int(numeric))
    if not values:
        raise ValueError("alert_capacities must contain at least one capacity")
    if any(value <= 0 for value in values):
        raise ValueError("alert_capacities must contain positive integers")
    return tuple(sorted(values))


def _cost_key(candidate: tuple[float, int, dict[str, Any]]) -> tuple[float, float, int]:
    """Project a cost candidate onto the comparable (cost, -recall, volume) key."""
    _cost, _capacity, summary = candidate
    return (summary["total_cost_chf"], -summary["recall"], summary["alert_volume"])


__all__ = [
    "DEFAULT_FP_SEGMENT_COLUMNS",
    "DEFAULT_THRESHOLDS",
    "LIMITATION_SUMMARY",
    "concentrate_false_positives",
    "evaluate_alert_scores",
    "recommend_lowest_cost_threshold",
]
