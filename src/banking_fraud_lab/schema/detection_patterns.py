"""Detection pattern vocabulary for cross-module references."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PatternSpec:
    """Structured metadata for one detection pattern identifier."""

    pattern_id: str
    display_name: str
    description: str
    track: str
    activity_types: tuple[str, ...]
    institution: str


PB_HIGH_VALUE_MOVEMENT = PatternSpec(
    pattern_id="pb_high_value_movement",
    display_name="Private-banking high-value movement",
    description=(
        "Unusual high-value transactions within a private-banking relationship "
        "that deviate from the Client's historical profile and the Banking "
        "relationship's typical transaction band."
    ),
    track="private_banking",
    activity_types=("private_banking_high_value",),
    institution="Alpine Crest Private Bank",
)

NEW_BENEFICIARY_PAYMENT = PatternSpec(
    pattern_id="new_beneficiary_payment",
    display_name="New beneficiary payment",
    description=(
        "A payment directed to a recently added beneficiary, often observed "
        "in digital-banking channels where rapid beneficiary creation followed "
        "by an immediate outbound transfer signals potential account takeover "
        "or authorised scam activity."
    ),
    track="digital_banking",
    activity_types=("new_beneficiary_payment",),
    institution="NovaBank Digital",
)

SESSION_PAYMENT_VELOCITY = PatternSpec(
    pattern_id="session_payment_velocity",
    display_name="Session payment velocity",
    description=(
        "An elevated number of payments within a single digital session, "
        "exceeding the User's typical session-level velocity and suggesting "
        "automated or coerced transaction behaviour."
    ),
    track="digital_banking",
    activity_types=("session_payment_velocity",),
    institution="NovaBank Digital",
)

PB_TRANSACTION_FRAUD = PatternSpec(
    pattern_id="pb_transaction_fraud",
    display_name="Private-banking transaction fraud",
    description=(
        "Injected transaction-fraud scenarios in a private-banking context "
        "covering relationship-manager-assisted or self-initiated payments "
        "that exhibit structural fraud signals detectable through feature "
        "engineering and scoring rules."
    ),
    track="private_banking",
    activity_types=("private_banking_transaction_fraud",),
    institution="Alpine Crest Private Bank",
)

DIGITAL_SCAM_TO_MULE = PatternSpec(
    pattern_id="digital_scam_to_mule",
    display_name="Digital scam-to-mule flow",
    description=(
        "A digital-banking fraud scenario where a scam victim authorises a "
        "payment that moves into a mule or rented account and is rapidly "
        "passed onward, observed through beneficiary-change events, early-life "
        "mule accounts, shared-device signals, and pass-through velocity."
    ),
    track="digital_banking",
    activity_types=("digital_scam_to_mule_flow",),
    institution="NovaBank Digital",
)

MULE_RING = PatternSpec(
    pattern_id="mule_ring",
    display_name="Mule ring and shared-beneficiary cluster",
    description=(
        "A digital-banking network pattern where several mule or rented "
        "accounts move funds through shared beneficiaries and devices, forming "
        "a connected ring that the single-edge scam-to-mule flow does not "
        "capture on its own. This pattern is graph-derived: it is the target of "
        "connected-component, degree, and community graph features rather than "
        "a single generator activity type."
    ),
    track="digital_banking",
    activity_types=(),
    institution="NovaBank Digital",
)

CIRCULAR_FUNDS_MOVEMENT = PatternSpec(
    pattern_id="circular_funds_movement",
    display_name="Circular funds movement among related entities",
    description=(
        "A private-banking network pattern where funds cycle among related "
        "Partner, Client, and Banking relationship entities through layered "
        "accounts and counterparties, forming circular transaction structures "
        "that the high-value-movement and transaction-fraud patterns do not "
        "capture on their own. This pattern is graph-derived: it is the target "
        "of cycle, path-length, and bridge-node graph features rather than a "
        "single generator activity type."
    ),
    track="private_banking",
    activity_types=(),
    institution="Alpine Crest Private Bank",
)

FOUNDATION_DETECTION_PATTERNS: tuple[PatternSpec, ...] = (
    PB_HIGH_VALUE_MOVEMENT,
    NEW_BENEFICIARY_PAYMENT,
    SESSION_PAYMENT_VELOCITY,
    PB_TRANSACTION_FRAUD,
    DIGITAL_SCAM_TO_MULE,
    MULE_RING,
    CIRCULAR_FUNDS_MOVEMENT,
)

PATTERN_IDS: tuple[str, ...] = tuple(p.pattern_id for p in FOUNDATION_DETECTION_PATTERNS)

ACTIVITY_TYPE_TO_PATTERN: dict[str, str] = {
    activity_type: pattern.pattern_id
    for pattern in FOUNDATION_DETECTION_PATTERNS
    for activity_type in pattern.activity_types
}

__all__ = [
    "ACTIVITY_TYPE_TO_PATTERN",
    "CIRCULAR_FUNDS_MOVEMENT",
    "DIGITAL_SCAM_TO_MULE",
    "FOUNDATION_DETECTION_PATTERNS",
    "MULE_RING",
    "NEW_BENEFICIARY_PAYMENT",
    "PB_HIGH_VALUE_MOVEMENT",
    "PB_TRANSACTION_FRAUD",
    "PATTERN_IDS",
    "SESSION_PAYMENT_VELOCITY",
    "PatternSpec",
]
