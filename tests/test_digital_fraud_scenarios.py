"""Tests for the expanded v0.4 NovaBank Digital fraud scenarios and noisy outcomes."""

from __future__ import annotations

import math

import pandas as pd
import pytest

from banking_fraud_lab import (
    build_learner_facing_views,
    generate_digital_fraud_scenarios_world,
    generate_minimal_banking_world,
    inject_digital_fraud_scenarios,
)
from banking_fraud_lab.generators.digital_banking import (
    ACCOUNT_TAKEOVER_BENEFICIARY_ACTIVITY_TYPE,
    ACCOUNT_TAKEOVER_SCENARIO_NAME,
    ACCOUNT_TAKEOVER_VELOCITY_ACTIVITY_TYPE,
    LABEL_TRUE_BENIGN,
    LABEL_TRUE_FRAUD,
    ONBOARDING_ABUSE_ACTIVITY_TYPE,
    ONBOARDING_ABUSE_SCENARIO_NAME,
    SUSPICIOUS_BENEFICIARY_CHANGE_ACTIVITY_TYPE,
    SUSPICIOUS_BENEFICIARY_CHANGE_SCENARIO_NAME,
)
from banking_fraud_lab.schema import PROTECTED_SCENARIO_ANSWER_KEYS
from banking_fraud_lab.schema.detection_patterns import (
    ACTIVITY_TYPE_TO_PATTERN,
    PATTERN_IDS,
)

NOVABANK = "NovaBank Digital"

SCENARIO_ACTIVITY_TYPES: dict[str, tuple[str, ...]] = {
    ACCOUNT_TAKEOVER_SCENARIO_NAME: (
        ACCOUNT_TAKEOVER_BENEFICIARY_ACTIVITY_TYPE,
        ACCOUNT_TAKEOVER_VELOCITY_ACTIVITY_TYPE,
    ),
    ONBOARDING_ABUSE_SCENARIO_NAME: (ONBOARDING_ABUSE_ACTIVITY_TYPE,),
    SUSPICIOUS_BENEFICIARY_CHANGE_SCENARIO_NAME: (
        SUSPICIOUS_BENEFICIARY_CHANGE_ACTIVITY_TYPE,
    ),
}


def test_expanded_scenarios_inject_all_four_families() -> None:
    """Each scenario family must contribute protected answer-key rows at the small scale."""
    tables = generate_digital_fraud_scenarios_world(
        seed=42, scale="small", scenario_prevalence=0.5, noisy_outcome_rate=0.3
    )
    answer_keys = tables[PROTECTED_SCENARIO_ANSWER_KEYS]

    for scenario_name in SCENARIO_ACTIVITY_TYPES:
        scenario_keys = answer_keys[answer_keys["scenario_name"] == scenario_name]
        assert not scenario_keys.empty, f"{scenario_name} produced no answer-key rows"


def test_each_scenario_maps_to_a_valid_existing_pattern_id() -> None:
    """Scenario activity types must resolve to existing Detection pattern IDs only."""
    for activity_types in SCENARIO_ACTIVITY_TYPES.values():
        for activity_type in activity_types:
            assert activity_type in ACTIVITY_TYPE_TO_PATTERN, (
                f"activity_type {activity_type!r} is not in ACTIVITY_TYPE_TO_PATTERN"
            )
            pattern_id = ACTIVITY_TYPE_TO_PATTERN[activity_type]
            assert pattern_id in PATTERN_IDS
            assert pattern_id in {
                "digital_scam_to_mule",
                "new_beneficiary_payment",
                "session_payment_velocity",
            }, f"Scenario mapped to a non-digital pattern ID: {pattern_id}"


def test_scenario_activity_types_only_use_valid_pattern_ids_in_data() -> None:
    """Generated scenario activities must reference only valid digital pattern IDs."""
    tables = generate_digital_fraud_scenarios_world(seed=42, scale="small")

    scenario_activities = tables["suspicious_activities"][
        tables["suspicious_activities"]["activity_type"].isin(
            {activity for group in SCENARIO_ACTIVITY_TYPES.values() for activity in group}
        )
    ]
    assert not scenario_activities.empty
    observed_patterns = {
        ACTIVITY_TYPE_TO_PATTERN[activity_type]
        for activity_type in scenario_activities["activity_type"]
    }
    assert observed_patterns <= {
        "digital_scam_to_mule",
        "new_beneficiary_payment",
        "session_payment_velocity",
    }


