"""Tests for the alert-decision, reviewer-action & audit-event builders (v0.8 Wave 3).

Builds score rows via the #201 batch-scoring builder, then chains
``decide_alerts`` -> ``record_reviewer_action`` and asserts the full score ->
alert_decision -> reviewer_action -> audit_event lineage conforms to the #200
frozen table vocabulary and carries Client / User / Banking relationship /
Detection-pattern lineage at every hop.
"""

from __future__ import annotations

import json

import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression

from banking_fraud_lab import monitoring
from banking_fraud_lab.interpretability.explanations import extract_feature_importance
from banking_fraud_lab.monitoring import decide_alerts, record_reviewer_action, run_batch_scoring

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


def _score_rows() -> pd.DataFrame:
    """Materialize score rows via the #201 batch-scoring builder."""
    batch = run_batch_scoring(
        _tiny_scored_frame(),
        detection_pattern_id=_PATTERN_ID,
        threshold=0.5,
        scorer="baseline-logreg",
        score_version="0.1.0",
    )
    return batch.score_rows


def test_decide_alerts_threshold_split() -> None:
    """Scores above/below threshold split into alert/suppress; lineage + ids carried."""
    score_rows = _score_rows()
    result = decide_alerts(score_rows, threshold=0.5, threshold_id="thr-1")

    decisions = result.alert_decision_rows
    assert list(decisions.columns) == [c.name for c in monitoring.ALERT_DECISION.columns]

    expected = ["alert" if score >= 0.5 else "suppress" for score in score_rows["score"]]
    assert decisions["decision"].tolist() == expected
    assert (decisions["score_at_decision"] == score_rows["score"].to_numpy()).all()

    assert decisions["score_id"].isin(score_rows["score_id"]).all()
    assert (decisions["threshold_id"] == "thr-1").all()
    assert (decisions["detection_pattern_id"] == _PATTERN_ID).all()
    assert decisions["banking_relationship_id"].isin(score_rows["banking_relationship_id"]).all()
    assert decisions["client_id"].isin(score_rows["client_id"]).any()
    assert decisions["user_id"].isin(score_rows["user_id"]).any()
    assert decisions["decided_at"].is_monotonic_increasing


def test_decide_alerts_emits_audit_with_frozen_type() -> None:
    """The audit chain matches AUDIT_EVENT spec and uses the frozen decision type."""
    score_rows = _score_rows()
    result = decide_alerts(score_rows, threshold=0.5, threshold_id="thr-1")

    audit = result.audit_rows
    assert list(audit.columns) == [c.name for c in monitoring.AUDIT_EVENT.columns]
    assert (audit["audit_event_type"] == monitoring.AUDIT_ALERT_DECISION_MADE).all()
    assert monitoring.AUDIT_ALERT_DECISION_MADE in monitoring.AUDIT_EVENT_TYPES
    assert audit["score_id"].isin(score_rows["score_id"]).all()
    assert audit["alert_decision_id"].isin(result.alert_decision_rows["alert_decision_id"]).all()
    assert audit["banking_relationship_id"].isin(score_rows["banking_relationship_id"]).all()
    assert audit["occurred_at"].is_monotonic_increasing
    assert audit["occurred_at"].is_unique


def test_record_reviewer_action_conforms_and_carries_lineage() -> None:
    """reviewer_action rows match REVIEWER_ACTION spec and carry decision lineage."""
    decisions = decide_alerts(_score_rows(), threshold=0.5, threshold_id="thr-1").alert_decision_rows
    result = record_reviewer_action(
        decisions,
        reviewer="rev-alice",
        action="confirm",
        rationale="Matches high-value movement playbook.",
    )

    actions = result.reviewer_action_rows
    assert list(actions.columns) == [c.name for c in monitoring.REVIEWER_ACTION.columns]
    assert "evidence" in actions.columns
    assert actions["alert_decision_id"].isin(decisions["alert_decision_id"]).all()
    assert (actions["reviewer"] == "rev-alice").all()
    assert (actions["action"] == "confirm").all()
    assert (actions["rationale"] == "Matches high-value movement playbook.").all()
    assert actions["banking_relationship_id"].isin(decisions["banking_relationship_id"]).all()
    assert actions["reviewed_at"].is_monotonic_increasing


