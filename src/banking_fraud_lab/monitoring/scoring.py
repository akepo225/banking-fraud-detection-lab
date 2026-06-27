"""Deterministic batch scoring that materializes monitoring score and threshold rows.

Turns a scored frame into production-monitoring ``score`` and ``threshold`` table
rows per the #200 frozen table vocabulary, reusing the v0.7 threshold recommender
(:func:`banking_fraud_lab.evaluation.recommend_lowest_cost_threshold`) /
:func:`banking_fraud_lab.evaluation.evaluate_alert_scores` as the threshold source
rather than recomputing a threshold. The PRD names "local batch scoring as the
required production pattern", so this builder is deterministic and table-shaped:
fixed inputs yield byte-identical output across runs, and rows conform exactly to
:mod:`banking_fraud_lab.monitoring.spec`.

Glossary terms are used verbatim where natural: each score row is scoped to a
Banking relationship and carries Client / User lineage; the Detection pattern and
Alert lifecycle vocabulary are reused unchanged.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from typing import Any

import pandas as pd

from banking_fraud_lab.monitoring.spec import SCORE, THRESHOLD
from banking_fraud_lab.schema import PATTERN_IDS

_OPTIONAL_LINEAGE_COLUMNS: tuple[str, ...] = (
    "client_id",
    "user_id",
    "account_id",
    "transaction_id",
    "alert_id",
)

_SORT_KEYS: tuple[str, ...] = (
    "banking_relationship_id",
    "transaction_id",
    "alert_id",
    "account_id",
    "client_id",
    "user_id",
)

_DEFAULT_TIMESTAMP_BASE = pd.Timestamp("2024-01-01")


@dataclass(frozen=True)
class BatchScoringResult:
    """Deterministic batch-scoring output: score + threshold monitoring rows."""

    batch_id: str
    score_rows: "pd.DataFrame"
    threshold_rows: "pd.DataFrame"


def run_batch_scoring(
    scored_frame: "pd.DataFrame",
    *,
    detection_pattern_id: str,
    threshold: float,
    scorer: str,
    score_version: str,
    seed: int = 42,
    selection_method: str = "cost-optimal",
    evidence_ref: str = "",
    scored_at: "pd.Timestamp | None" = None,
    selected_at: "pd.Timestamp | None" = None,
) -> BatchScoringResult:
    """Materialize deterministic monitoring score + threshold rows from a scored frame.

    Args:
        scored_frame: Rows = one per scored entity. REQUIRED columns: ``score``
            (float in [0, 1]) and ``banking_relationship_id``. OPTIONAL lineage
            columns carried through when present: ``client_id``, ``user_id``,
            ``account_id``, ``transaction_id``, ``alert_id``. Missing optional
            columns become null.
        detection_pattern_id: Must be in
            :data:`banking_fraud_lab.schema.PATTERN_IDS`, else ``ValueError``.
        threshold: Must be in ``(0.0, 1.0]`` (strictly greater than 0), else
            ``ValueError``. The caller sources this from the v0.7 recommender
            (:func:`recommend_lowest_cost_threshold` /
            :func:`evaluate_alert_scores`); this builder does NOT recompute it.
        scorer: Identifier of the scorer, recorded on every score row.
        score_version: Version of the scorer/model, recorded on every score row.
        seed: Drives the deterministic ``batch_id``, row ordering, and the
            default timestamps.
        selection_method: How the threshold was chosen; recorded on the threshold
            row for provenance.
        evidence_ref: Pointer to the evaluation artifact supporting the
            threshold; recorded on the threshold row.
        scored_at: Score timestamp. If ``None``, defaults to a seed-derived
            deterministic timestamp.
        selected_at: Threshold-selection timestamp. If ``None``, defaults to a
            seed-derived deterministic timestamp.

    Returns:
        A :class:`BatchScoringResult` whose ``score_rows`` conform exactly to
        :data:`banking_fraud_lab.monitoring.SCORE` and whose ``threshold_rows``
        conform exactly to :data:`banking_fraud_lab.monitoring.THRESHOLD`.

    Raises:
        ValueError: If ``detection_pattern_id`` is not a known Detection pattern,
            if ``threshold`` is outside ``(0.0, 1.0]``, if ``scored_frame`` is
            missing a required column, or if any ``score`` value is outside
            ``[0, 1]``.
    """
    if detection_pattern_id not in PATTERN_IDS:
        raise ValueError(
            f"detection_pattern_id must be one of {PATTERN_IDS}; got {detection_pattern_id!r}"
        )
    threshold = _validate_threshold(threshold)
    _validate_scored_frame(scored_frame)

    resolved_scored_at = _resolve_timestamp(scored_at, seed)
    resolved_selected_at = _resolve_timestamp(selected_at, seed)

    sort_keys = [key for key in _SORT_KEYS if key in scored_frame.columns]
    ordered = scored_frame.sort_values(
        by=sort_keys, kind="stable", na_position="last"
    ).reset_index(drop=True)

    batch_id = _derive_batch_id(
        ordered,
        detection_pattern_id=detection_pattern_id,
        scorer=scorer,
        score_version=score_version,
        seed=seed,
        threshold=threshold,
    )

    score_rows = _build_score_rows(
        ordered,
        batch_id=batch_id,
        detection_pattern_id=detection_pattern_id,
        scorer=scorer,
        score_version=score_version,
        scored_at=resolved_scored_at,
    )
    threshold_rows = _build_threshold_row(
        batch_id=batch_id,
        detection_pattern_id=detection_pattern_id,
        threshold=threshold,
        selected_at=resolved_selected_at,
        selection_method=selection_method,
        evidence_ref=evidence_ref,
    )

    return BatchScoringResult(
        batch_id=batch_id,
        score_rows=score_rows,
        threshold_rows=threshold_rows,
    )


def score_from_recommended_threshold(
    scored_frame: "pd.DataFrame",
    *,
    recommendation: "dict[str, Any]",
    detection_pattern_id: str,
    scorer: str,
    score_version: str,
    seed: int = 42,
) -> BatchScoringResult:
    """Run batch scoring using a v0.7 recommender threshold (the PRD #201 path).

    A thin provenance wrapper around :func:`run_batch_scoring` that makes the
    intended v0.8 path the easy path: the threshold is read verbatim from a
    :func:`banking_fraud_lab.evaluation.recommend_lowest_cost_threshold`
    recommendation (``recommendation['recommended_threshold']``) and recorded with
    its v0.7 provenance, so a reviewer can see the threshold came from the
    recommender / :func:`evaluate_alert_scores` rather than a hand-picked number.

    Args:
        scored_frame: Scored frame, same contract as :func:`run_batch_scoring`.
        recommendation: A
            :func:`~banking_fraud_lab.evaluation.recommend_lowest_cost_threshold`
            result dict; must carry a numeric ``recommended_threshold`` in
            ``(0.0, 1.0]``.
        detection_pattern_id: Known Detection pattern id.
        scorer: Identifier of the scorer.
        score_version: Version of the scorer/model.
        seed: Determinism seed forwarded to :func:`run_batch_scoring`.

    Returns:
        A :class:`BatchScoringResult` whose ``threshold_rows`` record the
        recommender threshold, ``selection_method='v0.7-recommend_lowest_cost_threshold'``
        and ``evidence_ref='recommend_lowest_cost_threshold'``.

    Raises:
        ValueError: If ``recommendation`` is missing ``recommended_threshold``
            or if the recommended threshold fails :func:`run_batch_scoring`'s
            ``(0.0, 1.0]`` validation.
    """
    if not isinstance(recommendation, dict) or "recommended_threshold" not in recommendation:
        raise ValueError(
            "recommendation must be a recommend_lowest_cost_threshold result carrying "
            "'recommended_threshold'"
        )
    recommended = recommendation["recommended_threshold"]
    return run_batch_scoring(
        scored_frame,
        detection_pattern_id=detection_pattern_id,
        threshold=recommended,
        scorer=scorer,
        score_version=score_version,
        seed=seed,
        selection_method="v0.7-recommend_lowest_cost_threshold",
        evidence_ref="recommend_lowest_cost_threshold",
    )


def _validate_threshold(threshold: float) -> float:
    """Return the threshold coerced to float, raising ValueError outside (0, 1]."""
    try:
        numeric = float(threshold)
    except (TypeError, ValueError) as exc:
        raise ValueError("threshold must be a finite number in (0.0, 1.0]") from exc
    if not math.isfinite(numeric) or numeric <= 0.0 or numeric > 1.0:
        raise ValueError("threshold must be in (0.0, 1.0]")
    return numeric


def _validate_scored_frame(scored_frame: "pd.DataFrame") -> None:
    """Raise ValueError when required columns are missing or scores are out of range."""
    required = {"score", "banking_relationship_id"}
    missing = sorted(required - set(scored_frame.columns))
    if missing:
        raise ValueError(f"scored_frame is missing required columns: {missing}")
    if scored_frame.empty:
        raise ValueError("scored_frame must contain at least one scored row")
    scores = pd.to_numeric(scored_frame["score"], errors="coerce")
    if scores.isna().any() or not scores.between(0.0, 1.0).all():
        raise ValueError("scored_frame.score values must be finite floats in [0, 1]")
    if scored_frame["banking_relationship_id"].isna().any():
        raise ValueError("scored_frame.banking_relationship_id values must be non-null")


def _resolve_timestamp(
    value: "pd.Timestamp | None", seed: int
) -> "pd.Timestamp":
    """Return the supplied timestamp or a seed-derived deterministic default."""
    if value is not None:
        return pd.Timestamp(value)
    return _DEFAULT_TIMESTAMP_BASE + pd.Timedelta(seconds=int(seed))


def _derive_batch_id(
    ordered_frame: "pd.DataFrame",
    *,
    detection_pattern_id: str,
    scorer: str,
    score_version: str,
    seed: int,
    threshold: float,
) -> str:
    """Build a deterministic batch id from the inputs AND the scored-frame contents.

    The fingerprint combines the batch parameters with a content digest of the
    sorted frame's score + lineage columns, so two batches that share parameters
    but score different entities get different batch ids (and therefore different
    score ids) instead of colliding.
    """
    content_columns = [
        column
        for column in ("score", "banking_relationship_id", *_OPTIONAL_LINEAGE_COLUMNS)
        if column in ordered_frame.columns
    ]
    content_csv = ordered_frame[content_columns].to_csv(index=False)
    fingerprint = "|".join(
        [
            detection_pattern_id,
            scorer,
            score_version,
            str(int(seed)),
            repr(float(threshold)),
            hashlib.sha256(content_csv.encode("utf-8")).hexdigest()[:12],
        ]
    )
    digest = hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()[:12]
    return f"batch-{digest}"


def _build_score_rows(
    ordered: "pd.DataFrame",
    *,
    batch_id: str,
    detection_pattern_id: str,
    scorer: str,
    score_version: str,
    scored_at: "pd.Timestamp",
) -> "pd.DataFrame":
    """Build score rows conforming exactly to the SCORE spec column order."""
    rows = len(ordered)
    score_ids = [f"{batch_id}-s{idx:06d}" for idx in range(rows)]
    column_sources: dict[str, pd.Series | list] = {
        "score_id": score_ids,
        "detection_pattern_id": [detection_pattern_id] * rows,
        "banking_relationship_id": ordered["banking_relationship_id"].to_numpy(),
        "scored_at": pd.Series(
            pd.Timestamp(scored_at), index=ordered.index, dtype="datetime64[ns]"
        ).to_numpy()
        if rows
        else [],
        "score": pd.to_numeric(ordered["score"], errors="raise").to_numpy(),
        "scorer": [scorer] * rows,
        "score_version": [score_version] * rows,
    }
    for column in _OPTIONAL_LINEAGE_COLUMNS:
        if column in ordered.columns:
            column_sources[column] = ordered[column].to_numpy()
        else:
            column_sources[column] = [None] * rows
    column_order = [column.name for column in SCORE.columns]
    return pd.DataFrame(column_sources)[column_order]


def _build_threshold_row(
    *,
    batch_id: str,
    detection_pattern_id: str,
    threshold: float,
    selected_at: "pd.Timestamp",
    selection_method: str,
    evidence_ref: str,
) -> "pd.DataFrame":
    """Build the single threshold row conforming exactly to the THRESHOLD spec."""
    threshold_id = f"{batch_id}-threshold"
    column_order = [column.name for column in THRESHOLD.columns]
    return pd.DataFrame(
        [
            {
                "threshold_id": threshold_id,
                "detection_pattern_id": detection_pattern_id,
                "threshold_value": float(threshold),
                "selected_at": pd.Timestamp(selected_at),
                "selection_method": selection_method,
                "review_status": "active",
                "evidence_ref": evidence_ref,
            }
        ]
    )[column_order]


__all__ = [
    "BatchScoringResult",
    "run_batch_scoring",
    "score_from_recommended_threshold",
]
