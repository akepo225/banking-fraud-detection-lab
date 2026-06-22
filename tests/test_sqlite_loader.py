"""Tests for loading generated banking data into SQLite."""

from pathlib import Path

import sqlite3

import pandas as pd
import pytest

from banking_fraud_lab import (
    create_minimal_banking_world_sqlite,
    generate_minimal_banking_world,
    load_tables_to_sqlite,
)
from banking_fraud_lab.progressive_views import FOUNDATION_PROGRESSIVE_VIEW_SPECS
from banking_fraud_lab.run_sql import main as run_sql_main
from banking_fraud_lab.schema import (
    LEARNER_FACING_TABLE_NAMES,
    PROTECTED_SCENARIO_ANSWER_KEYS,
    RELATIONSHIP_MANAGER_HISTORY,
    ROLES,
    TABLE_NAMES,
)

EXAMPLE_SQL_FILES = (
    Path("sql/examples/00_smoke_tables.sql"),
    Path("sql/examples/01_alert_lifecycle_join.sql"),
    Path("sql/examples/02_alert_review_window.sql"),
    Path("sql/examples/03_client_relationship_cohorts.sql"),
    Path("sql/examples/04_progressive_alert_queue.sql"),
    Path("sql/examples/05_transaction_feature_extraction.sql"),
    Path("sql/examples/06_private_banking_value_features.sql"),
    Path("sql/examples/07_private_banking_context_features.sql"),
    Path("sql/examples/08_private_banking_relationship_features.sql"),
    Path("sql/examples/09_digital_session_channel_features.sql"),
    Path("sql/examples/10_digital_beneficiary_passthrough_features.sql"),
    Path("sql/examples/11_digital_velocity_account_features.sql"),
)


def test_generated_tables_can_be_loaded_into_sqlite_database(tmp_path: Path) -> None:
    """The loader must create a local SQLite database containing generated tables."""
    tables = generate_minimal_banking_world(seed=42)
    connection = load_tables_to_sqlite(tables, tmp_path / "full_world.sqlite")

    try:
        assert _sqlite_table_names(connection) == set(TABLE_NAMES)
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        transaction_count = connection.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
        assert transaction_count == len(tables["transactions"])
    finally:
        connection.close()


def test_sqlite_schema_includes_core_foreign_key_relationships(tmp_path: Path) -> None:
    """SQLite tables must preserve schema relationships needed by SQL exercises."""
    connection = create_minimal_banking_world_sqlite(
        tmp_path / "learner_world.sqlite",
        seed=42,
    )

    try:
        alert_foreign_keys = _foreign_keys_for_table(connection, "alerts")
        case_foreign_keys = _foreign_keys_for_table(connection, "cases")
        suspicious_activity_fk = (
            "suspicious_activity_id",
            "suspicious_activities",
            "suspicious_activity_id",
        )
        banking_relationship_fk = (
            "banking_relationship_id",
            "banking_relationships",
            "banking_relationship_id",
        )

        assert suspicious_activity_fk in alert_foreign_keys
        assert banking_relationship_fk in alert_foreign_keys
        assert ("alert_id", "alerts", "alert_id") in case_foreign_keys
    finally:
        connection.close()


def test_default_sqlite_database_is_learner_facing(tmp_path: Path) -> None:
    """Default SQLite creation should exclude protected scenario answer keys."""
    connection = create_minimal_banking_world_sqlite(
        tmp_path / "learner_world.sqlite",
        seed=42,
    )

    try:
        assert _sqlite_table_names(connection) == set(LEARNER_FACING_TABLE_NAMES)
        assert PROTECTED_SCENARIO_ANSWER_KEYS not in _sqlite_table_names(connection)
    finally:
        connection.close()


def test_default_sqlite_database_exposes_foundation_progressive_views(
    tmp_path: Path,
) -> None:
    """Default SQLite creation should expose foundation Progressive data views."""
    connection = create_minimal_banking_world_sqlite(
        tmp_path / "learner_world.sqlite",
        seed=42,
    )

    try:
        view_names = _sqlite_view_names(connection)
        assert view_names == {spec.name for spec in FOUNDATION_PROGRESSIVE_VIEW_SPECS}

        for spec in FOUNDATION_PROGRESSIVE_VIEW_SPECS:
            assert _sqlite_view_column_names(connection, spec.name) == spec.columns
            row_count = connection.execute(
                "SELECT COUNT(*) FROM " + _quote_identifier(spec.name)
            ).fetchone()[0]
            assert row_count > 0

        protected_view_columns = _sqlite_view_column_names(
            connection,
            "foundation_alert_lifecycle",
        )
        assert "available_to_learners" not in protected_view_columns
        assert PROTECTED_SCENARIO_ANSWER_KEYS not in view_names
    finally:
        connection.close()


