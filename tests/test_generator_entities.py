"""Tests for entity presence, referential integrity, and committed sample CSVs."""

from pathlib import Path

import pandas as pd
import pytest

from banking_fraud_lab import generate_minimal_banking_world
from banking_fraud_lab.schema import COLUMN_NAMES, TABLE_NAMES, TABLE_SPECS

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
    "alerts",
    "cases",
    "case_outcomes",
    "protected_scenario_answer_keys",
}
MAX_SAMPLE_CSV_SIZE_BYTES = 20_000
FK_RELATIONSHIPS = (
    ("clients", "partner_id", "partners", "partner_id", False),
    ("banking_relationships", "primary_client_id", "clients", "client_id", False),
    ("partner_roles", "partner_id", "partners", "partner_id", False),
    ("partner_roles", "role_id", "roles", "role_id", False),
    (
        "partner_roles",
        "banking_relationship_id",
        "banking_relationships",
        "banking_relationship_id",
        False,
    ),
    ("accounts", "banking_relationship_id", "banking_relationships", "banking_relationship_id", False),
    ("transactions", "account_id", "accounts", "account_id", False),
    (
        "transactions",
        "payment_beneficiary_id",
        "payment_beneficiaries",
        "payment_beneficiary_id",
        True,
    ),
    ("users", "client_id", "clients", "client_id", False),
    ("sessions", "user_id", "users", "user_id", False),
    ("payment_beneficiaries", "client_id", "clients", "client_id", False),
    ("payment_beneficiaries", "added_by_user_id", "users", "user_id", False),
    ("alerts", "triggered_transaction_id", "transactions", "transaction_id", False),
    ("cases", "alert_id", "alerts", "alert_id", False),
    ("case_outcomes", "case_id", "cases", "case_id", False),
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
        transactions[["transaction_id", "account_id"]],
        left_on="triggered_transaction_id",
        right_on="transaction_id",
        how="left",
    ).merge(accounts[["account_id", "institution_name"]], on="account_id", how="left")
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
