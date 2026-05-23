"""Generate the deterministic minimal banking world used by v0.1 samples."""

from __future__ import annotations

from collections.abc import Mapping
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
    LEARNER_FACING_TABLE_NAMES,
    PARTNERS,
    PARTNER_ROLES,
    PAYMENT_BENEFICIARIES,
    PROTECTED_SCENARIO_ANSWER_KEYS,
    ROLES,
    SESSIONS,
    SUSPICIOUS_ACTIVITIES,
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
ActivitySpec = tuple[str, str, str, str, str | None]
DEFAULT_SUSPICIOUS_ACTIVITY_SPECS: tuple[ActivitySpec, ...] = (
    (
        "T-0003",
        "private_banking_high_value",
        "High-value movement relative to sample relationship profile.",
        "medium",
        None,
    ),
    (
        "T-0008",
        "new_beneficiary_payment",
        "Payment followed recent beneficiary setup.",
        "high",
        "payment_authorized",
    ),
    (
        "T-0007",
        "session_payment_velocity",
        "Multiple session and payment events observed close together.",
        "medium",
        "add_beneficiary",
    ),
)


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
    suspicious_activities = _generate_suspicious_activities(
        transactions,
        accounts,
        banking_relationships,
        users,
        sessions,
    )
    alerts = _generate_alerts(suspicious_activities)
    cases = _generate_cases(alerts)
    case_outcomes = _generate_case_outcomes(cases, transactions, alerts)
    protected_answer_keys = _generate_protected_scenario_answer_keys(
        suspicious_activities,
        case_outcomes,
    )

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
        SUSPICIOUS_ACTIVITIES: suspicious_activities,
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


def generate_learner_facing_minimal_banking_world(
    seed: int = 42, output_dir: Path | None = None
) -> dict[str, pd.DataFrame]:
    """Generate default learner-facing tables without protected scenario answer keys."""
    tables = generate_minimal_banking_world(seed=seed)
    learner_tables = build_learner_facing_views(tables)

    if output_dir is not None:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        for table_name, frame in learner_tables.items():
            frame.to_csv(output_path / f"{table_name}.csv", index=False, encoding="utf-8")

    return learner_tables


def build_learner_facing_views(
    tables: Mapping[str, pd.DataFrame],
) -> dict[str, pd.DataFrame]:
    """Return the generated tables intended for learners by default."""
    return {table_name: tables[table_name].copy() for table_name in LEARNER_FACING_TABLE_NAMES}


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


def _generate_suspicious_activities(
    transactions: pd.DataFrame,
    accounts: pd.DataFrame,
    relationships: pd.DataFrame,
    users: pd.DataFrame,
    sessions: pd.DataFrame,
    activity_specs: tuple[ActivitySpec, ...] = DEFAULT_SUSPICIOUS_ACTIVITY_SPECS,
) -> pd.DataFrame:
    """Create suspicious activity observations before alert generation."""
    transactions_by_id = transactions.set_index("transaction_id")
    account_context = accounts.set_index("account_id")[
        ["banking_relationship_id", "institution_name"]
    ]
    client_by_relationship = relationships.set_index("banking_relationship_id")[
        "primary_client_id"
    ]
    user_by_client = users.set_index("client_id")["user_id"]

    rows = []
    for index, (transaction_id, activity_type, signal, priority, session_event) in enumerate(
        activity_specs,
        start=1,
    ):
        if transaction_id not in transactions_by_id.index:
            raise ValueError(f"Suspicious activity trigger {transaction_id} is not present")
        transaction = transactions_by_id.loc[transaction_id]
        account = account_context.loc[transaction["account_id"]]
        banking_relationship_id = str(account["banking_relationship_id"])
        client_id = str(client_by_relationship.loc[banking_relationship_id])
        user_id = user_by_client.get(client_id)
        if user_id is not None and account["institution_name"] != NOVABANK:
            user_id = None
        session_id = _session_id_for_user(sessions, user_id, session_event)
        beneficiary_id = transaction["payment_beneficiary_id"]
        if pd.isna(beneficiary_id):
            beneficiary_id = None

        rows.append(
            {
                "suspicious_activity_id": _identifier("SA", index),
                "institution_name": str(account["institution_name"]),
                "banking_relationship_id": banking_relationship_id,
                "account_id": str(transaction["account_id"]),
                "transaction_id": transaction_id,
                "user_id": user_id,
                "session_id": session_id,
                "payment_beneficiary_id": beneficiary_id,
                "activity_type": activity_type,
                "detected_at": pd.Timestamp(transaction["booked_at"]) + pd.Timedelta(minutes=15),
                "detection_signal": signal,
                "suspected_amount_chf": transaction["amount_chf"],
                "review_priority": priority,
            }
        )
    return _frame(SUSPICIOUS_ACTIVITIES, rows)


