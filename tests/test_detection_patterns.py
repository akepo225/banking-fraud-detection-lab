"""Stability and documentation tests for the detection pattern vocabulary."""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from banking_fraud_lab.schema.detection_patterns import (
    ACTIVITY_TYPE_TO_PATTERN,
    FOUNDATION_DETECTION_PATTERNS,
    PATTERN_IDS,
    PatternSpec,
)

ROOT = Path(__file__).resolve().parents[1]

PATTERNS_DOC = ROOT / "docs" / "schema" / "detection_patterns.md"

REQUIRED_ACTIVITY_TYPES = {
    "private_banking_high_value",
    "new_beneficiary_payment",
    "session_payment_velocity",
    "private_banking_transaction_fraud",
    "digital_scam_to_mule_flow",
}

VALID_TRACKS = {"private_banking", "digital_banking"}

VALID_INSTITUTIONS = {"Alpine Crest Private Bank", "NovaBank Digital"}

PROHIBITED_TERMS = (
    "Julius Baer",
    "UBS",
    "Credit Suisse",
    "real client data",
    "reconstruct real events",
    "legal advice",
    "compliance advice",
    "audit advice",
)


def test_every_pattern_has_non_empty_required_fields() -> None:
    for pattern in FOUNDATION_DETECTION_PATTERNS:
        assert pattern.pattern_id, f"pattern_id is empty for {pattern}"
        assert pattern.display_name, f"display_name is empty for {pattern}"
        assert pattern.description, f"description is empty for {pattern}"
        assert pattern.track, f"track is empty for {pattern}"
        assert pattern.activity_types, f"activity_types is empty for {pattern}"
        assert pattern.institution, f"institution is empty for {pattern}"


@pytest.mark.parametrize("field_name", ["pattern_id", "display_name", "description"])
def test_no_duplicate_field_values_across_patterns(field_name: str) -> None:
    values = [getattr(p, field_name) for p in FOUNDATION_DETECTION_PATTERNS]
    assert len(values) == len(set(values)), f"Duplicate {field_name} values: {values}"


def test_all_generator_activity_types_map_to_exactly_one_pattern() -> None:
    for activity_type in REQUIRED_ACTIVITY_TYPES:
        assert activity_type in ACTIVITY_TYPE_TO_PATTERN, (
            f"activity_type {activity_type!r} is not in ACTIVITY_TYPE_TO_PATTERN"
        )
    assert set(ACTIVITY_TYPE_TO_PATTERN.keys()) == REQUIRED_ACTIVITY_TYPES


def test_pattern_track_values_are_valid() -> None:
    for pattern in FOUNDATION_DETECTION_PATTERNS:
        assert pattern.track in VALID_TRACKS, (
            f"{pattern.pattern_id} has invalid track {pattern.track!r}"
        )


def test_pattern_institution_values_are_valid() -> None:
    for pattern in FOUNDATION_DETECTION_PATTERNS:
        assert pattern.institution in VALID_INSTITUTIONS, (
            f"{pattern.pattern_id} has invalid institution {pattern.institution!r}"
        )


def test_pattern_ids_matches_registry() -> None:
    expected = tuple(p.pattern_id for p in FOUNDATION_DETECTION_PATTERNS)
    assert PATTERN_IDS == expected
    assert len(PATTERN_IDS) == len(set(PATTERN_IDS))


def test_patterns_doc_exists_and_contains_all_pattern_ids() -> None:
    assert PATTERNS_DOC.exists(), f"{PATTERNS_DOC} does not exist"
    doc_text = PATTERNS_DOC.read_text(encoding="utf-8")
    for pattern_id in PATTERN_IDS:
        assert pattern_id in doc_text, (
            f"Pattern ID {pattern_id!r} not found in {PATTERNS_DOC}"
        )


def test_patterns_doc_contains_no_prohibited_terms() -> None:
    assert PATTERNS_DOC.exists()
    doc_text = PATTERNS_DOC.read_text(encoding="utf-8")
    for term in PROHIBITED_TERMS:
        assert term.lower() not in doc_text.lower(), (
            f"Prohibited term {term!r} found in {PATTERNS_DOC}"
        )


def test_pattern_spec_is_frozen() -> None:
    assert dataclasses.is_dataclass(PatternSpec)
    assert hasattr(PatternSpec, "__dataclass_params__")
    assert PatternSpec.__dataclass_params__.frozen is True

    pattern = FOUNDATION_DETECTION_PATTERNS[0]
    with pytest.raises(dataclasses.FrozenInstanceError):
        pattern.pattern_id = "mutated"
