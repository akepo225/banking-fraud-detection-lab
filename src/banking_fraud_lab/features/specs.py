"""Feature-family metadata for private-banking analytics."""

from __future__ import annotations

from dataclasses import dataclass

from banking_fraud_lab.schema import (
    ACCOUNTS,
    ALERTS,
    BANKING_RELATIONSHIPS,
    CASES,
    CLIENTS,
    PARTNERS,
    PAYMENT_BENEFICIARIES,
    PATTERN_IDS,
    TRANSACTIONS,
)


@dataclass(frozen=True)
class FeatureFamilySpec:
    """Structured metadata for one reusable feature family."""

    family_id: str
    display_name: str
    description: str
    detection_pattern_id: str
    source_tables: tuple[str, ...]
    source_columns: tuple[str, ...]
    output_columns: tuple[str, ...]


AMOUNT_TO_AUM = FeatureFamilySpec(
    family_id="amount_to_aum",
    display_name="Amount-to-AUM ratio",
    description=(
        "Compares transaction size with the Banking relationship's CHF assets "
        "under management so high-value movement is evaluated in relationship context."
    ),
    detection_pattern_id="pb_high_value_movement",
    source_tables=(TRANSACTIONS, ACCOUNTS, BANKING_RELATIONSHIPS),
    source_columns=(
        "transactions.transaction_id",
        "transactions.account_id",
        "transactions.amount_chf",
        "accounts.banking_relationship_id",
        "banking_relationships.aum_chf",
    ),
    output_columns=("amount_to_aum_ratio",),
)

AMOUNT_TO_RELATIONSHIP_BASELINE = FeatureFamilySpec(
    family_id="amount_to_relationship_baseline",
    display_name="Amount-to-relationship-baseline ratio",
    description=(
        "Compares each transaction with earlier CHF transaction activity in the "
        "same Banking relationship."
    ),
    detection_pattern_id="pb_high_value_movement",
    source_tables=(TRANSACTIONS, ACCOUNTS, BANKING_RELATIONSHIPS),
    source_columns=(
        "transactions.transaction_id",
        "transactions.account_id",
        "transactions.booked_at",
        "transactions.amount_chf",
        "accounts.banking_relationship_id",
    ),
    output_columns=(
        "relationship_amount_baseline_chf",
        "amount_to_relationship_baseline_ratio",
    ),
)

NEW_COUNTERPARTY = FeatureFamilySpec(
    family_id="new_counterparty",
    display_name="New counterparty behavior",
    description=(
        "Flags outbound transaction counterparties that are first observed in "
        "transaction history or recently created for the Client attached to the "
        "Banking relationship."
    ),
    detection_pattern_id="pb_transaction_fraud",
    source_tables=(TRANSACTIONS, PAYMENT_BENEFICIARIES),
    source_columns=(
        "transactions.transaction_id",
        "transactions.payment_beneficiary_id",
        "transactions.booked_at",
        "payment_beneficiaries.created_at",
        "payment_beneficiaries.beneficiary_change_event",
    ),
    output_columns=("counterparty_age_days", "is_new_counterparty"),
)

OFF_HOURS_ACTIVITY = FeatureFamilySpec(
    family_id="off_hours_activity",
    display_name="Off-hours activity",
    description=(
        "Extracts the booking hour and flags activity outside a normal private-"
        "banking business-day review window."
    ),
    detection_pattern_id="pb_transaction_fraud",
    source_tables=(TRANSACTIONS,),
    source_columns=("transactions.transaction_id", "transactions.booked_at"),
    output_columns=("booked_hour", "is_off_hours"),
)

