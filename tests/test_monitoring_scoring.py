"""Tests for the deterministic batch-scoring pipeline (v0.8 Wave 2, issue #201)."""

from __future__ import annotations

import pandas as pd
import pytest

from banking_fraud_lab import monitoring
from banking_fraud_lab import recommend_lowest_cost_threshold
from banking_fraud_lab.monitoring import run_batch_scoring

_PATTERN_ID = "pb_high_value_movement"


def _tiny_scored_frame() -> pd.DataFrame:
    """Return a tiny scored frame with lineage incl. client_id and user_id."""
    return pd.DataFrame(
        {
            "score": [0.91, 0.12, 0.77, 0.55],
            "banking_relationship_id": ["BR-3", "BR-1", "BR-2", "BR-1"],
            "client_id": ["CL-1", None, "CL-3", "CL-1"],
            "user_id": [None, "U-2", "U-3", "U-2"],
            "account_id": ["AC-1", "AC-2", "AC-3", "AC-4"],
            "transaction_id": ["TX-1", "TX-2", "TX-3", "TX-4"],
            "alert_id": ["AL-1", "AL-2", "AL-3", "AL-4"],
        }
    )


def test_deterministic_output() -> None:
    """Same inputs + seed yield identical score/threshold rows and a stable timestamp."""
    frame = _tiny_scored_frame()
    first = run_batch_scoring(
        frame,
        detection_pattern_id=_PATTERN_ID,
        threshold=0.5,
        scorer="baseline-logreg",
        score_version="0.1.0",
        seed=42,
    )
    second = run_batch_scoring(
        frame,
        detection_pattern_id=_PATTERN_ID,
        threshold=0.5,
        scorer="baseline-logreg",
        score_version="0.1.0",
        seed=42,
    )

    assert first.batch_id == second.batch_id
    assert first.score_rows.equals(second.score_rows)
    assert first.threshold_rows.equals(second.threshold_rows)

    expected_scored_at = pd.Timestamp("2024-01-01") + pd.Timedelta(seconds=42)
    assert (first.score_rows["scored_at"] == expected_scored_at).all()
    assert first.threshold_rows["selected_at"].iloc[0] == expected_scored_at


def test_different_seed_changes_batch_id() -> None:
    """A different seed changes the batch id (and therefore the score ids)."""
    frame = _tiny_scored_frame()
    common = dict(
        detection_pattern_id=_PATTERN_ID,
        threshold=0.5,
        scorer="baseline-logreg",
        score_version="0.1.0",
    )
    first = run_batch_scoring(frame, seed=42, **common)
    second = run_batch_scoring(frame, seed=7, **common)

    assert first.batch_id != second.batch_id


def test_stable_order_independent_of_input_order() -> None:
    """Shuffling the input rows does not change the materialized score rows."""
    frame = _tiny_scored_frame()
    common = dict(
        detection_pattern_id=_PATTERN_ID,
        threshold=0.5,
        scorer="baseline-logreg",
        score_version="0.1.0",
        seed=42,
    )
    baseline = run_batch_scoring(frame, **common)

    shuffled = frame.sample(frac=1.0, random_state=123).reset_index(drop=True)
    rerun = run_batch_scoring(shuffled, **common)

    assert baseline.batch_id == rerun.batch_id
    pd.testing.assert_frame_equal(
        baseline.score_rows.reset_index(drop=True),
        rerun.score_rows.reset_index(drop=True),
    )


def test_score_rows_conform_to_score_spec() -> None:
    """Score rows match the SCORE spec columns and carry lineage plus the score."""
    frame = _tiny_scored_frame()
    result = run_batch_scoring(
        frame,
        detection_pattern_id=_PATTERN_ID,
        threshold=0.5,
        scorer="baseline-logreg",
        score_version="0.1.0",
    )

    assert list(result.score_rows.columns) == [c.name for c in monitoring.SCORE.columns]
    assert (result.score_rows["detection_pattern_id"] == _PATTERN_ID).all()
    assert (
        result.score_rows["banking_relationship_id"]
        .isin(frame["banking_relationship_id"])
        .all()
    )
    for column in ("client_id", "user_id", "account_id", "transaction_id", "alert_id"):
        assert column in result.score_rows.columns
    assert sorted(result.score_rows["score"].tolist()) == sorted(frame["score"].tolist())


