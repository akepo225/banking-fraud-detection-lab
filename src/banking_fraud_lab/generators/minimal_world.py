"""Generate the deterministic minimal banking world used by v0.1 samples."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
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
    RELATIONSHIP_MANAGER_HISTORY,
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
DATASET_AS_OF = pd.Timestamp("2026-03-31 23:59:59")
CHF_RATES = {
    "CHF": Decimal("1.00"),
    "EUR": Decimal("0.96"),
    "GBP": Decimal("1.12"),
    "USD": Decimal("0.91"),
}
MONEY_QUANT = Decimal("0.01")
ActivitySpec = tuple[str, str, str, str, str | None]


@dataclass(frozen=True)
class DatasetScaleProfile:
    """Named row-count profile for deterministic synthetic data generation."""

    name: str
    partner_count: int
    client_count: int
    session_count: int
    transaction_count: int
    suspicious_activity_count: int
    description: str


SCALE_PROFILES: dict[str, DatasetScaleProfile] = {
    "tiny": DatasetScaleProfile(
        name="tiny",
        partner_count=8,
        client_count=6,
        session_count=7,
        transaction_count=12,
        suspicious_activity_count=3,
        description="Committed sample and CI smoke-test scale.",
    ),
    "small": DatasetScaleProfile(
        name="small",
        partner_count=32,
        client_count=24,
        session_count=36,
        transaction_count=96,
        suspicious_activity_count=24,
        description="Local learner exercise scale with visibly larger joins.",
    ),
    "medium": DatasetScaleProfile(
        name="medium",
        partner_count=120,
        client_count=90,
        session_count=180,
        transaction_count=600,
        suspicious_activity_count=120,
        description="Laptop-feasible development scale for richer SQL and validation checks.",
    ),
    "large": DatasetScaleProfile(
        name="large",
        partner_count=320,
        client_count=240,
        session_count=480,
        transaction_count=2400,
        suspicious_activity_count=480,
        description="Optional local stress-test scale; generated data should stay out of git.",
    ),
}
DEFAULT_SCALE_PROFILE = "tiny"
DEFAULT_SUSPICIOUS_ACTIVITY_SPECS: tuple[ActivitySpec, ...] = (
    (
        "T-0003",
        "private_banking_high_value",
        "High-value movement relative to sample Banking relationship profile.",
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
PRIVATE_BANKING_TRANSACTION_TYPE_SEQUENCE = (
    "wire_transfer",
    "wire_transfer",
    "fx_trade",
    "management_fee",
    "wire_transfer",
    "custody_fee",
    "securities_purchase",
    "wire_transfer",
    "fx_trade",
    "securities_sale",
    "wire_transfer",
    "wire_transfer",
    "wire_transfer",
    "management_fee",
    "wire_transfer",
    "fx_trade",
    "wire_transfer",
    "wire_transfer",
    "wire_transfer",
    "wire_transfer",
)
PRIVATE_AUM_MULTIPLIERS = (
    Decimal("3.25"),
    Decimal("4.50"),
    Decimal("5.75"),
    Decimal("7.25"),
    Decimal("6.00"),
)


def generate_minimal_banking_world(
    seed: int = 42,
    output_dir: Path | None = None,
    *,
    scale: str | DatasetScaleProfile = DEFAULT_SCALE_PROFILE,
) -> dict[str, pd.DataFrame]:
    """Generate a deterministic banking dataset and optionally write CSV files."""

    profile = _resolve_scale_profile(scale)
    fake = Faker("en_US")
    fake.seed_instance(seed)
    rng = np.random.default_rng(seed)

    partners = _generate_partners(fake, rng, profile)
    clients = _generate_clients(rng, partners, profile)
    roles = _generate_roles()
    banking_relationships = _generate_banking_relationships(fake, rng, clients)
    partner_roles = _generate_partner_roles(clients, roles, banking_relationships, partners)
    accounts = _generate_accounts(rng, banking_relationships, profile)
    banking_relationships = _add_relationship_aum_context(banking_relationships, accounts)
    relationship_manager_history = _generate_relationship_manager_history(banking_relationships)
    users = _generate_users(rng, clients)
    sessions = _generate_sessions(rng, users, profile)
    payment_beneficiaries = _generate_payment_beneficiaries(fake, rng, clients, users)
    transactions = _generate_transactions(
        rng,
        accounts,
        banking_relationships,
        payment_beneficiaries,
        profile,
    )
    activity_specs = _activity_specs_for_profile(profile, transactions, accounts)
    suspicious_activities = _generate_suspicious_activities(
        transactions,
        accounts,
        banking_relationships,
        users,
        sessions,
        activity_specs=activity_specs,
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
        RELATIONSHIP_MANAGER_HISTORY: relationship_manager_history,
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
            # Pin LF line endings so generated CSVs are byte-identical on every platform
            # (pandas defaults to os.linesep, which is CRLF on Windows). The committed
            # data/sample CSVs are normalized to LF by .gitattributes (issue #158).
            frame.to_csv(
                output_path / f"{table_name}.csv",
                index=False,
                encoding="utf-8",
                lineterminator="\n",
            )

    return ordered_tables


def generate_learner_facing_minimal_banking_world(
    seed: int = 42,
    output_dir: Path | None = None,
    *,
    scale: str | DatasetScaleProfile = DEFAULT_SCALE_PROFILE,
) -> dict[str, pd.DataFrame]:
    """Generate default learner-facing tables without protected scenario answer keys."""
    tables = generate_minimal_banking_world(seed=seed, scale=scale)
    learner_tables = build_learner_facing_views(tables)

    if output_dir is not None:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        for table_name, frame in learner_tables.items():
            # Pin LF line endings for cross-platform byte-identity (see issue #158).
            frame.to_csv(
                output_path / f"{table_name}.csv",
                index=False,
                encoding="utf-8",
                lineterminator="\n",
            )

    return learner_tables


def build_learner_facing_views(
    tables: Mapping[str, pd.DataFrame],
) -> dict[str, pd.DataFrame]:
    """Return the generated tables intended for learners by default."""
    return {table_name: tables[table_name].copy() for table_name in LEARNER_FACING_TABLE_NAMES}


def _resolve_scale_profile(scale: str | DatasetScaleProfile) -> DatasetScaleProfile:
    """Return a known scale profile or validate a custom profile."""
    if isinstance(scale, DatasetScaleProfile):
        _validate_scale_profile(scale)
        return scale
    try:
        profile = SCALE_PROFILES[scale]
    except KeyError as exc:
        valid_scales = ", ".join(SCALE_PROFILES)
        raise ValueError(f"Unknown scale profile {scale!r}; expected one of: {valid_scales}") from exc
    _validate_scale_profile(profile)
    return profile


def _validate_scale_profile(profile: DatasetScaleProfile) -> None:
    """Validate profile sizes needed by the foundation generator."""
    if not profile.name:
        raise ValueError("Scale profile name must be non-empty")
    if profile.partner_count < 4:
        raise ValueError("Scale profile partner_count must be at least 4")
    if profile.client_count < 3:
        raise ValueError("Scale profile client_count must be at least 3")
    if profile.client_count > profile.partner_count:
        raise ValueError("Scale profile client_count cannot exceed partner_count")
    if profile.session_count < 1:
        raise ValueError("Scale profile session_count must be positive")
    if profile.transaction_count < 3:
        raise ValueError("Scale profile transaction_count must be at least 3")
    if profile.suspicious_activity_count < 1:
        raise ValueError("Scale profile suspicious_activity_count must be positive")
    if profile.suspicious_activity_count > profile.transaction_count:
        raise ValueError("Scale profile suspicious_activity_count cannot exceed transaction_count")


def _generate_partners(
    fake: Faker, rng: np.random.Generator, profile: DatasetScaleProfile
) -> pd.DataFrame:
    """Create partner records spanning both institutions with randomised attributes."""
    countries = ("CH", "DE", "FR", "IT", "GB", "US")
    rows = []
    alpine_partner_count = profile.partner_count // 2
    for index in range(1, profile.partner_count + 1):
        partner_type = "legal_entity" if index in {3, 7} else "natural_person"
        institution_name = ALPINE_CREST if index <= alpine_partner_count else NOVABANK
        created_at = _timestamp(days=-365 - index * 12, hours=index)
        kyc_risk_effective_from = created_at + pd.Timedelta(days=30)
        kyc_risk_reviewed_at = min(
            kyc_risk_effective_from + pd.Timedelta(days=90 + index % 30),
            DATASET_AS_OF - pd.Timedelta(days=index % 7),
        )
        rows.append(
            {
                "partner_id": _identifier("P", index),
                "institution_name": institution_name,
                "partner_type": partner_type,
                "display_name": fake.company() if partner_type == "legal_entity" else fake.name(),
                "country": rng.choice(countries),
                "created_at": created_at,
                "risk_rating": rng.choice(("low", "medium", "high"), p=(0.5, 0.35, 0.15)),
                "kyc_risk_effective_from": kyc_risk_effective_from,
                "kyc_risk_reviewed_at": kyc_risk_reviewed_at,
            }
        )
    return _frame(PARTNERS, rows)


def _generate_clients(
    rng: np.random.Generator, partners: pd.DataFrame, profile: DatasetScaleProfile
) -> pd.DataFrame:
    """Derive client records from the configured partners with institution-matched segments."""
    segments = {
        ALPINE_CREST: ("private_banking_individual", "family_office", "operating_company"),
        NOVABANK: ("digital_retail", "digital_sme", "digital_premium"),
    }
    rows = []
    for index, partner in enumerate(
        partners.iloc[: profile.client_count].itertuples(index=False),
        start=1,
    ):
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
                "relationship_manager_assigned_at": (
                    pd.Timestamp(client.onboarded_at) + pd.Timedelta(days=3, hours=-1)
                ),
                "aum_chf": _money(0),
            }
        )
    return _frame(BANKING_RELATIONSHIPS, rows)


def _add_relationship_aum_context(
    relationships: pd.DataFrame,
    accounts: pd.DataFrame,
) -> pd.DataFrame:
    """Add deterministic AUM context correlated with relationship account balances."""
    balances = accounts.groupby("banking_relationship_id")["balance_chf"].apply(
        lambda values: sum(values, Decimal("0.00"))
    )
    relationship_rows = relationships.copy()
    aum_values = []
    for index, relationship in enumerate(relationship_rows.itertuples(index=False), start=1):
        relationship_balance = balances.get(relationship.banking_relationship_id, Decimal("0.00"))
        if relationship.institution_name == ALPINE_CREST:
            multiplier = PRIVATE_AUM_MULTIPLIERS[(index - 1) % len(PRIVATE_AUM_MULTIPLIERS)]
            aum_values.append((relationship_balance * multiplier).quantize(MONEY_QUANT))
        else:
            aum_values.append(relationship_balance.quantize(MONEY_QUANT))
    relationship_rows["aum_chf"] = aum_values
    return relationship_rows.loc[:, COLUMN_NAMES[BANKING_RELATIONSHIPS]]


def _generate_relationship_manager_history(relationships: pd.DataFrame) -> pd.DataFrame:
    """Create current effective-dated relationship-manager assignment rows."""
    rows = []
    for index, relationship in enumerate(relationships.itertuples(index=False), start=1):
        rows.append(
            {
                "rm_history_id": _identifier("RMH", index),
                "banking_relationship_id": relationship.banking_relationship_id,
                "relationship_manager_code": relationship.relationship_manager_code,
                "effective_from": relationship.relationship_manager_assigned_at,
                "effective_to": pd.NaT,
            }
        )
    return _frame(RELATIONSHIP_MANAGER_HISTORY, rows)


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


def _generate_accounts(
    rng: np.random.Generator, relationships: pd.DataFrame, profile: DatasetScaleProfile
) -> pd.DataFrame:
    """Open current and optional custody/savings accounts under each relationship."""
    rows = []
    for index, relationship in enumerate(relationships.itertuples(index=False), start=1):
        account_count = 2 if _has_secondary_account(profile, index) else 1
        for account_number in range(account_count):
            currency = str(rng.choice(("CHF", "EUR", "USD", "GBP")))
            balance = _money(int(rng.integers(25_000, 850_000)))
            opened_at = pd.Timestamp(relationship.opened_at) + pd.Timedelta(days=account_number)
            rows.append(
                {
                    "account_id": _identifier("A", len(rows) + 1),
                    "banking_relationship_id": relationship.banking_relationship_id,
                    "institution_name": relationship.institution_name,
                    "account_type": _account_type(relationship.institution_name, account_number),
                    "currency": currency,
                    "opened_at": opened_at,
                    "status": "active",
                    "status_effective_from": opened_at,
                    "status_effective_to": pd.NaT,
                    "balance_original": balance,
                    "balance_currency": currency,
                    "balance_chf": _to_chf(balance, currency),
                }
            )
    return _frame(ACCOUNTS, rows)


def _has_secondary_account(profile: DatasetScaleProfile, relationship_index: int) -> bool:
    """Return whether the relationship receives a second account at this scale."""
    if profile.name == "tiny":
        return relationship_index in {1, 4}
    return relationship_index % 4 == 1


def _generate_users(rng: np.random.Generator, clients: pd.DataFrame) -> pd.DataFrame:
    """Create digital user identities for generated clients."""
    rows = []
    for index, client in enumerate(clients.itertuples(index=False), start=1):
        rows.append(
            {
                "user_id": _identifier("U", index),
                "client_id": client.client_id,
                "institution_name": client.institution_name,
                "username_hash": f"usr_{int(rng.integers(10**11, 10**12)):x}",
                "created_at": pd.Timestamp(client.onboarded_at) + pd.Timedelta(days=14),
                "status": "active",
                "authorized_from": pd.Timestamp(client.onboarded_at)
                + pd.Timedelta(days=14, hours=1),
                "authorized_to": pd.NaT,
            }
        )
    return _frame(USERS, rows)


def _generate_sessions(
    rng: np.random.Generator, users: pd.DataFrame, profile: DatasetScaleProfile
) -> pd.DataFrame:
    """Generate login and activity sessions for digital users."""
    rows = []
    events = ("login", "view_accounts", "add_beneficiary", "payment_authorized")
    session_users = users[users["institution_name"] == NOVABANK]
    if session_users.empty:
        session_users = users
    for index in range(1, profile.session_count + 1):
        user = session_users.iloc[(index - 1) % len(session_users)]
        channel = str(rng.choice(("web", "mobile_app")))
        started_at = _bounded_timestamp(
            index,
            profile.session_count,
            start=max(
                pd.Timestamp(user["created_at"]) + pd.Timedelta(days=1),
                DATASET_AS_OF - pd.Timedelta(days=60),
            ),
            end=DATASET_AS_OF - pd.Timedelta(days=10),
        )
        rows.append(
            {
                "session_id": _identifier("S", index),
                "user_id": user["user_id"],
                "started_at": started_at,
                "channel": channel,
                "user_agent": _user_agent(channel, index),
                "app_or_browser_version": _app_or_browser_version(channel, index),
                "device_fingerprint_hash": f"dev_{int(rng.integers(10**10, 10**11)):x}",
                "ip_country": rng.choice(("CH", "DE", "FR", "GB", "NL")),
                "asn_risk_score": int(rng.integers(3, 86)),
                "coarse_geolocation": _coarse_geolocation(index),
                "is_vpn_or_proxy": rng.choice((False, False, False, True)),
                "auth_method": rng.choice(("password_sms", "passkey", "push_mfa")),
                "session_event": _session_event(str(user["institution_name"]), events, index),
            }
        )
    return _frame(SESSIONS, rows)


def _generate_payment_beneficiaries(
    fake: Faker, rng: np.random.Generator, clients: pd.DataFrame, users: pd.DataFrame
) -> pd.DataFrame:
    """Add saved beneficiaries and private-banking counterparties for client context."""
    rows = []
    users_by_client = users.set_index("client_id")
    eligible_clients = clients[clients["client_id"].isin(users_by_client.index)]
    for client_index, client in enumerate(eligible_clients.itertuples(index=False), start=1):
        user = users_by_client.loc[client.client_id]
        beneficiary_count = _beneficiary_count(client.institution_name, client_index)
        for beneficiary_offset in range(1, beneficiary_count + 1):
            row_index = len(rows) + 1
            change_event = _beneficiary_change_event(
                client.institution_name,
                beneficiary_count,
                beneficiary_offset,
            )
            account_country = _beneficiary_account_country(
                rng,
                client.institution_name,
                client_index,
                beneficiary_offset,
            )
            rows.append(
                {
                    "payment_beneficiary_id": _identifier("B", row_index),
                    "client_id": client.client_id,
                    "added_by_user_id": user["user_id"],
                    "beneficiary_name": fake.company(),
                    "beneficiary_account_country": account_country,
                    "beneficiary_bank_country": _beneficiary_bank_country(
                        rng,
                        client.institution_name,
                        account_country,
                        beneficiary_offset,
                    ),
                    "beneficiary_change_event": change_event,
                    "created_at": _beneficiary_created_at(
                        client,
                        user,
                        change_event,
                        client_index,
                        beneficiary_offset,
                    ),
                    "status": "active",
                }
            )
    return _frame(PAYMENT_BENEFICIARIES, rows)


def _beneficiary_count(institution_name: str, client_index: int) -> int:
    """Return the number of saved counterparties created for one Client."""
    if institution_name == ALPINE_CREST:
        return 1 + (client_index % 3)
    return 1


def _beneficiary_change_event(
    institution_name: str,
    beneficiary_count: int,
    beneficiary_offset: int,
) -> str:
    """Return private-banking newness context or the digital default event."""
    if institution_name == ALPINE_CREST:
        if beneficiary_offset == beneficiary_count:
            return "new_beneficiary_added"
        return "established_beneficiary"
    return "beneficiary_created"


def _beneficiary_account_country(
    rng: np.random.Generator,
    institution_name: str,
    client_index: int,
    beneficiary_offset: int,
) -> str:
    """Return deterministic account-country context for private and digital beneficiaries."""
    if institution_name == ALPINE_CREST:
        private_countries = ("CH", "DE", "FR", "IT", "LI", "SG", "AE", "PA")
        return private_countries[(client_index + beneficiary_offset - 2) % len(private_countries)]
    return str(rng.choice(("CH", "DE", "FR", "IT", "GB")))


def _beneficiary_bank_country(
    rng: np.random.Generator,
    institution_name: str,
    account_country: str,
    beneficiary_offset: int,
) -> str:
    """Return bank-country context, including occasional correspondent-bank differences."""
    if institution_name == ALPINE_CREST:
        if beneficiary_offset % 3 == 0:
            return "CH"
        if beneficiary_offset % 2 == 0 and account_country != "GB":
            return "GB"
        return account_country
    return str(rng.choice(("CH", "DE", "FR", "IT", "GB")))


def _beneficiary_created_at(
    client: object,
    user: pd.Series,
    change_event: str,
    client_index: int,
    beneficiary_offset: int,
) -> pd.Timestamp:
    """Return beneficiary creation time suitable for old/new counterparty features."""
    if change_event == "new_beneficiary_added":
        return DATASET_AS_OF - pd.Timedelta(days=35 + client_index % 5 + beneficiary_offset)
    if change_event == "established_beneficiary":
        established_at = pd.Timestamp(client.onboarded_at) + pd.Timedelta(
            days=45 + beneficiary_offset * 20
        )
        return min(established_at, DATASET_AS_OF - pd.Timedelta(days=120))
    return min(
        pd.Timestamp(user["created_at"]) + pd.Timedelta(days=client_index),
        DATASET_AS_OF - pd.Timedelta(days=20),
    )


def _generate_transactions(
    rng: np.random.Generator,
    accounts: pd.DataFrame,
    relationships: pd.DataFrame,
    beneficiaries: pd.DataFrame,
    profile: DatasetScaleProfile,
) -> pd.DataFrame:
    """Book transactions with private-banking and digital beneficiary context."""
    relationship_clients = relationships.set_index("banking_relationship_id")["primary_client_id"]
    beneficiaries_by_client = {
        client_id: tuple(
            client_beneficiaries.sort_values(
                ["created_at", "payment_beneficiary_id"],
                kind="stable",
            ).to_dict("records")
        )
        for client_id, client_beneficiaries in beneficiaries.groupby("client_id")
    }
    rows = []
    private_transaction_index = 0
    for index in range(1, profile.transaction_count + 1):
        account = accounts.iloc[(index - 1) % len(accounts)]
        client_id = str(relationship_clients.loc[account["banking_relationship_id"]])
        is_digital_payment = account["institution_name"] == NOVABANK and index % 2 == 0
        if account["institution_name"] == ALPINE_CREST:
            private_transaction_index += 1
        transaction_type = _transaction_type(
            account["institution_name"],
            is_digital_payment,
            private_transaction_index,
        )
        direction = _transaction_direction(index, transaction_type)
        currency = str(account["currency"])
        amount = _transaction_amount(rng, transaction_type)
        booked_at = _bounded_timestamp(
            index,
            profile.transaction_count,
            start=DATASET_AS_OF - pd.Timedelta(days=90),
            end=DATASET_AS_OF - pd.Timedelta(days=5),
        )
        beneficiary_id = _transaction_beneficiary_id(
            beneficiaries_by_client.get(client_id, ()),
            transaction_type=transaction_type,
            direction=direction,
            booked_at=booked_at,
            sequence_index=private_transaction_index if account["institution_name"] == ALPINE_CREST else index,
            is_digital_payment=is_digital_payment,
        )
        rows.append(
            {
                "transaction_id": _identifier("T", index),
                "account_id": account["account_id"],
                "payment_beneficiary_id": beneficiary_id,
                "booked_at": booked_at,
                "transaction_type": transaction_type,
                "channel": _channel(account["institution_name"], is_digital_payment, transaction_type),
                "direction": direction,
                "amount_original": amount,
                "currency": currency,
                "amount_chf": _to_chf(amount, currency),
                "description": _transaction_description(
                    account["institution_name"],
                    is_digital_payment,
                    transaction_type,
                ),
            }
        )
    return _frame(TRANSACTIONS, rows)


def _activity_specs_for_profile(
    profile: DatasetScaleProfile,
    transactions: pd.DataFrame,
    accounts: pd.DataFrame,
) -> tuple[ActivitySpec, ...]:
    """Return deterministic suspicious activity triggers for the requested scale."""
    if profile.name == "tiny":
        return DEFAULT_SUSPICIOUS_ACTIVITY_SPECS

    transaction_context = transactions.merge(
        accounts[["account_id", "institution_name"]],
        on="account_id",
        how="left",
        validate="many_to_one",
    )
    private_transactions = transaction_context[
        transaction_context["institution_name"] == ALPINE_CREST
    ]["transaction_id"]
    digital_payment_transactions = transaction_context[
        (transaction_context["institution_name"] == NOVABANK)
        & (transaction_context["payment_beneficiary_id"].notna())
    ]["transaction_id"]
    digital_transactions = transaction_context[transaction_context["institution_name"] == NOVABANK][
        "transaction_id"
    ]
    candidates = {
        "private_banking_high_value": tuple(private_transactions),
        "new_beneficiary_payment": tuple(digital_payment_transactions),
        "session_payment_velocity": tuple(digital_transactions),
    }
    signals = {
        "private_banking_high_value": (
            "High-value movement relative to sample Banking relationship profile."
        ),
        "new_beneficiary_payment": "Payment followed recent beneficiary setup.",
        "session_payment_velocity": "Multiple session and payment events observed close together.",
    }
    priorities = {
        "private_banking_high_value": "medium",
        "new_beneficiary_payment": "high",
        "session_payment_velocity": "medium",
    }

    rows: list[ActivitySpec] = []
    used_transaction_ids: set[str] = set()
    # Cycle through pattern families so scaled alerts stay balanced and deterministic.
    pattern_order = (
        "private_banking_high_value",
        "new_beneficiary_payment",
        "session_payment_velocity",
    )
    while len(rows) < profile.suspicious_activity_count:
        row_count_before_cycle = len(rows)
        for activity_type in pattern_order:
            # Select one unused candidate per pattern before repeating the cycle.
            transaction_id = _next_unused_transaction(candidates[activity_type], used_transaction_ids)
            if transaction_id is None:
                continue
            used_transaction_ids.add(transaction_id)
            rows.append(
                (
                    transaction_id,
                    activity_type,
                    signals[activity_type],
                    priorities[activity_type],
                    None,
                )
            )
            if len(rows) == profile.suspicious_activity_count:
                break
        # Safety exit for custom profiles whose candidate pools are exhausted.
        if len(rows) == row_count_before_cycle:
            break

    if not rows:
        raise ValueError(f"Scale profile {profile.name!r} did not produce suspicious activities")
    return tuple(rows)


def _next_unused_transaction(
    candidates: tuple[str, ...],
    used_transaction_ids: set[str],
) -> str | None:
    """Return the first unused transaction ID from a deterministic candidate list."""
    for transaction_id in candidates:
        if transaction_id not in used_transaction_ids:
            return transaction_id
    return None


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
    rows = []
    for index, activity in enumerate(suspicious_activities.itertuples(index=False), start=1):
        generated_at = pd.Timestamp(activity.detected_at) + pd.Timedelta(minutes=5)
        status_updated_at = generated_at + pd.Timedelta(minutes=30)
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
                "generated_at": generated_at,
                "alert_type": activity.activity_type,
                "alert_status": status_by_activity_type[activity.activity_type],
                "status_updated_at": status_updated_at,
                "severity": activity.review_priority,
                "reason": activity.detection_signal,
            }
        )
    return _frame(ALERTS, rows)


def _generate_cases(alerts: pd.DataFrame) -> pd.DataFrame:
    """Open investigation cases for escalated and closed alerts."""
    rows = []
    case_alerts = alerts[alerts["alert_status"].isin(("escalated", "closed"))]
    for index, alert in enumerate(case_alerts.itertuples(index=False), start=1):
        opened_at = pd.Timestamp(alert.generated_at) + pd.Timedelta(hours=6)
        case_status = "closed" if alert.alert_status == "closed" else "open"
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
                "opened_at": opened_at,
                "assigned_team": "digital investigations"
                if alert.institution_name == NOVABANK
                else "private banking investigations",
                "case_status": case_status,
                "closed_at": opened_at + pd.Timedelta(days=2) if case_status == "closed" else pd.NaT,
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
        decided_at = pd.Timestamp(case.opened_at) + pd.Timedelta(days=2)
        rows.append(
            {
                "case_outcome_id": _identifier("OUT", index),
                "case_id": case.case_id,
                "decided_at": decided_at,
                "recorded_at": decided_at + pd.Timedelta(hours=1),
                "outcome_type": "confirmed-fraud" if confirmed_fraud else "false-positive",
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

    rows = []
    answer_key_index = 1
    for confirmed_activity in confirmed_activities.itertuples(index=False):
        rows.extend(
            [
                {
                    "answer_key_id": _identifier("AK", answer_key_index),
                    "scenario_name": "minimal_alert_lifecycle",
                    "entity_table": SUSPICIOUS_ACTIVITIES,
                    "entity_id": confirmed_activity.suspicious_activity_id,
                    "label_type": "scenario_label",
                    "label_value": "confirmed_fraud",
                    "available_to_learners": False,
                },
                {
                    "answer_key_id": _identifier("AK", answer_key_index + 1),
                    "scenario_name": "minimal_alert_lifecycle",
                    "entity_table": TRANSACTIONS,
                    "entity_id": confirmed_activity.transaction_id,
                    "label_type": "scenario_label",
                    "label_value": "confirmed_fraud",
                    "available_to_learners": False,
                },
            ]
        )
        answer_key_index += 2
    for confirmed_outcome in confirmed_outcomes.itertuples(index=False):
        rows.append(
            {
                "answer_key_id": _identifier("AK", answer_key_index),
                "scenario_name": "minimal_alert_lifecycle",
                "entity_table": CASE_OUTCOMES,
                "entity_id": confirmed_outcome.case_outcome_id,
                "label_type": "case_outcome_answer",
                "label_value": "confirmed_fraud",
                "available_to_learners": False,
            }
        )
        answer_key_index += 1
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
        if event_sessions.empty:
            raise ValueError(
                f"Session event {session_event!r} was not found for user_id {user_id!r}"
            )
        return str(event_sessions.iloc[0]["session_id"])
    return str(user_sessions.iloc[0]["session_id"])


def _identifier(prefix: str, index: int) -> str:
    """Format a zero-padded entity identifier like ``P-0001``."""
    return f"{prefix}-{index:04d}"


def _timestamp(days: int, hours: int = 0) -> pd.Timestamp:
    """Return a timestamp offset from the generation baseline."""
    return BASE_TIMESTAMP + pd.Timedelta(days=days, hours=hours)


def _bounded_timestamp(
    index: int,
    total: int,
    *,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> pd.Timestamp:
    """Spread deterministic timestamps across a bounded historical window."""
    if start > end:
        raise ValueError("Timestamp window start cannot be after end")
    slot_count = max(total - 1, 1)
    offset_nanos = (end - start).value * (index - 1) // slot_count
    return (start + pd.Timedelta(offset_nanos, unit="ns")).floor("min")


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


def _transaction_type(
    institution_name: str,
    is_digital_payment: bool,
    private_sequence_index: int = 0,
) -> str:
    """Choose transaction typology based on institution and deterministic context."""
    if is_digital_payment:
        return "instant_payment"
    if institution_name == ALPINE_CREST:
        sequence_index = max(private_sequence_index, 1)
        return PRIVATE_BANKING_TRANSACTION_TYPE_SEQUENCE[
            (sequence_index - 1) % len(PRIVATE_BANKING_TRANSACTION_TYPE_SEQUENCE)
        ]
    return "card_payment"


def _transaction_amount(rng: np.random.Generator, transaction_type: str) -> Decimal:
    """Return deterministic amount ranges that reflect the transaction typology."""
    amount_ranges = {
        "management_fee": (500, 8_000),
        "custody_fee": (125, 4_000),
        "securities_purchase": (25_000, 260_000),
        "securities_sale": (25_000, 260_000),
        "fx_trade": (10_000, 180_000),
        "wire_transfer": (5_000, 170_000),
    }
    minimum, maximum = amount_ranges.get(transaction_type, (75, 65_000))
    return _money(int(rng.integers(minimum, maximum)))


def _transaction_direction(index: int, transaction_type: str) -> str:
    """Return account-perspective direction consistent with the transaction typology."""
    if transaction_type in {"management_fee", "custody_fee", "securities_purchase", "fx_trade"}:
        return "debit"
    if transaction_type == "securities_sale":
        return "credit"
    return "debit" if index % 3 else "credit"


def _transaction_beneficiary_id(
    beneficiaries: tuple[dict[str, object], ...],
    *,
    transaction_type: str,
    direction: str,
    booked_at: pd.Timestamp,
    sequence_index: int,
    is_digital_payment: bool,
) -> str | None:
    """Select a beneficiary/counterparty only when the transaction type supports it."""
    eligible_beneficiaries = tuple(
        beneficiary
        for beneficiary in beneficiaries
        if pd.Timestamp(beneficiary["created_at"]) <= booked_at
    )
    if is_digital_payment:
        if not eligible_beneficiaries:
            return None
        return str(eligible_beneficiaries[sequence_index % len(eligible_beneficiaries)]["payment_beneficiary_id"])

    private_counterparty_types = {"wire_transfer", "fx_trade", "securities_purchase"}
    if direction != "debit" or transaction_type not in private_counterparty_types:
        return None
    if not eligible_beneficiaries:
        return None

    if sequence_index % 7 == 0:
        new_beneficiaries = tuple(
            beneficiary
            for beneficiary in eligible_beneficiaries
            if beneficiary["beneficiary_change_event"] == "new_beneficiary_added"
        )
        if new_beneficiaries:
            return str(
                new_beneficiaries[(sequence_index - 1) % len(new_beneficiaries)][
                    "payment_beneficiary_id"
                ]
            )

    established_beneficiaries = tuple(
        beneficiary
        for beneficiary in eligible_beneficiaries
        if beneficiary["beneficiary_change_event"] == "established_beneficiary"
    )
    candidates = established_beneficiaries or eligible_beneficiaries
    return str(candidates[(sequence_index - 1) % len(candidates)]["payment_beneficiary_id"])


def _channel(institution_name: str, is_digital_payment: bool, transaction_type: str) -> str:
    """Pick relationship_manager, web, mobile_app, or batch based on context."""
    if is_digital_payment:
        return "mobile_app"
    if transaction_type in {"management_fee", "custody_fee"}:
        return "batch"
    if institution_name == ALPINE_CREST:
        return "relationship_manager"
    return "web"


def _transaction_description(
    institution_name: str,
    is_digital_payment: bool,
    transaction_type: str,
) -> str:
    """Return a human-readable transaction description based on context."""
    if is_digital_payment:
        return "Outbound payment to saved beneficiary"
    if institution_name == ALPINE_CREST:
        descriptions = {
            "wire_transfer": "Private banking wire transfer",
            "fx_trade": "Private banking FX trade",
            "management_fee": "Private banking management fee",
            "custody_fee": "Private banking custody fee",
            "securities_purchase": "Private banking securities purchase",
            "securities_sale": "Private banking securities sale",
        }
        return descriptions[transaction_type]
    return "Digital banking account activity"


def _user_agent(channel: str, index: int) -> str:
    """Return a deterministic synthetic user-agent family for the session channel."""
    if channel == "mobile_app":
        user_agents = ("NovaBankMobile/iOS", "NovaBankMobile/Android")
    elif channel == "web":
        user_agents = ("Firefox/Desktop", "Chrome/Desktop")
    else:
        raise ValueError(f"Unsupported session channel: {channel}")
    return user_agents[(index - 1) % len(user_agents)]


def _app_or_browser_version(channel: str, index: int) -> str:
    """Return a deterministic synthetic app or browser version for the channel."""
    if channel == "mobile_app":
        versions = ("17.4", "14.1")
    elif channel == "web":
        versions = ("126.0", "124.0")
    else:
        raise ValueError(f"Unsupported session channel: {channel}")
    return versions[(index - 1) % len(versions)]


def _coarse_geolocation(index: int) -> str:
    """Return a deterministic coarse geolocation signal."""
    locations = ("Zurich-CH", "Geneva-CH", "Berlin-DE", "Paris-FR", "London-GB")
    return locations[(index - 1) % len(locations)]


def _session_event(institution_name: str, events: tuple[str, ...], index: int) -> str:
    """Return deterministic session events with NovaBank payment coverage."""
    if institution_name == NOVABANK:
        return "payment_authorized" if index % 2 == 0 else "add_beneficiary"
    return events[(index - 1) % len(events)]


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