def test_reviewer_evidence_is_real_v0_7_summary() -> None:
    """Reviewer evidence embeds a real v0.7 feature-importance summary, not a placeholder."""
    feature_cols = ["amount_zscore", "velocity_7d", "new_beneficiary_flag"]
    feature_frame = pd.DataFrame(
        {
            "amount_zscore": [0.1, 2.5, -0.3, 1.1, 3.2, 0.0, 0.8, 2.0],
            "velocity_7d": [1, 5, 0, 2, 6, 1, 3, 4],
            "new_beneficiary_flag": [0, 1, 0, 0, 1, 0, 1, 1],
        }
    )
    y = pd.Series([0, 1, 0, 0, 1, 0, 1, 1])
    model = LogisticRegression(random_state=42).fit(feature_frame, y)

    importance = extract_feature_importance(
        model,
        feature_cols,
        feature_frame=feature_frame,
        detection_pattern_id=_PATTERN_ID,
    )
    top_row = importance.sort_values("native_importance", ascending=False).iloc[0]
    evidence = {
        "explanation_family_id": str(top_row["explanation_family_id"]),
        "top_feature": str(top_row["feature"]),
        "native_importance": float(top_row["native_importance"]),
    }

    decisions = decide_alerts(_score_rows(), threshold=0.5, threshold_id="thr-1").alert_decision_rows
    result = record_reviewer_action(
        decisions,
        reviewer="rev-bob",
        action="escalate",
        rationale="Top driver flagged.",
        evidence=evidence,
    )

    cell = result.reviewer_action_rows["evidence"].iloc[0]
    assert isinstance(cell, str)
    assert top_row["feature"] in cell
    assert top_row["explanation_family_id"] in cell
    parsed = json.loads(cell)
    assert parsed["top_feature"] == top_row["feature"]


def test_lineage_walk_audit_to_score() -> None:
    """Walk an audit_event_id back through reviewer_action -> alert_decision -> score (story 7)."""
    score_rows = _score_rows()
    decision_result = decide_alerts(score_rows, threshold=0.5, threshold_id="thr-1")
    action_result = record_reviewer_action(
        decision_result.alert_decision_rows,
        reviewer="rev-carol",
        action="dismiss",
        rationale="Reviewed.",
    )

    decision_by_id = decision_result.alert_decision_rows.set_index("alert_decision_id")
    action_by_id = action_result.reviewer_action_rows.set_index("reviewer_action_id")
    score_by_id = score_rows.set_index("score_id")
    reviewer_audit = action_result.audit_rows
    first = reviewer_audit.iloc[0]

    reviewer_action = action_by_id.loc[first["reviewer_action_id"]]
    decision = decision_by_id.loc[reviewer_action["alert_decision_id"]]
    score = score_by_id.loc[decision["score_id"]]

    for node in (first, decision, score):
        assert pd.notna(node["banking_relationship_id"])
        assert pd.notna(node["detection_pattern_id"])
        assert pd.notna(node["client_id"]) or pd.notna(node["user_id"])

    assert pd.notna(reviewer_action["banking_relationship_id"])
    assert (
        pd.notna(reviewer_action["client_id"]) or pd.notna(reviewer_action["user_id"])
    )
    assert first["score_id"] == decision["score_id"] == score.name


def test_audit_chain_is_monotonic() -> None:
    """Audit occurred_at values are non-decreasing within each result."""
    decision_result = decide_alerts(_score_rows(), threshold=0.5, threshold_id="thr-1")
    action_result = record_reviewer_action(
        decision_result.alert_decision_rows,
        reviewer="rev-dan",
        action="confirm",
        rationale="ok",
    )
    assert decision_result.audit_rows["occurred_at"].is_monotonic_increasing
    assert action_result.audit_rows["occurred_at"].is_monotonic_increasing


