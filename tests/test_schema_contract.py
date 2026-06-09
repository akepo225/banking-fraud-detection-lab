"""Tests verifying generated data conforms to the schema contract."""

from decimal import Decimal
from pathlib import Path

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


def test_schema_contract_is_documented_in_data_dictionary() -> None:
    """Every schema table and column must appear in the foundation data dictionary."""
    data_dictionary = Path("docs/schema/data_dictionary.md").read_text(encoding="utf-8")

    assert "# Canonical Data Dictionary" in data_dictionary

    for table_name, table_spec in TABLE_SPECS.items():
        section = _data_dictionary_section(data_dictionary, table_name)
        for column_spec in table_spec.columns:
            nullable = "yes" if column_spec.nullable else "no"
            references = f"`{column_spec.references}`" if column_spec.references else ""
            expected_row = (
                f"| `{column_spec.name}` | {column_spec.dtype} | "
                f"{nullable} | {references} |"
            )
            assert expected_row in section, (
                f"docs/schema/data_dictionary.md is missing the schema row for "
                f"{table_name}.{column_spec.name}"
            )


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


def _data_dictionary_section(data_dictionary: str, table_name: str) -> str:
    """Return the markdown section documenting one schema table."""
    heading = f"## `{table_name}`"
    if data_dictionary.startswith(heading):
        start = 0
    else:
        start = data_dictionary.find(f"\n{heading}")
        assert start != -1, f"docs/schema/data_dictionary.md is missing {heading}"
        start += 1
    next_start = data_dictionary.find("\n## `", start + len(heading))
    if next_start == -1:
        return data_dictionary[start:]
    return data_dictionary[start:next_start]
