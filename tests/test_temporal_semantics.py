"""Tests for v0.2 foundation temporal semantics."""

import pytest

from banking_fraud_lab import SCALE_PROFILES, generate_minimal_banking_world
from banking_fraud_lab.generators import (
    generate_digital_scam_to_mule_world,
    generate_private_banking_transaction_fraud_world,
)
from banking_fraud_lab.generators.minimal_world import DATASET_AS_OF
from banking_fraud_lab.schema import TABLE_SPECS

REQUIRED_TEMPORAL_COLUMNS = {
    "partners": {"kyc_risk_effective_from", "kyc_risk_reviewed_at"},
    "banking_relationships": {"relationship_manager_assigned_at"},
    "relationship_manager_history": {"effective_from", "effective_to"},
    "accounts": {"status_effective_from", "status_effective_to"},
    "users": {"authorized_from", "authorized_to"},
    "alerts": {"status_updated_at"},
    "cases": {"closed_at"},
    "case_outcomes": {"recorded_at"},
}


def test_required_temporal_columns_are_generated_and_documented() -> None:
    """v0.2 temporal columns must be present in generated data and schema specs."""
    tables = generate_minimal_banking_world(seed=42, scale="tiny")

    for table_name, columns in REQUIRED_TEMPORAL_COLUMNS.items():
        assert columns.issubset(tables[table_name].columns)
        documented_columns = {column.name for column in TABLE_SPECS[table_name].columns}
        assert columns.issubset(documented_columns)


@pytest.mark.parametrize("scale", tuple(SCALE_PROFILES))
def test_temporal_fields_do_not_exceed_dataset_as_of(scale: str) -> None:
    """Historical generated timestamps must not extend beyond the dataset snapshot."""
    tables = generate_minimal_banking_world(seed=42, scale=scale)

    for table_name, table_spec in TABLE_SPECS.items():
        frame = tables[table_name]
        for column in table_spec.columns:
            if column.dtype != "datetime64[ns]":
                continue
            values = frame[column.name].dropna()
            assert (values <= DATASET_AS_OF).all(), f"{table_name}.{column.name} exceeds as-of"


@pytest.mark.parametrize("scale", tuple(SCALE_PROFILES))
def test_effective_date_ordering_holds_for_foundation_entities(scale: str) -> None:
    """KYC, RM, authorization, role, and account effective dates must be coherent."""
    tables = generate_minimal_banking_world(seed=42, scale=scale)

    partners = tables["partners"]
    assert (partners["created_at"] <= partners["kyc_risk_effective_from"]).all()
    assert (partners["kyc_risk_effective_from"] <= partners["kyc_risk_reviewed_at"]).all()

    relationships = tables["banking_relationships"]
    assert (relationships["relationship_manager_assigned_at"] <= relationships["opened_at"]).all()

    relationship_manager_history = tables["relationship_manager_history"]
    current_rm_history = relationship_manager_history[
        relationship_manager_history["effective_to"].isna()
    ]
    assert current_rm_history["banking_relationship_id"].is_unique
    assert set(current_rm_history["banking_relationship_id"]) == set(
        relationships["banking_relationship_id"]
    )
    rm_history_ends = relationship_manager_history.dropna(subset=["effective_to"])
    assert (relationship_manager_history["effective_from"] <= DATASET_AS_OF).all()
    assert (rm_history_ends["effective_from"] <= rm_history_ends["effective_to"]).all()
    rm_history_context = relationship_manager_history.merge(
        relationships[
            [
                "banking_relationship_id",
                "opened_at",
                "relationship_manager_assigned_at",
            ]
        ],
        on="banking_relationship_id",
        how="left",
        validate="many_to_one",
    )
    assert (rm_history_context["effective_from"] <= rm_history_context["opened_at"]).all()
    assert (
        rm_history_context["effective_from"]
        == rm_history_context["relationship_manager_assigned_at"]
    ).all()

    partner_roles = tables["partner_roles"]
    role_ends = partner_roles.dropna(subset=["effective_to"])
    assert (partner_roles["effective_from"] <= DATASET_AS_OF).all()
    assert (role_ends["effective_from"] <= role_ends["effective_to"]).all()

    accounts = tables["accounts"]
    assert (accounts["opened_at"] <= accounts["status_effective_from"]).all()
    account_status_ends = accounts.dropna(subset=["status_effective_to"])
    assert (account_status_ends["status_effective_from"] <= account_status_ends["status_effective_to"]).all()

    users = tables["users"]
    assert (users["created_at"] <= users["authorized_from"]).all()
    user_auth_ends = users.dropna(subset=["authorized_to"])
    assert (user_auth_ends["authorized_from"] <= user_auth_ends["authorized_to"]).all()


