"""Tests for the v0.9 capstone datasets (issue #225).

The capstone is an integration surface: it reuses the existing scenario-injection
generators and the learner-facing / protected-answer-key separation. These tests
verify the four acceptance criteria that a later capstone slice depends on —
determinism, protected-key exclusion from learner exports and inclusion in
grading exports, scenario prevalence bounds, and referential integrity.
"""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd
import pytest

from banking_fraud_lab import (
    CAPSTONE_SCALE,
    CAPSTONE_SEED,
    generate_capstone_digital_banking_world,
    generate_capstone_private_banking_world,
    generate_learner_facing_capstone_digital_banking_world,
    generate_learner_facing_capstone_private_banking_world,
)
from banking_fraud_lab.capstone import main as capstone_main
from banking_fraud_lab.generators.digital_banking import (
    DIGITAL_SCAM_TO_MULE_SCENARIO_NAME,
)
from banking_fraud_lab.generators.private_banking import (
    PRIVATE_BANKING_SCENARIO_NAME,
)
from banking_fraud_lab.schema import (
    LEARNER_FACING_TABLE_NAMES,
    PROTECTED_SCENARIO_ANSWER_KEYS,
    TABLE_NAMES,
    TRANSACTIONS,
)

ALPINE_CREST = "Alpine Crest Private Bank"
NOVABANK = "NovaBank Digital"
PROTECTED_KEY_COLUMNS = {"available_to_learners", "label_type", "label_value"}


def test_capstone_constants_are_fixed_and_documented() -> None:
    """The capstone seed/scale must be fixed so every slice shares one substrate."""
    assert CAPSTONE_SEED == 42
    assert CAPSTONE_SCALE == "tiny"


@pytest.mark.parametrize(
    ("grading", "learner"),
    [
        (
            generate_capstone_private_banking_world,
            generate_learner_facing_capstone_private_banking_world,
        ),
        (
            generate_capstone_digital_banking_world,
            generate_learner_facing_capstone_digital_banking_world,
        ),
    ],
)
def test_capstone_grading_and_learner_exports_split_protected_keys(
    grading: object, learner: object
) -> None:
    """Grading exports carry protected keys; learner exports exclude them entirely."""
    grading_tables = grading()  # type: ignore[operator]
    learner_tables = learner()  # type: ignore[operator]

    assert set(grading_tables) == set(TABLE_NAMES)
    assert PROTECTED_SCENARIO_ANSWER_KEYS in grading_tables
    assert set(learner_tables) == set(LEARNER_FACING_TABLE_NAMES)
    assert PROTECTED_SCENARIO_ANSWER_KEYS not in learner_tables

    for table_name, frame in learner_tables.items():
        assert not (PROTECTED_KEY_COLUMNS & set(frame.columns)), (
            f"protected column leaked into learner-facing {table_name}"
        )

    grading_keys = grading_tables[PROTECTED_SCENARIO_ANSWER_KEYS]
    assert set(grading_keys["available_to_learners"]) == {False}
    assert not grading_keys.empty


@pytest.mark.parametrize(
    "generator",
    [
        generate_capstone_private_banking_world,
        generate_capstone_digital_banking_world,
    ],
)
def test_capstone_datasets_are_deterministic_at_fixed_seed_and_scale(
    generator: object,
) -> None:
    """Regenerating at the same seed + scale produces byte-identical protected keys."""
    first = generator()  # type: ignore[operator]
    second = generator()  # type: ignore[operator]

    pd.testing.assert_frame_equal(
        first[PROTECTED_SCENARIO_ANSWER_KEYS],
        second[PROTECTED_SCENARIO_ANSWER_KEYS],
    )
    pd.testing.assert_frame_equal(first[TRANSACTIONS], second[TRANSACTIONS])
    pd.testing.assert_frame_equal(first["alerts"], second["alerts"])


def test_capstone_protected_answer_keys_reference_generated_rows() -> None:
    """Every protected answer key's entity_id must exist in its entity_table."""
    for generator in (
        generate_capstone_private_banking_world,
        generate_capstone_digital_banking_world,
    ):
        tables = generator()
        keys = tables[PROTECTED_SCENARIO_ANSWER_KEYS]
        for entity_table, group in keys.groupby("entity_table"):
            assert entity_table in tables, f"answer key references unknown table {entity_table}"
            entity_ids = set(tables[entity_table].iloc[:, 0])
            assert set(group["entity_id"]).issubset(entity_ids), (
                f"answer-key entity_id missing from {entity_table}"
            )


def test_capstone_private_banking_prevalence_is_bounded() -> None:
    """Private-banking capstone scenario prevalence falls in the expected band."""
    tables = generate_capstone_private_banking_world()
    private_transactions = tables["transactions"].merge(
        tables["accounts"][["account_id", "institution_name"]],
        on="account_id",
        how="inner",
        validate="many_to_one",
    )
    private_transactions = private_transactions[
        private_transactions["institution_name"] == ALPINE_CREST
    ]
    private_transaction_count = len(private_transactions)
    scenario_keys = tables[PROTECTED_SCENARIO_ANSWER_KEYS][
        (tables[PROTECTED_SCENARIO_ANSWER_KEYS]["scenario_name"] == PRIVATE_BANKING_SCENARIO_NAME)
        & (tables[PROTECTED_SCENARIO_ANSWER_KEYS]["entity_table"] == TRANSACTIONS)
    ]

    expected = math.ceil(private_transaction_count * 0.2)
    assert len(scenario_keys) == expected
    if private_transaction_count:
        assert 0.15 <= len(scenario_keys) / private_transaction_count <= 0.25


def test_capstone_digital_banking_prevalence_is_bounded() -> None:
    """Digital-banking capstone scam-to-mule prevalence scales with account count."""
    tables = generate_capstone_digital_banking_world()
    digital_accounts = tables["accounts"][
        tables["accounts"]["institution_name"] == NOVABANK
    ]
    digital_account_count = len(digital_accounts)
    scam_keys = tables[PROTECTED_SCENARIO_ANSWER_KEYS][
        tables[PROTECTED_SCENARIO_ANSWER_KEYS]["scenario_name"]
        == DIGITAL_SCAM_TO_MULE_SCENARIO_NAME
    ]

    expected = math.ceil(digital_account_count * 0.5)
    assert len(scam_keys) == expected
    if digital_account_count:
        assert 0.45 <= len(scam_keys) / digital_account_count <= 0.55


def test_capstone_cli_generates_learner_facing_csvs(tmp_path: Path) -> None:
    """The capstone CLI reproduces learner-facing CSVs for both tracks."""
    rc = capstone_main(
        ["--track", "both", "--learner-facing", "--output", str(tmp_path)]
    )
    assert rc == 0

    for track in ("private_banking", "digital_banking"):
        track_dir = tmp_path / track
        assert track_dir.is_dir()
        csvs = {p.name for p in track_dir.glob("*.csv")}
        assert csvs == {f"{name}.csv" for name in LEARNER_FACING_TABLE_NAMES}
        assert "protected_scenario_answer_keys.csv" not in csvs
