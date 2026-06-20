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
    SESSIONS,
    SUSPICIOUS_ACTIVITIES,
    TRANSACTIONS,
    USERS,
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

# v0.4 digital-banking feature families. Every family uses the ``db_`` prefix and
# maps to an existing digital Detection pattern ID (digital_scam_to_mule,
# new_beneficiary_payment, or session_payment_velocity). No new pattern IDs are
# introduced. Source of truth: src/banking_fraud_lab/schema/detection_patterns.py.

DB_SESSION_RISK = FeatureFamilySpec(
    family_id="db_session_risk",
    display_name="Session risk telemetry",
    description=(
        "Surfaces session-level risk telemetry such as VPN/proxy use, ASN/network "
        "risk, unfamiliar geolocation, and authentication method for digital "
        "payments."
    ),
    detection_pattern_id="session_payment_velocity",
    source_tables=(TRANSACTIONS, SESSIONS, ACCOUNTS, BANKING_RELATIONSHIPS, USERS),
    source_columns=(
        "transactions.transaction_id",
        "transactions.account_id",
        "accounts.banking_relationship_id",
        "suspicious_activities.session_id",
        "sessions.session_id",
        "sessions.is_vpn_or_proxy",
        "sessions.asn_risk_score",
        "sessions.coarse_geolocation",
        "sessions.auth_method",
    ),
    output_columns=(
        "db_is_vpn_or_proxy",
        "db_asn_risk_score",
        "db_is_high_risk_network",
        "db_is_password_sms_auth",
    ),
)

DB_BENEFICIARY_NOVELTY = FeatureFamilySpec(
    family_id="db_beneficiary_novelty",
    display_name="Beneficiary novelty",
    description=(
        "Flags outbound payments to recently added or updated beneficiaries so "
        "new-beneficiary-payment behavior is evaluated against beneficiary history."
    ),
    detection_pattern_id="new_beneficiary_payment",
    source_tables=(TRANSACTIONS, PAYMENT_BENEFICIARIES),
    source_columns=(
        "transactions.transaction_id",
        "transactions.payment_beneficiary_id",
        "transactions.booked_at",
        "payment_beneficiaries.created_at",
        "payment_beneficiaries.beneficiary_change_event",
    ),
    output_columns=("db_beneficiary_age_days", "db_is_new_beneficiary"),
)

DB_PAYMENT_VELOCITY = FeatureFamilySpec(
    family_id="db_payment_velocity",
    display_name="Session payment velocity",
    description=(
        "Counts outbound payments authorized within the same session so elevated "
        "session-level velocity supports session_payment_velocity review."
    ),
    detection_pattern_id="session_payment_velocity",
    source_tables=(TRANSACTIONS, SUSPICIOUS_ACTIVITIES, SESSIONS, ACCOUNTS),
    source_columns=(
        "transactions.transaction_id",
        "transactions.account_id",
        "suspicious_activities.transaction_id",
        "suspicious_activities.session_id",
        "sessions.session_id",
        "sessions.started_at",
    ),
    output_columns=(
        "db_session_payment_count",
        "db_session_payment_amount_chf",
        "db_session_max_payment_chf",
    ),
)

DB_ACCOUNT_AGE = FeatureFamilySpec(
    family_id="db_account_age",
    display_name="Account age",
    description=(
        "Measures account age at payment time and flags early-life accounts that "
        "are typical of digital scam-to-mule behavior."
    ),
    detection_pattern_id="digital_scam_to_mule",
    source_tables=(TRANSACTIONS, ACCOUNTS),
    source_columns=(
        "transactions.transaction_id",
        "transactions.account_id",
        "transactions.booked_at",
        "accounts.opened_at",
    ),
    output_columns=("db_account_age_days", "db_is_early_life_account"),
)

