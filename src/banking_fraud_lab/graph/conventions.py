"""Frozen node-type and edge-type conventions for the NetworkX graph layer."""

from __future__ import annotations

from dataclasses import dataclass

from banking_fraud_lab.schema import (
    ACCOUNTS,
    ALERTS,
    BANKING_RELATIONSHIPS,
    CASES,
    CLIENTS,
    PAYMENT_BENEFICIARIES,
    PARTNERS,
    PARTNER_ROLES,
    SESSIONS,
    TRANSACTIONS,
    USERS,
)

# Virtual source label for the Detection pattern node vocabulary. The Detection
# pattern vocabulary is defined in the schema package rather than generated as a
# table; this constant is documented on the spec so downstream code treats it as
# a non-generated source.
DETECTION_PATTERNS = "detection_patterns"

# Stable node-type identifiers (the values used as node ``node_type`` tags).
PARTNER = "partner"
CLIENT = "client"
USER = "user"
BANKING_RELATIONSHIP = "banking_relationship"
ACCOUNT = "account"
BENEFICIARY = "beneficiary"
DEVICE = "device"
SESSION = "session"
TRANSACTION = "transaction"
ALERT = "alert"
CASE = "case"
DETECTION_PATTERN = "detection_pattern"

# Stable edge-category identifiers (the nine PRD-listed edge relationships).
OWNERSHIP = "ownership"
AUTHORIZATION = "authorization"
LOGIN_SESSION = "login_session"
PAYMENT = "payment"
COUNTERPARTY = "counterparty"
SHARED_DEVICE = "shared_device"
ALERT_RELATION = "alert"
CASE_RELATION = "case"
SCENARIO = "scenario"


@dataclass(frozen=True)
class NodeSpec:
    """Stable contract for one graph node type."""

    node_type: str
    display_name: str
    description: str
    source_table: str
    key_column: str


@dataclass(frozen=True)
class EdgeSpec:
    """Stable contract for one typed directed graph edge."""

    edge_type: str
    category: str
    display_name: str
    description: str
    source_table: str
    source_node_type: str
    target_node_type: str
    source_key_column: str
    target_key_column: str


# --- Node-type catalog -----------------------------------------------------

PARTNER_NODE = NodeSpec(
    node_type=PARTNER,
    display_name="Partner",
    description=(
        "Natural or legal person represented in the fictional bank core model, "
        "keyed by the partner identifier."
    ),
    source_table=PARTNERS,
    key_column="partner_id",
)

CLIENT_NODE = NodeSpec(
    node_type=CLIENT,
    display_name="Client",
    description="The bank's legal customer, keyed by the client identifier.",
    source_table=CLIENTS,
    key_column="client_id",
)

USER_NODE = NodeSpec(
    node_type=USER,
    display_name="User",
    description=(
        "The digital login identity that authenticates sessions and acts through "
        "e-banking or app channels, keyed by the user identifier."
    ),
    source_table=USERS,
    key_column="user_id",
)

BANKING_RELATIONSHIP_NODE = NodeSpec(
    node_type=BANKING_RELATIONSHIP,
    display_name="Banking relationship",
    description=(
        "The Swiss-bank-style container grouping related Partners, Clients, "
        "accounts, and service arrangements, keyed by the banking relationship "
        "identifier."
    ),
    source_table=BANKING_RELATIONSHIPS,
    key_column="banking_relationship_id",
)

ACCOUNT_NODE = NodeSpec(
    node_type=ACCOUNT,
    display_name="account",
    description="Deposit, custody, or payment account, keyed by the account identifier.",
    source_table=ACCOUNTS,
    key_column="account_id",
)

BENEFICIARY_NODE = NodeSpec(
    node_type=BENEFICIARY,
    display_name="beneficiary",
    description=(
        "Saved payment beneficiary or private-banking counterparty, keyed by the "
        "payment beneficiary identifier."
    ),
    source_table=PAYMENT_BENEFICIARIES,
    key_column="payment_beneficiary_id",
)

DEVICE_NODE = NodeSpec(
    node_type=DEVICE,
    display_name="device",
    description=(
        "Digital device observed through session telemetry. Devices have no "
        "dedicated table; each distinct ``device_fingerprint_hash`` value in the "
        "sessions table becomes one device node."
    ),
    source_table=SESSIONS,
    key_column="device_fingerprint_hash",
)

SESSION_NODE = NodeSpec(
    node_type=SESSION,
    display_name="session",
    description="A digital session, keyed by the session identifier.",
    source_table=SESSIONS,
    key_column="session_id",
)

TRANSACTION_NODE = NodeSpec(
    node_type=TRANSACTION,
    display_name="transaction",
    description="Money movement event, keyed by the transaction identifier.",
    source_table=TRANSACTIONS,
    key_column="transaction_id",
)