def _scenario_answer_keys(tables: dict[str, pd.DataFrame], scenario_name: str) -> pd.DataFrame:
    """Return protected answer-key rows for one scenario."""
    return tables[PROTECTED_SCENARIO_ANSWER_KEYS][
        tables[PROTECTED_SCENARIO_ANSWER_KEYS]["scenario_name"] == scenario_name
    ]


def _scenario_activities(tables: dict[str, pd.DataFrame], scenario_name: str) -> pd.DataFrame:
    """Return suspicious-activity rows traced from one scenario's answer-key transactions."""
    transactions = _scenario_answer_keys(tables, scenario_name)["entity_id"]
    return tables["suspicious_activities"][
        tables["suspicious_activities"]["transaction_id"].isin(transactions)
    ]


def _scenario_cases(tables: dict[str, pd.DataFrame], scenario_name: str) -> pd.DataFrame:
    """Return case rows traced from one scenario's answer-key transactions."""
    transactions = _scenario_answer_keys(tables, scenario_name)["entity_id"]
    return tables["cases"][tables["cases"]["transaction_id"].isin(transactions)]


def test_account_takeover_surfaces_new_beneficiary_and_velocity_signals() -> None:
    """Account-takeover alerts must carry new-beneficiary and session velocity context."""
    tables = generate_digital_fraud_scenarios_world(seed=42, scale="small")
    activities = _scenario_activities(tables, ACCOUNT_TAKEOVER_SCENARIO_NAME)
    assert not activities.empty
    assert set(activities["activity_type"]) <= {
        ACCOUNT_TAKEOVER_BENEFICIARY_ACTIVITY_TYPE,
        ACCOUNT_TAKEOVER_VELOCITY_ACTIVITY_TYPE,
    }

    takeover_alerts = tables["alerts"][
        tables["alerts"]["suspicious_activity_id"].isin(activities["suspicious_activity_id"])
    ]
    reasons = " ".join(takeover_alerts["reason"]).lower()
    assert "new beneficiary" in reasons or "newly changed beneficiary" in reasons
    assert "velocity" in reasons

    takeover_sessions = tables["sessions"][
        tables["sessions"]["session_id"].isin(takeover_alerts["session_id"])
    ]
    assert takeover_sessions["device_fingerprint_hash"].notna().all()
    assert (takeover_sessions["asn_risk_score"] >= 50).all()


def test_onboarding_abuse_uses_early_life_accounts_and_onward_payments() -> None:
    """Onboarding-abuse must move funds onward from recently opened accounts."""
    tables = generate_digital_fraud_scenarios_world(seed=42, scale="small")
    activities = _scenario_activities(tables, ONBOARDING_ABUSE_SCENARIO_NAME)
    assert not activities.empty

    onward_transactions = tables["transactions"][
        tables["transactions"]["transaction_id"].isin(activities["transaction_id"])
    ]
    assert set(onward_transactions["direction"]) == {"debit"}
    assert set(onward_transactions["description"]) == {
        "Rapid onward payment from an onboarding-abuse account"
    }
    scenario_accounts = tables["accounts"][
        tables["accounts"]["account_id"].isin(activities["account_id"])
    ]
    incoming_by_account = (
        tables["transactions"][
            tables["transactions"]["description"]
            == "Incoming funds into a recently onboarded NovaBank account"
        ]
        .set_index("account_id")["booked_at"]
    )
    assert all(
        pd.Timestamp(account.opened_at)
        <= pd.Timestamp(incoming_by_account.loc[account.account_id]) - pd.Timedelta(hours=12)
        for account in scenario_accounts.itertuples(index=False)
        if account.account_id in incoming_by_account.index
    )


def test_suspicious_beneficiary_change_records_beneficiary_update_event() -> None:
    """Suspicious beneficiary-change beneficiaries must record an update lifecycle event."""
    tables = generate_digital_fraud_scenarios_world(seed=42, scale="small")
    activities = _scenario_activities(tables, SUSPICIOUS_BENEFICIARY_CHANGE_SCENARIO_NAME)
    assert not activities.empty
    change_beneficiaries = tables["payment_beneficiaries"][
        tables["payment_beneficiaries"]["payment_beneficiary_id"].isin(
            activities["payment_beneficiary_id"]
        )
    ]
    assert set(change_beneficiaries["beneficiary_change_event"]) == {"beneficiary_updated"}


