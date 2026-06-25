"""Tests for v0.7 false-positive concentration and threshold recommender.

These utilities are ADDITIVE to ``evaluate_alert_scores``: its signature and
output remain unchanged. The tests cover the FP-concentration-by-segment analysis
and the lowest-cost-threshold recommender that sweeps alert capacity and cost
parameters.
"""

from __future__ import annotations

from decimal import Decimal

import pandas as pd
import pytest

from banking_fraud_lab import (
    DEFAULT_FP_SEGMENT_COLUMNS,
    concentrate_false_positives,
    evaluate_alert_scores,
    recommend_lowest_cost_threshold,
)
from banking_fraud_lab.evaluation import (
    DEFAULT_THRESHOLDS,
)


# --- Shared deterministic fixtures -----------------------------------------


def _known_frames() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return (cases, case_outcomes, alert_scores, alerts) with known FP structure.

    Two false positives (AL-2, AL-4) clear the 0.5 threshold. AL-2 and AL-3
    share the same alert_type so concentration by alert_type groups them.
    """
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
            "loss_amount_chf": [
                Decimal("1000.00"),
                Decimal("0.00"),
                Decimal("500.00"),
                Decimal("0.00"),
            ],
        }
    )
    alert_scores = pd.DataFrame(
        {
            "alert_id": ["AL-1", "AL-2", "AL-3", "AL-4"],
            "score": [0.9, 0.8, 0.7, 0.6],
        }
    )
    alerts = pd.DataFrame(
        {
            "alert_id": ["AL-1", "AL-2", "AL-3", "AL-4"],
            "alert_type": [
                "private_banking_high_value",
                "new_beneficiary_payment",
                "new_beneficiary_payment",
                "session_payment_velocity",
            ],
            "banking_relationship_id": ["BR-1", "BR-2", "BR-2", "BR-3"],
        }
    )
    return cases, case_outcomes, alert_scores, alerts


# --- False-positive concentration -----------------------------------------


def test_concentrate_false_positives_groups_by_alert_type() -> None:
    """FPs must group by alert_type and report counts/shares/rates."""
    cases, outcomes, scores, alerts = _known_frames()
    result = concentrate_false_positives(
        cases, outcomes, scores, threshold=0.5, segment_columns=["alert_type"], alerts=alerts
    )
    expected_columns = {
        "alert_type",
        "false_positive_count",
        "false_positive_share",
        "alerted_count",
        "false_positive_rate",
    }
    assert expected_columns == set(result.columns)
    # Two false positives: new_beneficiary_payment (AL-2) and session_payment_velocity (AL-4).
    assert len(result) == 2
    by_type = result.set_index("alert_type")
    assert by_type.loc["new_beneficiary_payment", "false_positive_count"] == 1
    assert by_type.loc["session_payment_velocity", "false_positive_count"] == 1
    # Each segment is half of all false positives.
    assert pytest.approx(float(result["false_positive_share"].sum()), abs=1e-6) == 1.0
    # Sorted descending by false_positive_count (tie here, so deterministic by name).
    assert list(result["false_positive_count"]) == sorted(
        result["false_positive_count"], reverse=True
    )


def test_concentrate_false_positives_share_sums_to_one() -> None:
    """False-positive shares must partition all false positives (sum to 1)."""
    cases, outcomes, scores, alerts = _known_frames()
    result = concentrate_false_positives(
        cases, outcomes, scores, threshold=0.5, segment_columns=["alert_type"], alerts=alerts
    )
    assert pytest.approx(float(result["false_positive_share"].sum()), abs=1e-6) == 1.0


def test_concentrate_false_positives_by_banking_relationship() -> None:
    """Concentration by banking_relationship_id uses the glossary container."""
    cases, outcomes, scores, alerts = _known_frames()
    result = concentrate_false_positives(
        cases,
        outcomes,
        scores,
        threshold=0.5,
        segment_columns=["banking_relationship_id"],
        alerts=alerts,
    )
    by_br = result.set_index("banking_relationship_id")
    # AL-2 is on BR-2 (a false positive); AL-4 is on BR-3 (a false positive).
    assert by_br.loc["BR-2", "false_positive_count"] == 1
    assert by_br.loc["BR-3", "false_positive_count"] == 1


def test_concentrate_false_positives_derives_track_via_mapping() -> None:
    """activity_type_to_track must derive a track segment column."""
    cases, outcomes, scores, alerts = _known_frames()
    mapping = {
        "private_banking_high_value": "private_banking",
        "new_beneficiary_payment": "digital_banking",
        "session_payment_velocity": "digital_banking",
    }
    result = concentrate_false_positives(
        cases,
        outcomes,
        scores,
        threshold=0.5,
        segment_columns=["track"],
        alerts=alerts,
        activity_type_to_track=mapping,
    )
    # Both false positives (AL-2, AL-4) map to digital_banking.
    assert len(result) == 1
    assert result.iloc[0]["track"] == "digital_banking"
    assert result.iloc[0]["false_positive_count"] == 2


def test_concentrate_false_positives_is_deterministic() -> None:
    """The same inputs must produce identical concentration output."""
    cases, outcomes, scores, alerts = _known_frames()
    first = concentrate_false_positives(
        cases, outcomes, scores, threshold=0.5, segment_columns=["alert_type"], alerts=alerts
    )
    second = concentrate_false_positives(
        cases, outcomes, scores, threshold=0.5, segment_columns=["alert_type"], alerts=alerts
    )
    pd.testing.assert_frame_equal(first, second)


def test_concentrate_false_positives_empty_when_no_alerts_clear() -> None:
    """When no alerts clear the threshold the result is an empty frame."""
    cases, outcomes, scores, alerts = _known_frames()
    result = concentrate_false_positives(
        cases, outcomes, scores, threshold=0.95, segment_columns=["alert_type"], alerts=alerts
    )
    assert result.empty
    assert "false_positive_count" in result.columns


def test_concentrate_false_positives_default_segments_include_glossary_terms() -> None:
    """Default segment columns must reference alert_type, track, and Banking relationship."""
    assert "alert_type" in DEFAULT_FP_SEGMENT_COLUMNS
    assert "track" in DEFAULT_FP_SEGMENT_COLUMNS
    assert "banking_relationship_id" in DEFAULT_FP_SEGMENT_COLUMNS


def test_concentrate_false_positives_rejects_invalid_threshold() -> None:
    """Out-of-range thresholds must raise."""
    cases, outcomes, scores, alerts = _known_frames()
    with pytest.raises(ValueError, match="between 0 and 1"):
        concentrate_false_positives(
            cases, outcomes, scores, threshold=1.5, segment_columns=["alert_type"], alerts=alerts
        )


def test_concentrate_false_positives_rejects_no_resolved_segments() -> None:
    """When no requested segment column resolves to a present column, raise."""
    cases, outcomes, scores, alerts = _known_frames()
    with pytest.raises(ValueError, match="no segment_columns resolve"):
        concentrate_false_positives(
            cases,
            outcomes,
            scores,
            threshold=0.5,
            segment_columns=["nonexistent_column"],
            alerts=alerts,
        )


def test_concentrate_false_positives_uses_generated_data() -> None:
    """Concentration must work end-to-end on generated data with real segments."""
    from banking_fraud_lab import generate_minimal_banking_world

    tables = generate_minimal_banking_world(seed=42)
    labeled = tables["cases"].merge(
        tables["case_outcomes"][["case_id", "confirmed_fraud"]], on="case_id"
    )
    alert_scores = pd.DataFrame(
        {
            "alert_id": labeled["alert_id"],
            "score": labeled["confirmed_fraud"].map({True: 0.91, False: 0.8}),
        }
    )
    result = concentrate_false_positives(
        tables["cases"],
        tables["case_outcomes"],
        alert_scores,
        threshold=0.5,
        segment_columns=["alert_type"],
        alerts=tables["alerts"],
    )
    # The seeded minimal world always has at least one non-fraud alert.
    assert "false_positive_count" in result.columns


# --- Threshold recommender ------------------------------------------------


def test_recommend_threshold_returns_required_fields() -> None:
    """The recommender must return per_capacity, recommended_*, and cost_surface."""
    cases, outcomes, scores, _ = _known_frames()
    result = recommend_lowest_cost_threshold(
        cases,
        outcomes,
        scores,
        candidate_thresholds=(0.5, 0.75),
        alert_capacities=(1, 5),
        investigation_cost_chf=10.0,
        false_positive_cost_chf=5.0,
        missed_fraud_cost_chf=100.0,
    )
    expected_keys = {
        "per_capacity",
        "recommended_threshold",
        "recommended_summary",
        "recommended_alert_capacity",
        "cost_surface",
    }
    assert expected_keys <= set(result)
    assert set(result["per_capacity"]) == {1, 5}
    # cost_surface has one row per threshold x capacity combination.
    assert len(result["cost_surface"]) == 2 * 2


def test_recommend_threshold_global_minimum_is_lowest_cost() -> None:
    """The recommended threshold must be the global minimum of total cost."""
    cases, outcomes, scores, _ = _known_frames()
    result = recommend_lowest_cost_threshold(
        cases,
        outcomes,
        scores,
        candidate_thresholds=(0.5, 0.75, 0.85),
        alert_capacities=(1, 5, 10),
        investigation_cost_chf=10.0,
        false_positive_cost_chf=5.0,
        missed_fraud_cost_chf=100.0,
    )
    surface = pd.DataFrame(result["cost_surface"])
    min_row = surface.loc[surface["total_cost_chf"].idxmin()]
    assert result["recommended_threshold"] == min_row["threshold"]
    assert result["recommended_alert_capacity"] == min_row["alert_capacity"]


def test_recommend_threshold_is_deterministic() -> None:
    """The same inputs must produce an identical recommendation."""
    cases, outcomes, scores, _ = _known_frames()
    first = recommend_lowest_cost_threshold(
        cases, outcomes, scores, candidate_thresholds=(0.5, 0.75), alert_capacities=(1, 5)
    )
    second = recommend_lowest_cost_threshold(
        cases, outcomes, scores, candidate_thresholds=(0.5, 0.75), alert_capacities=(1, 5)
    )
    assert first["recommended_threshold"] == second["recommended_threshold"]
    assert first["recommended_alert_capacity"] == second["recommended_alert_capacity"]
    assert first["cost_surface"] == second["cost_surface"]


def test_recommend_threshold_higher_missed_cost_raises_threshold() -> None:
    """A higher missed-fraud cost must not lower the recommended threshold."""
    cases, outcomes, scores, _ = _known_frames()
    cheap_miss = recommend_lowest_cost_threshold(
        cases,
        outcomes,
        scores,
        candidate_thresholds=(0.5, 0.75),
        alert_capacities=(5,),
        missed_fraud_cost_chf=1.0,
    )
    expensive_miss = recommend_lowest_cost_threshold(
        cases,
        outcomes,
        scores,
        candidate_thresholds=(0.5, 0.75),
        alert_capacities=(5,),
        missed_fraud_cost_chf=10_000.0,
    )
    assert expensive_miss["recommended_threshold"] <= cheap_miss["recommended_threshold"]


def test_recommend_threshold_rejects_invalid_capacities() -> None:
    """Empty or non-positive capacities must raise."""
    cases, outcomes, scores, _ = _known_frames()
    with pytest.raises(ValueError, match="at least one capacity"):
        recommend_lowest_cost_threshold(cases, outcomes, scores, alert_capacities=())
    with pytest.raises(ValueError, match="positive integers"):
        recommend_lowest_cost_threshold(cases, outcomes, scores, alert_capacities=(0,))


@pytest.mark.parametrize("invalid", (1.5, True, False))
def test_recommend_threshold_rejects_non_integer_capacities(invalid: object) -> None:
    """Non-integer / boolean capacities must raise rather than be coerced."""
    cases, outcomes, scores, _ = _known_frames()
    with pytest.raises(ValueError, match="integer values"):
        recommend_lowest_cost_threshold(cases, outcomes, scores, alert_capacities=(invalid,))  # type: ignore[arg-type]


def test_recommend_threshold_capacity_affects_cost() -> None:
    """Alert capacity must actually change the cost (over-capacity positives missed).

    With a tight capacity, true-positive alerts that cannot be investigated are
    treated as missed fraud, so the total cost must differ from the unconstrained
    capacity case. This locks in the operational semantics the recommender must
    reflect: sweeping capacity genuinely changes the recommendation.
    """
    cases, outcomes, scores, _ = _known_frames()
    # 4 alerts clear a low threshold; capacity=1 means 3 overflow, of which the
    # overflowed true positives become missed fraud.
    tight = recommend_lowest_cost_threshold(
        cases,
        outcomes,
        scores,
        candidate_thresholds=(0.5,),
        alert_capacities=(1,),
        investigation_cost_chf=0.0,
        false_positive_cost_chf=0.0,
        missed_fraud_cost_chf=100.0,
    )
    loose = recommend_lowest_cost_threshold(
        cases,
        outcomes,
        scores,
        candidate_thresholds=(0.5,),
        alert_capacities=(100,),
        investigation_cost_chf=0.0,
        false_positive_cost_chf=0.0,
        missed_fraud_cost_chf=100.0,
    )
    tight_cost = tight["per_capacity"][1]["lowest_cost_summary"]["total_cost_chf"]
    loose_cost = loose["per_capacity"][100]["lowest_cost_summary"]["total_cost_chf"]
    # Tight capacity misses overflow fraud; loose capacity catches everything.
    assert tight_cost > loose_cost


def test_recommend_threshold_rejects_invalid_thresholds() -> None:
    """Empty or invalid thresholds must raise."""
    cases, outcomes, scores, _ = _known_frames()
    with pytest.raises(ValueError, match="at least one threshold"):
        recommend_lowest_cost_threshold(cases, outcomes, scores, candidate_thresholds=())
    with pytest.raises(ValueError, match="between 0 and 1"):
        recommend_lowest_cost_threshold(cases, outcomes, scores, candidate_thresholds=(1.5,))


def test_recommend_threshold_rejects_negative_costs() -> None:
    """Negative costs must raise."""
    cases, outcomes, scores, _ = _known_frames()
    with pytest.raises(ValueError, match="investigation_cost_chf"):
        recommend_lowest_cost_threshold(
            cases, outcomes, scores, investigation_cost_chf=-1.0
        )


# --- Backward compatibility of evaluate_alert_scores ----------------------


def test_evaluate_alert_scores_signature_and_output_unchanged() -> None:
    """The additive utilities must NOT change evaluate_alert_scores output."""
    cases, outcomes, scores, _ = _known_frames()
    report = evaluate_alert_scores(
        cases,
        outcomes,
        scores,
        thresholds=(0.75,),
        alert_capacity=1,
        investigation_cost_chf=10.0,
        false_positive_cost_chf=5.0,
        missed_fraud_cost_chf=100.0,
    )
    # The exact known-output contract from test_evaluation_metrics.py.
    summary = report["threshold_summaries"][0]
    assert summary["total_cost_chf"] == 125.0
    assert report["lowest_cost_threshold"] == 0.75
    assert "accuracy is out of scope" in report["limitation_summary"]


def test_default_thresholds_constant_unchanged() -> None:
    """The DEFAULT_THRESHOLDS constant must remain backward compatible."""
    assert DEFAULT_THRESHOLDS == (0.25, 0.5, 0.75)
