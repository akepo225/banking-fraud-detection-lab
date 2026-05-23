"""Stable table and column contract for v0.1 generated datasets."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ColumnSpec:
    """Column-level schema metadata used by generators, docs, and tests."""

    name: str
    dtype: str
    nullable: bool
    description: str
    references: str | None = None


@dataclass(frozen=True)
class TableSpec:
    """Table-level schema metadata for one generated dataset table."""

    name: str
    purpose: str
    columns: tuple[ColumnSpec, ...]
    allow_empty: bool = False


PARTNERS = "partners"
CLIENTS = "clients"
ROLES = "roles"
PARTNER_ROLES = "partner_roles"
BANKING_RELATIONSHIPS = "banking_relationships"
ACCOUNTS = "accounts"
TRANSACTIONS = "transactions"
USERS = "users"
SESSIONS = "sessions"
PAYMENT_BENEFICIARIES = "payment_beneficiaries"
SUSPICIOUS_ACTIVITIES = "suspicious_activities"
ALERTS = "alerts"
CASES = "cases"
CASE_OUTCOMES = "case_outcomes"
PROTECTED_SCENARIO_ANSWER_KEYS = "protected_scenario_answer_keys"


TABLE_SPECS: dict[str, TableSpec] = {
    PARTNERS: TableSpec(
        name=PARTNERS,
        purpose=(
            "Natural and legal persons represented in the fictional banking core model."
        ),
        columns=(
            ColumnSpec("partner_id", "string", False, "Stable synthetic partner identifier."),
            ColumnSpec(
                "institution_name",
                "string",
                False,
                "Fictional institution that owns the partner record.",
            ),
            ColumnSpec(
                "partner_type",
                "string",
                False,
                "Natural person or legal entity classification.",
            ),
            ColumnSpec("display_name", "string", False, "Synthetic display name."),
            ColumnSpec("country", "string", False, "Primary country code."),
            ColumnSpec("created_at", "datetime64[ns]", False, "Partner creation timestamp."),
            ColumnSpec("risk_rating", "string", False, "Low, medium, or high KYC risk band."),
        ),
    ),
    CLIENTS: TableSpec(
        name=CLIENTS,
        purpose="Legal customer records that map client identity to a core partner.",
        columns=(
            ColumnSpec("client_id", "string", False, "Stable synthetic client identifier."),
            ColumnSpec(
                "partner_id",
                "string",
                False,
                "Partner that represents the legal customer.",
                references="partners.partner_id",
            ),
            ColumnSpec(
                "institution_name",
                "string",
                False,
                "Fictional institution that owns the client record.",
            ),
            ColumnSpec(
                "client_segment",
                "string",
                False,
                "Client segment used for progressive learner views.",
            ),
            ColumnSpec("onboarded_at", "datetime64[ns]", False, "Client onboarding timestamp."),
            ColumnSpec("status", "string", False, "Client status."),
        ),
    ),
    ROLES: TableSpec(
        name=ROLES,
        purpose="Controlled vocabulary of relationship roles used by partner_roles.",
        columns=(
            ColumnSpec("role_id", "string", False, "Stable synthetic role identifier."),
            ColumnSpec("role_code", "string", False, "Machine-readable role code."),
            ColumnSpec("role_name", "string", False, "Human-readable role name."),
            ColumnSpec("description", "string", False, "Role meaning in learner-facing language."),
        ),
    ),
    PARTNER_ROLES: TableSpec(
        name=PARTNER_ROLES,
        purpose="Effective-dated partner roles within a banking relationship.",
        columns=(
            ColumnSpec(
                "partner_role_id", "string", False, "Stable synthetic partner-role identifier."
            ),
            ColumnSpec(
                "partner_id",
                "string",
                False,
                "Partner assigned to the role.",
                references="partners.partner_id",
            ),
            ColumnSpec(
                "role_id",
                "string",
                False,
                "Assigned role.",
                references="roles.role_id",
            ),
            ColumnSpec(
                "banking_relationship_id",
                "string",
                False,
                "Banking relationship where the role applies.",
                references="banking_relationships.banking_relationship_id",
            ),
            ColumnSpec("effective_from", "datetime64[ns]", False, "Role start timestamp."),
            ColumnSpec("effective_to", "datetime64[ns]", True, "Role end timestamp, if closed."),
        ),
    ),
    BANKING_RELATIONSHIPS: TableSpec(
        name=BANKING_RELATIONSHIPS,
        purpose="Swiss-bank-style containers grouping clients, partners, and accounts.",
        columns=(
            ColumnSpec(
                "banking_relationship_id",
                "string",
                False,
                "Stable synthetic banking relationship identifier.",
            ),
            ColumnSpec(
                "primary_client_id",
                "string",
                False,
                "Primary legal client for the relationship.",
                references="clients.client_id",
            ),
            ColumnSpec(
                "institution_name",
                "string",
                False,
                "Fictional institution that owns the relationship.",
            ),
            ColumnSpec("relationship_name", "string", False, "Learner-readable relationship label."),
            ColumnSpec("opened_at", "datetime64[ns]", False, "Relationship opening timestamp."),
            ColumnSpec("status", "string", False, "Relationship status."),
            ColumnSpec(
                "relationship_manager_code",
                "string",
                False,
                "Synthetic relationship manager assignment code.",
            ),
        ),
    ),
    ACCOUNTS: TableSpec(
        name=ACCOUNTS,
        purpose="Deposit, custody, and payment accounts under banking relationships.",
        columns=(
            ColumnSpec("account_id", "string", False, "Stable synthetic account identifier."),
            ColumnSpec(
                "banking_relationship_id",
                "string",
                False,
                "Owning banking relationship.",
                references="banking_relationships.banking_relationship_id",
            ),
            ColumnSpec(
                "institution_name",
                "string",
                False,
                "Fictional institution that owns the account.",
            ),
            ColumnSpec("account_type", "string", False, "Account product type."),
            ColumnSpec("currency", "string", False, "Account currency."),
            ColumnSpec("opened_at", "datetime64[ns]", False, "Account opening timestamp."),
            ColumnSpec("status", "string", False, "Account status."),
            ColumnSpec("balance_original", "Decimal", False, "Exact account balance in original currency."),
            ColumnSpec("balance_currency", "string", False, "Currency for `balance_original`."),
            ColumnSpec("balance_chf", "Decimal", False, "Exact CHF-normalized account balance."),
        ),
    ),
    TRANSACTIONS: TableSpec(
        name=TRANSACTIONS,
        purpose="Money movement events used by both private-banking and digital-banking tracks.",
        columns=(
            ColumnSpec(
                "transaction_id", "string", False, "Stable synthetic transaction identifier."
            ),
            ColumnSpec(
                "account_id",
                "string",
                False,
                "Account where the transaction is booked.",
                references="accounts.account_id",
            ),
            ColumnSpec(
                "payment_beneficiary_id",
                "string",
                True,
                "Payment beneficiary for outbound digital payments.",
                references="payment_beneficiaries.payment_beneficiary_id",
            ),
            ColumnSpec("booked_at", "datetime64[ns]", False, "Transaction booking timestamp."),
            ColumnSpec("transaction_type", "string", False, "Wire, card, cash, FX, or fee type."),
            ColumnSpec("channel", "string", False, "Branch, relationship manager, web, app, or batch channel."),
            ColumnSpec("direction", "string", False, "Debit or credit from the account perspective."),
            ColumnSpec("amount_original", "Decimal", False, "Exact transaction amount in original currency."),
            ColumnSpec("currency", "string", False, "Original transaction currency."),
            ColumnSpec("amount_chf", "Decimal", False, "Exact CHF-normalized transaction amount."),
            ColumnSpec("description", "string", False, "Synthetic transaction description."),
        ),
    ),
    USERS: TableSpec(
        name=USERS,
        purpose="Digital login identities that authenticate sessions for clients.",
        columns=(
            ColumnSpec("user_id", "string", False, "Stable synthetic user identifier."),
            ColumnSpec(
                "client_id",
                "string",
                False,
                "Client that owns the login identity.",
                references="clients.client_id",
            ),
            ColumnSpec(
                "institution_name",
                "string",
                False,
                "Fictional institution that owns the user record.",
            ),
            ColumnSpec("username_hash", "string", False, "Synthetic hash-like username token."),
            ColumnSpec("created_at", "datetime64[ns]", False, "Digital user creation timestamp."),
            ColumnSpec("status", "string", False, "Digital user status."),
        ),
    ),
    SESSIONS: TableSpec(
        name=SESSIONS,
        purpose="Digital session telemetry for e-banking and app behavior.",
        columns=(
            ColumnSpec("session_id", "string", False, "Stable synthetic session identifier."),
            ColumnSpec(
                "user_id",
                "string",
                False,
                "Digital login identity for the session.",
                references="users.user_id",
            ),
            ColumnSpec("started_at", "datetime64[ns]", False, "Session start timestamp."),
            ColumnSpec("channel", "string", False, "Web or mobile app channel."),
            ColumnSpec("device_fingerprint_hash", "string", False, "Synthetic device fingerprint token."),
            ColumnSpec("ip_country", "string", False, "Country inferred from IP address."),
            ColumnSpec("asn_risk_score", "int64", False, "Coarse ASN/network risk score from 0 to 100."),
            ColumnSpec("is_vpn_or_proxy", "bool", False, "Whether the session used VPN or proxy signals."),
            ColumnSpec("auth_method", "string", False, "Authentication method used."),
            ColumnSpec("session_event", "string", False, "Main event observed during the session."),
        ),
    ),
    PAYMENT_BENEFICIARIES: TableSpec(
        name=PAYMENT_BENEFICIARIES,
        purpose="Saved payment beneficiaries used by digital-banking payments.",
        columns=(
            ColumnSpec(
                "payment_beneficiary_id",
                "string",
                False,
                "Stable synthetic payment beneficiary identifier.",
            ),
            ColumnSpec(
                "client_id",
                "string",
                False,
                "Client that owns the beneficiary.",
                references="clients.client_id",
            ),
            ColumnSpec(
                "added_by_user_id",
                "string",
                False,
                "User that added the beneficiary.",
                references="users.user_id",
            ),
            ColumnSpec("beneficiary_name", "string", False, "Synthetic beneficiary name."),
            ColumnSpec(
                "beneficiary_account_country",
                "string",
                False,
                "Country code for the beneficiary account.",
            ),
            ColumnSpec("beneficiary_bank_country", "string", False, "Country code for the beneficiary bank."),
            ColumnSpec("created_at", "datetime64[ns]", False, "Beneficiary creation timestamp."),
            ColumnSpec("status", "string", False, "Beneficiary status."),
        ),
    ),
    SUSPICIOUS_ACTIVITIES: TableSpec(
        name=SUSPICIOUS_ACTIVITIES,
        purpose=(
            "Suspicious activity observations that sit before generated alerts in the "
            "alert lifecycle."
        ),
        columns=(
            ColumnSpec(
                "suspicious_activity_id",
                "string",
                False,
                "Stable synthetic suspicious activity identifier.",
            ),
            ColumnSpec(
                "institution_name",
                "string",
                False,
                "Fictional institution that owns the observation.",
            ),
            ColumnSpec(
                "banking_relationship_id",
                "string",
                False,
                "Banking relationship where the suspicious activity was observed.",
                references="banking_relationships.banking_relationship_id",
            ),
            ColumnSpec(
                "account_id",
                "string",
                False,
                "Account linked to the suspicious activity.",
                references="accounts.account_id",
            ),
            ColumnSpec(
                "transaction_id",
                "string",
                False,
                "Transaction that carried the observed suspicious activity.",
                references="transactions.transaction_id",
            ),
            ColumnSpec(
                "user_id",
                "string",
                True,
                "Digital login identity linked to the activity, where applicable.",
                references="users.user_id",
            ),
            ColumnSpec(
                "session_id",
                "string",
                True,
                "Digital session linked to the activity, where applicable.",
                references="sessions.session_id",
            ),
            ColumnSpec(
                "payment_beneficiary_id",
                "string",
                True,
                "Payment beneficiary linked to the activity, where applicable.",
                references="payment_beneficiaries.payment_beneficiary_id",
            ),
            ColumnSpec("activity_type", "string", False, "Detection pattern observed."),
            ColumnSpec("detected_at", "datetime64[ns]", False, "Time the activity was detected."),
            ColumnSpec("detection_signal", "string", False, "Learner-readable signal summary."),
            ColumnSpec("suspected_amount_chf", "Decimal", False, "CHF-normalized amount under review."),
            ColumnSpec("review_priority", "string", False, "Low, medium, or high review priority."),
        ),
    ),
    ALERTS: TableSpec(
        name=ALERTS,
        purpose="Alerts generated from suspicious activities that may trigger case investigations.",
        columns=(
            ColumnSpec("alert_id", "string", False, "Stable synthetic alert identifier."),
            ColumnSpec(
                "suspicious_activity_id",
                "string",
                False,
                "Suspicious activity that generated the alert.",
                references="suspicious_activities.suspicious_activity_id",
            ),
            ColumnSpec(
                "banking_relationship_id",
                "string",
                False,
                "Banking relationship linked to the alert.",
                references="banking_relationships.banking_relationship_id",
            ),
            ColumnSpec(
                "account_id",
                "string",
                False,
                "Account linked to the alert.",
                references="accounts.account_id",
            ),
            ColumnSpec(
                "triggered_transaction_id",
                "string",
                False,
                "Transaction that triggered the alert.",
                references="transactions.transaction_id",
            ),
            ColumnSpec(
                "user_id",
                "string",
                True,
                "Digital login identity linked to the alert, where applicable.",
                references="users.user_id",
            ),
            ColumnSpec(
                "session_id",
                "string",
                True,
                "Digital session linked to the alert, where applicable.",
                references="sessions.session_id",
            ),
            ColumnSpec(
                "payment_beneficiary_id",
                "string",
                True,
                "Payment beneficiary linked to the alert, where applicable.",
                references="payment_beneficiaries.payment_beneficiary_id",
            ),
            ColumnSpec(
                "institution_name",
                "string",
                False,
                "Fictional institution that owns the alert.",
            ),
            ColumnSpec("generated_at", "datetime64[ns]", False, "Alert generation timestamp."),
            ColumnSpec("alert_type", "string", False, "Alert typology or rule family."),
            ColumnSpec("alert_status", "string", False, "Generated, triaged, escalated, or closed."),
            ColumnSpec("severity", "string", False, "Low, medium, or high alert severity."),
            ColumnSpec("reason", "string", False, "Learner-readable alert reason."),
        ),
    ),
    CASES: TableSpec(
        name=CASES,
        purpose="Investigation cases opened from alerts in the alert lifecycle.",
        columns=(
            ColumnSpec("case_id", "string", False, "Stable synthetic case identifier."),
            ColumnSpec(
                "alert_id",
                "string",
                False,
                "Alert that opened the case.",
                references="alerts.alert_id",
            ),
            ColumnSpec(
                "suspicious_activity_id",
                "string",
                False,
                "Suspicious activity being investigated.",
                references="suspicious_activities.suspicious_activity_id",
            ),
            ColumnSpec(
                "banking_relationship_id",
                "string",
                False,
                "Banking relationship linked to the case.",
                references="banking_relationships.banking_relationship_id",
            ),
            ColumnSpec(
                "account_id",
                "string",
                False,
                "Account linked to the case.",
                references="accounts.account_id",
            ),
            ColumnSpec(
                "transaction_id",
                "string",
                False,
                "Primary transaction under investigation.",
                references="transactions.transaction_id",
            ),
            ColumnSpec(
                "user_id",
                "string",
                True,
                "Digital login identity linked to the case, where applicable.",
                references="users.user_id",
            ),
            ColumnSpec(
                "session_id",
                "string",
                True,
                "Digital session linked to the case, where applicable.",
                references="sessions.session_id",
            ),
            ColumnSpec(
                "payment_beneficiary_id",
                "string",
                True,
                "Payment beneficiary linked to the case, where applicable.",
                references="payment_beneficiaries.payment_beneficiary_id",
            ),
            ColumnSpec("opened_at", "datetime64[ns]", False, "Case opening timestamp."),
            ColumnSpec("assigned_team", "string", False, "Investigation team assignment."),
            ColumnSpec("case_status", "string", False, "Open, closed, or escalated case status."),
            ColumnSpec("investigation_summary", "string", False, "Brief synthetic investigation note."),
        ),
    ),
    CASE_OUTCOMES: TableSpec(
        name=CASE_OUTCOMES,
        purpose="Case decisions that separate confirmed fraud from other lifecycle states.",
        columns=(
            ColumnSpec("case_outcome_id", "string", False, "Stable synthetic case outcome identifier."),
            ColumnSpec(
                "case_id",
                "string",
                False,
                "Case that received the outcome.",
                references="cases.case_id",
            ),
            ColumnSpec("decided_at", "datetime64[ns]", False, "Outcome decision timestamp."),
            ColumnSpec("outcome_type", "string", False, "confirmed-fraud, false-positive, or unresolved."),
            ColumnSpec("confirmed_fraud", "bool", False, "Whether the case outcome confirmed fraud."),
            ColumnSpec("loss_amount_original", "Decimal", False, "Exact loss amount in original currency."),
            ColumnSpec("loss_currency", "string", False, "Currency for `loss_amount_original`."),
            ColumnSpec("loss_amount_chf", "Decimal", False, "Exact CHF-normalized loss amount."),
            ColumnSpec("notes", "string", False, "Learner-readable outcome note."),
        ),
    ),
    PROTECTED_SCENARIO_ANSWER_KEYS: TableSpec(
        name=PROTECTED_SCENARIO_ANSWER_KEYS,
        purpose=(
            "Protected placeholder table for future scenario labels that are excluded from "
            "normal learner-facing views."
        ),
        columns=(
            ColumnSpec("answer_key_id", "string", False, "Stable synthetic answer-key identifier."),
            ColumnSpec("scenario_name", "string", False, "Scenario that produced the protected label."),
            ColumnSpec("entity_table", "string", False, "Generated table containing the labeled entity."),
            ColumnSpec("entity_id", "string", False, "Identifier of the labeled entity."),
            ColumnSpec("label_type", "string", False, "Type of protected label."),
            ColumnSpec("label_value", "string", False, "Protected label value."),
            ColumnSpec(
                "available_to_learners",
                "bool",
                False,
                "Always false for protected answer keys.",
            ),
        ),
        allow_empty=True,
    ),
}

TABLE_NAMES = tuple(TABLE_SPECS)
PROTECTED_TABLE_NAMES = (PROTECTED_SCENARIO_ANSWER_KEYS,)
LEARNER_FACING_TABLE_NAMES = tuple(
    table_name for table_name in TABLE_NAMES if table_name not in PROTECTED_TABLE_NAMES
)
COLUMN_NAMES = {
    table_name: tuple(column.name for column in table_spec.columns)
    for table_name, table_spec in TABLE_SPECS.items()
}

__all__ = [
    "ACCOUNTS",
    "ALERTS",
    "BANKING_RELATIONSHIPS",
    "CASES",
    "CASE_OUTCOMES",
    "CLIENTS",
    "COLUMN_NAMES",
    "ColumnSpec",
    "LEARNER_FACING_TABLE_NAMES",
    "PARTNERS",
    "PARTNER_ROLES",
    "PAYMENT_BENEFICIARIES",
    "PROTECTED_SCENARIO_ANSWER_KEYS",
    "PROTECTED_TABLE_NAMES",
    "ROLES",
    "SESSIONS",
    "SUSPICIOUS_ACTIVITIES",
    "TABLE_NAMES",
    "TABLE_SPECS",
    "TRANSACTIONS",
    "TableSpec",
    "USERS",
]
