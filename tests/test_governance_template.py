"""Tests for the v0.7 model-documentation template and monitoring checklist.

Covers the frozen section/dimension vocabulary and the deterministic fillable
builders (build_model_documentation, build_monitoring_checklist).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

from banking_fraud_lab import (
    MODEL_DOCUMENTATION_SECTIONS,
    MODEL_DOCUMENTATION_SECTION_IDS,
    MONITORING_CHECKLIST_DIMENSIONS,
    MONITORING_CHECKLIST_DIMENSION_IDS,
    ModelDocumentationSectionSpec,
    MonitoringChecklistDimensionSpec,
    build_model_documentation,
    build_monitoring_checklist,
    concentrate_false_positives,
    evaluate_alert_scores,
)
from banking_fraud_lab.governance import (
    REQUIRED_DOCUMENTATION_SECTION_IDS,
    REQUIRED_MONITORING_DIMENSION_IDS,
)


# --- Frozen vocabulary -----------------------------------------------------


def test_documentation_sections_are_frozen_dataclasses() -> None:
    """Each documentation section spec must be a frozen dataclass."""
    for spec in MODEL_DOCUMENTATION_SECTIONS:
        assert isinstance(spec, ModelDocumentationSectionSpec)
        with pytest.raises((AttributeError, TypeError)):
            spec.section_id = "mutated"  # type: ignore[misc]  # frozen contract


def test_monitoring_dimensions_are_frozen_dataclasses() -> None:
    """Each monitoring dimension spec must be a frozen dataclass."""
    for spec in MONITORING_CHECKLIST_DIMENSIONS:
        assert isinstance(spec, MonitoringChecklistDimensionSpec)
        with pytest.raises((AttributeError, TypeError)):
            spec.dimension_id = "mutated"  # type: ignore[misc]  # frozen contract


def test_required_sections_present() -> None:
    """The five PRD-required sections must all be in the vocabulary."""
    assert set(MODEL_DOCUMENTATION_SECTION_IDS) == {
        "purpose",
        "data_lineage",
        "assumptions",
        "limitations",
        "monitoring_needs",
    }
    assert REQUIRED_DOCUMENTATION_SECTION_IDS == frozenset(MODEL_DOCUMENTATION_SECTION_IDS)


def test_required_dimensions_present() -> None:
    """The five PRD-required monitoring dimensions must all be present."""
    assert set(MONITORING_CHECKLIST_DIMENSION_IDS) == {
        "score_drift",
        "metric_stability",
        "false_positive_concentration",
        "segment_review",
        "data_quality",
    }
    assert REQUIRED_MONITORING_DIMENSION_IDS == frozenset(MONITORING_CHECKLIST_DIMENSION_IDS)


# --- Deterministic model-documentation builder -----------------------------


@pytest.fixture
def fitted_model() -> tuple[Pipeline, list[str], pd.DataFrame]:
    """Return a fitted Pipeline + feature columns + a small model frame."""
    rng = np.random.default_rng(42)
    columns = ["amount_to_aum_ratio", "is_cross_border", "is_new_counterparty"]
    frame = pd.DataFrame(
        {
            "amount_to_aum_ratio": rng.uniform(0.0, 5.0, 60),
            "is_cross_border": rng.integers(0, 2, 60).astype(float),
            "is_new_counterparty": rng.integers(0, 2, 60).astype(float),
        }
    )
    labels = (frame["amount_to_aum_ratio"] > 3.0).astype(int)
    model = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("model", LogisticRegression(random_state=42, max_iter=1000, class_weight="balanced")),
        ]
    )
    model.fit(frame.to_numpy(), labels)
    return model, columns, frame


def test_build_model_documentation_has_all_sections(
    fitted_model: tuple[Pipeline, list[str], pd.DataFrame],
) -> None:
    """The documentation artifact must contain every required section, filled."""
    model, columns, frame = fitted_model
    doc = build_model_documentation(
        model,
        institution="Alpine Crest Private Bank",
        detection_pattern_id="pb_high_value_movement",
        feature_columns=columns,
        model_frame=frame,
        seed=42,
        scale="small",
    )
    assert set(doc["sections"]) == set(MODEL_DOCUMENTATION_SECTION_IDS)
    for section_id, section in doc["sections"].items():
        assert section["text"], f"section {section_id} text must be non-empty"
        assert section["display_name"]
    assert doc["institution"] == "Alpine Crest Private Bank"
    assert doc["detection_pattern_id"] == "pb_high_value_movement"


def test_build_model_documentation_is_deterministic(
    fitted_model: tuple[Pipeline, list[str], pd.DataFrame],
) -> None:
    """The same inputs must produce an identical documentation artifact."""
    model, columns, frame = fitted_model
    kwargs = dict(
        institution="NovaBank Digital",
        detection_pattern_id="digital_scam_to_mule",
        feature_columns=columns,
        model_frame=frame,
        seed=7,
        scale="tiny",
        cost_parameters={"investigation_cost_chf": 75.0, "missed_fraud_cost_chf": 100.0},
    )
    first = build_model_documentation(model, **kwargs)
    second = build_model_documentation(model, **kwargs)
    assert first == second


def test_build_model_documentation_records_lineage_and_metadata(
    fitted_model: tuple[Pipeline, list[str], pd.DataFrame],
) -> None:
    """Data lineage and metadata must record seed/scale/columns/row counts."""
    model, columns, frame = fitted_model
    doc = build_model_documentation(
        model,
        institution="Alpine Crest Private Bank",
        detection_pattern_id="pb_transaction_fraud",
        feature_columns=columns,
        model_frame=frame,
        seed=42,
        scale="small",
    )
    lineage = doc["sections"]["data_lineage"]["text"]
    assert "seed=42" in lineage
    assert "scale='small'" in lineage
    assert "60 rows x 3 columns" in lineage
    meta = doc["metadata"]
    assert meta["seed"] == 42
    assert meta["scale"] == "small"
    assert meta["row_count"] == 60
    assert meta["column_count"] == 3
    assert meta["feature_columns"] == columns


def test_build_model_documentation_rejects_unknown_institution(
    fitted_model: tuple[Pipeline, list[str], pd.DataFrame],
) -> None:
    """A non-glossary institution must raise (no real banks)."""
    model, columns, _ = fitted_model
    with pytest.raises(ValueError, match="institution must be one of"):
        build_model_documentation(
            model,
            institution="Real Bank PLC",
            detection_pattern_id="pb_high_value_movement",
            feature_columns=columns,
        )


def test_build_model_documentation_rejects_unknown_extra_section(
    fitted_model: tuple[Pipeline, list[str], pd.DataFrame],
) -> None:
    """An extra_section_text key not in the vocabulary must raise."""
    model, columns, _ = fitted_model
    with pytest.raises(ValueError, match="unknown sections"):
        build_model_documentation(
            model,
            institution="NovaBank Digital",
            detection_pattern_id="new_beneficiary_payment",
            feature_columns=columns,
            extra_section_text={"nonexistent_section": "text"},
        )


def test_build_model_documentation_appends_extra_section_text(
    fitted_model: tuple[Pipeline, list[str], pd.DataFrame],
) -> None:
    """extra_section_text must APPEND to a section's generated text."""
    model, columns, _ = fitted_model
    doc = build_model_documentation(
        model,
        institution="Alpine Crest Private Bank",
        detection_pattern_id="pb_high_value_movement",
        feature_columns=columns,
        extra_section_text={"limitations": "Bespoke limitation for this exercise."},
    )
    assert "Bespoke limitation for this exercise." in doc["sections"]["limitations"]["text"]