def test_noisy_outcomes_disagree_with_true_protected_labels() -> None:
    """A deterministic subset of scenario outcomes must disagree with the true label."""
    tables = generate_digital_fraud_scenarios_world(
        seed=42, scale="small", scenario_prevalence=0.5, noisy_outcome_rate=0.3
    )
    answer_keys = tables[PROTECTED_SCENARIO_ANSWER_KEYS]
    scenario_names = (
        ACCOUNT_TAKEOVER_SCENARIO_NAME,
        ONBOARDING_ABUSE_SCENARIO_NAME,
        SUSPICIOUS_BENEFICIARY_CHANGE_SCENARIO_NAME,
    )
    scenario_keys = answer_keys[answer_keys["scenario_name"].isin(scenario_names)]

    outcomes = tables["case_outcomes"].merge(
        tables["cases"][["case_id", "transaction_id"]],
        on="case_id",
        how="left",
    ).merge(
        scenario_keys[["entity_id", "label_value"]],
        left_on="transaction_id",
        right_on="entity_id",
        how="left",
    )
    scenario_outcomes = outcomes.dropna(subset=["label_value"])

    uninvestigated_but_fraud = scenario_outcomes[
        (scenario_outcomes["label_value"] == LABEL_TRUE_FRAUD)
        & (~scenario_outcomes["confirmed_fraud"])
    ]
    confirmed_but_benign = scenario_outcomes[
        (scenario_outcomes["label_value"] == LABEL_TRUE_BENIGN)
        & (scenario_outcomes["confirmed_fraud"])
    ]
    assert not uninvestigated_but_fraud.empty, (
        "Expected at least one uninvestigated-but-fraud noisy outcome"
    )
    assert not confirmed_but_benign.empty, (
        "Expected at least one confirmed-but-benign noisy outcome"
    )
    noisy_notes = " ".join(
        scenario_outcomes.loc[
            (scenario_outcomes["label_value"] == LABEL_TRUE_FRAUD)
            & (~scenario_outcomes["confirmed_fraud"]),
            "notes",
        ]
    ).lower()
    assert "noisy" in noisy_notes or "capacity" in noisy_notes


def test_noisy_outcome_rate_zero_keeps_clean_labels() -> None:
    """With noisy_outcome_rate=0 every true-fraud scenario outcome must confirm fraud."""
    tables = generate_digital_fraud_scenarios_world(
        seed=42, scale="small", scenario_prevalence=0.5, noisy_outcome_rate=0.0
    )
    answer_keys = tables[PROTECTED_SCENARIO_ANSWER_KEYS]
    scenario_names = (
        ACCOUNT_TAKEOVER_SCENARIO_NAME,
        SUSPICIOUS_BENEFICIARY_CHANGE_SCENARIO_NAME,
    )
    scenario_keys = answer_keys[answer_keys["scenario_name"].isin(scenario_names)]
    true_fraud_transactions = scenario_keys.loc[
        scenario_keys["label_value"] == LABEL_TRUE_FRAUD, "entity_id"
    ]
    outcomes = tables["case_outcomes"].merge(
        tables["cases"][["case_id", "transaction_id"]],
        on="case_id",
        how="left",
    )
    true_fraud_outcomes = outcomes[
        outcomes["transaction_id"].isin(true_fraud_transactions)
    ]
    assert true_fraud_outcomes["confirmed_fraud"].all()
    assert set(true_fraud_outcomes["outcome_type"]) == {"confirmed-fraud"}
    assert set(scenario_keys["label_value"]) == {LABEL_TRUE_FRAUD}