ALERT_NODE = NodeSpec(
    node_type=ALERT,
    display_name="alert",
    description="Alert generated from a suspicious activity, keyed by the alert identifier.",
    source_table=ALERTS,
    key_column="alert_id",
)

CASE_NODE = NodeSpec(
    node_type=CASE,
    display_name="case",
    description="Investigation case opened from an alert, keyed by the case identifier.",
    source_table=CASES,
    key_column="case_id",
)

DETECTION_PATTERN_NODE = NodeSpec(
    node_type=DETECTION_PATTERN,
    display_name="Detection pattern",
    description=(
        "Recurring observable signal that can be translated into analytics or "
        "model features, keyed by the pattern identifier. Detection pattern nodes "
        "derive from the frozen schema vocabulary rather than a generated table."
    ),
    source_table=DETECTION_PATTERNS,
    key_column="pattern_id",
)

NODE_SPECS: tuple[NodeSpec, ...] = (
    PARTNER_NODE,
    CLIENT_NODE,
    USER_NODE,
    BANKING_RELATIONSHIP_NODE,
    ACCOUNT_NODE,
    BENEFICIARY_NODE,
    DEVICE_NODE,
    SESSION_NODE,
    TRANSACTION_NODE,
    ALERT_NODE,
    CASE_NODE,
    DETECTION_PATTERN_NODE,
)

NODE_TYPE_IDS: tuple[str, ...] = tuple(spec.node_type for spec in NODE_SPECS)


# --- Edge-type catalog -----------------------------------------------------

CLIENT_PARTNER = EdgeSpec(
    edge_type="client_partner",
    category=OWNERSHIP,
    display_name="Client to Partner ownership",
    description="A Client is represented by its underlying Partner.",
    source_table=CLIENTS,
    source_node_type=CLIENT,
    target_node_type=PARTNER,
    source_key_column="client_id",
    target_key_column="partner_id",
)

RELATIONSHIP_PRIMARY_CLIENT = EdgeSpec(
    edge_type="relationship_primary_client",
    category=OWNERSHIP,
    display_name="Banking relationship to primary Client",
    description="A Banking relationship is anchored by its primary Client.",
    source_table=BANKING_RELATIONSHIPS,
    source_node_type=BANKING_RELATIONSHIP,
    target_node_type=CLIENT,
    source_key_column="banking_relationship_id",
    target_key_column="primary_client_id",
)

ACCOUNT_RELATIONSHIP = EdgeSpec(
    edge_type="account_relationship",
    category=OWNERSHIP,
    display_name="account to Banking relationship",
    description="An account belongs to a Banking relationship.",
    source_table=ACCOUNTS,
    source_node_type=ACCOUNT,
    target_node_type=BANKING_RELATIONSHIP,
    source_key_column="account_id",
    target_key_column="banking_relationship_id",
)

USER_CLIENT = EdgeSpec(
    edge_type="user_client",
    category=AUTHORIZATION,
    display_name="User to Client authorization",
    description="A User is the digital login identity of a Client.",
    source_table=USERS,
    source_node_type=USER,
    target_node_type=CLIENT,
    source_key_column="user_id",
    target_key_column="client_id",
)

PARTNER_ROLE_PARTNER = EdgeSpec(
    edge_type="partner_role_partner",
    category=AUTHORIZATION,
    display_name="partner role to Partner",
    description="A partner role assigns a Partner into a Banking relationship.",
    source_table=PARTNER_ROLES,
    source_node_type=PARTNER,
    target_node_type=BANKING_RELATIONSHIP,
    source_key_column="partner_id",
    target_key_column="banking_relationship_id",
)

SESSION_USER = EdgeSpec(
    edge_type="session_user",
    category=LOGIN_SESSION,
    display_name="session to User",
    description="A session authenticates a User.",
    source_table=SESSIONS,
    source_node_type=SESSION,
    target_node_type=USER,
    source_key_column="session_id",
    target_key_column="user_id",
)

SESSION_DEVICE = EdgeSpec(
    edge_type="session_device",
    category=SHARED_DEVICE,
    display_name="session to device",
    description=(
        "A session was observed on a device. Shared-device signals arise when "
        "distinct sessions (and therefore Users) connect to the same device "
        "fingerprint."
    ),
    source_table=SESSIONS,
    source_node_type=SESSION,
    target_node_type=DEVICE,
    source_key_column="session_id",
    target_key_column="device_fingerprint_hash",
)