def test_sqlite_pb_relationship_context_selects_latest_current_rm_history(
    tmp_path: Path,
) -> None:
    """SQLite pb_relationship_context must match Python latest-current RM selection."""
    tables = generate_minimal_banking_world(seed=42)
    first_history = tables[RELATIONSHIP_MANAGER_HISTORY].iloc[[0]].copy()
    first_relationship_id = str(first_history.iloc[0]["banking_relationship_id"])
    latest_effective_from = pd.Timestamp(first_history.iloc[0]["effective_from"]) + pd.Timedelta(
        minutes=30
    )
    first_history.loc[:, "rm_history_id"] = "RMH-9999"
    first_history.loc[:, "relationship_manager_code"] = "RM-999"
    first_history.loc[:, "effective_from"] = latest_effective_from
    tables[RELATIONSHIP_MANAGER_HISTORY] = pd.concat(
        [tables[RELATIONSHIP_MANAGER_HISTORY], first_history],
        ignore_index=True,
    )
    connection = load_tables_to_sqlite(tables, tmp_path / "world.sqlite")

    try:
        row = connection.execute(
            """
            SELECT COUNT(*), MAX("relationship_manager_code"), MAX("rm_effective_from")
            FROM "pb_relationship_context"
            WHERE "banking_relationship_id" = ?
            """,
            (first_relationship_id,),
        ).fetchone()

        assert row == (1, "RM-999", latest_effective_from.isoformat(sep=" "))
    finally:
        connection.close()


def test_sqlite_nb_user_session_context_matches_python_builder(
    tmp_path: Path,
) -> None:
    """SQLite nb_user_session_context must match the Python builder across scales."""
    from banking_fraud_lab.progressive_views import (
        NB_USER_SESSION_CONTEXT,
        build_foundation_progressive_views,
    )

    for scale in ("tiny", "small"):
        tables = generate_minimal_banking_world(seed=42, scale=scale)
        python_view = build_foundation_progressive_views(tables)[
            NB_USER_SESSION_CONTEXT.name
        ].sort_values("session_id", kind="stable").reset_index(drop=True)
        connection = load_tables_to_sqlite(tables, tmp_path / f"world_{scale}.sqlite")

        try:
            sqlite_columns = _sqlite_view_column_names(
                connection,
                NB_USER_SESSION_CONTEXT.name,
            )
            assert sqlite_columns == NB_USER_SESSION_CONTEXT.columns
            sqlite_view = pd.read_sql_query(
                'SELECT * FROM "nb_user_session_context"',
                connection,
            ).sort_values("session_id", kind="stable").reset_index(drop=True)
        finally:
            connection.close()

        assert tuple(sqlite_view.columns) == NB_USER_SESSION_CONTEXT.columns
        assert len(sqlite_view) == len(python_view)
        assert list(sqlite_view["session_id"]) == list(python_view["session_id"])
        assert set(sqlite_view["institution_name"]) == {"NovaBank Digital"}
        for column in (
            "client_id",
            "user_id",
            "channel",
            "device_fingerprint_hash",
            "asn_risk_score",
            "is_vpn_or_proxy",
            "auth_method",
        ):
            assert list(sqlite_view[column]) == list(python_view[column]), (
                f"Column {column} differs between SQLite and Python views at {scale}"
            )


def test_replace_removes_protected_tables_when_switching_to_learner_facing(
    tmp_path: Path,
) -> None:
    """Replacing a full internal DB with learner-facing mode must remove protected tables."""
    database_path = tmp_path / "world.sqlite"
    full_connection = create_minimal_banking_world_sqlite(
        database_path,
        seed=42,
        learner_facing=False,
    )
    try:
        assert PROTECTED_SCENARIO_ANSWER_KEYS in _sqlite_table_names(full_connection)
    finally:
        full_connection.close()

    learner_connection = create_minimal_banking_world_sqlite(
        database_path,
        seed=42,
    )
    try:
        table_names = _sqlite_table_names(learner_connection)
        assert table_names == set(LEARNER_FACING_TABLE_NAMES)
        assert PROTECTED_SCENARIO_ANSWER_KEYS not in table_names
    finally:
        learner_connection.close()


