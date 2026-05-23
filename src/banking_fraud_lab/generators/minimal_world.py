"""Generate the deterministic minimal banking world used by v0.1 samples."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import numpy as np
import pandas as pd
from faker import Faker

from banking_fraud_lab.schema.tables import (
    ACCOUNTS,
    ALERTS,
    BANKING_RELATIONSHIPS,
    CASE_OUTCOMES,
    CASES,
    CLIENTS,
    COLUMN_NAMES,
    PARTNERS,
    PARTNER_ROLES,
    PAYMENT_BENEFICIARIES,
    PROTECTED_SCENARIO_ANSWER_KEYS,
    ROLES,
    SESSIONS,
    TABLE_NAMES,
    TRANSACTIONS,
    USERS,
)

ALPINE_CREST = "Alpine Crest Private Bank"
NOVABANK = "NovaBank Digital"
BASE_TIMESTAMP = pd.Timestamp("2026-01-15 09:00:00")
CHF_RATES = {
    "CHF": Decimal("1.00"),
    "EUR": Decimal("0.96"),
    "GBP": Decimal("1.12"),
    "USD": Decimal("0.91"),
}
MONEY_QUANT = Decimal("0.01")


def generate_minimal_banking_world(
    seed: int = 42, output_dir: Path | None = None
) -> dict[str, pd.DataFrame]:
    """Generate a tiny deterministic banking dataset and optionally write CSV files."""

    fake = Faker("en_US")
    fake.seed_instance(seed)
    rng = np.random.default_rng(seed)

    partners = _generate_partners(fake, rng)
    clients = _generate_clients(rng, partners)
    roles = _generate_roles()
    banking_relationships = _generate_banking_relationships(fake, rng, clients)
    partner_roles = _generate_partner_roles(clients, roles, banking_relationships, partners)
    accounts = _generate_accounts(rng, banking_relationships)
    users = _generate_users(rng, clients)
    sessions = _generate_sessions(rng, users)
    payment_beneficiaries = _generate_payment_beneficiaries(fake, rng, clients, users)
    transactions = _generate_transactions(rng, accounts, banking_relationships, payment_beneficiaries)
    alerts = _generate_alerts(transactions)
    cases = _generate_cases(alerts)
    case_outcomes = _generate_case_outcomes(cases, transactions, alerts)
    protected_answer_keys = _empty_frame(PROTECTED_SCENARIO_ANSWER_KEYS)

    tables = {
        PARTNERS: partners,
        CLIENTS: clients,
        ROLES: roles,
        PARTNER_ROLES: partner_roles,
        BANKING_RELATIONSHIPS: banking_relationships,
        ACCOUNTS: accounts,
        TRANSACTIONS: transactions,
        USERS: users,
        SESSIONS: sessions,
        PAYMENT_BENEFICIARIES: payment_beneficiaries,
        ALERTS: alerts,
        CASES: cases,
        CASE_OUTCOMES: case_outcomes,
        PROTECTED_SCENARIO_ANSWER_KEYS: protected_answer_keys,
    }
    ordered_tables = {table_name: tables[table_name] for table_name in TABLE_NAMES}

    if output_dir is not None:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        for table_name, frame in ordered_tables.items():
            frame.to_csv(output_path / f"{table_name}.csv", index=False, encoding="utf-8")

    return ordered_tables


def _generate_partners(fake: Faker, rng: np.random.Generator) -> pd.DataFrame:
    """Create partner records spanning both institutions with randomised attributes."""
    countries = ("CH", "DE", "FR", "IT", "GB", "US")
    rows = []
    for index in range(1, 9):
        partner_type = "legal_entity" if index in {3, 7} else "natural_person"
        institution_name = ALPINE_CREST if index <= 4 else NOVABANK
        rows.append(
            {
                "partner_id": _identifier("P", index),
                "institution_name": institution_name,
                "partner_type": partner_type,
                "display_name": fake.company() if partner_type == "legal_entity" else fake.name(),
                "country": rng.choice(countries),
                "created_at": _timestamp(days=-365 - index * 12, hours=index),
                "risk_rating": rng.choice(("low", "medium", "high"), p=(0.5, 0.35, 0.15)),
            }
        )
    return _frame(PARTNERS, rows)


def _generate_clients(rng: np.random.Generator, partners: pd.DataFrame) -> pd.DataFrame:
    """Derive client records from the first six partners with institution-matched segments."""
    segments = {
        ALPINE_CREST: ("private_banking_individual", "family_office", "operating_company"),
        NOVABANK: ("digital_retail", "digital_sme", "digital_premium"),
    }
    rows = []
    for index, partner in enumerate(partners.iloc[:6].itertuples(index=False), start=1):
        institution_name = partner.institution_name
        rows.append(
            {
                "client_id": _identifier("C", index),
                "partner_id": partner.partner_id,
                "institution_name": institution_name,
                "client_segment": rng.choice(segments[institution_name]),
                "onboarded_at": pd.Timestamp(partner.created_at) + pd.Timedelta(days=10),
                "status": "active",
            }
        )
    return _frame(CLIENTS, rows)


def _generate_roles() -> pd.DataFrame:
    """Return the static role catalog used across banking relationships."""
    rows = [
        {
            "role_id": "ROLE-001",
            "role_code": "primary_client",
            "role_name": "Primary Client",
            "description": "Legal client that owns the banking relationship.",
        },
        {
            "role_id": "ROLE-002",
            "role_code": "beneficial_owner",
            "role_name": "Beneficial Owner",
            "description": "Partner treated as a beneficial owner in relationship context.",
        },
        {
            "role_id": "ROLE-003",
            "role_code": "authorized_signatory",
            "role_name": "Authorized Signatory",
            "description": "Partner authorized to act on a banking relationship.",
        },
        {
            "role_id": "ROLE-004",
            "role_code": "digital_login_user",
            "role_name": "Digital Login User",
            "description": "Partner associated with digital login activity.",
        },
    ]
    return _frame(ROLES, rows)


def _generate_banking_relationships(
    fake: Faker, rng: np.random.Generator, clients: pd.DataFrame
) -> pd.DataFrame:
    """Open one banking relationship per client with a named RM code."""
    rows = []
    for index, client in enumerate(clients.itertuples(index=False), start=1):
        relationship_prefix = "PB" if client.institution_name == ALPINE_CREST else "DB"
        rows.append(
            {
                "banking_relationship_id": _identifier("BR", index),
                "primary_client_id": client.client_id,
                "institution_name": client.institution_name,
                "relationship_name": f"{relationship_prefix} {fake.last_name()} Relationship",
                "opened_at": pd.Timestamp(client.onboarded_at) + pd.Timedelta(days=3),
                "status": "active",
                "relationship_manager_code": f"RM-{int(rng.integers(101, 1000))}",
            }
        )
    return _frame(BANKING_RELATIONSHIPS, rows)


def _generate_partner_roles(
    clients: pd.DataFrame, roles: pd.DataFrame, relationships: pd.DataFrame, partners: pd.DataFrame
) -> pd.DataFrame:
    """Assign primary-client and supporting partner roles per relationship.

    Each relationship gets a primary_client role for the owning partner and a
    supporting role (beneficial_owner or authorized_signatory) for another
    partner from the same institution.
    """
    role_by_code = dict(zip(roles["role_code"], roles["role_id"], strict=True))
    client_by_id = clients.set_index("client_id")
    partners_by_institution = {
        institution_name: tuple(institution_partners["partner_id"])
        for institution_name, institution_partners in partners.groupby("institution_name")
    }
    rows = []
    for index, relationship in enumerate(relationships.itertuples(index=False), start=1):
        primary_client = client_by_id.loc[relationship.primary_client_id]
        primary_partner_id = str(primary_client["partner_id"])
        effective_from = pd.Timestamp(relationship.opened_at)
        rows.append(
            {
                "partner_role_id": _identifier("PR", len(rows) + 1),
                "partner_id": primary_partner_id,
                "role_id": role_by_code["primary_client"],
                "banking_relationship_id": relationship.banking_relationship_id,
                "effective_from": effective_from,
                "effective_to": pd.NaT,
            }
        )
        same_institution_partners = tuple(
            partner_id
            for partner_id in partners_by_institution[str(relationship.institution_name)]
            if partner_id != primary_partner_id
        )
        supporting_partner = same_institution_partners[(index - 1) % len(same_institution_partners)]
        role_code = "beneficial_owner" if index % 2 else "authorized_signatory"
        rows.append(
            {
                "partner_role_id": _identifier("PR", len(rows) + 1),
                "partner_id": supporting_partner,
                "role_id": role_by_code[role_code],
                "banking_relationship_id": relationship.banking_relationship_id,
                "effective_from": effective_from + pd.Timedelta(days=1),
                "effective_to": pd.NaT,
            }
        )
    return _frame(PARTNER_ROLES, rows)


def _generate_accounts(rng: np.random.Generator, relationships: pd.DataFrame) -> pd.DataFrame:
    """Open current and optional custody/savings accounts under each relationship."""
    rows = []
    for index, relationship in enumerate(relationships.itertuples(index=False), start=1):
        account_count = 2 if index in {1, 4} else 1
        for account_number in range(account_count):
            currency = str(rng.choice(("CHF", "EUR", "USD", "GBP")))
            balance = _money(int(rng.integers(25_000, 850_000)))
            rows.append(
                {
                    "account_id": _identifier("A", len(rows) + 1),
                    "banking_relationship_id": relationship.banking_relationship_id,
                    "institution_name": relationship.institution_name,
                    "account_type": _account_type(relationship.institution_name, account_number),
                    "currency": currency,
                    "opened_at": pd.Timestamp(relationship.opened_at) + pd.Timedelta(days=account_number),
                    "status": "active",
                    "balance_original": balance,
                    "balance_currency": currency,
                    "balance_chf": _to_chf(balance, currency),
                }
            )
    return _frame(ACCOUNTS, rows)


def _generate_users(rng: np.random.Generator, clients: pd.DataFrame) -> pd.DataFrame:
    """Create digital user identities for the last four clients (those eligible)."""
    rows = []
    for index, client in enumerate(clients.iloc[2:].itertuples(index=False), start=1):
        rows.append(
            {
                "user_id": _identifier("U", index),
                "client_id": client.client_id,
                "institution_name": client.institution_name,
                "username_hash": f"usr_{int(rng.integers(10**11, 10**12)):x}",
                "created_at": pd.Timestamp(client.onboarded_at) + pd.Timedelta(days=14),
                "status": "active",
            }
        )
    return _frame(USERS, rows)


def _generate_sessions(rng: np.random.Generator, users: pd.DataFrame) -> pd.DataFrame:
    """Generate login and activity sessions for digital users."""
    rows = []
    events = ("login", "view_accounts", "add_beneficiary", "payment_authorized")
    for index in range(1, 8):
        user = users.iloc[(index - 1) % len(users)]
        rows.append(
            {
                "session_id": _identifier("S", index),
                "user_id": user["user_id"],
                "started_at": pd.Timestamp(user["created_at"]) + pd.Timedelta(days=index, hours=index),
                "channel": rng.choice(("web", "mobile_app")),
                "device_fingerprint_hash": f"dev_{int(rng.integers(10**10, 10**11)):x}",
                "ip_country": rng.choice(("CH", "DE", "FR", "GB", "NL")),
                "asn_risk_score": int(rng.integers(3, 86)),
                "is_vpn_or_proxy": rng.choice((False, False, False, True)),
                "auth_method": rng.choice(("password_sms", "passkey", "push_mfa")),
                "session_event": events[(index - 1) % len(events)],
            }
        )
    return _frame(SESSIONS, rows)


def _generate_payment_beneficiaries(
    fake: Faker, rng: np.random.Generator, clients: pd.DataFrame, users: pd.DataFrame
) -> pd.DataFrame:
    """Add one saved beneficiary per client that has a digital user identity."""
    rows = []
    users_by_client = users.set_index("client_id")
    eligible_clients = clients[clients["client_id"].isin(users_by_client.index)]
    for index, client in enumerate(eligible_clients.itertuples(index=False), start=1):
        user = users_by_client.loc[client.client_id]
        rows.append(
            {
                "payment_beneficiary_id": _identifier("B", index),
                "client_id": client.client_id,
                "added_by_user_id": user["user_id"],
                "beneficiary_name": fake.company(),
                "beneficiary_account_country": str(rng.choice(("CH", "DE", "FR", "IT", "GB"))),
                "beneficiary_bank_country": str(rng.choice(("CH", "DE", "FR", "IT", "GB"))),
                "created_at": pd.Timestamp(user["created_at"]) + pd.Timedelta(days=index),
                "status": "active",
            }
        )
    return _frame(PAYMENT_BENEFICIARIES, rows)


def _generate_transactions(
    rng: np.random.Generator,
    accounts: pd.DataFrame,
    relationships: pd.DataFrame,
    beneficiaries: pd.DataFrame,
) -> pd.DataFrame:
    """Book transactions across accounts with optional beneficiary references for digital payments."""
    relationship_clients = relationships.set_index("banking_relationship_id")["primary_client_id"]
    beneficiary_ids_by_client = {
        client_id: tuple(client_beneficiaries["payment_beneficiary_id"])
        for client_id, client_beneficiaries in beneficiaries.groupby("client_id")
    }
    rows = []
    for index in range(1, 13):
        account = accounts.iloc[(index - 1) % len(accounts)]
        client_id = str(relationship_clients.loc[account["banking_relationship_id"]])
        is_digital_payment = account["institution_name"] == NOVABANK and index % 2 == 0
        beneficiary_ids = beneficiary_ids_by_client.get(client_id, ())
        beneficiary_id = (
            beneficiary_ids[index % len(beneficiary_ids)]
            if is_digital_payment and beneficiary_ids
            else None
        )
        currency = str(account["currency"])
        amount = _money(int(rng.integers(75, 65_000)))
        rows.append(
            {
                "transaction_id": _identifier("T", index),
                "account_id": account["account_id"],
                "payment_beneficiary_id": beneficiary_id,
                "booked_at": BASE_TIMESTAMP + pd.Timedelta(days=index, hours=index % 5),
                "transaction_type": _transaction_type(account["institution_name"], is_digital_payment),
                "channel": _channel(account["institution_name"], is_digital_payment),
                "direction": "debit" if index % 3 else "credit",
                "amount_original": amount,
                "currency": currency,
                "amount_chf": _to_chf(amount, currency),
                "description": _transaction_description(account["institution_name"], is_digital_payment),
            }
        )
    return _frame(TRANSACTIONS, rows)


def _generate_alerts(transactions: pd.DataFrame) -> pd.DataFrame:
    """Create sample fraud alerts triggered by specific transactions.

    Raises ValueError if a hard-coded trigger transaction is missing.
    """
    alert_specs = (
        ("T-0003", ALPINE_CREST, "private_banking_high_value", "triaged", "medium"),
        ("T-0008", NOVABANK, "new_beneficiary_payment", "escalated", "high"),
        ("T-0007", NOVABANK, "session_payment_velocity", "closed", "low"),
    )
    transaction_ids = set(transactions["transaction_id"])
    rows = []
    for index, (transaction_id, institution, alert_type, status, severity) in enumerate(
        alert_specs, start=1
    ):
        if transaction_id not in transaction_ids:
            raise ValueError(f"Alert trigger {transaction_id} is not present in transactions")
        rows.append(
            {
                "alert_id": _identifier("AL", index),
                "triggered_transaction_id": transaction_id,
                "institution_name": institution,
                "generated_at": BASE_TIMESTAMP + pd.Timedelta(days=20 + index),
                "alert_type": alert_type,
                "alert_status": status,
                "severity": severity,
                "reason": _alert_reason(alert_type),
            }
        )
    return _frame(ALERTS, rows)


def _generate_cases(alerts: pd.DataFrame) -> pd.DataFrame:
    """Open investigation cases for escalated and closed alerts."""
    rows = []
    case_alerts = alerts[alerts["alert_status"].isin(("escalated", "closed"))]
    for index, alert in enumerate(case_alerts.itertuples(index=False), start=1):
        rows.append(
            {
                "case_id": _identifier("CASE", index),
                "alert_id": alert.alert_id,
                "opened_at": pd.Timestamp(alert.generated_at) + pd.Timedelta(hours=6),
                "assigned_team": "digital investigations"
                if alert.institution_name == NOVABANK
                else "private banking investigations",
                "case_status": "closed" if alert.alert_status == "closed" else "open",
                "investigation_summary": "Minimal lifecycle example for learner inspection.",
            }
        )
    return _frame(CASES, rows)


def _generate_case_outcomes(
    cases: pd.DataFrame, transactions: pd.DataFrame, alerts: pd.DataFrame
) -> pd.DataFrame:
    """Record false-positive or unresolved outcomes for each case with zero loss amounts."""
    transaction_currencies = transactions.set_index("transaction_id")["currency"]
    alert_triggers = alerts.set_index("alert_id")["triggered_transaction_id"]
    rows = []
    for index, case in enumerate(cases.itertuples(index=False), start=1):
        transaction_id = alert_triggers.loc[case.alert_id]
        currency = str(transaction_currencies.loc[transaction_id])
        is_closed = case.case_status == "closed"
        rows.append(
            {
                "case_outcome_id": _identifier("OUT", index),
                "case_id": case.case_id,
                "decided_at": pd.Timestamp(case.opened_at) + pd.Timedelta(days=2),
                "outcome_type": "false_positive" if is_closed else "unresolved",
                "confirmed_fraud": False,
                "loss_amount_original": Decimal("0.00"),
                "loss_currency": currency,
                "loss_amount_chf": Decimal("0.00"),
                "notes": "No protected scenario label is exposed in this tracer bullet.",
            }
        )
    return _frame(CASE_OUTCOMES, rows)


def _frame(table_name: str, rows: list[dict[str, object]]) -> pd.DataFrame:
    """Build a DataFrame with column order enforced by the schema contract."""
    return pd.DataFrame(rows, columns=COLUMN_NAMES[table_name])


def _empty_frame(table_name: str) -> pd.DataFrame:
    """Create a header-only DataFrame for placeholder tables."""
    return pd.DataFrame(columns=COLUMN_NAMES[table_name])


def _identifier(prefix: str, index: int) -> str:
    """Format a zero-padded entity identifier like ``P-0001``."""
    return f"{prefix}-{index:04d}"


def _timestamp(days: int, hours: int = 0) -> pd.Timestamp:
    """Return a timestamp offset from the generation baseline."""
    return BASE_TIMESTAMP + pd.Timedelta(days=days, hours=hours)


def _money(whole_units: int) -> Decimal:
    """Convert an integer amount to a Decimal quantised to two decimal places."""
    return Decimal(whole_units).quantize(MONEY_QUANT)


def _to_chf(amount: Decimal, currency: str) -> Decimal:
    """Convert a monetary amount to CHF using fixed v0.1 exchange rates.

    Raises ValueError for unknown currency codes.
    """
    if currency not in CHF_RATES:
        raise ValueError(f"Unknown currency: {currency}")
    return (amount * CHF_RATES[currency]).quantize(MONEY_QUANT)


def _account_type(institution_name: str, account_number: int) -> str:
    """Select account type based on institution and whether it is the secondary account."""
    if institution_name == ALPINE_CREST:
        return "custody" if account_number else "private_current"
    return "digital_savings" if account_number else "digital_current"


def _transaction_type(institution_name: str, is_digital_payment: bool) -> str:
    """Choose wire_transfer, card_payment, or instant_payment based on context."""
    if is_digital_payment:
        return "instant_payment"
    if institution_name == ALPINE_CREST:
        return "wire_transfer"
    return "card_payment"


def _channel(institution_name: str, is_digital_payment: bool) -> str:
    """Pick relationship_manager, web, or mobile_app based on payment context."""
    if is_digital_payment:
        return "mobile_app"
    if institution_name == ALPINE_CREST:
        return "relationship_manager"
    return "web"


def _transaction_description(institution_name: str, is_digital_payment: bool) -> str:
    """Return a human-readable transaction description based on context."""
    if is_digital_payment:
        return "Outbound payment to saved beneficiary"
    if institution_name == ALPINE_CREST:
        return "Private banking account movement"
    return "Digital banking account activity"


def _alert_reason(alert_type: str) -> str:
    """Look up a canned alert reason string for the given alert type."""
    reasons = {
        "private_banking_high_value": "High-value movement relative to sample relationship profile.",
        "new_beneficiary_payment": "Payment followed recent beneficiary setup.",
        "session_payment_velocity": "Multiple session and payment events observed close together.",
    }
    return reasons[alert_type]
