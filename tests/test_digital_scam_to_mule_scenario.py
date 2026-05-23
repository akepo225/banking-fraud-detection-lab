"""Tests for the NovaBank Digital scam-to-mule scenario."""

from __future__ import annotations

import math

import pandas as pd
import pytest

from banking_fraud_lab import build_learner_facing_views, generate_digital_scam_to_mule_world
from banking_fraud_lab.generators.digital_banking import (
    DIGITAL_SCAM_TO_MULE_ACTIVITY_TYPE,
    DIGITAL_SCAM_TO_MULE_SCENARIO_NAME,
)
from banking_fraud_lab.schema import PROTECTED_SCENARIO_ANSWER_KEYS, TRANSACTIONS

NOVABANK = "NovaBank Digital"
REQUIRED_TELEMETRY_COLUMNS = {
    "user_agent",
    "app_or_browser_version",
    "device_fingerprint_hash",
    "ip_country",
    "asn_risk_score",
    "coarse_geolocation",
    "is_vpn_or_proxy",
    "auth_method",
    "session_event",
}


def test_digital_scam_to_mule_prevalence_is_configurable() -> None:
    """Scam-to-mule scenario labels should scale with requested prevalence."""
    low_prevalence_tables = generate_digital_scam_to_mule_world(
        seed=42,
        scenario_prevalence=0.5,
    )
    high_prevalence_tables = generate_digital_scam_to_mule_world(
        seed=42,
        scenario_prevalence=1.0,
    )
    digital_account_count = _digital_account_count(high_prevalence_tables)

    low_count = _scenario_answer_key_count(low_prevalence_tables)
    high_count = _scenario_answer_key_count(high_prevalence_tables)

    assert low_count == math.ceil(digital_account_count * 0.5)
    assert high_count == math.ceil(digital_account_count * 1.0)
    assert high_count > low_count


def test_digital_scam_to_mule_distinguishes_client_user_and_partner() -> None:
    """Scenario activity must keep Client, User, and Partner identities distinct."""
    tables = generate_digital_scam_to_mule_world(seed=42, scenario_prevalence=1.0)
    scenario_activities = tables["suspicious_activities"][
        tables["suspicious_activities"]["activity_type"] == DIGITAL_SCAM_TO_MULE_ACTIVITY_TYPE
    ]
    identity_context = (
        scenario_activities[["user_id"]]
        .merge(tables["users"][["user_id", "client_id"]], on="user_id", how="left")
        .merge(tables["clients"][["client_id", "partner_id"]], on="client_id", how="left")
        .merge(tables["partners"][["partner_id", "institution_name"]], on="partner_id", how="left")
    )

    assert not identity_context.empty
    assert identity_context["user_id"].notna().all()
    assert identity_context["client_id"].notna().all()
    assert identity_context["partner_id"].notna().all()
    assert (identity_context["user_id"] != identity_context["client_id"]).all()
    assert (identity_context["client_id"] != identity_context["partner_id"]).all()
    assert set(identity_context["institution_name"]) == {NOVABANK}


def test_digital_scam_to_mule_telemetry_and_mule_behavior() -> None:
    """Scenario rows must carry telemetry, mule behavior, shared devices, and noisy outcomes."""
    tables = generate_digital_scam_to_mule_world(seed=42, scenario_prevalence=1.0)
    learner_tables = build_learner_facing_views(tables)

    assert PROTECTED_SCENARIO_ANSWER_KEYS in tables
    assert PROTECTED_SCENARIO_ANSWER_KEYS not in learner_tables
    assert REQUIRED_TELEMETRY_COLUMNS.issubset(tables["sessions"].columns)
    assert "beneficiary_change_event" in tables["payment_beneficiaries"].columns

    scenario_activities = tables["suspicious_activities"][
        tables["suspicious_activities"]["activity_type"] == DIGITAL_SCAM_TO_MULE_ACTIVITY_TYPE
    ]
    scenario_sessions = tables["sessions"][
        tables["sessions"]["session_id"].isin(scenario_activities["session_id"])
    ]
    scenario_beneficiaries = tables["payment_beneficiaries"][
        tables["payment_beneficiaries"]["payment_beneficiary_id"].isin(
            scenario_activities["payment_beneficiary_id"]
        )
    ]
    scenario_transactions = tables["transactions"][
        tables["transactions"]["transaction_id"].isin(scenario_activities["transaction_id"])
    ]
    scenario_accounts = tables["accounts"][
        tables["accounts"]["account_id"].isin(scenario_activities["account_id"])
    ]
    incoming_victim_payments = tables["transactions"][
        tables["transactions"]["description"].eq("Incoming victim payment to early-life mule account")
    ]
    shared_devices = _shared_device_user_counts(tables["sessions"])
    digital_case_outcomes = _digital_case_outcomes(tables)

    assert scenario_sessions[list(REQUIRED_TELEMETRY_COLUMNS)].notna().all().all()
    assert set(scenario_beneficiaries["beneficiary_change_event"]) == {"new_beneficiary_added"}
    assert set(scenario_transactions["description"]) == {"Rapid pass-through to new beneficiary"}
    assert set(incoming_victim_payments["direction"]) == {"credit"}
    assert set(scenario_transactions["direction"]) == {"debit"}
    assert shared_devices["user_count"].max() > 1
    assert "shared device" in " ".join(scenario_activities["detection_signal"]).lower()
    assert "early-life account" in " ".join(scenario_activities["detection_signal"]).lower()
    incoming_by_account = incoming_victim_payments.set_index("account_id")["booked_at"]
    assert all(
        pd.Timestamp(account.opened_at)
        <= pd.Timestamp(incoming_by_account.loc[account.account_id]) - pd.Timedelta(days=1)
        for account in scenario_accounts.itertuples(index=False)
    )
    assert set(digital_case_outcomes["confirmed_fraud"]) == {False, True}