TRANSACTION_ACCOUNT = EdgeSpec(
    edge_type="transaction_account",
    category=PAYMENT,
    display_name="transaction to account",
    description="A transaction is booked against an account.",
    source_table=TRANSACTIONS,
    source_node_type=TRANSACTION,
    target_node_type=ACCOUNT,
    source_key_column="transaction_id",
    target_key_column="account_id",
)

TRANSACTION_BENEFICIARY = EdgeSpec(
    edge_type="transaction_beneficiary",
    category=PAYMENT,
    display_name="transaction to beneficiary",
    description="An outbound transaction is paid to a beneficiary when present.",
    source_table=TRANSACTIONS,
    source_node_type=TRANSACTION,
    target_node_type=BENEFICIARY,
    source_key_column="transaction_id",
    target_key_column="payment_beneficiary_id",
)

BENEFICIARY_CLIENT = EdgeSpec(
    edge_type="beneficiary_client",
    category=COUNTERPARTY,
    display_name="beneficiary to Client",
    description="A beneficiary is owned by a Client.",
    source_table=PAYMENT_BENEFICIARIES,
    source_node_type=BENEFICIARY,
    target_node_type=CLIENT,
    source_key_column="payment_beneficiary_id",
    target_key_column="client_id",
)

BENEFICIARY_ADDED_BY_USER = EdgeSpec(
    edge_type="beneficiary_added_by_user",
    category=COUNTERPARTY,
    display_name="beneficiary added by User",
    description="A beneficiary was added by a User.",
    source_table=PAYMENT_BENEFICIARIES,
    source_node_type=BENEFICIARY,
    target_node_type=USER,
    source_key_column="payment_beneficiary_id",
    target_key_column="added_by_user_id",
)

DEVICE_USER = EdgeSpec(
    edge_type="device_user",
    category=SHARED_DEVICE,
    display_name="device to User",
    description=(
        "A device was used by a User. Derived from session telemetry: each "
        "session's device fingerprint links the device node to the session's "
        "User; multiple Users on one device signal shared-device risk."
    ),
    source_table=SESSIONS,
    source_node_type=DEVICE,
    target_node_type=USER,
    source_key_column="device_fingerprint_hash",
    target_key_column="user_id",
)

ALERT_TRANSACTION = EdgeSpec(
    edge_type="alert_transaction",
    category=ALERT_RELATION,
    display_name="alert to transaction",
    description="An alert is triggered by a transaction.",
    source_table=ALERTS,
    source_node_type=ALERT,
    target_node_type=TRANSACTION,
    source_key_column="alert_id",
    target_key_column="triggered_transaction_id",
)

ALERT_RELATIONSHIP = EdgeSpec(
    edge_type="alert_relationship",
    category=ALERT_RELATION,
    display_name="alert to Banking relationship",
    description="An alert is linked to a Banking relationship.",
    source_table=ALERTS,
    source_node_type=ALERT,
    target_node_type=BANKING_RELATIONSHIP,
    source_key_column="alert_id",
    target_key_column="banking_relationship_id",
)

ALERT_ACCOUNT = EdgeSpec(
    edge_type="alert_account",
    category=ALERT_RELATION,
    display_name="alert to account",
    description="An alert is linked to an account.",
    source_table=ALERTS,
    source_node_type=ALERT,
    target_node_type=ACCOUNT,
    source_key_column="alert_id",
    target_key_column="account_id",
)

CASE_ALERT = EdgeSpec(
    edge_type="case_alert",
    category=CASE_RELATION,
    display_name="case to alert",
    description="A case is opened from an alert.",
    source_table=CASES,
    source_node_type=CASE,
    target_node_type=ALERT,
    source_key_column="case_id",
    target_key_column="alert_id",
)

CASE_TRANSACTION = EdgeSpec(
    edge_type="case_transaction",
    category=CASE_RELATION,
    display_name="case to transaction",
    description="A case investigates a primary transaction.",
    source_table=CASES,
    source_node_type=CASE,
    target_node_type=TRANSACTION,
    source_key_column="case_id",
    target_key_column="transaction_id",
)

CASE_RELATIONSHIP = EdgeSpec(
    edge_type="case_relationship",
    category=CASE_RELATION,
    display_name="case to Banking relationship",
    description="A case is linked to a Banking relationship.",
    source_table=CASES,
    source_node_type=CASE,
    target_node_type=BANKING_RELATIONSHIP,
    source_key_column="case_id",
    target_key_column="banking_relationship_id",
)

ALERT_PATTERN = EdgeSpec(
    edge_type="alert_pattern",
    category=SCENARIO,
    display_name="alert to Detection pattern",
    description=(
        "An alert's underlying suspicious activity maps to a Detection pattern. "
        "Derived from the alert's suspicious activity: the activity type is "
        "resolved via the alert's suspicious_activity_id and mapped to a pattern "
        "through the activity-type vocabulary."
    ),
    source_table=ALERTS,
    source_node_type=ALERT,
    target_node_type=DETECTION_PATTERN,
    source_key_column="alert_id",
    target_key_column="pattern_id",
)