def test_build_model_documentation_estimator_summary_derived(
    fitted_model: tuple[Pipeline, list[str], pd.DataFrame],
) -> None:
    """When estimator_summary is omitted, it must be derived from the model."""
    model, columns, _ = fitted_model
    doc = build_model_documentation(
        model,
        institution="NovaBank Digital",
        detection_pattern_id="session_payment_velocity",
        feature_columns=columns,
    )
    assert "LogisticRegression" in doc["metadata"]["estimator_summary"]


def test_build_model_documentation_works_with_tree_model() -> None:
    """The builder must accept a bare tree estimator (no Pipeline)."""
    rng = np.random.default_rng(1)
    columns = ["db_session_payment_count", "db_asn_risk_score"]
    frame = pd.DataFrame(
        {
            "db_session_payment_count": rng.integers(1, 10, 40).astype(float),
            "db_asn_risk_score": rng.uniform(0.0, 1.0, 40),
        }
    )
    labels = (frame["db_session_payment_count"] >= 5).astype(int)
    tree = DecisionTreeClassifier(random_state=1).fit(frame.to_numpy(), labels)
    doc = build_model_documentation(
        tree,
        institution="NovaBank Digital",
        detection_pattern_id="digital_scam_to_mule",
        feature_columns=columns,
    )
    assert "DecisionTreeClassifier" in doc["metadata"]["estimator_summary"]


# --- Monitoring checklist builder ------------------------------------------


