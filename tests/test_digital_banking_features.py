"""Tests for digital-banking feature-family metadata, calculations, and SQL exercises."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

from banking_fraud_lab import (
    build_digital_banking_features,
    calculate_db_account_age_features,
    calculate_db_beneficiary_novelty_features,
    calculate_db_pass_through_features,
    calculate_db_payment_velocity_features,
    calculate_db_risky_channel_features,
    calculate_db_session_risk_features,
    calculate_db_shared_device_features,
    create_minimal_banking_world_sqlite,
    generate_digital_fraud_scenarios_world,
)
from banking_fraud_lab.features import (
    DB_ACCOUNT_AGE,
    DB_BENEFICIARY_NOVELTY,
    DB_PASS_THROUGH,
    DB_PAYMENT_VELOCITY,
    DB_RISKY_CHANNEL,
    DB_SESSION_RISK,
    DB_SHARED_DEVICE,
    DIGITAL_BANKING_FEATURE_FAMILIES,
    FeatureFamilySpec,
)
from banking_fraud_lab.schema import PATTERN_IDS, PROTECTED_SCENARIO_ANSWER_KEYS

DIGITAL_PATTERN_IDS = {
    "digital_scam_to_mule",
    "new_beneficiary_payment",
    "session_payment_velocity",
}
DIGITAL_SQL_EXERCISES = {
    "db_session_channel_features": Path(
        "sql/examples/09_digital_session_channel_features.sql"
    ),
    "db_beneficiary_passthrough_features": Path(
        "sql/examples/10_digital_beneficiary_passthrough_features.sql"
    ),
    "db_velocity_account_features": Path(
        "sql/examples/11_digital_velocity_account_features.sql"
    ),
}


def _scenario_tables() -> dict[str, pd.DataFrame]:
    """Return deterministic NovaBank Digital scenario tables for feature tests."""
    return generate_digital_fraud_scenarios_world(
        seed=42, scale="small", scenario_prevalence=0.5, noisy_outcome_rate=0.3
    )


def test_digital_feature_specs_are_pattern_linked_and_db_prefixed() -> None:
    """Digital feature-family metadata must be complete and tied to digital patterns."""
    assert len(DIGITAL_BANKING_FEATURE_FAMILIES) == 7
    family_ids = [spec.family_id for spec in DIGITAL_BANKING_FEATURE_FAMILIES]
    assert len(family_ids) == len(set(family_ids))
    assert all(isinstance(spec, FeatureFamilySpec) for spec in DIGITAL_BANKING_FEATURE_FAMILIES)

    for spec in DIGITAL_BANKING_FEATURE_FAMILIES:
        assert spec.family_id.startswith("db_")
        assert all(column.startswith("db_") for column in spec.output_columns)
        assert spec.display_name
        assert spec.description
        assert spec.detection_pattern_id in PATTERN_IDS
        assert spec.detection_pattern_id in DIGITAL_PATTERN_IDS, (
            f"{spec.family_id} maps to a non-digital pattern: {spec.detection_pattern_id}"
        )
        assert spec.source_tables
        assert spec.source_columns
        assert PROTECTED_SCENARIO_ANSWER_KEYS not in spec.source_tables


def test_digital_feature_specs_cover_required_families() -> None:
    """All seven required v0.4 feature families must be present."""
    family_ids = {spec.family_id for spec in DIGITAL_BANKING_FEATURE_FAMILIES}
    assert family_ids == {
        "db_session_risk",
        "db_beneficiary_novelty",
        "db_payment_velocity",
        "db_account_age",
        "db_shared_device",
        "db_pass_through",
        "db_risky_channel",
    }


def test_digital_feature_calculators_return_spec_outputs() -> None:
    """Every calculator should return the columns promised by its feature spec."""
    tables = _scenario_tables()
    outputs = {
        DB_SESSION_RISK.family_id: calculate_db_session_risk_features(
            tables["transactions"], tables["sessions"], tables["suspicious_activities"]
        ),
        DB_BENEFICIARY_NOVELTY.family_id: calculate_db_beneficiary_novelty_features(
            tables["transactions"], tables["payment_beneficiaries"]
        ),
        DB_PAYMENT_VELOCITY.family_id: calculate_db_payment_velocity_features(
            tables["transactions"], tables["sessions"], tables["suspicious_activities"]
        ),
        DB_ACCOUNT_AGE.family_id: calculate_db_account_age_features(
            tables["transactions"], tables["accounts"]
        ),
        DB_SHARED_DEVICE.family_id: calculate_db_shared_device_features(
            tables["transactions"], tables["sessions"], tables["suspicious_activities"]
        ),
        DB_PASS_THROUGH.family_id: calculate_db_pass_through_features(
            tables["transactions"], tables["payment_beneficiaries"]
        ),
        DB_RISKY_CHANNEL.family_id: calculate_db_risky_channel_features(
            tables["transactions"], tables["payment_beneficiaries"]
        ),
    }
    spec_by_family = {
        spec.family_id: spec for spec in DIGITAL_BANKING_FEATURE_FAMILIES
    }
    for family_id, frame in outputs.items():
        spec = spec_by_family[family_id]
        assert "transaction_id" in frame.columns
        assert set(spec.output_columns).issubset(frame.columns)
        assert len(frame) == len(tables["transactions"])


def test_build_digital_banking_features_returns_all_db_columns() -> None:
    """The merged digital feature frame must expose every db_ output column."""
    tables = _scenario_tables()
    feature_frame = build_digital_banking_features(tables)

    expected_outputs = {
        column
        for spec in DIGITAL_BANKING_FEATURE_FAMILIES
        for column in spec.output_columns
    }
    assert expected_outputs.issubset(set(feature_frame.columns))
    assert "institution_name" not in feature_frame.columns
    assert "confirmed_fraud" not in feature_frame.columns
    assert not feature_frame.empty


def test_digital_features_flag_scenario_behavior() -> None:
    """Scenario transactions must trigger digital risk signals above baseline."""
    tables = _scenario_tables()
    feature_frame = build_digital_banking_features(tables)

    scenario_transaction_ids = set(
        tables[PROTECTED_SCENARIO_ANSWER_KEYS]["entity_id"]
    )
    scenario_frame = feature_frame[
        feature_frame["transaction_id"].isin(scenario_transaction_ids)
    ]
    assert not scenario_frame.empty

    signal_columns = (
        "db_is_vpn_or_proxy",
        "db_is_high_risk_network",
        "db_is_new_beneficiary",
        "db_is_early_life_account",
        "db_is_rapid_pass_through",
        "db_is_shared_device",
        "db_is_beneficiary_country_risky",
    )
    scenario_signal_rate = (
        scenario_frame[list(signal_columns)].sum().sum() / len(scenario_frame)
    )
    baseline_frame = feature_frame[
        ~feature_frame["transaction_id"].isin(scenario_transaction_ids)
    ]
    baseline_signal_rate = (
        baseline_frame[list(signal_columns)].sum().sum() / max(len(baseline_frame), 1)
    )
    assert scenario_signal_rate > baseline_signal_rate


def test_digital_features_include_legitimate_false_positive_examples() -> None:
    """Legitimate NovaBank transactions must produce at least one low-risk example."""
    tables = _scenario_tables()
    feature_frame = build_digital_banking_features(tables)
    scenario_transaction_ids = set(
        tables[PROTECTED_SCENARIO_ANSWER_KEYS]["entity_id"]
    )
    legitimate_frame = feature_frame[
        ~feature_frame["transaction_id"].isin(scenario_transaction_ids)
    ]

    risk_columns = (
        "db_is_vpn_or_proxy",
        "db_is_high_risk_network",
        "db_is_new_beneficiary",
        "db_is_early_life_account",
        "db_is_rapid_pass_through",
        "db_is_shared_device",
        "db_is_beneficiary_country_risky",
    )
    benign_rows = legitimate_frame[
        (legitimate_frame[list(risk_columns)].sum(axis=1) == 0)
    ]
    assert not benign_rows.empty, "Expected at least one legitimate low-risk false-positive row"


def test_digital_sql_exercises_execute_against_learner_database(
    tmp_path: Path,
) -> None:
    """Digital SQL exercises must run through the SQLite learner path only."""
    connection = create_minimal_banking_world_sqlite(
        tmp_path / "learner_world.sqlite", seed=42, scale="small"
    )
    connection.row_factory = sqlite3.Row

    try:
        for topic, path in DIGITAL_SQL_EXERCISES.items():
            sql = path.read_text(encoding="utf-8")
            assert PROTECTED_SCENARIO_ANSWER_KEYS not in sql
            cursor = connection.execute(sql)
            columns = tuple(description[0] for description in cursor.description)
            rows = cursor.fetchall()
            assert rows, f"{path} returned no rows"
            assert any(column.startswith("db_") for column in columns), (
                f"{topic} did not expose any db_ feature columns"
            )
    finally:
        connection.close()


def test_digital_sql_session_channel_exercise_surfaces_risk_signals(
    tmp_path: Path,
) -> None:
    """The session/channel SQL exercise must expose risk and beneficiary signals."""
    connection = create_minimal_banking_world_sqlite(
        tmp_path / "learner_world.sqlite", seed=42, scale="small"
    )
    connection.row_factory = sqlite3.Row

    try:
        sql = DIGITAL_SQL_EXERCISES["db_session_channel_features"].read_text(
            encoding="utf-8"
        )
        rows = connection.execute(sql).fetchall()
        assert rows, "Session/channel SQL exercise returned no rows"
        columns = rows[0].keys()
        assert "db_is_vpn_or_proxy" in columns
        assert "db_is_high_risk_network" in columns
        assert "db_is_mobile_app_channel" in columns
        assert "db_is_beneficiary_country_risky" in columns
        assert any(row["db_is_mobile_app_channel"] == 1 for row in rows)
    finally:
        connection.close()


def test_digital_sql_guide_documents_digital_exercises() -> None:
    """The SQL guide must document the digital exercises and db_ feature lineage."""
    sql_guide = Path("sql/README.md").read_text(encoding="utf-8")

    for path in DIGITAL_SQL_EXERCISES.values():
        assert path.name in sql_guide
    assert "NovaBank Digital" in sql_guide
    assert "digital_scam_to_mule" in sql_guide
    assert "new_beneficiary_payment" in sql_guide
    assert "session_payment_velocity" in sql_guide
    assert "db_" in sql_guide


def test_digital_sql_beneficiary_passthrough_exercise_produces_valid_age_days(
    tmp_path: Path,
) -> None:
    """SQL 10 must produce non-negative beneficiary age days using datetime strings.

    Regression guard for CAST(pb.created_at AS REAL), which would silently return
    0 or NULL on an ISO datetime string; the exercise instead passes the ISO
    string directly to julianday().
    """
    connection = create_minimal_banking_world_sqlite(
        tmp_path / "learner_world.sqlite", seed=42, scale="small"
    )
    connection.row_factory = sqlite3.Row

    try:
        sql = DIGITAL_SQL_EXERCISES["db_beneficiary_passthrough_features"].read_text(
            encoding="utf-8"
        )
        rows = connection.execute(sql).fetchall()
        assert rows, "Beneficiary pass-through SQL exercise returned no rows"
        columns = rows[0].keys()

        assert "db_beneficiary_age_days" in columns
        assert "db_is_new_beneficiary" in columns
        assert "db_is_rapid_pass_through" in columns

        # Rows with a known beneficiary must have a non-negative age in days.
        rows_with_beneficiary = [
            row
            for row in rows
            if row["db_beneficiary_age_days"] != -1
        ]
        assert rows_with_beneficiary, "Expected at least one row with a known beneficiary"
        for row in rows_with_beneficiary:
            assert row["db_beneficiary_age_days"] >= 0, (
                f"Negative beneficiary age detected: {row['db_beneficiary_age_days']}. "
                "This suggests CAST(AS REAL) epoch arithmetic was applied instead of "
                "direct julianday() on an ISO datetime string."
            )

        # Rows without a beneficiary link must return the sentinel -1.
        rows_without_beneficiary = [
            row
            for row in rows
            if row["db_beneficiary_age_days"] == -1
        ]
        assert rows_without_beneficiary, (
            "Expected at least one row with a NULL beneficiary (sentinel -1)"
        )
    finally:
        connection.close()


def test_digital_sql_beneficiary_passthrough_exercise_uses_datetime_column_not_epoch() -> None:
    """SQL 10 must reference beneficiary_created_at (datetime), not an epoch alias.

    An epoch alias derived via CAST(pb.created_at AS REAL) produced incorrect
    arithmetic; the exercise passes the ISO string directly to julianday().
    """
    sql_text = DIGITAL_SQL_EXERCISES["db_beneficiary_passthrough_features"].read_text(
        encoding="utf-8"
    )
    assert "beneficiary_created_epoch" not in sql_text, (
        "SQL 10 still contains a 'beneficiary_created_epoch' alias. "
        "It should use 'beneficiary_created_at' to pass ISO datetimes to julianday()."
    )
    assert "beneficiary_created_at" in sql_text


def test_digital_sql_velocity_account_exercise_produces_valid_account_age_days(
    tmp_path: Path,
) -> None:
    """SQL 11 must produce non-negative account age days using ISO datetime strings.

    Regression guard for CAST(a.opened_at AS REAL), which broke julianday()
    arithmetic on an ISO datetime string.
    """
    connection = create_minimal_banking_world_sqlite(
        tmp_path / "learner_world.sqlite", seed=42, scale="small"
    )
    connection.row_factory = sqlite3.Row

    try:
        sql = DIGITAL_SQL_EXERCISES["db_velocity_account_features"].read_text(
            encoding="utf-8"
        )
        rows = connection.execute(sql).fetchall()
        assert rows, "Velocity/account SQL exercise returned no rows"
        columns = rows[0].keys()

        assert "db_account_age_days" in columns
        assert "db_is_early_life_account" in columns
        assert "db_session_payment_count" in columns

        for row in rows:
            age = row["db_account_age_days"]
            assert age >= 0, (
                f"Negative account age detected: {age}. "
                "This suggests CAST(AS REAL) epoch arithmetic broke julianday()."
            )
            early_life = row["db_is_early_life_account"]
            assert early_life in (0, 1)
            if 0 <= age <= 30:
                assert early_life == 1, (
                    f"Account with age {age} days should be flagged as early-life."
                )
            else:
                assert early_life == 0, (
                    f"Account with age {age} days should NOT be flagged as early-life."
                )
    finally:
        connection.close()


def test_digital_sql_velocity_account_exercise_uses_datetime_column_not_epoch() -> None:
    """SQL 11 must reference opened_at (datetime column), not an epoch alias.

    An epoch alias derived via CAST(a.opened_at AS REAL) broke the julianday()
    arithmetic in SQLite when opened_at is an ISO datetime string.
    """
    sql_text = DIGITAL_SQL_EXERCISES["db_velocity_account_features"].read_text(
        encoding="utf-8"
    )
    assert "account_opened_epoch" not in sql_text, (
        "SQL 11 still contains an 'account_opened_epoch' alias. "
        "It should use 'opened_at' directly for julianday() arithmetic."
    )
    assert "opened_at" in sql_text


def test_digital_sql_velocity_account_exercise_early_life_boundary_is_inclusive(
    tmp_path: Path,
) -> None:
    """SQL 11 BETWEEN 0 AND 30 must include the boundaries (0 and 30 days exactly).

    A bare '<= 30' would allow negative account ages to be flagged as early-life;
    BETWEEN 0 AND 30 guards against that even when dates are stored as ISO strings.
    """
    sql_text = DIGITAL_SQL_EXERCISES["db_velocity_account_features"].read_text(
        encoding="utf-8"
    )
    # The BETWEEN 0 AND 30 phrasing must be present (not just <= 30).
    assert "BETWEEN 0 AND 30" in sql_text, (
        "SQL 11 must use 'BETWEEN 0 AND 30' for the early-life account boundary. "
        "A bare '<= 30' would allow negative account ages to be flagged."
    )

    connection = create_minimal_banking_world_sqlite(
        tmp_path / "learner_world.sqlite", seed=42, scale="small"
    )
    connection.row_factory = sqlite3.Row

    try:
        rows = connection.execute(sql_text).fetchall()
        # Every early-life flag must correspond to an age of 0-30 days (inclusive).
        for row in rows:
            if row["db_is_early_life_account"] == 1:
                assert 0 <= row["db_account_age_days"] <= 30, (
                    f"Row flagged as early-life has age {row['db_account_age_days']} days "
                    "(out of the 0-30 day window)."
                )
    finally:
        connection.close()
