"""Tests verifying generated data conforms to the schema contract."""

from decimal import Decimal

import pandas as pd

from banking_fraud_lab import generate_minimal_banking_world
from banking_fraud_lab.schema import COLUMN_NAMES, TABLE_NAMES, TABLE_SPECS


def test_schema_contract_column_names_match_generated_tables() -> None:
    """Every generated DataFrame must have exactly the columns declared in the schema."""
    tables = generate_minimal_banking_world(seed=42)

    for table_name in TABLE_NAMES:
        assert tuple(tables[table_name].columns) == COLUMN_NAMES[table_name]


def test_schema_contract_type_families_match_generated_tables() -> None:
    """Non-nullable columns must contain no nulls; non-null values must match declared types."""
    tables = generate_minimal_banking_world(seed=42)

    for table_name, table_spec in TABLE_SPECS.items():
        frame = tables[table_name]
        for column_spec in table_spec.columns:
            col = frame[column_spec.name]
            if not column_spec.nullable:
                assert col.notna().all(), (
                    f"{table_name}.{column_spec.name} is non-nullable but contains nulls"
                )
            values = col.dropna()
            if values.empty:
                continue
            _assert_type_family(values, column_spec.dtype)


def test_schema_contract_contains_documented_purposes() -> None:
    """Every table spec must carry a non-empty purpose and at least one column."""
    for table_name, table_spec in TABLE_SPECS.items():
        assert table_spec.name == table_name
        assert table_spec.purpose
        assert table_spec.columns


def _assert_type_family(values: pd.Series, expected_dtype: str) -> None:
    """Assert that all values in the Series belong to the expected type family."""
    if expected_dtype == "datetime64[ns]":
        assert pd.api.types.is_datetime64_any_dtype(values)
    elif expected_dtype == "int64":
        assert pd.api.types.is_integer_dtype(values)
    elif expected_dtype == "bool":
        assert pd.api.types.is_bool_dtype(values)
    elif expected_dtype == "Decimal":
        bad_types = {type(value).__name__ for value in values if not isinstance(value, Decimal)}
        assert not bad_types, f"Expected Decimal values, found: {sorted(bad_types)}"
    elif expected_dtype == "string":
        bad_types = {type(value).__name__ for value in values if not isinstance(value, str)}
        assert not bad_types, f"Expected string values, found: {sorted(bad_types)}"
    else:
        raise AssertionError(f"Unsupported schema dtype: {expected_dtype}")