def test_digital_scam_to_mule_referential_integrity() -> None:
    """Scenario activities, alerts, cases, outcomes, and protected keys must join cleanly."""
    tables = generate_digital_scam_to_mule_world(seed=42, scenario_prevalence=1.0)

    scenario_activities = tables["suspicious_activities"][
        tables["suspicious_activities"]["activity_type"] == DIGITAL_SCAM_TO_MULE_ACTIVITY_TYPE
    ]
    scenario_alerts = tables["alerts"][
        tables["alerts"]["alert_type"] == DIGITAL_SCAM_TO_MULE_ACTIVITY_TYPE
    ]
    scenario_cases = tables["cases"][tables["cases"]["alert_id"].isin(scenario_alerts["alert_id"])]
    scenario_outcomes = tables["case_outcomes"][
        tables["case_outcomes"]["case_id"].isin(scenario_cases["case_id"])
    ]
    scenario_keys = tables[PROTECTED_SCENARIO_ANSWER_KEYS][
        tables[PROTECTED_SCENARIO_ANSWER_KEYS]["scenario_name"]
        == DIGITAL_SCAM_TO_MULE_SCENARIO_NAME
    ]

    assert len(scenario_activities) == len(scenario_alerts) == len(scenario_cases)
    assert len(scenario_cases) == len(scenario_outcomes) == len(scenario_keys)
    assert set(scenario_activities["transaction_id"]) <= set(tables["transactions"]["transaction_id"])
    assert set(scenario_activities["user_id"]) <= set(tables["users"]["user_id"])
    assert set(scenario_activities["session_id"]) <= set(tables["sessions"]["session_id"])
    assert set(scenario_activities["payment_beneficiary_id"]) <= set(
        tables["payment_beneficiaries"]["payment_beneficiary_id"]
    )
    assert set(scenario_alerts["suspicious_activity_id"]) == set(
        scenario_activities["suspicious_activity_id"]
    )
    assert set(scenario_cases["alert_id"]) == set(scenario_alerts["alert_id"])
    assert set(scenario_outcomes["case_id"]) == set(scenario_cases["case_id"])
    assert set(scenario_keys["entity_id"]) == set(scenario_activities["transaction_id"])
    assert set(scenario_keys["entity_table"]) == {TRANSACTIONS}
    assert scenario_outcomes["confirmed_fraud"].all()


def test_digital_scam_to_mule_rejects_invalid_prevalence() -> None:
    """Prevalence must be a proportion."""
    with pytest.raises(ValueError, match="scenario_prevalence"):
        generate_digital_scam_to_mule_world(scenario_prevalence=-0.1)


def _digital_account_count(tables: dict[str, pd.DataFrame]) -> int:
    """Count NovaBank Digital accounts in generated tables."""
    return int(tables["accounts"].query("institution_name == @NOVABANK").shape[0])


def _scenario_answer_key_count(tables: dict[str, pd.DataFrame]) -> int:
    """Count protected transaction labels for the digital scenario."""
    answer_keys = tables[PROTECTED_SCENARIO_ANSWER_KEYS]
    return int(
        answer_keys[
            (answer_keys["scenario_name"] == DIGITAL_SCAM_TO_MULE_SCENARIO_NAME)
            & (answer_keys["entity_table"] == TRANSACTIONS)
            & (answer_keys["label_value"] == "confirmed_fraud")
        ].shape[0]
    )


def _shared_device_user_counts(sessions: pd.DataFrame) -> pd.DataFrame:
    """Count distinct Users per device fingerprint."""
    return (
        sessions.groupby("device_fingerprint_hash", as_index=False)["user_id"]
        .nunique()
        .rename(columns={"user_id": "user_count"})
    )


def _digital_case_outcomes(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Return case outcomes for NovaBank Digital cases."""
    digital_cases = tables["cases"].merge(
        tables["alerts"][["alert_id", "institution_name"]],
        on="alert_id",
        how="left",
        validate="many_to_one",
    )
    digital_cases = digital_cases[digital_cases["institution_name"] == NOVABANK]
    return tables["case_outcomes"][
        tables["case_outcomes"]["case_id"].isin(digital_cases["case_id"])
    ]