def test_loader_recreates_stale_progressive_views_when_replace_is_false() -> None:
    """Existing SQLite views must not block a caller-managed no-replace load."""
    connection = sqlite3.connect(":memory:")

    try:
        load_tables_to_sqlite(generate_minimal_banking_world(seed=42), connection)
        _drop_sqlite_tables_for_test(connection, TABLE_NAMES)

        load_tables_to_sqlite(
            generate_minimal_banking_world(seed=42),
            connection,
            replace=False,
        )

        assert _sqlite_view_names(connection) == {
            spec.name for spec in FOUNDATION_PROGRESSIVE_VIEW_SPECS
        }
        row_count = connection.execute(
            "SELECT COUNT(*) FROM " + _quote_identifier("foundation_alert_lifecycle")
        ).fetchone()[0]
        assert row_count > 0
    finally:
        connection.close()


def test_loader_recreates_progressive_views_from_existing_tables_on_staged_load() -> None:
    """No-replace staged loads must rebuild views from all tables already in SQLite."""
    tables = generate_minimal_banking_world(seed=42)
    first_batch = {
        table_name: frame
        for table_name, frame in tables.items()
        if table_name not in {ROLES, "partner_roles", PROTECTED_SCENARIO_ANSWER_KEYS}
    }
    connection = sqlite3.connect(":memory:")

    try:
        load_tables_to_sqlite(first_batch, connection)
        assert _sqlite_view_names(connection) == {
            spec.name for spec in FOUNDATION_PROGRESSIVE_VIEW_SPECS
        }

        load_tables_to_sqlite({ROLES: tables[ROLES]}, connection, replace=False)

        assert ROLES in _sqlite_table_names(connection)
        assert _sqlite_view_names(connection) == {
            spec.name for spec in FOUNDATION_PROGRESSIVE_VIEW_SPECS
        }
        row_count = connection.execute(
            "SELECT COUNT(*) FROM " + _quote_identifier("foundation_alert_lifecycle")
        ).fetchone()[0]
        assert row_count > 0
    finally:
        connection.close()


def test_loader_rejects_active_transaction_without_foreign_keys() -> None:
    """Caller-owned active transactions must already have SQLite FK checks enabled."""
    connection = sqlite3.connect(":memory:")
    connection.execute("BEGIN")

    try:
        with pytest.raises(ValueError, match="foreign_keys"):
            load_tables_to_sqlite(generate_minimal_banking_world(seed=42), connection)
        assert connection.in_transaction
    finally:
        connection.rollback()
        connection.close()


def test_loader_preserves_caller_owned_transaction_control() -> None:
    """Caller-owned connections keep transaction ownership after table loading."""
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("BEGIN")

    try:
        load_tables_to_sqlite(generate_minimal_banking_world(seed=42), connection)

        assert connection.in_transaction
        assert _sqlite_table_names(connection) == set(TABLE_NAMES)

        connection.rollback()
        assert _sqlite_table_names(connection) == set()
    finally:
        if connection.in_transaction:
            connection.rollback()
        connection.close()


def test_loader_commits_implicit_transaction_on_caller_owned_connection() -> None:
    """Caller-owned connections without an active transaction should not be left open."""
    connection = sqlite3.connect(":memory:")

    try:
        load_tables_to_sqlite(generate_minimal_banking_world(seed=42), connection)

        assert not connection.in_transaction
        assert _sqlite_table_names(connection) == set(TABLE_NAMES)
    finally:
        connection.close()


def test_representative_sql_examples_execute_successfully(tmp_path: Path) -> None:
    """Learner SQL examples must run against the generated SQLite database."""
    connection = create_minimal_banking_world_sqlite(
        tmp_path / "learner_world.sqlite",
        seed=42,
    )

    try:
        for sql_file in EXAMPLE_SQL_FILES:
            rows = connection.execute(sql_file.read_text(encoding="utf-8")).fetchall()
            assert rows, f"{sql_file} returned no rows"
    finally:
        connection.close()