def test_deterministic_output() -> None:
    """Same inputs + seed yield identical decision / reviewer / audit rows."""
    score_rows = _score_rows()
    dec_a = decide_alerts(score_rows, threshold=0.5, threshold_id="thr-1", seed=42)
    dec_b = decide_alerts(score_rows, threshold=0.5, threshold_id="thr-1", seed=42)
    assert dec_a.alert_decision_rows.equals(dec_b.alert_decision_rows)
    assert dec_a.audit_rows.equals(dec_b.audit_rows)

    act_a = record_reviewer_action(
        dec_a.alert_decision_rows, reviewer="r", action="confirm", rationale="x", seed=42
    )
    act_b = record_reviewer_action(
        dec_b.alert_decision_rows, reviewer="r", action="confirm", rationale="x", seed=42
    )
    assert act_a.reviewer_action_rows.equals(act_b.reviewer_action_rows)
    assert act_a.audit_rows.equals(act_b.audit_rows)


@pytest.mark.parametrize("bad_threshold", [0.0, 1.5])
def test_decide_alerts_rejects_bad_threshold(bad_threshold: float) -> None:
    """Thresholds outside (0, 1] are rejected; 1.0 is accepted."""
    with pytest.raises(ValueError):
        decide_alerts(_score_rows(), threshold=bad_threshold, threshold_id="thr-1")


def test_decide_alerts_accepts_threshold_of_one() -> None:
    """A threshold of exactly 1.0 is the upper bound and is accepted."""
    result = decide_alerts(_score_rows(), threshold=1.0, threshold_id="thr-1")
    assert (result.alert_decision_rows["score_at_decision"] <= 1.0).all()


def test_decide_alerts_rejects_empty_threshold_id() -> None:
    """An empty threshold id is rejected."""
    with pytest.raises(ValueError):
        decide_alerts(_score_rows(), threshold=0.5, threshold_id="")


def test_record_reviewer_action_serializes_dict_evidence() -> None:
    """Dict evidence is JSON-serialized, str evidence stored verbatim, None stays null."""
    decisions = decide_alerts(_score_rows(), threshold=0.5, threshold_id="thr-1").alert_decision_rows

    dict_result = record_reviewer_action(
        decisions, reviewer="r", action="confirm", rationale="x", evidence={"b": 2, "a": 1}
    )
    dict_cell = dict_result.reviewer_action_rows["evidence"].iloc[0]
    assert dict_cell == json.dumps({"a": 1, "b": 2}, sort_keys=True)
    assert json.loads(dict_cell) == {"a": 1, "b": 2}

    str_result = record_reviewer_action(
        decisions, reviewer="r", action="confirm", rationale="x", evidence="see-note-7"
    )
    assert (str_result.reviewer_action_rows["evidence"] == "see-note-7").all()

    none_result = record_reviewer_action(
        decisions, reviewer="r", action="confirm", rationale="x", evidence=None
    )
    assert none_result.reviewer_action_rows["evidence"].isna().all()


def test_alert_decision_id_differs_by_threshold() -> None:
    """Re-deciding the same score under a different threshold must not collide (#202 review)."""
    score_rows = _score_rows()
    result_a = decide_alerts(score_rows, threshold=0.5, threshold_id="thr-A")
    result_b = decide_alerts(score_rows, threshold=0.5, threshold_id="thr-B")
    ids_a = set(result_a.alert_decision_rows["alert_decision_id"])
    ids_b = set(result_b.alert_decision_rows["alert_decision_id"])
    assert ids_a.isdisjoint(ids_b)


def test_reviewer_action_id_differs_by_action() -> None:
    """Different reviewer actions on the same decision must not collide (#202 review)."""
    decisions = decide_alerts(_score_rows(), threshold=0.5, threshold_id="thr-1").alert_decision_rows
    confirmed = record_reviewer_action(
        decisions, reviewer="rev-x", action="confirm", rationale="ok"
    )
    dismissed = record_reviewer_action(
        decisions, reviewer="rev-x", action="dismiss", rationale="no"
    )
    ids_confirm = set(confirmed.reviewer_action_rows["reviewer_action_id"])
    ids_dismiss = set(dismissed.reviewer_action_rows["reviewer_action_id"])
    assert ids_confirm.isdisjoint(ids_dismiss)


