"""Tests verifying that the minimal banking world generator is deterministic."""

import pandas as pd

from banking_fraud_lab import generate_minimal_banking_world
from banking_fraud_lab.schema import TABLE_NAMES


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
