"""Tests for alert-aware fraud evaluation metrics."""

import math
from decimal import Decimal

import pandas as pd
import pytest

from banking_fraud_lab import evaluate_alert_scores, generate_minimal_banking_world


def test_alert_metrics_report_uses_generated_case_outcomes() -> None:
    """Generated case outcomes can be evaluated with model-like alert scores."""
    tables = generate_minimal_banking_world(seed=42)
    labeled_cases = tables["cases"].merge(
        tables["case_outcomes"][["case_id", "confirmed_fraud"]],
        on="case_id",
        how="inner",
        validate="one_to_one",
    )
    alert_scores = pd.DataFrame(
        {
            "alert_id": labeled_cases["alert_id"],
            "score": labeled_cases["confirmed_fraud"].map({True: 0.91, False: 0.12}),
        }
    )

    report = evaluate_alert_scores(
        tables["cases"],
        tables["case_outcomes"],
        alert_scores,
        thresholds=(0.5,),
        alert_capacity=1,
        investigation_cost_chf=50.0,
        false_positive_cost_chf=10.0,
    )

    summary = report["threshold_summaries"][0]
    assert report["population"] == {
        "case_count": 2,
        "confirmed_fraud_count": 1,
        "non_fraud_count": 1,
    }
    assert report["pr_auc"] == 1.0
    assert summary["precision"] == 1.0
    assert summary["recall"] == 1.0
    assert summary["alert_volume"] == 1
    assert summary["alert_capacity"] == 1
    assert summary["over_capacity_alerts"] == 0
    assert "accuracy is out of scope" in report["limitation_summary"]


def test_alert_metrics_report_known_confusion_matrix_and_costs() -> None:
    """Known score distributions should produce deterministic metrics and costs."""
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
            "score": [0.9, 0.8, 0.7, 0.1],
        }
    )

    report = evaluate_alert_scores(
        cases,
        case_outcomes,
        alert_scores,
        thresholds=(0.75,),
        alert_capacity=1,
        investigation_cost_chf=10.0,
        false_positive_cost_chf=5.0,
        missed_fraud_cost_chf=100.0,
    )

    summary = report["threshold_summaries"][0]
    assert math.isclose(report["pr_auc"], 0.833333)
    assert summary["precision"] == 0.5
    assert summary["recall"] == 0.5
    assert summary["true_positives"] == 1
    assert summary["false_positives"] == 1
    assert summary["false_negatives"] == 1
    assert summary["true_negatives"] == 1
    assert summary["alert_volume"] == 2
    assert summary["over_capacity_alerts"] == 1
    assert summary["investigation_cost_chf"] == 20.0
    assert summary["false_positive_cost_chf"] == 5.0
    assert summary["missed_fraud_cost_chf"] == 100.0
    assert summary["total_cost_chf"] == 125.0
    assert report["cost_curve"][0]["total_cost_chf"] == 125.0


def test_alert_metrics_report_uses_losses_for_missed_fraud_cost_by_default() -> None:
    """When no missed-fraud unit cost is supplied, missed loss amounts drive cost."""
    cases = pd.DataFrame({"case_id": ["CASE-1"], "alert_id": ["AL-1"]})
    case_outcomes = pd.DataFrame(
        {
            "case_id": ["CASE-1"],
            "confirmed_fraud": [True],
            "loss_amount_chf": [Decimal("250.00")],
        }
    )
    alert_scores = pd.DataFrame({"alert_id": ["AL-1"], "score": [0.1]})

    report = evaluate_alert_scores(
        cases,
        case_outcomes,
        alert_scores,
        thresholds=(0.5,),
        investigation_cost_chf=10.0,
    )

    summary = report["threshold_summaries"][0]
    assert summary["alert_volume"] == 0
    assert summary["missed_fraud_cost_chf"] == 250.0
    assert summary["total_cost_chf"] == 250.0