CROSS_BORDER_MOVEMENT = FeatureFamilySpec(
    family_id="cross_border_movement",
    display_name="Cross-border movement",
    description=(
        "Compares the Client's partner country with beneficiary account and bank "
        "countries for counterparty-linked movement."
    ),
    detection_pattern_id="pb_high_value_movement",
    source_tables=(
        TRANSACTIONS,
        ACCOUNTS,
        BANKING_RELATIONSHIPS,
        CLIENTS,
        PARTNERS,
        PAYMENT_BENEFICIARIES,
    ),
    source_columns=(
        "transactions.transaction_id",
        "transactions.account_id",
        "transactions.payment_beneficiary_id",
        "accounts.banking_relationship_id",
        "banking_relationships.primary_client_id",
        "clients.partner_id",
        "partners.country",
        "payment_beneficiaries.beneficiary_account_country",
        "payment_beneficiaries.beneficiary_bank_country",
    ),
    output_columns=(
        "partner_country",
        "beneficiary_account_country",
        "beneficiary_bank_country",
        "is_cross_border",
    ),
)

VELOCITY_CHANGE = FeatureFamilySpec(
    family_id="velocity_change",
    display_name="Velocity change",
    description=(
        "Counts and sums recent relationship-level transaction activity in 7-day "
        "and 30-day windows."
    ),
    detection_pattern_id="pb_transaction_fraud",
    source_tables=(TRANSACTIONS, ACCOUNTS, BANKING_RELATIONSHIPS),
    source_columns=(
        "transactions.transaction_id",
        "transactions.account_id",
        "transactions.booked_at",
        "transactions.amount_chf",
        "accounts.banking_relationship_id",
    ),
    output_columns=(
        "relationship_txn_count_7d",
        "relationship_amount_sum_7d_chf",
        "relationship_txn_count_30d",
        "relationship_amount_sum_30d_chf",
        "txn_count_7d_to_30d_ratio",
        "amount_7d_to_30d_ratio",
    ),
)

RM_CONCENTRATION = FeatureFamilySpec(
    family_id="rm_concentration",
    display_name="Relationship-manager concentration",
    description=(
        "Measures alert and case concentration by current relationship-manager "
        "assignment across private-banking relationships."
    ),
    detection_pattern_id="pb_transaction_fraud",
    source_tables=(ALERTS, CASES, BANKING_RELATIONSHIPS),
    source_columns=(
        "alerts.alert_id",
        "alerts.banking_relationship_id",
        "cases.case_id",
        "cases.banking_relationship_id",
        "banking_relationships.relationship_manager_code",
    ),
    output_columns=("rm_alert_count", "rm_case_count", "rm_alert_share"),
)

PRIVATE_BANKING_FEATURE_FAMILIES: tuple[FeatureFamilySpec, ...] = (
    AMOUNT_TO_AUM,
    AMOUNT_TO_RELATIONSHIP_BASELINE,
    NEW_COUNTERPARTY,
    OFF_HOURS_ACTIVITY,
    CROSS_BORDER_MOVEMENT,
    VELOCITY_CHANGE,
    RM_CONCENTRATION,
)

FEATURE_FAMILY_IDS: tuple[str, ...] = tuple(
    feature.family_id for feature in PRIVATE_BANKING_FEATURE_FAMILIES
)

_UNKNOWN_PATTERN_IDS = sorted(
    {
        feature.detection_pattern_id
        for feature in PRIVATE_BANKING_FEATURE_FAMILIES
    }
    - set(PATTERN_IDS)
)
if _UNKNOWN_PATTERN_IDS:
    raise ValueError(
        "Private-banking feature families reference unknown Detection pattern IDs: "
        f"{_UNKNOWN_PATTERN_IDS}"
    )


__all__ = [
    "AMOUNT_TO_AUM",
    "AMOUNT_TO_RELATIONSHIP_BASELINE",
    "CROSS_BORDER_MOVEMENT",
    "FEATURE_FAMILY_IDS",
    "FeatureFamilySpec",
    "NEW_COUNTERPARTY",
    "OFF_HOURS_ACTIVITY",
    "PRIVATE_BANKING_FEATURE_FAMILIES",
    "RM_CONCENTRATION",
    "VELOCITY_CHANGE",
]