def test_sqlite_private_banking_transaction_context_is_queryable(tmp_path: Path) -> None:
    """SQLite learner path should expose AUM and counterparty transaction context."""
    connection = create_minimal_banking_world_sqlite(
        tmp_path / "learner_world.sqlite",
        seed=42,
    )

    try:
        row = connection.execute(
            """
            SELECT
              COUNT(DISTINCT t.transaction_type) AS private_typologies,
              SUM(CASE WHEN t.payment_beneficiary_id IS NOT NULL THEN 1 ELSE 0 END)
                AS linked_counterparty_rows,
              MIN(CAST(br.aum_chf AS REAL)) AS min_aum_chf
            FROM transactions AS t
            JOIN accounts AS a
              ON a.account_id = t.account_id
            JOIN banking_relationships AS br
              ON br.banking_relationship_id = a.banking_relationship_id
            LEFT JOIN payment_beneficiaries AS pb
              ON pb.payment_beneficiary_id = t.payment_beneficiary_id
            WHERE a.institution_name = 'Alpine Crest Private Bank'
            """
        ).fetchone()

        assert row[0] >= 6
        assert row[1] > 0
        assert row[2] > 0
    finally:
        connection.close()


def test_run_sql_module_executes_example_without_external_sqlite_cli(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Learners should be able to run SQL examples through the Python environment."""
    database_path = tmp_path / "learner_world.sqlite"
    connection = create_minimal_banking_world_sqlite(database_path, seed=42)
    connection.close()

    exit_code = run_sql_main(
        [
            str(database_path),
            str(Path("sql/examples/00_smoke_tables.sql")),
        ]
    )

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "table_name" in output
    assert "transactions" in output


def test_run_sql_module_preserves_comment_token_boundaries(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """SQL comments should behave like whitespace between adjacent tokens."""
    database_path = tmp_path / "learner_world.sqlite"
    sqlite3.connect(database_path).close()
    sql_path = tmp_path / "comment_between_tokens.sql"
    sql_path.write_text("SELECT/* learner note */1 AS value;\n", encoding="utf-8")

    exit_code = run_sql_main([str(database_path), str(sql_path)])

    assert exit_code == 0
    assert capsys.readouterr().out.splitlines() == ["value", "1"]


def test_run_sql_module_rejects_multi_statement_files(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The SQL runner should fail clearly for scripts outside its single-query scope."""
    database_path = tmp_path / "learner_world.sqlite"
    connection = create_minimal_banking_world_sqlite(database_path, seed=42)
    connection.close()
    sql_path = tmp_path / "multi_statement.sql"
    sql_path.write_text("SELECT 1;\nSELECT 2;\n", encoding="utf-8")

    with pytest.raises(SystemExit) as error:
        run_sql_main([str(database_path), str(sql_path)])

    assert error.value.code == 2
    assert "one SQL statement per file" in capsys.readouterr().err


def _sqlite_table_names(connection: sqlite3.Connection) -> set[str]:
    """Return table names present in the SQLite database."""
    rows = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
    ).fetchall()
    return {str(row[0]) for row in rows}


def _sqlite_view_names(connection: sqlite3.Connection) -> set[str]:
    """Return view names present in the SQLite database."""
    rows = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'view' ORDER BY name"
    ).fetchall()
    return {str(row[0]) for row in rows}


def _sqlite_view_column_names(
    connection: sqlite3.Connection,
    view_name: str,
) -> tuple[str, ...]:
    """Return column names for one SQLite view."""
    rows = connection.execute(
        "PRAGMA table_info(" + _quote_identifier(view_name) + ")"
    ).fetchall()
    return tuple(str(row[1]) for row in rows)


def _drop_sqlite_tables_for_test(
    connection: sqlite3.Connection,
    table_names: tuple[str, ...],
) -> None:
    """Drop tables while deliberately leaving SQLite views behind."""
    connection.execute("PRAGMA foreign_keys = OFF")
    for table_name in reversed(table_names):
        connection.execute("DROP TABLE IF EXISTS " + _quote_identifier(table_name))
    connection.commit()
    connection.execute("PRAGMA foreign_keys = ON")


def _foreign_keys_for_table(
    connection: sqlite3.Connection, table_name: str
) -> set[tuple[str, str, str]]:
    """Return child column, parent table, and parent column for one SQLite table."""
    quoted_table_name = '"' + table_name.replace('"', '""') + '"'
    rows = connection.execute(
        "PRAGMA foreign_key_list(" + quoted_table_name + ")"
    ).fetchall()
    return {(str(row[3]), str(row[2]), str(row[4])) for row in rows}


def _quote_identifier(identifier: str) -> str:
    """Quote a trusted SQLite identifier for tests."""
    return '"' + identifier.replace('"', '""') + '"'
