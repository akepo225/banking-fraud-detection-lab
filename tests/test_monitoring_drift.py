"""Tests for drift and data-quality monitoring checks (v0.8 Wave 4, issue #204)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from banking_fraud_lab.monitoring import (
    DataQualityResult,
    ScoreDriftResult,
    check_feature_drift,
    check_monitoring_data_quality,
    check_score_drift,
)


def test_score_drift_flags_controlled_shift() -> None:
    """A review window shifted off the reference distribution is flagged as drift."""
    rng = np.random.default_rng(42)
    reference = rng.normal(loc=0.2, scale=0.05, size=500).clip(0.0, 1.0)
    shifted = rng.normal(loc=0.6, scale=0.05, size=500).clip(0.0, 1.0)
    stable = rng.normal(loc=0.2, scale=0.05, size=500).clip(0.0, 1.0)

    flagged = check_score_drift(reference, shifted, tolerance=0.1)
    assert flagged.dimension_id == "score_drift"
    assert flagged.evidence_source == "alert_scores"
    assert flagged.drifted is True
    assert flagged.mean_shift > 0.1

    stable_result = check_score_drift(reference, stable, tolerance=0.1)
    assert stable_result.drifted is False


def test_score_drift_deterministic() -> None:
    """Identical inputs yield identical results across calls."""
    reference = [0.1, 0.2, 0.2, 0.3, 0.15]
    review = [0.4, 0.5, 0.45, 0.55, 0.5]
    first = check_score_drift(reference, review, tolerance=0.05)
    second = check_score_drift(reference, review, tolerance=0.05)
    assert first == second
    assert isinstance(first, ScoreDriftResult)


def test_score_drift_rejects_out_of_range_scores() -> None:
    """Scores outside [0, 1] are rejected."""
    with pytest.raises(ValueError):
        check_score_drift([0.1, 1.5], [0.2, 0.3], tolerance=0.1)


def test_score_drift_rejects_bad_tolerance() -> None:
    """A negative or non-finite tolerance is rejected."""
    with pytest.raises(ValueError):
        check_score_drift([0.1, 0.2], [0.3, 0.4], tolerance=-0.1)
    with pytest.raises(ValueError):
        check_score_drift([0.1, 0.2], [0.3, 0.4], tolerance=float("nan"))


def test_feature_drift_numeric_and_categorical() -> None:
    """Numeric mean shift and categorical distribution shift are both reported."""
    reference = pd.DataFrame(
        {
            "amount": [10.0, 20.0, 30.0, 40.0],
            "channel": ["online", "online", "branch", "branch"],
        }
    )
    review = pd.DataFrame(
        {
            "amount": [100.0, 110.0, 120.0, 130.0],
            "channel": ["online", "branch", "branch", "branch"],
        }
    )

    result = check_feature_drift(reference, review, feature_columns=["amount", "channel"])
    result = result.set_index("feature")

    assert result.loc["amount", "dtype_kind"] == "numeric"
    assert result.loc["amount", "mean_shift"] == pytest.approx(90.0)
    assert result.loc["amount", "shifted"] is np.True_ or bool(result.loc["amount", "shifted"])

    assert result.loc["channel", "dtype_kind"] == "categorical"
    assert result.loc["channel", "distribution_shift"] >= 0.0
    assert result.loc["channel", "distribution_shift"] <= 1.0


def test_feature_drift_unknown_column_raises() -> None:
    """An unknown feature column raises ValueError listing it."""
    reference = pd.DataFrame({"amount": [1.0, 2.0]})
    review = pd.DataFrame({"amount": [3.0, 4.0]})
    with pytest.raises(ValueError):
        check_feature_drift(reference, review, feature_columns=["amount", "missing_col"])


def test_feature_drift_covers_user_story_5_set() -> None:
    """The user-story-5 feature families each produce a shift summary row."""
    columns = [
        "amount",
        "geography",
        "channel",
        "device",
        "relationship_activity",
        "user_behavior",
    ]
    reference = pd.DataFrame(
        {
            "amount": [100.0, 200.0, 300.0],
            "geography": ["CH", "CH", "DE"],
            "channel": ["online", "branch", "online"],
            "device": ["mobile", "mobile", "desktop"],
            "relationship_activity": [1.0, 0.0, 1.0],
            "user_behavior": [5.0, 10.0, 7.0],
        }
    )
    review = pd.DataFrame(
        {
            "amount": [500.0, 600.0, 700.0],
            "geography": ["DE", "DE", "FR"],
            "channel": ["branch", "branch", "branch"],
            "device": ["desktop", "desktop", "desktop"],
            "relationship_activity": [0.0, 0.0, 0.0],
            "user_behavior": [20.0, 25.0, 22.0],
        }
    )

    result = check_feature_drift(reference, review, feature_columns=columns)
    assert set(result["feature"]) == set(columns)
    assert (result["shifted"]).all()
    assert list(result["feature"]) == sorted(columns)


def test_data_quality_reuses_report() -> None:
    """A null in a required column fails the check; a clean frame passes."""
    clean = pd.DataFrame(
        {
            "score": [0.1, 0.2, 0.3],
            "banking_relationship_id": ["BR-1", "BR-2", "BR-3"],
        }
    )
    result = check_monitoring_data_quality(
        clean, required_columns=["score", "banking_relationship_id"]
    )
    assert result.dimension_id == "data_quality"
    assert result.evidence_source == "generate_dataset_quality_report"
    assert result.missing_required_columns == ()
    assert result.passed is True
    assert isinstance(result, DataQualityResult)

    with_nulls = pd.DataFrame(
        {
            "score": [0.1, None, 0.3],
            "banking_relationship_id": ["BR-1", "BR-2", "BR-3"],
        }
    )
    failed = check_monitoring_data_quality(
        with_nulls, required_columns=["score", "banking_relationship_id"]
    )
    assert "score" in failed.missing_required_columns
    assert failed.passed is False
    assert failed.row_count == 3


def test_data_quality_reports_missing_required_column() -> None:
    """A required column absent from the frame is reported in missing_required_columns."""
    frame = pd.DataFrame({"score": [0.1, 0.2]})
    result = check_monitoring_data_quality(
        frame, required_columns=["score", "banking_relationship_id"]
    )
    assert "banking_relationship_id" in result.missing_required_columns
    assert result.passed is False
