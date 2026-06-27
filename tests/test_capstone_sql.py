"""Smoke tests for the v0.9 capstone SQL examples (issue #226).

The capstone SQL examples run against a capstone dataset loaded into a
learner-facing SQLite database. They reuse the existing SQL example vocabulary
(canonical tables, institution filters, window functions) and produce
meaningful rows tying back to Banking relationship / Client-or-User /
Detection pattern / Alert lineage, without leaking protected answer keys.
"""

from __future__ import annotations

from pathlib import Path

from banking_fraud_lab import load_tables_to_sqlite
from banking_fraud_lab.capstone import (
    generate_learner_facing_capstone_digital_banking_world,
    generate_learner_facing_capstone_private_banking_world,
)
from banking_fraud_lab.schema import PROTECTED_SCENARIO_ANSWER_KEYS

ROOT = Path(__file__).resolve().parents[1]
PROTECTED_KEY_COLUMNS = ("available_to_learners", "label_type", "label_value")

CAPSTONE_SQL_FILES = (
    (ROOT / "sql/examples/12_capstone_private_banking.sql", "private_banking"),
    (ROOT / "sql/examples/13_capstone_digital_banking.sql", "digital_banking"),
)


def test_capstone_sql_examples_exist() -> None:
    """Both capstone SQL examples live under sql/examples/."""
    for sql_file, _ in CAPSTONE_SQL_FILES:
        assert sql_file.is_file(), f"missing capstone SQL example {sql_file.name}"


def test_capstone_sql_examples_run_against_capstone_database(tmp_path: Path) -> None:
    """Each capstone SQL example returns meaningful rows from the capstone dataset."""
    generators = {
        "private_banking": generate_learner_facing_capstone_private_banking_world,
        "digital_banking": generate_learner_facing_capstone_digital_banking_world,
    }
    for sql_file, track in CAPSTONE_SQL_FILES:
        tables = generators[track]()
        connection = load_tables_to_sqlite(
            tables,
            tmp_path / f"capstone_{track}.sqlite",
        )
        try:
            rows = connection.execute(sql_file.read_text(encoding="utf-8")).fetchall()
            assert rows, f"{sql_file.name} returned no rows against the {track} capstone DB"
        finally:
            connection.close()


def test_capstone_sql_results_exclude_protected_answer_keys(tmp_path: Path) -> None:
    """Capstone SQL results must not expose protected answer-key columns or tables."""
    generators = {
        "private_banking": generate_learner_facing_capstone_private_banking_world,
        "digital_banking": generate_learner_facing_capstone_digital_banking_world,
    }
    for sql_file, track in CAPSTONE_SQL_FILES:
        tables = generators[track]()
        connection = load_tables_to_sqlite(
            tables,
            tmp_path / f"capstone_protected_{track}.sqlite",
        )
        try:
            table_names = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            assert PROTECTED_SCENARIO_ANSWER_KEYS not in table_names, (
                f"protected table present in {track} capstone DB"
            )
            cursor = connection.execute(sql_file.read_text(encoding="utf-8"))
            result_columns = {desc[0] for desc in cursor.description}
            assert not (set(PROTECTED_KEY_COLUMNS) & result_columns), (
                f"{sql_file.name} exposes protected columns: "
                f"{set(PROTECTED_KEY_COLUMNS) & result_columns}"
            )
        finally:
            connection.close()


def test_capstone_sql_ties_back_to_glossary_lineage(tmp_path: Path) -> None:
    """Capstone SQL results carry Banking relationship / Client-or-User / Alert lineage."""
    lineage_checks = {
        "private_banking": {
            "banking_relationship_id",
            "client_id",
            "relationship_manager_code",
            "alert_id",
        },
        "digital_banking": {"banking_relationship_id", "client_id", "user_id", "alert_id"},
    }
    generators = {
        "private_banking": generate_learner_facing_capstone_private_banking_world,
        "digital_banking": generate_learner_facing_capstone_digital_banking_world,
    }
    for sql_file, track in CAPSTONE_SQL_FILES:
        tables = generators[track]()
        connection = load_tables_to_sqlite(
            tables,
            tmp_path / f"capstone_lineage_{track}.sqlite",
        )
        try:
            cursor = connection.execute(sql_file.read_text(encoding="utf-8"))
            result_columns = {desc[0] for desc in cursor.description}
            required = lineage_checks[track]
            assert required.issubset(result_columns), (
                f"{sql_file.name} missing lineage columns {required - result_columns}"
            )
        finally:
            connection.close()