def _evaluation_output() -> dict:
    """Return a realistic evaluate_alert_scores output for the checklist."""
    cases = pd.DataFrame(
        {"case_id": ["C1", "C2", "C3", "C4"], "alert_id": ["A1", "A2", "A3", "A4"]}
    )
    outcomes = pd.DataFrame(
        {
            "case_id": ["C1", "C2", "C3", "C4"],
            "confirmed_fraud": [True, False, True, False],
        }
    )
    scores = pd.DataFrame(
        {"alert_id": ["A1", "A2", "A3", "A4"], "score": [0.9, 0.8, 0.7, 0.1]}
    )
    return evaluate_alert_scores(
        cases, outcomes, scores, thresholds=(0.5, 0.75), alert_capacity=2
    )


def _concentration_output() -> pd.DataFrame:
    """Return a realistic concentrate_false_positives output."""
    cases = pd.DataFrame(
        {"case_id": ["C1", "C2", "C3", "C4"], "alert_id": ["A1", "A2", "A3", "A4"]}
    )
    outcomes = pd.DataFrame(
        {
            "case_id": ["C1", "C2", "C3", "C4"],
            "confirmed_fraud": [True, False, True, False],
        }
    )
    scores = pd.DataFrame(
        {"alert_id": ["A1", "A2", "A3", "A4"], "score": [0.9, 0.8, 0.7, 0.6]}
    )
    alerts = pd.DataFrame(
        {
            "alert_id": ["A1", "A2", "A3", "A4"],
            "alert_type": [
                "new_beneficiary_payment",
                "new_beneficiary_payment",
                "session_payment_velocity",
                "session_payment_velocity",
            ],
        }
    )
    return concentrate_false_positives(
        cases, outcomes, scores, threshold=0.5, segment_columns=["alert_type"], alerts=alerts
    )


def test_build_monitoring_checklist_has_all_dimensions() -> None:
    """The checklist must contain every required dimension, filled."""
    checklist = build_monitoring_checklist(
        institution="NovaBank Digital",
        detection_pattern_id="digital_scam_to_mule",
        evaluation=_evaluation_output(),
        false_positive_concentration=_concentration_output(),
    )
    assert set(checklist["dimensions"]) == set(MONITORING_CHECKLIST_DIMENSION_IDS)
    for dimension_id, dimension in checklist["dimensions"].items():
        assert dimension["text"], f"dimension {dimension_id} text must be non-empty"
        assert dimension["status"] in {"review", "ok", "not_applicable"}
        assert dimension["evidence_source"]


def test_build_monitoring_checklist_is_deterministic() -> None:
    """The same inputs must produce an identical checklist."""
    kwargs = dict(
        institution="Alpine Crest Private Bank",
        detection_pattern_id="pb_high_value_movement",
        evaluation=_evaluation_output(),
        false_positive_concentration=_concentration_output(),
    )
    first = build_monitoring_checklist(**kwargs)
    second = build_monitoring_checklist(**kwargs)
    assert first == second


def test_build_monitoring_checklist_drift_status() -> None:
    """The drift dimension must report a shift and set status by tolerance."""
    baseline = pd.Series([0.1, 0.2, 0.15, 0.25])
    # Small shift within tolerance -> ok
    ok_checklist = build_monitoring_checklist(
        institution="NovaBank Digital",
        detection_pattern_id="session_payment_velocity",
        score_series=baseline,
        review_window_scores=pd.Series([0.12, 0.22, 0.17, 0.27]),
    )
    assert ok_checklist["dimensions"]["score_drift"]["status"] == "ok"
    # Large shift beyond tolerance -> review
    review_checklist = build_monitoring_checklist(
        institution="NovaBank Digital",
        detection_pattern_id="session_payment_velocity",
        score_series=baseline,
        review_window_scores=pd.Series([0.5, 0.6, 0.55, 0.65]),
    )
    assert review_checklist["dimensions"]["score_drift"]["status"] == "review"
    assert "shift" in review_checklist["dimensions"]["score_drift"]["text"].lower()


def test_build_monitoring_checklist_not_applicable_when_no_inputs() -> None:
    """Without evaluation/scores, dimensions must report not_applicable."""
    checklist = build_monitoring_checklist(
        institution="Alpine Crest Private Bank",
        detection_pattern_id="pb_transaction_fraud",
    )
    assert checklist["dimensions"]["score_drift"]["status"] == "not_applicable"
    assert checklist["dimensions"]["metric_stability"]["status"] == "not_applicable"
    assert checklist["dimensions"]["false_positive_concentration"]["status"] == "not_applicable"


