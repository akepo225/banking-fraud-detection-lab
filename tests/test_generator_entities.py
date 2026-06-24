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

REQUIRED_GENERATED_TABLES = {
    "partners",
    "clients",
    "roles",
    "partner_roles",
    "banking_relationships",
    "relationship_manager_history",
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
    """All generated tables must be present with correct columns and required rows."""
    tables = generate_minimal_banking_world(seed=42)

    assert set(TABLE_NAMES) == REQUIRED_GENERATED_TABLES
    assert set(tables) == REQUIRED_GENERATED_TABLES
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
    relationship_manager_history = tables["relationship_manager_history"]

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

    rm_history_context = relationship_manager_history.merge(
        relationships[
            [
                "banking_relationship_id",
                "relationship_manager_code",
                "relationship_manager_assigned_at",
            ]
        ],
        on="banking_relationship_id",
        how="left",
        validate="many_to_one",
        suffixes=("_history", "_relationship"),
    )
    assert (
        rm_history_context["relationship_manager_code_history"]
        == rm_history_context["relationship_manager_code_relationship"]
    ).all()
    assert (
        rm_history_context["effective_from"]
        == rm_history_context["relationship_manager_assigned_at"]
    ).all()

    account_balances = (
        accounts.groupby("banking_relationship_id", as_index=False)["balance_chf"]
        .sum()
        .rename(columns={"balance_chf": "relationship_balance_chf"})
    )
    relationship_balances = relationships.merge(
        account_balances,
        on="banking_relationship_id",
        how="left",
        validate="one_to_one",
    )
    assert relationship_balances["aum_chf"].notna().all()
    assert (relationship_balances["aum_chf"] > 0).all()
    alpine_relationships = relationship_balances[
        relationship_balances["institution_name"] == "Alpine Crest Private Bank"
    ]
    assert (alpine_relationships["aum_chf"] > alpine_relationships["relationship_balance_chf"]).all()


def test_minimal_world_private_banking_transaction_context_is_populated() -> None:
    """Private-banking rows should include AUM-ready typologies and counterparties."""
    tables = generate_minimal_banking_world(seed=42)
    transactions = tables["transactions"]
    accounts = tables["accounts"]
    clients = tables["clients"]
    beneficiaries = tables["payment_beneficiaries"]
    private_transactions = transactions.merge(
        accounts[["account_id", "banking_relationship_id", "institution_name"]],
        on="account_id",
        how="inner",
        validate="many_to_one",
    )
    private_transactions = private_transactions[
        private_transactions["institution_name"] == "Alpine Crest Private Bank"
    ]
    private_beneficiaries = beneficiaries.merge(
        clients[["client_id", "institution_name"]],
        on="client_id",
        how="left",
        validate="many_to_one",
    )
    private_beneficiaries = private_beneficiaries[
        private_beneficiaries["institution_name"] == "Alpine Crest Private Bank"
    ]

    assert {
        "wire_transfer",
        "fx_trade",
        "management_fee",
        "custody_fee",
        "securities_purchase",
        "securities_sale",
    }.issubset(set(private_transactions["transaction_type"]))
    assert private_transactions["payment_beneficiary_id"].notna().any()
    assert {"established_beneficiary", "new_beneficiary_added"}.issubset(
        set(private_beneficiaries["beneficiary_change_event"])
    )
    assert set(
        private_transactions.dropna(subset=["payment_beneficiary_id"])[
            "payment_beneficiary_id"
        ]
    ).issubset(set(private_beneficiaries["payment_beneficiary_id"]))


def test_session_telemetry_matches_declared_channel() -> None:
    """Session user-agent families and versions must agree with the declared channel."""
    tables = generate_minimal_banking_world(seed=42)
    sessions = tables["sessions"]
    session_user_context = sessions.merge(
        tables["users"][["user_id", "institution_name"]],
        on="user_id",
        how="left",
        validate="many_to_one",
    )
    expected = {
        "mobile_app": {
            "user_agents": {"NovaBankMobile/iOS", "NovaBankMobile/Android"},
            "versions": {"17.4", "14.1"},
        },
        "web": {
            "user_agents": {"Firefox/Desktop", "Chrome/Desktop"},
            "versions": {"126.0", "124.0"},
        },
    }

    assert set(session_user_context["institution_name"]) == {"NovaBank Digital"}
    assert set(sessions["channel"]) <= set(expected)
    for channel, telemetry in expected.items():
        channel_sessions = sessions[sessions["channel"] == channel]
        assert set(channel_sessions["user_agent"]) <= telemetry["user_agents"]
        assert set(channel_sessions["app_or_browser_version"]) <= telemetry["versions"]


def test_digital_client_user_session_device_chain_is_internally_consistent() -> None:
    """The NovaBank digital Client→User→session→device→beneficiary chain must join cleanly."""
    tables = generate_minimal_banking_world(seed=42)
    clients = tables["clients"]
    users = tables["users"]
    sessions = tables["sessions"]
    beneficiaries = tables["payment_beneficiaries"]

    # Sessions only exist for NovaBank Digital users and join back to a Client.
    session_chain = sessions.merge(
        users[["user_id", "client_id", "institution_name"]],
        on="user_id",
        how="left",
        validate="many_to_one",
    ).merge(
        clients[["client_id", "institution_name"]],
        on="client_id",
        how="left",
        validate="many_to_one",
        suffixes=("_user", "_client"),
    )
    assert not session_chain.empty
    assert set(session_chain["institution_name_user"]) == {"NovaBank Digital"}
    assert (session_chain["institution_name_user"] == session_chain["institution_name_client"]).all()

    # Every session carries a device fingerprint, network, and auth telemetry.
    telemetry_columns = (
        "device_fingerprint_hash",
        "ip_country",
        "asn_risk_score",
        "coarse_geolocation",
        "is_vpn_or_proxy",
        "auth_method",
        "session_event",
    )
    assert sessions[list(telemetry_columns)].notna().all().all()

    # A device fingerprint may be shared across Users in scenario data, but the
    # base computation must always resolve to a positive distinct-User count per
    # fingerprint and never to a null device.
    assert sessions["device_fingerprint_hash"].notna().all()
    shared_device_user_counts = (
        sessions.groupby("device_fingerprint_hash")["user_id"].nunique()
    )
    assert (shared_device_user_counts >= 1).all()
    assert len(shared_device_user_counts) == sessions["device_fingerprint_hash"].nunique()

    # Beneficiary-change trail for NovaBank Digital joins back to a Client and a User.
    nova_beneficiaries = beneficiaries.merge(
        clients[["client_id", "institution_name"]],
        on="client_id",
        how="left",
        validate="many_to_one",
    )
    nova_beneficiaries = nova_beneficiaries[
        nova_beneficiaries["institution_name"] == "NovaBank Digital"
    ]
    assert not nova_beneficiaries.empty
    assert nova_beneficiaries["added_by_user_id"].isin(users["user_id"]).all()
    beneficiary_user_context = nova_beneficiaries.merge(
        users[["user_id", "institution_name"]].rename(
            columns={
                "user_id": "added_by_user_id",
                "institution_name": "user_institution",
            }
        ),
        on="added_by_user_id",
        how="left",
        validate="many_to_one",
    )
    assert (beneficiary_user_context["institution_name"] == beneficiary_user_context["user_institution"]).all()
    assert {"beneficiary_created"}.issubset(set(nova_beneficiaries["beneficiary_change_event"]))


def test_alert_lifecycle_is_distinct_from_single_fraud_flag() -> None:
    """Suspicious activity, alerts, cases, outcomes, and fraud confirmation stay separate."""
    tables = generate_minimal_banking_world(seed=42)

    learner_tables = {
        table_name: frame
        for table_name, frame in tables.items()
        if table_name in LEARNER_FACING_TABLE_NAMES
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
    assert {"confirmed-fraud", "false-positive"}.issubset(set(outcomes["outcome_type"]))


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


def test_generated_csvs_use_lf_line_endings(tmp_path: Path) -> None:
    """Generated CSVs must use LF line endings on every platform.

    Regression guard for issue #158: pandas defaults to ``os.linesep``, which is
    CRLF on Windows, so the byte-identity check above failed whenever the
    generator ran on Windows. The generators now pin ``lineterminator="\\n"``.
    """
    generate_minimal_banking_world(seed=42, output_dir=tmp_path)

    for table_name in TABLE_NAMES:
        csv_bytes = (tmp_path / f"{table_name}.csv").read_bytes()
        assert b"\r" not in csv_bytes, f"{table_name}.csv must not contain CRLF (\\r\\n)"


def test_committed_sample_csvs_use_lf_line_endings() -> None:
    """Committed sample CSVs must use LF line endings, matching .gitattributes.

    Regression guard for issue #158 acceptance criterion: the ``data/sample``
    blobs are normalized to LF by ``.gitattributes`` (``* text=auto eol=lf``),
    so the committed files must never carry CRLF regardless of platform.
    """
    sample_dir = Path("data/sample")

    for table_name in TABLE_NAMES:
        csv_bytes = (sample_dir / f"{table_name}.csv").read_bytes()
        assert b"\r" not in csv_bytes, f"{table_name}.csv must not contain CRLF (\\r\\n)"


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