def test_prevalence_scales_scenario_answer_keys() -> None:
    """Scenario answer-key counts must scale with requested prevalence."""
    digital_account_count = (
        generate_minimal_banking_world(seed=42, scale="small")["accounts"]
        .query("institution_name == @NOVABANK")
        .shape[0]
    )

    low = generate_digital_fraud_scenarios_world(
        seed=42, scale="small", scenario_prevalence=0.3, noisy_outcome_rate=0.0
    )[PROTECTED_SCENARIO_ANSWER_KEYS]
    high = generate_digital_fraud_scenarios_world(
        seed=42, scale="small", scenario_prevalence=1.0, noisy_outcome_rate=0.0
    )[PROTECTED_SCENARIO_ANSWER_KEYS]

    takeover_low = _scenario_key_count(low, ACCOUNT_TAKEOVER_SCENARIO_NAME)
    takeover_high = _scenario_key_count(high, ACCOUNT_TAKEOVER_SCENARIO_NAME)
    assert takeover_low == math.ceil(digital_account_count * 0.3)
    assert takeover_high == math.ceil(digital_account_count * 1.0)
    assert takeover_high >= takeover_low


def test_digital_fraud_scenario_generation_is_deterministic() -> None:
    """The same seed, scale, and prevalence must reproduce identical scenario rows."""
    first = generate_digital_fraud_scenarios_world(
        seed=42, scale="small", scenario_prevalence=0.5, noisy_outcome_rate=0.3
    )
    second = generate_digital_fraud_scenarios_world(
        seed=42, scale="small", scenario_prevalence=0.5, noisy_outcome_rate=0.3
    )

    for table_name in ("alerts", "cases", "case_outcomes", PROTECTED_SCENARIO_ANSWER_KEYS):
        pd.testing.assert_frame_equal(
            first[table_name].sort_values(first[table_name].columns[0], kind="stable").reset_index(
                drop=True
            ),
            second[table_name].sort_values(second[table_name].columns[0], kind="stable").reset_index(
                drop=True
            ),
        )


def test_scenario_injection_preserves_referential_integrity() -> None:
    """All scenario rows must join cleanly back to canonical tables."""
    tables = generate_digital_fraud_scenarios_world(seed=42, scale="small")
    scenario_names = (
        ACCOUNT_TAKEOVER_SCENARIO_NAME,
        ONBOARDING_ABUSE_SCENARIO_NAME,
        SUSPICIOUS_BENEFICIARY_CHANGE_SCENARIO_NAME,
    )
    scenario_keys = tables[PROTECTED_SCENARIO_ANSWER_KEYS][
        tables[PROTECTED_SCENARIO_ANSWER_KEYS]["scenario_name"].isin(scenario_names)
    ]

    assert set(scenario_keys["entity_id"]) <= set(tables["transactions"]["transaction_id"])
    scenario_cases = tables["cases"][
        tables["cases"]["transaction_id"].isin(scenario_keys["entity_id"])
    ]
    assert set(scenario_cases["user_id"]) <= set(tables["users"]["user_id"])
    assert set(scenario_cases["session_id"]) <= set(tables["sessions"]["session_id"])
    assert set(scenario_cases["payment_beneficiary_id"]) <= set(
        tables["payment_beneficiaries"]["payment_beneficiary_id"]
    )
    scenario_outcomes = tables["case_outcomes"][
        tables["case_outcomes"]["case_id"].isin(scenario_cases["case_id"])
    ]
    assert set(scenario_outcomes["case_id"]) == set(scenario_cases["case_id"])


def test_learner_facing_outputs_exclude_protected_answer_keys() -> None:
    """Learner-facing scenario outputs must drop protected answer keys entirely."""
    tables = generate_digital_fraud_scenarios_world(seed=42, scale="small")
    learner_tables = build_learner_facing_views(tables)

    assert PROTECTED_SCENARIO_ANSWER_KEYS in tables
    assert PROTECTED_SCENARIO_ANSWER_KEYS not in learner_tables
    assert set(learner_tables["case_outcomes"]["outcome_type"]) <= {
        "confirmed-fraud",
        "false-positive",
        "unresolved",
    }


def test_scenario_prevalence_invalid_values_are_rejected() -> None:
    """Prevalence and noise rates outside [0, 1] must be rejected."""
    with pytest.raises(ValueError, match="scenario_prevalence"):
        generate_digital_fraud_scenarios_world(scenario_prevalence=1.5)
    with pytest.raises(ValueError, match="scenario_prevalence"):
        inject_digital_fraud_scenarios({}, noisy_outcome_rate=-0.2)


def _scenario_key_count(answer_keys: pd.DataFrame, scenario_name: str) -> int:
    """Count protected answer-key rows for one scenario."""
    return int((answer_keys["scenario_name"] == scenario_name).sum())