@pytest.mark.parametrize("null_column", ["banking_relationship_id", "detection_pattern_id"])
def test_decide_alerts_rejects_null_lineage(null_column: str) -> None:
    """A null required lineage value in score_rows is rejected (#202 review)."""
    score_rows = _score_rows().copy()
    score_rows.loc[0, null_column] = None
    with pytest.raises(ValueError):
        decide_alerts(score_rows, threshold=0.5, threshold_id="thr-1")


def test_decide_alerts_accepts_numeric_string_threshold() -> None:
    """A numeric-string threshold is coerced to float and applied verbatim (#202 review)."""
    score_rows = _score_rows()
    result = decide_alerts(score_rows, threshold="0.5", threshold_id="thr-1")
    expected = ["alert" if score >= 0.5 else "suppress" for score in score_rows["score"]]
    assert result.alert_decision_rows["decision"].tolist() == expected


# --- Caller discipline: reviewer evidence as v0.7 interpretability (#202) ----


def _decisions() -> pd.DataFrame:
    """Return alert_decision rows for reviewer-action tests."""
    return decide_alerts(_score_rows(), threshold=0.5, threshold_id="thr-1").alert_decision_rows


def test_validate_evidence_rejects_arbitrary_dict() -> None:
    """validate_evidence=True rejects a dict lacking a v0.7 interpretability marker."""
    with pytest.raises(ValueError, match="v0.7 interpretability"):
        record_reviewer_action(
            _decisions(),
            reviewer="r",
            action="confirm",
            rationale="x",
            evidence={"arbitrary": "dict"},
            validate_evidence=True,
        )


def test_validate_evidence_accepts_v0_7_interpretability_dict() -> None:
    """validate_evidence=True accepts a real extract_feature_importance-shaped dict."""
    feature_cols = ["amount_zscore", "velocity_7d", "new_beneficiary_flag"]
    feature_frame = pd.DataFrame(
        {
            "amount_zscore": [0.1, 2.5, -0.3, 1.1, 3.2, 0.0, 0.8, 2.0],
            "velocity_7d": [1, 5, 0, 2, 6, 1, 3, 4],
            "new_beneficiary_flag": [0, 1, 0, 0, 1, 0, 1, 1],
        }
    )
    y = pd.Series([0, 1, 0, 0, 1, 0, 1, 1])
    model = LogisticRegression(random_state=42).fit(feature_frame, y)
    importance = extract_feature_importance(
        model,
        feature_cols,
        feature_frame=feature_frame,
        detection_pattern_id=_PATTERN_ID,
    )
    top_row = importance.sort_values("native_importance", ascending=False).iloc[0]
    evidence = {
        "explanation_family_id": str(top_row["explanation_family_id"]),
        "top_feature": str(top_row["feature"]),
        "native_importance": float(top_row["native_importance"]),
    }

    result = record_reviewer_action(
        _decisions(),
        reviewer="r",
        action="escalate",
        rationale="v0.7 driver flagged",
        evidence=evidence,
        validate_evidence=True,
    )
    cell = result.reviewer_action_rows["evidence"].iloc[0]
    assert isinstance(cell, str)
    parsed = json.loads(cell)
    assert parsed["explanation_family_id"] == top_row["explanation_family_id"]


@pytest.mark.parametrize("bad_evidence", ["see-note-7", None])
def test_validate_evidence_rejects_str_and_none(bad_evidence: str | None) -> None:
    """validate_evidence=True requires v0.7 interpretability output, not placeholders."""
    with pytest.raises(ValueError, match="v0.7 interpretability"):
        record_reviewer_action(
            _decisions(),
            reviewer="r",
            action="confirm",
            rationale="x",
            evidence=bad_evidence,
            validate_evidence=True,
        )


def test_validate_evidence_default_is_noop() -> None:
    """With validate_evidence=False (the default), an arbitrary dict is accepted unchanged."""
    result = record_reviewer_action(
        _decisions(),
        reviewer="r",
        action="confirm",
        rationale="x",
        evidence={"arbitrary": "dict"},
    )
    cell = result.reviewer_action_rows["evidence"].iloc[0]
    assert json.loads(cell) == {"arbitrary": "dict"}