def test_threshold_row_conforms_and_records_source() -> None:
    """The threshold row matches THRESHOLD spec, the threshold value, and active status."""
    result = run_batch_scoring(
        _tiny_scored_frame(),
        detection_pattern_id=_PATTERN_ID,
        threshold=0.75,
        scorer="baseline-logreg",
        score_version="0.1.0",
        selection_method="cost-optimal",
        evidence_ref="eval/run-001",
    )

    assert list(result.threshold_rows.columns) == [
        c.name for c in monitoring.THRESHOLD.columns
    ]
    row = result.threshold_rows.iloc[0]
    assert row["threshold_value"] == 0.75
    assert row["review_status"] == "active"
    assert row["selection_method"] == "cost-optimal"
    assert row["evidence_ref"] == "eval/run-001"


def test_threshold_sourced_from_v0_7_recommender() -> None:
    """The recommended threshold flows straight into the threshold row (reuse, not reimpl)."""
    cases = pd.DataFrame(
        {
            "case_id": ["CASE-1", "CASE-2", "CASE-3", "CASE-4"],
            "alert_id": ["AL-1", "AL-2", "AL-3", "AL-4"],
        }
    )
    case_outcomes = pd.DataFrame(
        {
            "case_id": ["CASE-1", "CASE-2", "CASE-3", "CASE-4"],
            "confirmed_fraud": [True, False, True, False],
        }
    )
    alert_scores = pd.DataFrame(
        {
            "alert_id": ["AL-1", "AL-2", "AL-3", "AL-4"],
            "score": [0.9, 0.8, 0.7, 0.1],
        }
    )

    recommendation = recommend_lowest_cost_threshold(cases, case_outcomes, alert_scores)
    recommended = recommendation["recommended_threshold"]

    scored_frame = pd.DataFrame(
        {
            "score": alert_scores["score"].to_numpy(),
            "banking_relationship_id": ["BR-1", "BR-2", "BR-3", "BR-4"],
            "alert_id": alert_scores["alert_id"].to_numpy(),
        }
    )
    result = run_batch_scoring(
        scored_frame,
        detection_pattern_id=_PATTERN_ID,
        threshold=recommended,
        scorer="baseline-logreg",
        score_version="0.1.0",
    )

    assert result.threshold_rows["threshold_value"].iloc[0] == recommended


def test_rejects_unknown_pattern_id() -> None:
    """An unknown Detection pattern id is rejected."""
    with pytest.raises(ValueError):
        run_batch_scoring(
            _tiny_scored_frame(),
            detection_pattern_id="not_a_pattern",
            threshold=0.5,
            scorer="baseline-logreg",
            score_version="0.1.0",
        )


@pytest.mark.parametrize("bad_threshold", [0.0, -0.1, 1.5])
def test_rejects_threshold_out_of_range(bad_threshold: float) -> None:
    """Thresholds outside (0, 1] are rejected."""
    with pytest.raises(ValueError):
        run_batch_scoring(
            _tiny_scored_frame(),
            detection_pattern_id=_PATTERN_ID,
            threshold=bad_threshold,
            scorer="baseline-logreg",
            score_version="0.1.0",
        )


def test_accepts_threshold_of_one() -> None:
    """A threshold of exactly 1.0 is the upper bound and is accepted."""
    result = run_batch_scoring(
        _tiny_scored_frame(),
        detection_pattern_id=_PATTERN_ID,
        threshold=1.0,
        scorer="baseline-logreg",
        score_version="0.1.0",
    )
    assert result.threshold_rows["threshold_value"].iloc[0] == 1.0


@pytest.mark.parametrize("missing", ["score", "banking_relationship_id"])
def test_rejects_frame_missing_required_columns(missing: str) -> None:
    """A scored frame missing a required column is rejected."""
    frame = _tiny_scored_frame().drop(columns=[missing])
    with pytest.raises(ValueError):
        run_batch_scoring(
            frame,
            detection_pattern_id=_PATTERN_ID,
            threshold=0.5,
            scorer="baseline-logreg",
            score_version="0.1.0",
        )


