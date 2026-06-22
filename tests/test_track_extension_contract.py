"""Validation tests for the v0.3/v0.4 track extension contract."""

from __future__ import annotations

import re
from pathlib import Path

from banking_fraud_lab.schema.detection_patterns import (
    FOUNDATION_DETECTION_PATTERNS,
    PATTERN_IDS,
)

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "docs" / "schema" / "track-extension-conventions.md"
SCHEMA_README = ROOT / "docs" / "schema" / "README.md"
PATTERNS_DOC = ROOT / "docs" / "schema" / "detection_patterns.md"
NOTEBOOKS_README = ROOT / "notebooks" / "README.md"

REQUIRED_SECTIONS = (
    "## Feature Naming Conventions",
    "## Notebook Module Layout",
    "## Feature-Family Metadata",
    "## Evaluation Output Expectations",
    "## Case and Regulatory Link Structure",
    "## v0.4 Digital-Banking Track Mirroring",
    "## Human Approval",
    "## Source Boundaries",
)

PROHIBITED_TERMS = (
    "Julius Baer",
    "UBS",
    "Credit Suisse",
    "real client data",
    "reconstruct real events",
    "legal advice",
    "compliance advice",
    "audit advice",
    "job preparation",
)


def _contract_text() -> str:
    assert CONTRACT_PATH.exists(), f"{CONTRACT_PATH} does not exist"
    return CONTRACT_PATH.read_text(encoding="utf-8")


def test_track_extension_contract_has_required_sections() -> None:
    contract = _contract_text()

    for section in REQUIRED_SECTIONS:
        assert section in contract, f"Missing section {section!r}"


def test_track_extension_contract_reuses_detection_pattern_registry() -> None:
    contract = _contract_text()

    for term in [
        "src/banking_fraud_lab/schema/detection_patterns.py",
        "PatternSpec",
        "PATTERN_IDS",
        "ACTIVITY_TYPE_TO_PATTERN",
    ]:
        assert term in contract

    for pattern in FOUNDATION_DETECTION_PATTERNS:
        assert pattern.pattern_id in contract


def test_track_extension_contract_references_valid_pattern_ids() -> None:
    contract = _contract_text()
    registry_ids = set(PATTERN_IDS)
    candidate_lines = [
        line
        for line in contract.splitlines()
        if "pattern_id" in line or "pattern ID" in line or "Pattern ID" in line
    ]
    quoted_tokens = set(re.findall(r"`([a-z][a-z0-9_]+)`", "\n".join(candidate_lines)))
    pattern_like_tokens = {
        token
        for token in quoted_tokens
        if token.startswith("pb_")
        or token.startswith("digital_")
        or token in {"new_beneficiary_payment", "session_payment_velocity"}
    }

    assert pattern_like_tokens, "No pattern ID references found in the contract"
    invalid_pattern_ids = sorted(pattern_like_tokens - registry_ids)
    assert not invalid_pattern_ids, (
        "Contract references pattern IDs not present in PATTERN_IDS: "
        f"{invalid_pattern_ids}"
    )


def test_track_extension_contract_contains_no_prohibited_terms() -> None:
    contract = _contract_text()

    for term in PROHIBITED_TERMS:
        pattern = rf"(?<![A-Za-z0-9-]){re.escape(term)}(?![A-Za-z0-9-])"
        assert re.search(pattern, contract, flags=re.IGNORECASE) is None, (
            f"Prohibited term {term!r} found in {CONTRACT_PATH}"
        )


def test_track_extension_contract_has_hitl_markers() -> None:
    contract = _contract_text()

    assert "Status: draft for human review." in contract
    assert "<!-- HITL-REVIEW-REQUIRED:" in contract
    assert "## Human Approval" in contract
    assert "PENDING-HUMAN-APPROVAL" in contract


def test_track_extension_contract_includes_v04_mirroring_guidance() -> None:
    contract = _contract_text()

    assert "NovaBank Digital" in contract
    assert "NovaBank Digital scope is excluded from v0.3" in contract
    for pattern_id in [
        "digital_scam_to_mule",
        "new_beneficiary_payment",
        "session_payment_velocity",
    ]:
        assert pattern_id in contract


def test_track_extension_contract_pins_v04_conventions() -> None:
    contract = _contract_text()

    # Issue #97 resolves the open v0.4 placeholders.
    assert "Future digital-banking prefix" not in contract
    assert "Future numbered digital-banking module path" not in contract

    # The pinned v0.4 conventions are recorded in the contract.
    assert "db_" in contract
    assert "`novabank`" in contract
    assert "notebooks/05_digital_session_and_payment_fraud/" in contract

    # v0.4 reuses the existing registry instead of extending it and documents
    # how the existing pattern IDs map to the two v0.4 scenario families, so
    # downstream slices model account-takeover and onboarding-abuse correctly.
    assert "does not extend" in contract
    assert "account-takeover" in contract
    assert "onboarding-abuse" in contract


def test_track_extension_contract_is_linked_from_indexes() -> None:
    expected_link = "track-extension-conventions.md"

    for path in [SCHEMA_README, PATTERNS_DOC, NOTEBOOKS_README]:
        text = path.read_text(encoding="utf-8")
        assert expected_link in text, f"{expected_link} is not linked from {path}"