def _generate_alerts(suspicious_activities: pd.DataFrame) -> pd.DataFrame:
    """Create sample fraud alerts generated from suspicious activities."""
    status_by_activity_type = {
        "private_banking_high_value": "triaged",
        "new_beneficiary_payment": "closed",
        "session_payment_velocity": "closed",
    }
    severity_by_activity_type = {
        "private_banking_high_value": "medium",
        "new_beneficiary_payment": "high",
        "session_payment_velocity": "medium",
    }
    rows = []
    for index, activity in enumerate(suspicious_activities.itertuples(index=False), start=1):
        rows.append(
            {
                "alert_id": _identifier("AL", index),
                "suspicious_activity_id": activity.suspicious_activity_id,
                "banking_relationship_id": activity.banking_relationship_id,
                "account_id": activity.account_id,
                "triggered_transaction_id": activity.transaction_id,
                "user_id": activity.user_id,
                "session_id": activity.session_id,
                "payment_beneficiary_id": activity.payment_beneficiary_id,
                "institution_name": activity.institution_name,
                "generated_at": pd.Timestamp(activity.detected_at) + pd.Timedelta(minutes=5),
                "alert_type": activity.activity_type,
                "alert_status": status_by_activity_type[activity.activity_type],
                "severity": severity_by_activity_type[activity.activity_type],
                "reason": _alert_reason(activity.activity_type),
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
                "suspicious_activity_id": alert.suspicious_activity_id,
                "banking_relationship_id": alert.banking_relationship_id,
                "account_id": alert.account_id,
                "transaction_id": alert.triggered_transaction_id,
                "user_id": alert.user_id,
                "session_id": alert.session_id,
                "payment_beneficiary_id": alert.payment_beneficiary_id,
                "opened_at": pd.Timestamp(alert.generated_at) + pd.Timedelta(hours=6),
                "assigned_team": "digital investigations"
                if alert.institution_name == NOVABANK
                else "private banking investigations",
                "case_status": "closed" if alert.alert_status == "closed" else "open",
                "investigation_summary": _case_summary(alert.alert_type),
            }
        )
    return _frame(CASES, rows)


def _generate_case_outcomes(
    cases: pd.DataFrame, transactions: pd.DataFrame, alerts: pd.DataFrame
) -> pd.DataFrame:
    """Record fraud and non-fraud determinations for each opened case."""
    transaction_currencies = transactions.set_index("transaction_id")["currency"]
    transaction_amounts = transactions.set_index("transaction_id")["amount_original"]
    transaction_amounts_chf = transactions.set_index("transaction_id")["amount_chf"]
    alert_by_id = alerts.set_index("alert_id")
    rows = []
    for index, case in enumerate(cases.itertuples(index=False), start=1):
        if case.alert_id not in alert_by_id.index:
            raise ValueError(f"Case {case.case_id} references missing alert_id {case.alert_id}")
        alert = alert_by_id.loc[case.alert_id]
        transaction_id = alert["triggered_transaction_id"]
        currency = str(transaction_currencies.loc[transaction_id])
        confirmed_fraud = alert["alert_type"] == "new_beneficiary_payment"
        loss_original = transaction_amounts.loc[transaction_id] if confirmed_fraud else Decimal("0.00")
        loss_chf = transaction_amounts_chf.loc[transaction_id] if confirmed_fraud else Decimal("0.00")
        rows.append(
            {
                "case_outcome_id": _identifier("OUT", index),
                "case_id": case.case_id,
                "decided_at": pd.Timestamp(case.opened_at) + pd.Timedelta(days=2),
                "outcome_type": "confirmed_fraud" if confirmed_fraud else "false_positive",
                "confirmed_fraud": confirmed_fraud,
                "loss_amount_original": loss_original,
                "loss_currency": currency,
                "loss_amount_chf": loss_chf,
                "notes": _outcome_note(confirmed_fraud),
            }
        )
    return _frame(CASE_OUTCOMES, rows)


