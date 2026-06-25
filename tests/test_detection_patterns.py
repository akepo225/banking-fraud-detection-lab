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

# Graph-derived patterns express network structure rather than a single
# generator activity type, so their activity_types tuple is intentionally empty.
GRAPH_DERIVED_PATTERN_IDS = {"mule_ring", "circular_funds_movement"}

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
        assert pattern.institution, f"institution is empty for {pattern}"
        if pattern.pattern_id not in GRAPH_DERIVED_PATTERN_IDS:
            assert pattern.activity_types, f"activity_types is empty for {pattern}"


def test_graph_derived_patterns_have_empty_activity_types() -> None:
    """Graph-derived patterns intentionally carry no generator activity type."""
    for pattern in FOUNDATION_DETECTION_PATTERNS:
        if pattern.pattern_id in GRAPH_DERIVED_PATTERN_IDS:
            assert pattern.activity_types == (), (
                f"{pattern.pattern_id} should be graph-derived with empty activity_types"
            )


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


def test_graph_native_pattern_ids_are_registered() -> None:
    """The v0.6 graph-native patterns must be in the registry."""
    assert "mule_ring" in PATTERN_IDS
    assert "circular_funds_movement" in PATTERN_IDS


def test_graph_native_patterns_track_and_institution() -> None:
    """Graph-native patterns must use the correct track and synthetic institution."""
    by_id = {p.pattern_id: p for p in FOUNDATION_DETECTION_PATTERNS}
    mule_ring = by_id["mule_ring"]
    assert mule_ring.track == "digital_banking"
    assert mule_ring.institution == "NovaBank Digital"
    circular = by_id["circular_funds_movement"]
    assert circular.track == "private_banking"
    assert circular.institution == "Alpine Crest Private Bank"


def test_graph_native_patterns_document_graph_target() -> None:
    """Graph-derived pattern descriptions must state they are graph-feature targets."""
    by_id = {p.pattern_id: p for p in FOUNDATION_DETECTION_PATTERNS}
    for pattern_id in GRAPH_DERIVED_PATTERN_IDS:
        description = by_id[pattern_id].description.lower()
        assert "graph-derived" in description, (
            f"{pattern_id} description must document it is graph-derived"
        )
        assert "graph feature" in description, (
            f"{pattern_id} description must name the graph-feature target"
        )


def test_patterns_doc_documents_graph_native_patterns() -> None:
    """The patterns doc must cover the graph-native patterns and their graph nature."""
    doc_text = PATTERNS_DOC.read_text(encoding="utf-8")
    for pattern_id in GRAPH_DERIVED_PATTERN_IDS:
        assert pattern_id in doc_text, f"{pattern_id} missing from patterns doc"
    assert "graph-derived" in doc_text.lower() or "graph-derived" in doc_text
    assert "mule_ring" in doc_text
    assert "circular_funds_movement" in doc_text