EDGE_SPECS: tuple[EdgeSpec, ...] = (
    CLIENT_PARTNER,
    RELATIONSHIP_PRIMARY_CLIENT,
    ACCOUNT_RELATIONSHIP,
    USER_CLIENT,
    PARTNER_ROLE_PARTNER,
    SESSION_USER,
    TRANSACTION_ACCOUNT,
    TRANSACTION_BENEFICIARY,
    BENEFICIARY_CLIENT,
    BENEFICIARY_ADDED_BY_USER,
    DEVICE_USER,
    SESSION_DEVICE,
    ALERT_TRANSACTION,
    ALERT_RELATIONSHIP,
    ALERT_ACCOUNT,
    CASE_ALERT,
    CASE_TRANSACTION,
    CASE_RELATIONSHIP,
    ALERT_PATTERN,
)

EDGE_TYPE_IDS: tuple[str, ...] = tuple(spec.edge_type for spec in EDGE_SPECS)

EDGE_CATEGORY_IDS: tuple[str, ...] = tuple(
    category
    for category in (
        OWNERSHIP,
        AUTHORIZATION,
        LOGIN_SESSION,
        PAYMENT,
        COUNTERPARTY,
        SHARED_DEVICE,
        ALERT_RELATION,
        CASE_RELATION,
        SCENARIO,
    )
)

# --- Module-load integrity guard -------------------------------------------
# Every edge spec must reference node types that exist in the node catalog and
# belong to a known edge category. This mirrors the pattern-id guard used by the
# feature-family specs and fails fast at import time if the vocabulary drifts.

_UNKNOWN_NODE_TYPES = sorted(
    {
        node_type
        for spec in EDGE_SPECS
        for node_type in (spec.source_node_type, spec.target_node_type)
    }
    - set(NODE_TYPE_IDS)
)
if _UNKNOWN_NODE_TYPES:
    raise ValueError(
        f"Edge specs reference unknown node types: {_UNKNOWN_NODE_TYPES}"
    )

_UNKNOWN_EDGE_CATEGORIES = sorted({spec.category for spec in EDGE_SPECS} - set(EDGE_CATEGORY_IDS))
if _UNKNOWN_EDGE_CATEGORIES:
    raise ValueError(
        f"Edge specs reference unknown edge categories: {_UNKNOWN_EDGE_CATEGORIES}"
    )


__all__ = [
    "ACCOUNT",
    "ACCOUNT_NODE",
    "ACCOUNT_RELATIONSHIP",
    "ALERT",
    "ALERT_ACCOUNT",
    "ALERT_NODE",
    "ALERT_PATTERN",
    "ALERT_RELATION",
    "AUTHORIZATION",
    "BANKING_RELATIONSHIP",
    "BANKING_RELATIONSHIP_NODE",
    "BENEFICIARY",
    "BENEFICIARY_ADDED_BY_USER",
    "BENEFICIARY_CLIENT",
    "BENEFICIARY_NODE",
    "CASE",
    "CASE_ALERT",
    "CASE_NODE",
    "CASE_RELATION",
    "CASE_RELATIONSHIP",
    "CASE_TRANSACTION",
    "CLIENT",
    "CLIENT_NODE",
    "CLIENT_PARTNER",
    "COUNTERPARTY",
    "DETECTION_PATTERN",
    "DETECTION_PATTERN_NODE",
    "DETECTION_PATTERNS",
    "DEVICE",
    "DEVICE_NODE",
    "DEVICE_USER",
    "EdgeSpec",
    "EDGE_CATEGORY_IDS",
    "EDGE_SPECS",
    "EDGE_TYPE_IDS",
    "LOGIN_SESSION",
    "NodeSpec",
    "NODE_SPECS",
    "NODE_TYPE_IDS",
    "OWNERSHIP",
    "PARTNER",
    "PARTNER_NODE",
    "PARTNER_ROLE_PARTNER",
    "PAYMENT",
    "RELATIONSHIP_PRIMARY_CLIENT",
    "SCENARIO",
    "SESSION",
    "SESSION_USER",
    "SESSION_DEVICE",
    "SESSION_NODE",
    "SHARED_DEVICE",
    "TRANSACTION",
    "TRANSACTION_ACCOUNT",
    "TRANSACTION_BENEFICIARY",
    "TRANSACTION_NODE",
    "USER",
    "USER_CLIENT",
    "USER_NODE",
]
