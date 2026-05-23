"""Tests for entity presence, referential integrity, and committed sample CSVs."""

from pathlib import Path

import pandas as pd
import pytest

from banking_fraud_lab import (
    generate_learner_facing_minimal_banking_world,
    generate_minimal_banking_world,
)
from banking_fraud_lab.schema import (
    COLUMN_NAMES,
    LEARNER_FACING_TABLE_NAMES,
    TABLE_NAMES,
    TABLE_SPECS,
)

REQUIRED_V0_1_TABLES = {
    "partners",
    "clients",
    "roles",
    "partner_roles",
    "banking_relationships",
    "accounts",
    "transactions",
    "users",
    "sessions",
    "payment_beneficiaries",
    "suspicious_activities",
    "alerts",
    "cases",
    "case_outcomes",
    "protected_scenario_answer_keys",
}
MAX_SAMPLE_CSV_SIZE_BYTES = 20_000
FK_RELATIONSHIPS = tuple(
    (
        child_table,
        column.name,
        column.references.split(".", maxsplit=1)[0],
        column.references.split(".", maxsplit=1)[1],
        column.nullable,
    )
    for child_table, table_spec in TABLE_SPECS.items()
    for column in table_spec.columns
    if column.references is not None
)


def test_minimal_world_includes_required_v0_1_entities() -> None:
    """All v0.1 tables must be present with correct columns and non-empty rows where required."""
    tables = generate_minimal_banking_world(seed=42)

    assert set(TABLE_NAMES) == REQUIRED_V0_1_TABLES
    assert set(tables) == REQUIRED_V0_1_TABLES
    for table_name, frame in tables.items():
        assert tuple(frame.columns) == COLUMN_NAMES[table_name]
        if not TABLE_SPECS[table_name].allow_empty:
            assert not frame.empty, f"{table_name} should include sample rows"


@pytest.mark.parametrize(
    ("child_table", "child_column", "parent_table", "parent_column", "nullable"),
    FK_RELATIONSHIPS,
)
def test_minimal_world_preserves_referential_integrity(
    child_table: str,
    child_column: str,
    parent_table: str,
    parent_column: str,
    nullable: bool,
) -> None:
    """Every FK column must reference only values that exist in the parent table."""
    tables = generate_minimal_banking_world(seed=42)

    _assert_fk(tables, child_table, child_column, parent_table, parent_column, nullable=nullable)


def test_minimal_world_preserves_semantic_join_integrity() -> None:
    """Cross-table joins must not violate domain invariants (institution consistency)."""
    tables = generate_minimal_banking_world(seed=42)

    relationships = tables["banking_relationships"]
    accounts = tables["accounts"]
    transactions = tables["transactions"]
    beneficiaries = tables["payment_beneficiaries"]
    alerts = tables["alerts"]
    partner_roles = tables["partner_roles"]
    partners = tables["partners"]

    account_clients = accounts.merge(
        relationships[["banking_relationship_id", "primary_client_id"]],
        on="banking_relationship_id",
        how="left",
    )[["account_id", "primary_client_id"]]
    payment_transactions = transactions.dropna(subset=["payment_beneficiary_id"]).merge(
        account_clients,
        on="account_id",
        how="left",
    )
    payment_transactions = payment_transactions.merge(
        beneficiaries[["payment_beneficiary_id", "client_id"]],
        on="payment_beneficiary_id",
        how="left",
    )
    mismatches = payment_transactions[
        payment_transactions["primary_client_id"] != payment_transactions["client_id"]
    ]
    assert mismatches.empty, (
        "Payment beneficiary client_id must match account primary_client_id. "
        f"Found {len(mismatches)} mismatches:\n{mismatches.head()}"
    )

    alert_institutions = alerts.merge(
        accounts[["account_id", "institution_name"]], on="account_id", how="left"
    )
    mismatches = alert_institutions[
        alert_institutions["institution_name_x"] != alert_institutions["institution_name_y"]
    ]
    assert mismatches.empty, (
        "Alert institution_name must match transaction account institution_name. "
        f"Found {len(mismatches)} mismatches:\n{mismatches.head()}"
    )

    role_institutions = partner_roles.merge(
        partners[["partner_id", "institution_name"]], on="partner_id", how="left"
    ).merge(
        relationships[["banking_relationship_id", "institution_name"]],
        on="banking_relationship_id",
        how="left",
    )
    mismatches = role_institutions[
        role_institutions["institution_name_x"] != role_institutions["institution_name_y"]
    ]
    assert mismatches.empty, (
        "Partner role institution_name must match relationship institution_name. "
        f"Found {len(mismatches)} mismatches:\n{mismatches.head()}"
    )