@pytest.mark.parametrize("scale", tuple(SCALE_PROFILES))
def test_alert_case_outcome_lifecycle_ordering_holds(scale: str) -> None:
    """Suspicious activity, alert, case, and outcome timestamps must move forward."""
    tables = generate_minimal_banking_world(seed=42, scale=scale)

    activities = tables["suspicious_activities"].merge(
        tables["transactions"][["transaction_id", "booked_at"]],
        on="transaction_id",
        how="left",
        validate="many_to_one",
    )
    assert (activities["booked_at"] <= activities["detected_at"]).all()

    alerts = tables["alerts"].merge(
        tables["suspicious_activities"][["suspicious_activity_id", "detected_at"]],
        on="suspicious_activity_id",
        how="left",
        validate="many_to_one",
    )
    assert (alerts["detected_at"] <= alerts["generated_at"]).all()
    assert (alerts["generated_at"] <= alerts["status_updated_at"]).all()

    cases = tables["cases"].merge(
        tables["alerts"][["alert_id", "generated_at"]],
        on="alert_id",
        how="left",
        validate="many_to_one",
    )
    assert (cases["generated_at"] <= cases["opened_at"]).all()
    closed_cases = cases.dropna(subset=["closed_at"])
    assert (closed_cases["opened_at"] <= closed_cases["closed_at"]).all()

    outcomes = tables["case_outcomes"].merge(
        tables["cases"][["case_id", "opened_at", "closed_at"]],
        on="case_id",
        how="left",
        validate="many_to_one",
    )
    assert (outcomes["opened_at"] <= outcomes["decided_at"]).all()
    assert (outcomes["decided_at"] <= outcomes["recorded_at"]).all()
    closed_outcomes = outcomes.dropna(subset=["closed_at"])
    assert (closed_outcomes["decided_at"] <= closed_outcomes["closed_at"]).all()


@pytest.mark.parametrize("scale", tuple(SCALE_PROFILES))
def test_digital_sessions_stay_within_user_authorization_window(scale: str) -> None:
    """NovaBank Digital sessions must start after the User is created and authorized."""
    tables = generate_minimal_banking_world(seed=42, scale=scale)

    sessions = tables["sessions"].merge(
        tables["users"][["user_id", "created_at", "authorized_from", "authorized_to"]],
        on="user_id",
        how="left",
        validate="many_to_one",
    )
    assert (sessions["created_at"] <= sessions["authorized_from"]).all()
    assert (sessions["created_at"] <= sessions["started_at"]).all()
    assert (sessions["authorized_from"] <= sessions["started_at"]).all()

    bounded = sessions.dropna(subset=["authorized_to"])
    if not bounded.empty:
        assert (bounded["started_at"] <= bounded["authorized_to"]).all()


@pytest.mark.parametrize(
    "world_generator",
    (generate_private_banking_transaction_fraud_world, generate_digital_scam_to_mule_world),
)
def test_scenario_generators_preserve_temporal_invariants(world_generator) -> None:
    """Scenario injection must not break foundation temporal ordering."""
    tables = world_generator(seed=42, scale="small")

    _assert_temporal_fields_do_not_exceed_as_of(tables)
    _assert_alert_case_outcome_lifecycle_ordering(tables)


def _assert_temporal_fields_do_not_exceed_as_of(tables: dict) -> None:
    """Assert every schema datetime column stays within the dataset snapshot."""
    for table_name, table_spec in TABLE_SPECS.items():
        frame = tables[table_name]
        for column in table_spec.columns:
            if column.dtype != "datetime64[ns]":
                continue
            values = frame[column.name].dropna()
            assert (values <= DATASET_AS_OF).all(), f"{table_name}.{column.name} exceeds as-of"


def _assert_alert_case_outcome_lifecycle_ordering(tables: dict) -> None:
    """Assert lifecycle timestamps are ordered in generated tables."""
    activities = tables["suspicious_activities"].merge(
        tables["transactions"][["transaction_id", "booked_at"]],
        on="transaction_id",
        how="left",
        validate="many_to_one",
    )
    assert (activities["booked_at"] <= activities["detected_at"]).all()

    alerts = tables["alerts"].merge(
        tables["suspicious_activities"][["suspicious_activity_id", "detected_at"]],
        on="suspicious_activity_id",
        how="left",
        validate="many_to_one",
    )
    assert (alerts["detected_at"] <= alerts["generated_at"]).all()
    assert (alerts["generated_at"] <= alerts["status_updated_at"]).all()

    cases = tables["cases"].merge(
        tables["alerts"][["alert_id", "generated_at"]],
        on="alert_id",
        how="left",
        validate="many_to_one",
    )
    assert (cases["generated_at"] <= cases["opened_at"]).all()
    closed_cases = cases.dropna(subset=["closed_at"])
    assert (closed_cases["opened_at"] <= closed_cases["closed_at"]).all()

    outcomes = tables["case_outcomes"].merge(
        tables["cases"][["case_id", "opened_at", "closed_at"]],
        on="case_id",
        how="left",
        validate="many_to_one",
    )
    assert (outcomes["opened_at"] <= outcomes["decided_at"]).all()
    assert (outcomes["decided_at"] <= outcomes["recorded_at"]).all()
    closed_outcomes = outcomes.dropna(subset=["closed_at"])
    assert (closed_outcomes["decided_at"] <= closed_outcomes["closed_at"]).all()
