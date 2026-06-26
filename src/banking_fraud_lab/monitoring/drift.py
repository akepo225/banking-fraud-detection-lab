"""Runnable drift and data-quality monitoring checks for the v0.7 governance checklist.

Operationalizes two of the v0.7 governance monitoring dimensions defined in
:mod:`banking_fraud_lab.governance.spec`:

- :data:`~banking_fraud_lab.governance.spec.MON_DRIFT`
  (``dimension_id='score_drift'``, ``evidence_source='alert_scores'``) via
  :func:`check_score_drift`, which compares the alert-score distribution of a
  reference (training) window against a review window and flags a drift review
  when the mean shift exceeds a stated tolerance.
- :data:`~banking_fraud_lab.governance.spec.MON_DATA_QUALITY`
  (``dimension_id='data_quality'``,
  ``evidence_source='generate_dataset_quality_report'``) via
  :func:`check_monitoring_data_quality`, which wraps
  :func:`banking_fraud_lab.data_quality.generate_dataset_quality_report` for the
  report summary and checks the caller's monitoring frame for required-column
  completeness.

:func:`check_feature_drift` adds feature-level shift (PRD user story 5: amount,
geography, channel, device, relationship activity, user behavior) so a reviewer
can see which input family moved between windows. The caller passes the exact
column names, so the check stays schema-agnostic.

Every result references the governance ``dimension_id`` + ``evidence_source`` so
a finding maps onto the v0.7 monitoring checklist. All checks are deterministic:
fixed inputs yield byte-identical output across runs (no :func:`datetime.now`,
stable ordering).

Drift is measured on controlled synthetic shifts only; these checks never touch
real Client or User data.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from banking_fraud_lab.data_quality import DatasetQualityReport, generate_dataset_quality_report
from banking_fraud_lab.governance.spec import MON_DATA_QUALITY, MON_DRIFT


@dataclass(frozen=True)
class ScoreDriftResult:
    """Outcome of :func:`check_score_drift` for the ``score_drift`` dimension.

    Attributes mirror the MON_DRIFT governance vocabulary so a reviewer can trace
    a drift finding back to the v0.7 monitoring checklist item.
    """

    dimension_id: str
    evidence_source: str
    reference_mean: float
    review_mean: float
    mean_shift: float
    std_shift: float
    tolerance: float
    drifted: bool


@dataclass(frozen=True)
class DataQualityResult:
    """Outcome of :func:`check_monitoring_data_quality` for the ``data_quality`` dimension.

    Carries the ``generate_dataset_quality_report`` summary (row counts, issue
    count, the wrapped :class:`DatasetQualityReport`) plus the monitoring-frame
    required-column completeness check, so a reviewer sees both the generated-
    dataset report and the caller's monitoring-input completeness.
    """

    dimension_id: str
    evidence_source: str
    table_name: str
    row_count: int
    issue_count: int
    required_columns: tuple[str, ...]
    missing_required_columns: tuple[str, ...]
    report: DatasetQualityReport
    passed: bool


def check_score_drift(
    reference_scores: "pd.Series | np.ndarray | Sequence[float]",
    review_scores: "pd.Series | np.ndarray | Sequence[float]",
    *,
    tolerance: float,
) -> ScoreDriftResult:
    """Compare alert-score distributions between a reference and a review window.

    Implements MON_DRIFT.guidance ("flag a drift review when the shift exceeds a
    stated tolerance"): ``drifted`` is ``True`` when the absolute mean shift
    exceeds ``tolerance``. The result references
    :data:`~banking_fraud_lab.governance.spec.MON_DRIFT` so it maps onto the
    ``score_drift`` checklist dimension.

    Args:
        reference_scores: 1-D alert scores in ``[0, 1]`` from the training /
            reference window.
        review_scores: 1-D alert scores in ``[0, 1]`` from the review window.
        tolerance: Stated mean-shift tolerance; ``drifted`` is True when the
            absolute mean shift strictly exceeds it. Must be a finite
            non-negative number.

    Returns:
        A :class:`ScoreDriftResult` carrying the governance ``dimension_id`` and
        ``evidence_source``, both window means, the mean and std shifts, the
        tolerance, and the ``drifted`` flag.

    Raises:
        ValueError: If either input is empty, if ``tolerance`` is not a finite
            non-negative number, or if any score is outside ``[0, 1]``.
    """
    reference = _coerce_scores(reference_scores, name="reference_scores")
    review = _coerce_scores(review_scores, name="review_scores")
    if not np.isfinite(tolerance) or tolerance < 0:
        raise ValueError("tolerance must be a finite non-negative number")

    reference_mean = float(reference.mean())
    review_mean = float(review.mean())
    mean_shift = abs(review_mean - reference_mean)
    std_shift = abs(float(review.std()) - float(reference.std()))

    return ScoreDriftResult(
        dimension_id=MON_DRIFT.dimension_id,
        evidence_source=MON_DRIFT.evidence_source,
        reference_mean=reference_mean,
        review_mean=review_mean,
        mean_shift=float(mean_shift),
        std_shift=float(std_shift),
        tolerance=float(tolerance),
        drifted=bool(mean_shift > tolerance),
    )


def check_feature_drift(
    reference_frame: "pd.DataFrame",
    review_frame: "pd.DataFrame",
    *,
    feature_columns: "Sequence[str]",
) -> "pd.DataFrame":
    """Measure per-feature shift for the user-story-5 feature set.

    Numeric columns: ``mean_shift = abs(mean(review) - mean(reference))``.
    Categorical / object columns: distribution shift measured as the total-
    variation distance between value-share distributions
    (``sum |p_ref - p_review| / 2`` over the shared categories), in ``[0, 1]``.
    One row per feature, deterministically ordered by feature name.

    Args:
        reference_frame: Reference-window frame containing the feature columns.
        review_frame: Review-window frame containing the feature columns.
        feature_columns: Feature columns to measure (e.g. amount, geography,
            channel, device, relationship-activity, user-behavior columns).

    Returns:
        A frame with one row per feature and columns ``feature``, ``dtype_kind``
        (``'numeric'`` or ``'categorical'``), ``reference_mean`` and
        ``review_mean`` (numeric only), ``mean_shift`` (numeric) or
        ``distribution_shift`` (categorical), and ``shifted`` (True when the
        shift is greater than zero). Rows are ordered by feature name.

    Raises:
        ValueError: If any feature column is missing from either frame.
    """
    missing = sorted(
        column
        for column in feature_columns
        if column not in reference_frame.columns or column not in review_frame.columns
    )
    if missing:
        raise ValueError(f"feature_columns missing from reference/review frame: {missing}")

    rows: list[dict[str, Any]] = []
    for feature in sorted(feature_columns):
        reference_series = reference_frame[feature]
        review_series = review_frame[feature]
        if pd.api.types.is_numeric_dtype(reference_series) and pd.api.types.is_numeric_dtype(
            review_series
        ):
            reference_mean = float(pd.to_numeric(reference_series, errors="coerce").mean())
            review_mean = float(pd.to_numeric(review_series, errors="coerce").mean())
            shift = abs(review_mean - reference_mean)
            rows.append(
                {
                    "feature": feature,
                    "dtype_kind": "numeric",
                    "reference_mean": reference_mean,
                    "review_mean": review_mean,
                    "mean_shift": float(shift),
                    "distribution_shift": float("nan"),
                    "shifted": bool(shift > 0.0),
                }
            )
        else:
            shift = _total_variation_distance(reference_series, review_series)
            rows.append(
                {
                    "feature": feature,
                    "dtype_kind": "categorical",
                    "reference_mean": float("nan"),
                    "review_mean": float("nan"),
                    "mean_shift": float("nan"),
                    "distribution_shift": float(shift),
                    "shifted": bool(shift > 0.0),
                }
            )

    columns = [
        "feature",
        "dtype_kind",
        "reference_mean",
        "review_mean",
        "mean_shift",
        "distribution_shift",
        "shifted",
    ]
    return pd.DataFrame(rows, columns=columns)


def check_monitoring_data_quality(
    frame: "pd.DataFrame",
    *,
    required_columns: "Sequence[str]",
    table_name: str = "monitoring_inputs",
    seed: int = 42,
    scale: str = "tiny",
) -> DataQualityResult:
    """Check monitoring-input completeness, wrapping ``generate_dataset_quality_report``.

    Implements MON_DATA_QUALITY by reusing
    :func:`banking_fraud_lab.data_quality.generate_dataset_quality_report` for the
    report summary (row counts, issue count) and checking the caller's
    ``frame`` for required-column completeness. ``passed`` is True when no
    required column is missing from ``frame`` AND the wrapped report has no
    issues.

    Args:
        frame: Monitoring-input frame to check for required-column completeness.
        required_columns: Columns that must be present (and non-null) on
            ``frame``.
        table_name: Name recorded on the result for the monitoring-input table.
        seed: Seed forwarded to :func:`generate_dataset_quality_report` for the
            wrapped report summary.
        scale: Scale profile forwarded to :func:`generate_dataset_quality_report`
            for the wrapped report summary.

    Returns:
        A :class:`DataQualityResult` referencing the ``data_quality`` governance
        dimension and ``generate_dataset_quality_report`` evidence source,
        carrying the wrapped report, the row count, the issue count, the required
        columns, the sorted missing required columns, and the ``passed`` flag.

    Raises:
        ValueError: If any required column is missing from ``frame``.
    """
    missing = sorted(set(required_columns) - set(frame.columns))
    present_required = [column for column in required_columns if column in frame.columns]
    nullable_required = sorted(
        column
        for column in present_required
        if int(frame[column].isna().sum()) > 0
    )
    missing_required = tuple(sorted(missing + nullable_required))

    report = generate_dataset_quality_report(seed=seed, scale=scale)

    passed = not missing_required and report.passed

    return DataQualityResult(
        dimension_id=MON_DATA_QUALITY.dimension_id,
        evidence_source=MON_DATA_QUALITY.evidence_source,
        table_name=table_name,
        row_count=int(len(frame)),
        issue_count=int(len(report.issues)) + len(missing_required),
        required_columns=tuple(required_columns),
        missing_required_columns=missing_required,
        report=report,
        passed=bool(passed),
    )


def _coerce_scores(
    values: "pd.Series | np.ndarray | Sequence[float]", *, name: str
) -> np.ndarray:
    """Coerce a 1-D score input to a finite float64 numpy array, validating range."""
    array = np.asarray(values, dtype="float64")
    if array.ndim != 1:
        raise ValueError(f"{name} must be 1-D")
    if array.size == 0:
        raise ValueError(f"{name} must contain at least one score")
    if not np.isfinite(array).all():
        raise ValueError(f"{name} must contain only finite values")
    if (array < 0.0).any() or (array > 1.0).any():
        raise ValueError(f"{name} values must be in [0, 1]")
    return array


def _total_variation_distance(reference: "pd.Series", review: "pd.Series") -> float:
    """Return the total-variation distance between two categorical value-share distributions."""
    reference_counts = reference.astype("string").fillna("__null__").value_counts()
    review_counts = review.astype("string").fillna("__null__").value_counts()
    categories = sorted(set(reference_counts.index) | set(review_counts.index))
    reference_total = float(reference_counts.sum()) or 1.0
    review_total = float(review_counts.sum()) or 1.0
    total = 0.0
    for category in categories:
        p_ref = float(reference_counts.get(category, 0)) / reference_total
        p_review = float(review_counts.get(category, 0)) / review_total
        total += abs(p_ref - p_review)
    return total / 2.0


__all__ = [
    "DataQualityResult",
    "ScoreDriftResult",
    "check_feature_drift",
    "check_monitoring_data_quality",
    "check_score_drift",
]
