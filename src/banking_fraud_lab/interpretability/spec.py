"""Explanation-family metadata mapping interpretability signals to Detection patterns.

Mirrors the frozen-spec precedent set by :mod:`banking_fraud_lab.schema` (the
``PatternSpec`` / ``PATTERN_IDS`` vocabulary) and
:mod:`banking_fraud_lab.graph.features_spec` (``GraphFeatureFamilySpec``).

Every ``ExplanationFamilySpec`` references a Detection pattern id that already
exists in :data:`banking_fraud_lab.schema.PATTERN_IDS`; a module-load integrity
guard (see the bottom of this module) raises if any family references an unknown
pattern, mirroring the guards in :mod:`banking_fraud_lab.features.specs` and
:mod:`banking_fraud_lab.graph.features_spec`.
"""

from __future__ import annotations

from dataclasses import dataclass

from banking_fraud_lab.schema import PATTERN_IDS


@dataclass(frozen=True)
class ExplanationFamilySpec:
    """Structured metadata for one explainable model-feature family.

    Each family groups the numeric model features that explain one Detection
    pattern, so a learner can ask "which features drove this alert's score?" and
    trace the answer back to the pattern it supports (for example
    ``pb_high_value_movement`` for an Alpine Crest Private Bank high-value
    alert, or ``digital_scam_to_mule`` for a NovaBank Digital pass-through
    alert).
    """

    family_id: str
    display_name: str
    description: str
    detection_pattern_id: str
    track: str
    feature_columns: tuple[str, ...]


# --- Private-banking explanation families (Alpine Crest Private Bank) -------
# Feature columns are drawn verbatim from the v0.3 private-banking FeatureFamilySpec
# output_columns so the explanation families reference real model inputs.

PB_HIGH_VALUE_EXPLANATION = ExplanationFamilySpec(
    family_id="explanation_pb_high_value_movement",
    display_name="Private-banking high-value-movement explanations",
    description=(
        "Explains alerts driven by high-value movement inside a Banking "
        "relationship through amount-to-AUM, amount-to-baseline, and cross-border "
        "feature contributions, so a relationship manager can see why a Client's "
        "payment was scored against the relationship's profile."
    ),
    detection_pattern_id="pb_high_value_movement",
    track="private_banking",
    feature_columns=(
        "amount_to_aum_ratio",
        "amount_to_relationship_baseline_ratio",
        "is_cross_border",
    ),
)

PB_TRANSACTION_FRAUD_EXPLANATION = ExplanationFamilySpec(
    family_id="explanation_pb_transaction_fraud",
    display_name="Private-banking transaction-fraud explanations",
    description=(
        "Explains alerts driven by injected transaction-fraud scenarios through "
        "counterparty novelty, off-hours, velocity-change, and relationship-"
        "manager concentration feature contributions, so reviewers can separate "
        "structural fraud signals from ordinary Client activity."
    ),
    detection_pattern_id="pb_transaction_fraud",
    track="private_banking",
    feature_columns=(
        "counterparty_age_days",
        "is_new_counterparty",
        "is_off_hours",
        "relationship_txn_count_7d",
        "amount_7d_to_30d_ratio",
        "rm_alert_share",
    ),
)

# --- Digital-banking explanation families (NovaBank Digital) ----------------
# Feature columns are drawn verbatim from the v0.4 digital-banking FeatureFamilySpec
# output_columns (``db_`` prefix).

DB_NEW_BENEFICIARY_EXPLANATION = ExplanationFamilySpec(
    family_id="explanation_new_beneficiary_payment",
    display_name="New-beneficiary-payment explanations",
    description=(
        "Explains alerts driven by payments to a recently added beneficiary "
        "through beneficiary-novelty and risky-channel feature contributions, so "
        "a User's account-takeover risk is inspectable rather than opaque."
    ),
    detection_pattern_id="new_beneficiary_payment",
    track="digital_banking",
    feature_columns=(
        "db_beneficiary_age_days",
        "db_is_new_beneficiary",
        "db_is_mobile_app_channel",
        "db_is_beneficiary_country_risky",
    ),
)

DB_SESSION_VELOCITY_EXPLANATION = ExplanationFamilySpec(
    family_id="explanation_session_payment_velocity",
    display_name="Session-payment-velocity explanations",
    description=(
        "Explains alerts driven by elevated in-session payment velocity through "
        "session-risk and payment-count feature contributions, so an analyst can "
        "see which session telemetry raised a User's alert score."
    ),
    detection_pattern_id="session_payment_velocity",
    track="digital_banking",
    feature_columns=(
        "db_is_vpn_or_proxy",
        "db_asn_risk_score",
        "db_is_high_risk_network",
        "db_session_payment_count",
        "db_session_max_payment_chf",
    ),
)

DB_SCAM_TO_MULE_EXPLANATION = ExplanationFamilySpec(
    family_id="explanation_digital_scam_to_mule",
    display_name="Digital scam-to-mule explanations",
    description=(
        "Explains alerts driven by scam-to-mule pass-through behaviour through "
        "account-age, shared-device, and rapid pass-through feature "
        "contributions, so the path from an authorised scam payment into a mule "
        "account is inspectable per alert."
    ),
    detection_pattern_id="digital_scam_to_mule",
    track="digital_banking",
    feature_columns=(
        "db_account_age_days",
        "db_is_early_life_account",
        "db_device_user_count",
        "db_is_shared_device",
        "db_prior_credit_amount_chf",
        "db_hours_since_prior_credit",
        "db_is_rapid_pass_through",
    ),
)

EXPLANATION_FAMILY_SPECS: tuple[ExplanationFamilySpec, ...] = (
    PB_HIGH_VALUE_EXPLANATION,
    PB_TRANSACTION_FRAUD_EXPLANATION,
    DB_NEW_BENEFICIARY_EXPLANATION,
    DB_SESSION_VELOCITY_EXPLANATION,
    DB_SCAM_TO_MULE_EXPLANATION,
)

EXPLANATION_FAMILY_IDS: tuple[str, ...] = tuple(
    spec.family_id for spec in EXPLANATION_FAMILY_SPECS
)

#: Map each Detection pattern id to the explanation family that explains it.
PATTERN_TO_EXPLANATION_FAMILY: dict[str, ExplanationFamilySpec] = {
    spec.detection_pattern_id: spec for spec in EXPLANATION_FAMILY_SPECS
}

# --- Module-load integrity guard -------------------------------------------
# Every explanation family must reference a Detection pattern that exists in the
# schema vocabulary, mirroring the guards in features/specs.py and
# graph/features_spec.py. This keeps the interpretability vocabulary anchored to
# the shared Detection-pattern source of truth.

_UNKNOWN_PATTERN_IDS = sorted(
    {spec.detection_pattern_id for spec in EXPLANATION_FAMILY_SPECS} - set(PATTERN_IDS)
)
if _UNKNOWN_PATTERN_IDS:
    raise ValueError(
        "Explanation families reference unknown Detection pattern IDs: "
        f"{_UNKNOWN_PATTERN_IDS}"
    )


__all__ = [
    "DB_NEW_BENEFICIARY_EXPLANATION",
    "DB_SCAM_TO_MULE_EXPLANATION",
    "DB_SESSION_VELOCITY_EXPLANATION",
    "EXPLANATION_FAMILY_IDS",
    "EXPLANATION_FAMILY_SPECS",
    "ExplanationFamilySpec",
    "PATTERN_TO_EXPLANATION_FAMILY",
    "PB_HIGH_VALUE_EXPLANATION",
    "PB_TRANSACTION_FRAUD_EXPLANATION",
]
