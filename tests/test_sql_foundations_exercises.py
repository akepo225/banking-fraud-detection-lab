"""Tests for expanded SQLite-first foundation exercises."""

from pathlib import Path

import sqlite3

from banking_fraud_lab import create_minimal_banking_world_sqlite
from banking_fraud_lab.schema import PROTECTED_SCENARIO_ANSWER_KEYS

FOUNDATION_SQL_EXERCISES = {
    "joins": Path("sql/examples/01_alert_lifecycle_join.sql"),
    "windows": Path("sql/examples/02_alert_review_window.sql"),
    "cohorts": Path("sql/examples/03_client_relationship_cohorts.sql"),
    "alert_queues": Path("sql/examples/04_progressive_alert_queue.sql"),
    "feature_extraction": Path("sql/examples/05_transaction_feature_extraction.sql"),
}

PRIVATE_BANKING_SQL_EXERCISES = {
    "pb_value_features": Path("sql/examples/06_private_banking_value_features.sql"),
    "pb_context_features": Path("sql/examples/07_private_banking_context_features.sql"),
    "pb_relationship_features": Path(
        "sql/examples/08_private_banking_relationship_features.sql"
    ),
}

SQL_EXERCISES = {
    **FOUNDATION_SQL_EXERCISES,
    **PRIVATE_BANKING_SQL_EXERCISES,
}


def test_sql_foundation_exercises_cover_required_topics() -> None:
    """SQL examples must cover the v0.2 foundation exercise set."""
    sql_by_topic = {
        topic: path.read_text(encoding="utf-8")
        for topic, path in SQL_EXERCISES.items()
    }
    all_sql = "\n".join(sql_by_topic.values())

    assert "JOIN" in sql_by_topic["joins"].upper()
    assert "OVER (" in sql_by_topic["windows"].upper()
    assert "cohort" in sql_by_topic["cohorts"].lower()
    assert "alert_queue" in sql_by_topic["alert_queues"].lower()
    assert "feature" in sql_by_topic["feature_extraction"].lower()
    assert "foundation_client_relationships" in all_sql
    assert "foundation_alert_lifecycle" in all_sql


def test_private_banking_sql_exercises_cover_feature_topics() -> None:
    """Private-banking SQL examples should cover the v0.3 feature families."""
    sql_by_topic = {
        topic: path.read_text(encoding="utf-8")
        for topic, path in PRIVATE_BANKING_SQL_EXERCISES.items()
    }
    all_sql = "\n".join(sql_by_topic.values())

    assert "Alpine Crest Private Bank" in all_sql
    assert "pb_high_value_movement" in sql_by_topic["pb_value_features"]
    assert "amount_chf" in sql_by_topic["pb_value_features"]
    assert "balance_chf" in sql_by_topic["pb_value_features"]
    assert "OVER (" in sql_by_topic["pb_value_features"]
    assert "strftime" in sql_by_topic["pb_context_features"]
    assert "julianday" in sql_by_topic["pb_context_features"]
    assert "is_cross_border" in sql_by_topic["pb_context_features"]
    assert "relationship_manager_code" in sql_by_topic["pb_relationship_features"]
    assert "ROW_NUMBER() OVER" in sql_by_topic["pb_relationship_features"]


def test_sql_foundation_exercises_return_meaningful_learner_facing_rows(
    tmp_path: Path,
) -> None:
    """SQL exercises must assert real result shape against the learner database."""
    connection = create_minimal_banking_world_sqlite(
        tmp_path / "learner_world.sqlite",
        seed=42,
    )
    connection.row_factory = sqlite3.Row

    try:
        table_names = {
            str(row["name"])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        assert PROTECTED_SCENARIO_ANSWER_KEYS not in table_names

        results = {
            topic: _execute_sql_file(connection, path)
            for topic, path in SQL_EXERCISES.items()
        }

        alert_count = connection.execute("SELECT COUNT(*) AS count FROM alerts").fetchone()[
            "count"
        ]
        transaction_count = connection.execute(
            "SELECT COUNT(*) AS count FROM transactions"
        ).fetchone()["count"]

        assert len(results["joins"].rows) == alert_count
        assert len(results["windows"].rows) == alert_count
        assert len(results["alert_queues"].rows) == alert_count
        assert len(results["feature_extraction"].rows) == transaction_count
        assert any(
            row["cohort_transaction_count"] > 0 for row in results["cohorts"].rows
        )
    finally:
        connection.close()


def test_private_banking_sql_exercises_return_alpine_crest_rows(
    tmp_path: Path,
) -> None:
    """Private-banking SQL exercises should execute against the learner DB."""
    connection = create_minimal_banking_world_sqlite(
        tmp_path / "learner_world.sqlite",
        seed=42,
    )
    connection.row_factory = sqlite3.Row

    try:
        private_transaction_count = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM transactions AS t
            JOIN accounts AS a
              ON a.account_id = t.account_id
            WHERE a.institution_name = 'Alpine Crest Private Bank'
            """
        ).fetchone()["count"]
        results = {
            topic: _execute_sql_file(connection, path)
            for topic, path in PRIVATE_BANKING_SQL_EXERCISES.items()
        }

        assert private_transaction_count > 0
        for result in results.values():
            assert len(result.rows) == private_transaction_count

        assert "amount_to_aum_ratio" in results["pb_value_features"].columns
        assert "is_off_hours" in results["pb_context_features"].columns
        assert "rm_alert_share" in results["pb_relationship_features"].columns
        assert any(
            row["is_cross_border"] == 1 for row in results["pb_context_features"].rows
        )
        assert any(
            row["is_new_counterparty"] == 1
            for row in results["pb_relationship_features"].rows
        )
    finally:
        connection.close()


def test_sql_guide_and_foundations_notebook_reference_expanded_exercises() -> None:
    """Learner-facing docs should present the expanded SQL exercise order."""
    sql_guide = Path("sql/README.md").read_text(encoding="utf-8")
    notebook = Path("notebooks/00_foundations/foundations_data_tour.ipynb").read_text(
        encoding="utf-8"
    )

    previous_index = -1
    for path in SQL_EXERCISES.values():
        index = sql_guide.find(path.name)
        assert index > previous_index, f"{path.name} is missing or out of order"
        previous_index = index

    for path in FOUNDATION_SQL_EXERCISES.values():
        assert path.name in notebook

    assert "cohort" in sql_guide.lower()
    assert "alert queue" in sql_guide.lower()
    assert "feature extraction" in sql_guide.lower()
    assert "amount-to-AUM" in sql_guide
    assert "relationship-manager concentration" in sql_guide
    assert "Progressive data views" in sql_guide


class SqlResult:
    """Executed SQL result for one exercise file."""

    def __init__(self, columns: tuple[str, ...], rows: list[sqlite3.Row]) -> None:
        self.columns = columns
        self.rows = rows


def _execute_sql_file(connection: sqlite3.Connection, path: Path) -> SqlResult:
    """Execute one SQL file and return columns plus rows."""
    sql = path.read_text(encoding="utf-8")
    assert PROTECTED_SCENARIO_ANSWER_KEYS not in sql
    cursor = connection.execute(sql)
    columns = tuple(description[0] for description in cursor.description)
    rows = cursor.fetchall()

    assert rows, f"{path} returned no rows"
    assert len(columns) >= 3
    assert any(
        any(value not in (None, "") for value in row)
        for row in rows
    ), f"{path} returned only empty values"
    return SqlResult(columns=columns, rows=rows)
