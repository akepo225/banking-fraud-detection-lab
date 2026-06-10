"""Tests verifying that the minimal banking world generator is deterministic."""

import pandas as pd
import pytest

from banking_fraud_lab import (
    SCALE_PROFILES,
    create_minimal_banking_world_sqlite,
    generate_digital_scam_to_mule_world,
    generate_learner_facing_minimal_banking_world,
    generate_minimal_banking_world,
    generate_private_banking_transaction_fraud_world,
)
from banking_fraud_lab.generators.private_banking import PRIVATE_BANKING_FALSE_POSITIVE_TYPE
from banking_fraud_lab.schema import LEARNER_FACING_TABLE_NAMES, TABLE_NAMES


def test_minimal_world_is_deterministic_for_fixed_seed() -> None:
    """Two calls with the same seed must produce identical DataFrames."""
    first = generate_minimal_banking_world(seed=42)
    second = generate_minimal_banking_world(seed=42)

    assert tuple(first) == TABLE_NAMES
    assert tuple(second) == TABLE_NAMES
    for table_name in TABLE_NAMES:
        pd.testing.assert_frame_equal(first[table_name], second[table_name])


def test_minimal_world_changes_for_different_seed() -> None:
    """Different seeds must produce at least some different content."""
    seed_42 = generate_minimal_banking_world(seed=42)
    seed_99 = generate_minimal_banking_world(seed=99)

    changed_tables = {
        table_name for table_name in TABLE_NAMES if not seed_42[table_name].equals(seed_99[table_name])
    }

    assert "partners" in changed_tables
    assert "transactions" in changed_tables


def test_named_scale_profiles_are_deterministic_and_proportional() -> None:
    """Named scale profiles must be reproducible and grow the foundation tables."""
    assert tuple(SCALE_PROFILES) == ("tiny", "small", "medium", "large")

    tiny = generate_minimal_banking_world(seed=42, scale="tiny")
    small = generate_minimal_banking_world(seed=42, scale="small")
    medium = generate_minimal_banking_world(seed=42, scale="medium")

    for scale in ("tiny", "small", "medium"):
        first = generate_minimal_banking_world(seed=42, scale=scale)
        second = generate_minimal_banking_world(seed=42, scale=scale)
        for table_name in TABLE_NAMES:
            pd.testing.assert_frame_equal(first[table_name], second[table_name])

    assert len(tiny["transactions"]) < len(small["transactions"]) < len(medium["transactions"])
    assert len(tiny["clients"]) < len(small["clients"]) < len(medium["clients"])
    assert len(tiny["alerts"]) < len(small["alerts"]) < len(medium["alerts"])


def test_learner_facing_scale_profiles_exclude_protected_answer_keys() -> None:
    """Learner-facing scaled outputs must keep protected answer keys out by default."""
    learner_tables = generate_learner_facing_minimal_banking_world(seed=42, scale="medium")

    assert tuple(learner_tables) == LEARNER_FACING_TABLE_NAMES
    assert "protected_scenario_answer_keys" not in learner_tables
    for frame in learner_tables.values():
        assert "available_to_learners" not in frame.columns


@pytest.mark.parametrize(
    ("scale", "expected_ranges"),
    [
        (
            "tiny",
            {
                "clients": (6, 6),
                "transactions": (12, 12),
                "alerts": (3, 3),
                "protected_scenario_answer_keys": (3, 3),
            },
        ),
        (
            "small",
            {
                "clients": (20, 30),
                "transactions": (80, 120),
                "alerts": (20, 30),
                "protected_scenario_answer_keys": (20, 30),
            },
        ),
        (
            "medium",
            {
                "clients": (80, 100),
                "transactions": (500, 700),
                "alerts": (100, 140),
                "protected_scenario_answer_keys": (100, 140),
            },
        ),
        (
            "large",
            {
                "clients": (220, 260),
                "transactions": (2200, 2600),
                "alerts": (440, 520),
                "protected_scenario_answer_keys": (440, 520),
            },
        ),
    ],
)
def test_scale_profile_row_counts_stay_in_expected_ranges(
    scale: str,
    expected_ranges: dict[str, tuple[int, int]],
) -> None:
    """Scale-profile tests use stable ranges rather than row-level labels."""
    tables = generate_minimal_banking_world(seed=42, scale=scale)

    for table_name, (minimum, maximum) in expected_ranges.items():
        assert minimum <= len(tables[table_name]) <= maximum


def test_unknown_scale_profile_fails_clearly() -> None:
    """Invalid scale names should fail before generating partial datasets."""
    with pytest.raises(ValueError, match="Unknown scale profile"):
        generate_minimal_banking_world(seed=42, scale="pocket")


def test_scenario_generators_accept_scale_parameter() -> None:
    """Scenario entry points should forward scale without changing scenario code."""
    private_tiny = generate_private_banking_transaction_fraud_world(seed=42, scale="tiny")
    private_small = generate_private_banking_transaction_fraud_world(seed=42, scale="small")
    digital_tiny = generate_digital_scam_to_mule_world(seed=42, scale="tiny")
    digital_small = generate_digital_scam_to_mule_world(seed=42, scale="small")

    assert len(private_tiny["transactions"]) < len(private_small["transactions"])
    assert len(private_tiny["alerts"]) < len(private_small["alerts"])
    assert len(digital_tiny["transactions"]) < len(digital_small["transactions"])
    assert len(digital_tiny["alerts"]) < len(digital_small["alerts"])


def test_private_banking_false_positive_generation_is_deterministic() -> None:
    """Same seed and prevalence must produce the same false-positive examples."""
    first = generate_private_banking_transaction_fraud_world(
        seed=42,
        scale="small",
        scenario_prevalence=0.2,
    )
    second = generate_private_banking_transaction_fraud_world(
        seed=42,
        scale="small",
        scenario_prevalence=0.2,
    )

    first_alert_ids = first["alerts"].loc[
        first["alerts"]["alert_type"] == PRIVATE_BANKING_FALSE_POSITIVE_TYPE,
        "alert_id",
    ]
    second_alert_ids = second["alerts"].loc[
        second["alerts"]["alert_type"] == PRIVATE_BANKING_FALSE_POSITIVE_TYPE,
        "alert_id",
    ]
    first_cases = first["cases"][first["cases"]["alert_id"].isin(first_alert_ids)].reset_index(
        drop=True
    )
    second_cases = second["cases"][
        second["cases"]["alert_id"].isin(second_alert_ids)
    ].reset_index(drop=True)

    pd.testing.assert_frame_equal(first_cases, second_cases)


def test_sqlite_loader_accepts_scale_profile() -> None:
    """SQLite creation should expose the same learner-facing scale profile surface."""
    connection = create_minimal_banking_world_sqlite(":memory:", seed=42, scale="small")
    try:
        transaction_count = connection.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
        protected_table = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' "
            "AND name = 'protected_scenario_answer_keys'"
        ).fetchone()
    finally:
        connection.close()

    assert 80 <= transaction_count <= 120
    assert protected_table is None