def test_build_monitoring_checklist_empty_inputs_report_not_applicable_or_ok() -> None:
    """Empty series/frames must not produce NaN means or misleading status.

    - empty score_series -> drift not_applicable (no baseline)
    - baseline + empty review_window_scores -> drift not_applicable
    - empty false_positive_concentration frame -> FP concentration ok (nothing to review)
    """
    empty_drift = build_monitoring_checklist(
        institution="NovaBank Digital",
        detection_pattern_id="session_payment_velocity",
        score_series=pd.Series([], dtype=float),
        review_window_scores=pd.Series([], dtype=float),
    )
    assert empty_drift["dimensions"]["score_drift"]["status"] == "not_applicable"

    baseline_only_empty_review = build_monitoring_checklist(
        institution="NovaBank Digital",
        detection_pattern_id="session_payment_velocity",
        score_series=pd.Series([0.1, 0.2, 0.3]),
        review_window_scores=pd.Series([], dtype=float),
    )
    assert (
        baseline_only_empty_review["dimensions"]["score_drift"]["status"]
        == "not_applicable"
    )

    empty_fp = build_monitoring_checklist(
        institution="Alpine Crest Private Bank",
        detection_pattern_id="pb_high_value_movement",
        false_positive_concentration=pd.DataFrame(
            columns=[
                "alert_type", "false_positive_count", "false_positive_share",
                "alerted_count", "false_positive_rate",
            ]
        ),
    )
    assert empty_fp["dimensions"]["false_positive_concentration"]["status"] == "ok"


def test_build_monitoring_checklist_rejects_unknown_institution() -> None:
    """A non-glossary institution must raise."""
    with pytest.raises(ValueError, match="institution must be one of"):
        build_monitoring_checklist(
            institution="Generic Bank",
            detection_pattern_id="pb_high_value_movement",
        )


def test_build_monitoring_checklist_appends_extra_dimension_text() -> None:
    """extra_dimension_text must APPEND to a dimension's generated text."""
    checklist = build_monitoring_checklist(
        institution="NovaBank Digital",
        detection_pattern_id="new_beneficiary_payment",
        extra_dimension_text={"data_quality": "Bespoke review note."},
    )
    assert "Bespoke review note." in checklist["dimensions"]["data_quality"]["text"]


def test_build_monitoring_checklist_rejects_unknown_extra_dimension() -> None:
    """An extra_dimension_text key not in the vocabulary must raise."""
    with pytest.raises(ValueError, match="unknown dimensions"):
        build_monitoring_checklist(
            institution="NovaBank Digital",
            detection_pattern_id="new_beneficiary_payment",
            extra_dimension_text={"nonexistent_dimension": "text"},
        )


def test_build_monitoring_checklist_uses_real_evaluation_outputs() -> None:
    """The checklist must consume real evaluate_alert_scores + concentration output."""
    checklist = build_monitoring_checklist(
        institution="Alpine Crest Private Bank",
        detection_pattern_id="pb_high_value_movement",
        evaluation=_evaluation_output(),
        false_positive_concentration=_concentration_output(),
    )
    stability_text = checklist["dimensions"]["metric_stability"]["text"]
    assert "PR-AUC" in stability_text
    fp_text = checklist["dimensions"]["false_positive_concentration"]["text"]
    assert "false-positive segment" in fp_text


# --- Glossary / publication guardrail --------------------------------------


def test_documentation_uses_glossary_institutions_only(
    fitted_model: tuple[Pipeline, list[str], pd.DataFrame],
) -> None:
    """Generated text must use the glossary institutions, not real banks.

    Tightened so any certification / legal-advice / compliance wording fails
    unless it is the intended "no certification / no compliance claim"
    disclaimer: the word may only ever appear next to "no".
    """
    model, columns, _ = fitted_model
    forbidden = ("legal advice", "production deployment", "is certified")
    for institution in ("Alpine Crest Private Bank", "NovaBank Digital"):
        doc = build_model_documentation(
            model,
            institution=institution,
            detection_pattern_id="pb_high_value_movement",
            feature_columns=columns,
        )
        text = " ".join(s["text"] for s in doc["sections"].values()).lower()
        # No forbidden positive claims.
        for term in forbidden:
            assert term not in text, f"documentation text contains forbidden term {term!r}"
        # "certification" / "compliance" may only appear in a negated disclaimer.
        # Accept both "no X" and "no Y or X" / "no X ... Y" disclaimer phrasings
        # where a single "no" governs a list.
        for claim in ("certification", "compliance"):
            if claim in text:
                # The disclaimer sentence must contain "no" and both claim words
                # it lists together (e.g. "no certification or compliance claim").
                disclaimer_present = any(
                    f"no {claim}" in sentence or (
                        "no certification" in sentence and "compliance" in sentence
                    )
                    for sentence in text.split(".")
                    if claim in sentence
                )
                assert disclaimer_present, (
                    f"{claim!r} appears without a 'no' disclaimer"
                )
