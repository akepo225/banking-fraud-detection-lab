"""Alert-aware evaluation utilities for generated fraud case outcomes."""

from __future__ import annotations

from collections.abc import Sequence
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
    scored["_label"] = scored["confirmed_fraud"].astype(bool)
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
    normalized = tuple(sorted({float(threshold) for threshold in thresholds}, reverse=True))
    if not normalized:
        raise ValueError("thresholds must contain at least one threshold")
    if any(threshold < 0.0 or threshold > 1.0 for threshold in normalized):
        raise ValueError("thresholds must be between 0 and 1")
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


__all__ = ["DEFAULT_THRESHOLDS", "LIMITATION_SUMMARY", "evaluate_alert_scores"]