def test_alert_metrics_report_parses_string_confirmed_fraud_labels() -> None:
    """String exported fraud labels must not be coerced with Python truthiness."""
    cases = pd.DataFrame(
        {"case_id": ["CASE-1", "CASE-2"], "alert_id": ["AL-1", "AL-2"]}
    )
    case_outcomes = pd.DataFrame(
        {"case_id": ["CASE-1", "CASE-2"], "confirmed_fraud": ["True", "False"]}
    )
    alert_scores = pd.DataFrame({"alert_id": ["AL-1", "AL-2"], "score": [0.9, 0.8]})

    report = evaluate_alert_scores(cases, case_outcomes, alert_scores, thresholds=(0.5,))

    summary = report["threshold_summaries"][0]
    assert report["population"]["confirmed_fraud_count"] == 1
    assert report["population"]["non_fraud_count"] == 1
    assert summary["true_positives"] == 1
    assert summary["false_positives"] == 1


def test_alert_metrics_report_rejects_invalid_confirmed_fraud_labels() -> None:
    """Ambiguous fraud labels must fail before metric calculation."""
    cases = pd.DataFrame({"case_id": ["CASE-1"], "alert_id": ["AL-1"]})
    case_outcomes = pd.DataFrame({"case_id": ["CASE-1"], "confirmed_fraud": ["unknown"]})
    alert_scores = pd.DataFrame({"alert_id": ["AL-1"], "score": [0.8]})

    with pytest.raises(ValueError, match="confirmed_fraud"):
        evaluate_alert_scores(cases, case_outcomes, alert_scores)


def test_alert_metrics_report_rejects_missing_scores() -> None:
    """Every case outcome under evaluation must have an alert score."""
    cases = pd.DataFrame({"case_id": ["CASE-1"], "alert_id": ["AL-1"]})
    case_outcomes = pd.DataFrame({"case_id": ["CASE-1"], "confirmed_fraud": [True]})
    alert_scores = pd.DataFrame({"alert_id": ["AL-OTHER"], "score": [0.8]})

    with pytest.raises(ValueError, match="missing scores"):
        evaluate_alert_scores(cases, case_outcomes, alert_scores)


def test_alert_metrics_report_rejects_out_of_range_scores() -> None:
    """Scores must be normalized to the expected zero-to-one range."""
    cases = pd.DataFrame({"case_id": ["CASE-1"], "alert_id": ["AL-1"]})
    case_outcomes = pd.DataFrame({"case_id": ["CASE-1"], "confirmed_fraud": [True]})
    alert_scores = pd.DataFrame({"alert_id": ["AL-1"], "score": [1.2]})

    with pytest.raises(ValueError, match="between 0 and 1"):
        evaluate_alert_scores(cases, case_outcomes, alert_scores)


@pytest.mark.parametrize("threshold", (float("nan"), float("inf"), -float("inf")))
def test_alert_metrics_report_rejects_non_finite_thresholds(threshold: float) -> None:
    """Thresholds must be finite to produce meaningful alert summaries."""
    cases = pd.DataFrame({"case_id": ["CASE-1"], "alert_id": ["AL-1"]})
    case_outcomes = pd.DataFrame({"case_id": ["CASE-1"], "confirmed_fraud": [True]})
    alert_scores = pd.DataFrame({"alert_id": ["AL-1"], "score": [0.8]})

    with pytest.raises(ValueError, match="thresholds"):
        evaluate_alert_scores(cases, case_outcomes, alert_scores, thresholds=(threshold,))


@pytest.mark.parametrize(
    ("parameter_name", "kwargs"),
    (
        ("investigation_cost_chf", {"investigation_cost_chf": -1.0}),
        ("false_positive_cost_chf", {"false_positive_cost_chf": -1.0}),
        ("missed_fraud_cost_chf", {"missed_fraud_cost_chf": -1.0}),
    ),
)
def test_alert_metrics_report_rejects_negative_cost_inputs(
    parameter_name: str, kwargs: dict[str, float]
) -> None:
    """Cost inputs must be non-negative before cost summaries are calculated."""
    cases = pd.DataFrame({"case_id": ["CASE-1"], "alert_id": ["AL-1"]})
    case_outcomes = pd.DataFrame({"case_id": ["CASE-1"], "confirmed_fraud": [True]})
    alert_scores = pd.DataFrame({"alert_id": ["AL-1"], "score": [0.8]})

    with pytest.raises(ValueError, match=parameter_name):
        evaluate_alert_scores(cases, case_outcomes, alert_scores, **kwargs)