@pytest.mark.parametrize("bad_score", [1.5, -0.1])
def test_rejects_score_out_of_range(bad_score: float) -> None:
    """A score outside [0, 1] is rejected."""
    frame = pd.DataFrame(
        {
            "score": [bad_score],
            "banking_relationship_id": ["BR-1"],
        }
    )
    with pytest.raises(ValueError):
        run_batch_scoring(
            frame,
            detection_pattern_id=_PATTERN_ID,
            threshold=0.5,
            scorer="baseline-logreg",
            score_version="0.1.0",
        )


def test_batch_id_is_faithful_to_frame_contents() -> None:
    """Two frames with identical params but different entities get different batch ids.

    Guards the score_id primary key: distinct scored entities must never collide
    on batch_id / score_id just because they share row count and parameters.
    """
    common = dict(
        detection_pattern_id=_PATTERN_ID,
        threshold=0.5,
        scorer="baseline-logreg",
        score_version="0.1.0",
        seed=42,
    )
    frame_a = pd.DataFrame(
        {
            "score": [0.1, 0.2],
            "banking_relationship_id": ["BR-A", "BR-A"],
            "transaction_id": ["TX-1", "TX-2"],
        }
    )
    frame_b = pd.DataFrame(
        {
            "score": [0.9, 0.9],
            "banking_relationship_id": ["BR-Z", "BR-Z"],
            "transaction_id": ["TX-9", "TX-99"],
        }
    )
    result_a = run_batch_scoring(frame_a, **common)
    result_b = run_batch_scoring(frame_b, **common)

    assert result_a.batch_id != result_b.batch_id
    assert set(result_a.score_rows["score_id"]).isdisjoint(set(result_b.score_rows["score_id"]))


def test_threshold_is_not_recomputed() -> None:
    """The builder records the supplied threshold verbatim and never imports evaluation.

    The threshold source is the caller's responsibility (the v0.7 recommender); the
    builder neither recomputes it nor imports the evaluation threshold utilities, so
    the recorded threshold_value is the passed value exactly.
    """
    import banking_fraud_lab.monitoring.scoring as scoring_module

    result = run_batch_scoring(
        _tiny_scored_frame(),
        detection_pattern_id=_PATTERN_ID,
        threshold=0.37,
        scorer="baseline-logreg",
        score_version="0.1.0",
    )
    assert (result.threshold_rows["threshold_value"] == 0.37).all()
    assert not hasattr(scoring_module, "recommend_lowest_cost_threshold")
    assert not hasattr(scoring_module, "evaluate_alert_scores")


def test_rejects_empty_frame() -> None:
    """An empty scored frame is rejected (a batch scores at least one entity)."""
    frame = pd.DataFrame(
        {
            "score": pd.Series([], dtype="float64"),
            "banking_relationship_id": pd.Series([], dtype="object"),
        }
    )
    with pytest.raises(ValueError):
        run_batch_scoring(
            frame,
            detection_pattern_id=_PATTERN_ID,
            threshold=0.5,
            scorer="baseline-logreg",
            score_version="0.1.0",
        )


def test_accepts_numeric_string_threshold() -> None:
    """A numeric-string threshold is coerced to float and used verbatim (#201 review)."""
    result = run_batch_scoring(
        _tiny_scored_frame(),
        detection_pattern_id=_PATTERN_ID,
        threshold="0.5",
        scorer="baseline-logreg",
        score_version="0.1.0",
    )
    assert result.threshold_rows["threshold_value"].iloc[0] == 0.5


def test_rejects_null_banking_relationship_id() -> None:
    """A null banking_relationship_id is rejected as invalid lineage (#201 review)."""
    frame = pd.DataFrame(
        {
            "score": [0.9, 0.4],
            "banking_relationship_id": ["BR-1", None],
        }
    )
    with pytest.raises(ValueError):
        run_batch_scoring(
            frame,
            detection_pattern_id=_PATTERN_ID,
            threshold=0.5,
            scorer="baseline-logreg",
            score_version="0.1.0",
        )