DB_SHARED_DEVICE = FeatureFamilySpec(
    family_id="db_shared_device",
    display_name="Shared device usage",
    description=(
        "Counts distinct Users observed on the same device fingerprint so shared "
        "device usage supports digital scam-to-mule review."
    ),
    detection_pattern_id="digital_scam_to_mule",
    source_tables=(SESSIONS, USERS, SUSPICIOUS_ACTIVITIES, TRANSACTIONS),
    source_columns=(
        "suspicious_activities.transaction_id",
        "suspicious_activities.session_id",
        "sessions.session_id",
        "sessions.device_fingerprint_hash",
        "sessions.user_id",
    ),
    output_columns=(
        "db_device_user_count",
        "db_is_shared_device",
    ),
)

DB_PASS_THROUGH = FeatureFamilySpec(
    family_id="db_pass_through",
    display_name="Pass-through behavior",
    description=(
        "Detects incoming credits followed rapidly by outbound debits to a new "
        "beneficiary, the pass-through signature of digital scam-to-mule flows."
    ),
    detection_pattern_id="digital_scam_to_mule",
    source_tables=(TRANSACTIONS, ACCOUNTS, PAYMENT_BENEFICIARIES),
    source_columns=(
        "transactions.transaction_id",
        "transactions.account_id",
        "transactions.booked_at",
        "transactions.direction",
        "transactions.amount_chf",
        "transactions.payment_beneficiary_id",
        "payment_beneficiaries.beneficiary_change_event",
    ),
    output_columns=(
        "db_prior_credit_amount_chf",
        "db_hours_since_prior_credit",
        "db_is_rapid_pass_through",
    ),
)

DB_RISKY_CHANNEL = FeatureFamilySpec(
    family_id="db_risky_channel",
    display_name="Risky channel",
    description=(
        "Flags high-risk digital channels and country mismatch between the paying "
        "account institution and the beneficiary country for new-beneficiary review."
    ),
    detection_pattern_id="new_beneficiary_payment",
    source_tables=(TRANSACTIONS, PAYMENT_BENEFICIARIES),
    source_columns=(
        "transactions.transaction_id",
        "transactions.channel",
        "transactions.payment_beneficiary_id",
        "payment_beneficiaries.beneficiary_account_country",
    ),
    output_columns=("db_is_mobile_app_channel", "db_is_beneficiary_country_risky"),
)

DIGITAL_BANKING_FEATURE_FAMILIES: tuple[FeatureFamilySpec, ...] = (
    DB_SESSION_RISK,
    DB_BENEFICIARY_NOVELTY,
    DB_PAYMENT_VELOCITY,
    DB_ACCOUNT_AGE,
    DB_SHARED_DEVICE,
    DB_PASS_THROUGH,
    DB_RISKY_CHANNEL,
)

FEATURE_FAMILY_IDS: tuple[str, ...] = tuple(
    feature.family_id
    for feature in (*PRIVATE_BANKING_FEATURE_FAMILIES, *DIGITAL_BANKING_FEATURE_FAMILIES)
)

_UNKNOWN_PATTERN_IDS = sorted(
    {
        feature.detection_pattern_id
        for feature in (
            *PRIVATE_BANKING_FEATURE_FAMILIES,
            *DIGITAL_BANKING_FEATURE_FAMILIES,
        )
    }
    - set(PATTERN_IDS)
)
if _UNKNOWN_PATTERN_IDS:
    raise ValueError(
        "Feature families reference unknown Detection pattern IDs: "
        f"{_UNKNOWN_PATTERN_IDS}"
    )


__all__ = [
    "AMOUNT_TO_AUM",
    "AMOUNT_TO_RELATIONSHIP_BASELINE",
    "CROSS_BORDER_MOVEMENT",
    "DB_ACCOUNT_AGE",
    "DB_BENEFICIARY_NOVELTY",
    "DB_PASS_THROUGH",
    "DB_PAYMENT_VELOCITY",
    "DB_RISKY_CHANNEL",
    "DB_SESSION_RISK",
    "DB_SHARED_DEVICE",
    "DIGITAL_BANKING_FEATURE_FAMILIES",
    "FEATURE_FAMILY_IDS",
    "FeatureFamilySpec",
    "NEW_COUNTERPARTY",
    "OFF_HOURS_ACTIVITY",
    "PRIVATE_BANKING_FEATURE_FAMILIES",
    "RM_CONCENTRATION",
    "VELOCITY_CHANGE",
]