def _generate_protected_scenario_answer_keys(
    suspicious_activities: pd.DataFrame,
    case_outcomes: pd.DataFrame,
) -> pd.DataFrame:
    """Create protected scenario labels that are never part of learner-facing views."""
    confirmed_activities = suspicious_activities[
        suspicious_activities["activity_type"] == "new_beneficiary_payment"
    ]
    confirmed_outcomes = case_outcomes[case_outcomes["confirmed_fraud"]]
    if confirmed_activities.empty:
        raise ValueError(f"{SUSPICIOUS_ACTIVITIES} must include a new_beneficiary_payment row")
    if confirmed_outcomes.empty:
        raise ValueError(f"{CASE_OUTCOMES} must include at least one confirmed_fraud row")

    confirmed_activity = confirmed_activities.iloc[0]
    confirmed_outcome = confirmed_outcomes.iloc[0]
    rows = [
        {
            "answer_key_id": "AK-0001",
            "scenario_name": "minimal_alert_lifecycle",
            "entity_table": SUSPICIOUS_ACTIVITIES,
            "entity_id": confirmed_activity["suspicious_activity_id"],
            "label_type": "scenario_label",
            "label_value": "confirmed_fraud",
            "available_to_learners": False,
        },
        {
            "answer_key_id": "AK-0002",
            "scenario_name": "minimal_alert_lifecycle",
            "entity_table": TRANSACTIONS,
            "entity_id": confirmed_activity["transaction_id"],
            "label_type": "scenario_label",
            "label_value": "confirmed_fraud",
            "available_to_learners": False,
        },
        {
            "answer_key_id": "AK-0003",
            "scenario_name": "minimal_alert_lifecycle",
            "entity_table": CASE_OUTCOMES,
            "entity_id": confirmed_outcome["case_outcome_id"],
            "label_type": "case_outcome_answer",
            "label_value": "confirmed_fraud",
            "available_to_learners": False,
        },
    ]
    return _frame(PROTECTED_SCENARIO_ANSWER_KEYS, rows)


def _frame(table_name: str, rows: list[dict[str, object]]) -> pd.DataFrame:
    """Build a DataFrame with column order enforced by the schema contract."""
    return pd.DataFrame(rows, columns=COLUMN_NAMES[table_name])


def _session_id_for_user(
    sessions: pd.DataFrame, user_id: object | None, session_event: str | None
) -> str | None:
    """Pick a deterministic session for a digital activity, if one exists."""
    if user_id is None or pd.isna(user_id):
        return None
    user_sessions = sessions[sessions["user_id"] == user_id]
    if user_sessions.empty:
        return None
    if session_event is not None:
        event_sessions = user_sessions[user_sessions["session_event"] == session_event]
        if not event_sessions.empty:
            return str(event_sessions.iloc[0]["session_id"])
    return str(user_sessions.iloc[0]["session_id"])


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


def _case_summary(alert_type: str) -> str:
    """Return a learner-readable investigation summary for a case."""
    summaries = {
        "new_beneficiary_payment": "Case reviewed payment, User, session, and beneficiary context.",
        "session_payment_velocity": "Case reviewed digital telemetry and closed without fraud confirmation.",
    }
    return summaries.get(alert_type, "Case reviewed available alert context.")


def _outcome_note(confirmed_fraud: bool) -> str:
    """Describe whether the outcome confirmed fraud without exposing protected labels."""
    if confirmed_fraud:
        return "Case outcome confirmed fraud; protected scenario answer keys remain separate."
    return "Case outcome closed without a fraud confirmation."


def _alert_reason(alert_type: str) -> str:
    """Look up a canned alert reason string for the given alert type."""
    reasons = {
        "private_banking_high_value": "High-value movement relative to sample relationship profile.",
        "new_beneficiary_payment": "Payment followed recent beneficiary setup.",
        "session_payment_velocity": "Multiple session and payment events observed close together.",
    }
    return reasons[alert_type]
