"""Tests for drift and data-quality monitoring checks (v0.8 Wave 4, issue #204)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from banking_fraud_lab.monitoring import (
    DataQualityResult,
    FEATURE_DRIFT_FAMILIES,
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


def test_feature_drift_links_to_governance_and_feature_families() -> None:
    """Feature drift rows reference the score_drift dimension id + evidence source.

    Each row carries a ``feature_family`` (one of the user-story-5 families or
    ``'other'``), the frozen ``MON_DRIFT`` ``dimension_id`` ('score_drift'), and
    the ``MON_DRIFT.evidence_source`` ('alert_scores'), so a feature drift
    finding maps onto the v0.7 monitoring checklist (PRD #204 governance linkage).
    """
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

    # Governance linkage: every row maps to the score_drift checklist dimension.
    assert "dimension_id" in result.columns
    assert "evidence_source" in result.columns
    assert "feature_family" in result.columns
    assert (result["dimension_id"] == "score_drift").all()
    assert (result["evidence_source"] == "alert_scores").all()

    # Each user-story-5 feature maps to its own family id (substring match).
    family_by_feature = dict(zip(result["feature"], result["feature_family"]))
    for family in columns:
        assert family_by_feature[family] == family


def test_feature_drift_family_covers_prefixed_and_unknown_columns() -> None:
    """Prefixed feature names map to their family; unknown ones resolve to 'other'."""
    reference = pd.DataFrame(
        {"amount_zscore": [0.1, 0.2], "mystery_signal": [1.0, 2.0]}
    )
    review = pd.DataFrame(
        {"amount_zscore": [0.9, 1.0], "mystery_signal": [5.0, 6.0]}
    )

    result = check_feature_drift(
        reference, review, feature_columns=["amount_zscore", "mystery_signal"]
    )
    family = dict(zip(result["feature"], result["feature_family"]))
    assert family["amount_zscore"] == "amount"
    assert family["mystery_signal"] == "other"
    assert set(FEATURE_DRIFT_FAMILIES) == {
        "amount",
        "geography",
        "channel",
        "device",
        "relationship_activity",
        "user_behavior",
    }


def test_feature_drift_preserves_existing_columns_and_order() -> None:
    """The original columns + row ordering are preserved; governance columns appended last."""
    reference = pd.DataFrame({"amount": [1.0, 2.0]})
    review = pd.DataFrame({"amount": [5.0, 6.0]})

    result = check_feature_drift(reference, review, feature_columns=["amount"])
    expected_leading = [
        "feature",
        "dtype_kind",
        "reference_mean",
        "review_mean",
        "mean_shift",
        "distribution_shift",
        "shifted",
    ]
    assert list(result.columns)[: len(expected_leading)] == expected_leading
    assert list(result.columns)[-3:] == [
        "feature_family",
        "dimension_id",
        "evidence_source",
    ]


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


def test_data_quality_in_range_inputs_pass() -> None:
    """A clean monitoring frame with in-range score / confirmed_fraud / loss passes.

    Confirms non-null AND in-range monitoring inputs (PRD #204 data-quality input
    validation): score in [0, 1], confirmed_fraud boolean-like, and
    loss_amount_chf non-negative.
    """
    clean = pd.DataFrame(
        {
            "score": [0.1, 0.2, 0.3],
            "confirmed_fraud": [True, False, True],
            "loss_amount_chf": [100.0, 0.0, 50.5],
        }
    )
    result = check_monitoring_data_quality(clean, required_columns=["score"])
    assert result.passed is True
    assert result.out_of_range_columns == ()
    assert isinstance(result, DataQualityResult)


def test_data_quality_rejects_score_out_of_range() -> None:
    """A score above 1.0 is reported in out_of_range_columns and fails the check."""
    frame = pd.DataFrame({"score": [0.1, 1.5]})
    result = check_monitoring_data_quality(frame, required_columns=["score"])
    assert "score" in result.out_of_range_columns
    assert result.passed is False


def test_data_quality_rejects_negative_loss_amount() -> None:
    """A negative loss_amount_chf is reported in out_of_range_columns and fails."""
    frame = pd.DataFrame({"loss_amount_chf": [100.0, -5.0]})
    result = check_monitoring_data_quality(frame, required_columns=[])
    assert "loss_amount_chf" in result.out_of_range_columns
    assert result.passed is False


def test_data_quality_rejects_misshapen_confirmed_fraud() -> None:
    """A non-boolean-like confirmed_fraud value is reported and fails the check."""
    frame = pd.DataFrame({"confirmed_fraud": [True, "maybe"]})
    result = check_monitoring_data_quality(frame, required_columns=[])
    assert "confirmed_fraud" in result.out_of_range_columns
    assert result.passed is False


def test_data_quality_accepts_boolean_like_confirmed_fraud_spellings() -> None:
    """Boolean-like confirmed_fraud spellings (0/1, true/false strings) pass."""
    frame = pd.DataFrame(
        {
            "score": [0.1, 0.2, 0.3, 0.4],
            "confirmed_fraud": [True, False, "true", "false"],
        }
    )
    result = check_monitoring_data_quality(frame, required_columns=["score"])
    assert "confirmed_fraud" not in result.out_of_range_columns
    assert result.passed is True


def test_data_quality_null_score_reported_as_missing_not_out_of_range() -> None:
    """A null required column is reported as missing, not as out-of-range."""
    frame = pd.DataFrame({"score": [0.1, None]})
    result = check_monitoring_data_quality(frame, required_columns=["score"])
    assert "score" in result.missing_required_columns
    assert "score" not in result.out_of_range_columns
    assert result.passed is False


def test_data_quality_issue_count_includes_out_of_range() -> None:
    """issue_count folds in out-of-range failures alongside missing columns."""
    frame = pd.DataFrame({"score": [1.5], "loss_amount_chf": [-1.0]})
    result = check_monitoring_data_quality(frame, required_columns=[])
    assert set(result.out_of_range_columns) == {"score", "loss_amount_chf"}
    assert result.issue_count >= 2