def test_alert_lifecycle_is_distinct_from_single_fraud_flag() -> None:
    """Suspicious activity, alerts, cases, outcomes, and fraud confirmation stay separate."""
    tables = generate_minimal_banking_world(seed=42)

    learner_tables = {
        table_name: frame
        for table_name, frame in tables.items()
        if table_name != "protected_scenario_answer_keys"
    }
    for table_name, frame in learner_tables.items():
        assert "is_fraud" not in frame.columns, f"{table_name} should not expose is_fraud"

    suspicious_activities = tables["suspicious_activities"]
    alerts = tables["alerts"]
    cases = tables["cases"]
    outcomes = tables["case_outcomes"]

    assert not suspicious_activities.empty
    assert not alerts.empty
    assert not cases.empty
    assert not outcomes.empty
    assert set(alerts["suspicious_activity_id"]).issubset(
        set(suspicious_activities["suspicious_activity_id"])
    )
    assert set(cases["alert_id"]).issubset(set(alerts["alert_id"]))
    assert set(outcomes["case_id"]).issubset(set(cases["case_id"]))
    assert outcomes["confirmed_fraud"].any()
    assert (~outcomes["confirmed_fraud"]).any()
    assert {"triaged", "closed"}.issubset(set(alerts["alert_status"]))
    assert {"confirmed_fraud", "false_positive"}.issubset(set(outcomes["outcome_type"]))


def test_alert_and_case_records_carry_direct_lifecycle_references() -> None:
    """Alerts and cases must directly reference the relevant lifecycle entities."""
    tables = generate_minimal_banking_world(seed=42)

    direct_reference_columns = {
        "suspicious_activity_id",
        "banking_relationship_id",
        "account_id",
        "user_id",
        "session_id",
        "payment_beneficiary_id",
    }
    assert direct_reference_columns.issubset(tables["alerts"].columns)
    assert direct_reference_columns.issubset(tables["cases"].columns)
    assert "transaction_id" in tables["cases"].columns
    assert "triggered_transaction_id" in tables["alerts"].columns

    for table_name in ("alerts", "cases"):
        frame = tables[table_name]
        assert frame["banking_relationship_id"].notna().all()
        assert frame["account_id"].notna().all()
        assert frame["user_id"].notna().any()
        assert frame["session_id"].notna().any()
        assert frame["payment_beneficiary_id"].notna().any()


def test_protected_answer_keys_are_excluded_from_learner_facing_tables_by_default() -> None:
    """Protected answer keys exist internally but not in default learner-facing outputs."""
    tables = generate_minimal_banking_world(seed=42)
    learner_tables = generate_learner_facing_minimal_banking_world(seed=42)

    protected = tables["protected_scenario_answer_keys"]
    assert not protected.empty
    assert set(protected["available_to_learners"]) == {False}
    assert "protected_scenario_answer_keys" not in learner_tables
    assert tuple(learner_tables) == LEARNER_FACING_TABLE_NAMES


def test_protected_answer_key_entities_reference_generated_rows() -> None:
    """Generic answer-key entity references must point at generated table rows."""
    tables = generate_minimal_banking_world(seed=42)

    for answer_key in tables["protected_scenario_answer_keys"].itertuples(index=False):
        target_frame = tables[answer_key.entity_table]
        id_column = COLUMN_NAMES[answer_key.entity_table][0]
        assert answer_key.entity_id in set(target_frame[id_column])


def test_lifecycle_prevalence_uses_ranges_not_exact_row_outputs() -> None:
    """Scenario prevalence tests must assert ranges rather than exact row-level labels."""
    tables = generate_minimal_banking_world(seed=42)

    transaction_count = len(tables["transactions"])
    suspicious_activity_prevalence = len(tables["suspicious_activities"]) / transaction_count
    confirmed_fraud_prevalence = (
        int(tables["case_outcomes"]["confirmed_fraud"].sum()) / transaction_count
    )

    assert 0.15 <= suspicious_activity_prevalence <= 0.30
    assert 0.02 <= confirmed_fraud_prevalence <= 0.10


def test_committed_sample_csvs_exist_for_all_generated_tables() -> None:
    """Every table in the schema must have a committed sample CSV under data/sample/."""
    sample_dir = Path("data/sample")

    for table_name in TABLE_NAMES:
        csv_path = sample_dir / f"{table_name}.csv"
        assert csv_path.exists(), f"Missing sample file for {table_name}"
        assert csv_path.stat().st_size < MAX_SAMPLE_CSV_SIZE_BYTES, (
            f"{table_name} sample file is too large"
        )


def test_committed_sample_csvs_match_canonical_seed_output(tmp_path: Path) -> None:
    """Committed CSVs must be byte-identical to freshly generated seed-42 output."""
    sample_dir = Path("data/sample")
    generate_minimal_banking_world(seed=42, output_dir=tmp_path)

    for table_name in TABLE_NAMES:
        expected_bytes = (tmp_path / f"{table_name}.csv").read_bytes()
        committed_bytes = (sample_dir / f"{table_name}.csv").read_bytes()
        assert committed_bytes == expected_bytes, f"{table_name}.csv does not match seed=42 output"


def _assert_fk(
    tables: dict[str, pd.DataFrame],
    child_table: str,
    child_column: str,
    parent_table: str,
    parent_column: str,
    *,
    nullable: bool = False,
) -> None:
    """Assert every (non-null) value in child_column exists in parent_column."""
    child_values = tables[child_table][child_column]
    if nullable:
        child_values = child_values.dropna()
    parent_values = set(tables[parent_table][parent_column])

    assert set(child_values).issubset(parent_values), (
        f"{child_table}.{child_column} contains values missing from "
        f"{parent_table}.{parent_column}"
    )
