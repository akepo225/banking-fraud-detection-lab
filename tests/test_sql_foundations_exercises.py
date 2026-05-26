"""Tests for expanded SQLite-first foundation exercises."""

from pathlib import Path

import sqlite3

from banking_fraud_lab import create_minimal_banking_world_sqlite
from banking_fraud_lab.schema import PROTECTED_SCENARIO_ANSWER_KEYS

SQL_EXERCISES = {
    "joins": Path("sql/examples/01_alert_lifecycle_join.sql"),
    "windows": Path("sql/examples/02_alert_review_window.sql"),
    "cohorts": Path("sql/examples/03_client_relationship_cohorts.sql"),
    "alert_queues": Path("sql/examples/04_progressive_alert_queue.sql"),
    "feature_extraction": Path("sql/examples/05_transaction_feature_extraction.sql"),
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
        assert path.name in notebook

    assert "cohort" in sql_guide.lower()
    assert "alert queue" in sql_guide.lower()
    assert "feature extraction" in sql_guide.lower()
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
