"""Digital-banking feature calculations over canonical generated tables."""

from __future__ import annotations

from collections.abc import Mapping

import pandas as pd

from banking_fraud_lab.features.specs import DIGITAL_BANKING_FEATURE_FAMILIES
from banking_fraud_lab.schema import (
    ACCOUNTS,
    PAYMENT_BENEFICIARIES,
    SESSIONS,
    SUSPICIOUS_ACTIVITIES,
    TRANSACTIONS,
)

NOVA_BANK_DIGITAL = "NovaBank Digital"
# Risky beneficiary-account countries for the db_risky_channel family. These are
# synthetic high-risk markers used for educational feature extraction only; they
# are not compliance guidance and carry no affiliation with real institutions.
RISKY_BENEFICIARY_COUNTRIES = frozenset({"LT", "BG", "RU"})
EARLY_LIFE_ACCOUNT_DAYS = 30


def _transaction_session_links(suspicious_activities: pd.DataFrame) -> pd.DataFrame:
    """Return one deterministic session link per transaction.

    Suspicious activities should carry at most one session per transaction. When
    duplicates exist this keeps the earliest-detected link deterministically
    (sorted by detection order) so feature joining never depends on row order.
    """
    links = suspicious_activities[["transaction_id", "session_id"]].dropna(
        subset=["transaction_id"]
    )
    if links.empty:
        return links
    return (
        links.sort_values(["transaction_id", "session_id"], kind="stable")
        .drop_duplicates(subset=["transaction_id"], keep="first")
        .reset_index(drop=True)
    )


def calculate_db_session_risk_features(
    transactions: pd.DataFrame,
    sessions: pd.DataFrame,
    suspicious_activities: pd.DataFrame,
) -> pd.DataFrame:
    """Surface session-level risk telemetry for digital transactions.

    Transactions are linked to sessions through suspicious-activity rows, which
    carry both the ``transaction_id`` and ``session_id`` for digital activity.
    Transactions without a session link keep neutral (non-risky) feature values.
    """
    activity_links = _transaction_session_links(suspicious_activities)
    session_columns = [
        "session_id",
        "is_vpn_or_proxy",
        "asn_risk_score",
        "auth_method",
    ]
    context = transactions[["transaction_id"]].merge(
        activity_links,
        on="transaction_id",
        how="left",
        validate="one_to_one",
    ).merge(
        sessions[session_columns],
        on="session_id",
        how="left",
        validate="many_to_one",
    )

    is_vpn_or_proxy = context["is_vpn_or_proxy"].fillna(False).astype(bool)
    asn_risk_score = pd.to_numeric(context["asn_risk_score"], errors="coerce").fillna(0).astype(int)
    auth_method = context["auth_method"].fillna("")

    return pd.DataFrame(
        {
            "transaction_id": context["transaction_id"],
            "db_is_vpn_or_proxy": is_vpn_or_proxy.astype(int),
            "db_asn_risk_score": asn_risk_score,
            "db_is_high_risk_network": (asn_risk_score >= 70).astype(int),
            "db_is_password_sms_auth": auth_method.eq("password_sms").astype(int),
        }
    ).sort_values("transaction_id", kind="stable").reset_index(drop=True)


def calculate_db_beneficiary_novelty_features(
    transactions: pd.DataFrame,
    payment_beneficiaries: pd.DataFrame,
    *,
    lookback_days: int = 30,
) -> pd.DataFrame:
    """Flag payments to recently added or updated beneficiaries."""
    beneficiary_context = payment_beneficiaries[
        ["payment_beneficiary_id", "created_at", "beneficiary_change_event"]
    ].copy()
    beneficiary_context["beneficiary_created_at"] = pd.to_datetime(
        beneficiary_context["created_at"], errors="coerce"
    )
    context = transactions[["transaction_id", "payment_beneficiary_id", "booked_at"]].merge(
        beneficiary_context[
            ["payment_beneficiary_id", "beneficiary_created_at", "beneficiary_change_event"]
        ],
        on="payment_beneficiary_id",
        how="left",
        validate="many_to_one",
    )
    booked_at = pd.to_datetime(context["booked_at"], errors="coerce")
    age_days = (
        (booked_at - context["beneficiary_created_at"]) / pd.Timedelta(days=1)
    ).fillna(-1.0)
    has_beneficiary = context["payment_beneficiary_id"].notna()
    lifecycle_is_new = context["beneficiary_change_event"].isin(
        ("new_beneficiary_added", "beneficiary_updated")
    )
    is_recently_created = has_beneficiary & (age_days >= 0) & (age_days <= lookback_days)
    is_new = has_beneficiary & (lifecycle_is_new | is_recently_created | (age_days < 0))

    return (
        pd.DataFrame(
            {
                "transaction_id": context["transaction_id"],
                "db_beneficiary_age_days": age_days.round(2),
                "db_is_new_beneficiary": is_new.astype(int),
            }
        )
        .sort_values("transaction_id", kind="stable")
        .reset_index(drop=True)
    )


def calculate_db_payment_velocity_features(
    transactions: pd.DataFrame,
    sessions: pd.DataFrame,
    suspicious_activities: pd.DataFrame,
) -> pd.DataFrame:
    """Count outbound payments authorized within the same digital session."""
    del sessions  # Session details are not needed beyond the session_id link.
    activity_links = _transaction_session_links(suspicious_activities)
    context = transactions[["transaction_id", "direction", "amount_chf"]].merge(
        activity_links,
        on="transaction_id",
        how="left",
        validate="one_to_one",
    )
    context["amount_chf"] = pd.to_numeric(context["amount_chf"], errors="coerce").fillna(0.0)
    context["is_outbound"] = context["direction"].eq("debit") & context["session_id"].notna()

    outbound_session_stats = (
        context[context["is_outbound"]]
        .groupby("session_id", as_index=False)
        .agg(
            db_session_payment_count=("transaction_id", "count"),
            db_session_payment_amount_chf=("amount_chf", "sum"),
            db_session_max_payment_chf=("amount_chf", "max"),
        )
    )

    result = context[["transaction_id", "session_id"]].merge(
        outbound_session_stats,
        on="session_id",
        how="left",
        validate="many_to_one",
    )
    result["db_session_payment_count"] = result["db_session_payment_count"].fillna(0).astype(int)
    result["db_session_payment_amount_chf"] = (
        result["db_session_payment_amount_chf"].fillna(0.0).round(2)
    )
    result["db_session_max_payment_chf"] = result["db_session_max_payment_chf"].fillna(0.0).round(2)
    return (
        result[
            [
                "transaction_id",
                "db_session_payment_count",
                "db_session_payment_amount_chf",
                "db_session_max_payment_chf",
            ]
        ]
        .sort_values("transaction_id", kind="stable")
        .reset_index(drop=True)
    )


def calculate_db_account_age_features(
    transactions: pd.DataFrame,
    accounts: pd.DataFrame,
) -> pd.DataFrame:
    """Measure account age at payment time and flag early-life accounts."""
    context = transactions[["transaction_id", "account_id", "booked_at"]].merge(
        accounts[["account_id", "opened_at"]],
        on="account_id",
        how="left",
        validate="many_to_one",
    )
    booked_at = pd.to_datetime(context["booked_at"], errors="coerce")
    opened_at = pd.to_datetime(context["opened_at"], errors="coerce")
    age_days = ((booked_at - opened_at) / pd.Timedelta(days=1)).fillna(-1.0)
    is_early_life = (age_days >= 0) & (age_days <= EARLY_LIFE_ACCOUNT_DAYS)

    return (
        pd.DataFrame(
            {
                "transaction_id": context["transaction_id"],
                "db_account_age_days": age_days.round(2),
                "db_is_early_life_account": is_early_life.astype(int),
            }
        )
        .sort_values("transaction_id", kind="stable")
        .reset_index(drop=True)
    )


def calculate_db_shared_device_features(
    transactions: pd.DataFrame,
    sessions: pd.DataFrame,
    suspicious_activities: pd.DataFrame,
) -> pd.DataFrame:
    """Count distinct Users per device fingerprint for transactions with sessions."""
    activity_links = _transaction_session_links(suspicious_activities)
    session_context = sessions[["session_id", "device_fingerprint_hash", "user_id"]]
    device_user_counts = (
        session_context.dropna(subset=["device_fingerprint_hash"])
        .groupby("device_fingerprint_hash")["user_id"]
        .nunique()
        .rename("db_device_user_count")
        .reset_index()
    )
    context = transactions[["transaction_id"]].merge(
        activity_links,
        on="transaction_id",
        how="left",
        validate="one_to_one",
    ).merge(
        session_context,
        on="session_id",
        how="left",
        validate="many_to_one",
    ).merge(
        device_user_counts,
        on="device_fingerprint_hash",
        how="left",
        validate="many_to_one",
    )
    device_user_count = pd.to_numeric(
        context["db_device_user_count"], errors="coerce"
    ).fillna(0).astype(int)
    is_shared = device_user_count > 1

    return (
        pd.DataFrame(
            {
                "transaction_id": context["transaction_id"],
                "db_device_user_count": device_user_count,
                "db_is_shared_device": is_shared.astype(int),
            }
        )
        .sort_values("transaction_id", kind="stable")
        .reset_index(drop=True)
    )


def calculate_db_pass_through_features(
    transactions: pd.DataFrame,
    payment_beneficiaries: pd.DataFrame,
    *,
    rapid_window_hours: int = 24,
) -> pd.DataFrame:
    """Detect incoming credits followed rapidly by outbound debits."""
    context = transactions[
        ["transaction_id", "account_id", "booked_at", "direction", "amount_chf", "payment_beneficiary_id"]
    ].copy()
    context["booked_at"] = pd.to_datetime(context["booked_at"], errors="coerce")
    context["amount_chf"] = pd.to_numeric(context["amount_chf"], errors="coerce").fillna(0.0)
    context = context.sort_values(
        ["account_id", "booked_at", "transaction_id"], kind="stable"
    ).reset_index(drop=True)
    credits = context[context["direction"].eq("credit")][["account_id", "booked_at", "amount_chf"]]

    def _nearest_prior_credit(row: pd.Series) -> tuple[float, float]:
        """Return (prior credit amount, hours since) for the nearest prior credit."""
        prior = credits[
            (credits["account_id"] == row["account_id"])
            & (credits["booked_at"] <= row["booked_at"])
        ]
        if prior.empty:
            return 0.0, float(rapid_window_hours + 1)
        latest = prior.sort_values("booked_at", kind="stable").iloc[-1]
        hours = (row["booked_at"] - latest["booked_at"]) / pd.Timedelta(hours=1)
        return float(latest["amount_chf"]), float(hours)

    debit_rows = context[context["direction"].eq("debit")].copy()
    if debit_rows.empty:
        context["db_prior_credit_amount_chf"] = 0.0
        context["db_hours_since_prior_credit"] = float(rapid_window_hours + 1)
        context["db_is_rapid_pass_through"] = 0
    else:
        computed = debit_rows.apply(_nearest_prior_credit, axis=1, result_type="expand")
        computed.columns = ["db_prior_credit_amount_chf", "db_hours_since_prior_credit"]
        debit_rows = debit_rows.assign(
            db_prior_credit_amount_chf=computed["db_prior_credit_amount_chf"].values,
            db_hours_since_prior_credit=computed["db_hours_since_prior_credit"].values,
        )
        is_rapid = (
            (debit_rows["db_prior_credit_amount_chf"] > 0)
            & (debit_rows["db_hours_since_prior_credit"] >= 0)
            & (debit_rows["db_hours_since_prior_credit"] <= rapid_window_hours)
            & debit_rows["payment_beneficiary_id"].notna()
        )
        debit_rows["db_is_rapid_pass_through"] = is_rapid.astype(int)
        context = context.merge(
            debit_rows[
                [
                    "transaction_id",
                    "db_prior_credit_amount_chf",
                    "db_hours_since_prior_credit",
                    "db_is_rapid_pass_through",
                ]
            ],
            on="transaction_id",
            how="left",
            validate="one_to_one",
        )
        context["db_prior_credit_amount_chf"] = (
            context["db_prior_credit_amount_chf"].fillna(0.0).round(2)
        )
        context["db_hours_since_prior_credit"] = (
            context["db_hours_since_prior_credit"].fillna(rapid_window_hours + 1).round(2)
        )
        context["db_is_rapid_pass_through"] = (
            context["db_is_rapid_pass_through"].fillna(0).astype(int)
        )

    return (
        context[
            [
                "transaction_id",
                "db_prior_credit_amount_chf",
                "db_hours_since_prior_credit",
                "db_is_rapid_pass_through",
            ]
        ]
        .sort_values("transaction_id", kind="stable")
        .reset_index(drop=True)
    )


def calculate_db_risky_channel_features(
    transactions: pd.DataFrame,
    payment_beneficiaries: pd.DataFrame,
) -> pd.DataFrame:
    """Flag high-risk channels and risky beneficiary countries."""
    beneficiary_countries = payment_beneficiaries[
        ["payment_beneficiary_id", "beneficiary_account_country"]
    ]
    context = transactions[
        ["transaction_id", "channel", "payment_beneficiary_id"]
    ].merge(
        beneficiary_countries,
        on="payment_beneficiary_id",
        how="left",
        validate="many_to_one",
    )
    is_mobile_app = context["channel"].eq("mobile_app").astype(int)
    is_risky_country = (
        context["beneficiary_account_country"]
        .fillna("")
        .isin(RISKY_BENEFICIARY_COUNTRIES)
        .astype(int)
    )

    return (
        pd.DataFrame(
            {
                "transaction_id": context["transaction_id"],
                "db_is_mobile_app_channel": is_mobile_app,
                "db_is_beneficiary_country_risky": is_risky_country,
            }
        )
        .sort_values("transaction_id", kind="stable")
        .reset_index(drop=True)
    )


def build_digital_banking_features(
    tables: Mapping[str, pd.DataFrame],
) -> pd.DataFrame:
    """Build the merged NovaBank Digital transaction feature frame.

    Joins the ``db_`` feature-family outputs onto one row per NovaBank Digital
    transaction so the v0.4 feature-engineering and supervised-baseline notebooks
    consume a single, library-built frame instead of reimplementing feature logic.
    """
    _require_tables(
        tables,
        (
            TRANSACTIONS,
            ACCOUNTS,
            PAYMENT_BENEFICIARIES,
            SESSIONS,
            SUSPICIOUS_ACTIVITIES,
        ),
    )
    accounts = tables[ACCOUNTS]
    digital_account_ids = set(
        accounts.loc[accounts["institution_name"] == NOVA_BANK_DIGITAL, "account_id"]
    )
    base = tables[TRANSACTIONS][
        tables[TRANSACTIONS]["account_id"].isin(digital_account_ids)
    ].copy()
    feature_frame = base[
        [
            "transaction_id",
            "account_id",
            "booked_at",
            "transaction_type",
            "channel",
            "direction",
            "amount_chf",
            "payment_beneficiary_id",
        ]
    ].copy()

    feature_frames = (
        calculate_db_session_risk_features(
            tables[TRANSACTIONS], tables[SESSIONS], tables[SUSPICIOUS_ACTIVITIES]
        ),
        calculate_db_beneficiary_novelty_features(
            tables[TRANSACTIONS], tables[PAYMENT_BENEFICIARIES]
        ),
        calculate_db_payment_velocity_features(
            tables[TRANSACTIONS], tables[SESSIONS], tables[SUSPICIOUS_ACTIVITIES]
        ),
        calculate_db_account_age_features(tables[TRANSACTIONS], tables[ACCOUNTS]),
        calculate_db_shared_device_features(
            tables[TRANSACTIONS], tables[SESSIONS], tables[SUSPICIOUS_ACTIVITIES]
        ),
        calculate_db_pass_through_features(
            tables[TRANSACTIONS], tables[PAYMENT_BENEFICIARIES]
        ),
        calculate_db_risky_channel_features(
            tables[TRANSACTIONS], tables[PAYMENT_BENEFICIARIES]
        ),
    )
    for frame in feature_frames:
        feature_frame = feature_frame.merge(
            frame,
            on="transaction_id",
            how="left",
            validate="one_to_one",
        )

    output_columns = tuple(
        output_column
        for feature in DIGITAL_BANKING_FEATURE_FAMILIES
        for output_column in feature.output_columns
    )
    ordered_columns = (
        "transaction_id",
        "account_id",
        "booked_at",
        "transaction_type",
        "channel",
        "direction",
        "amount_chf",
        "payment_beneficiary_id",
        *output_columns,
    )
    return feature_frame.loc[:, ordered_columns].sort_values(
        ["booked_at", "transaction_id"], kind="stable"
    ).reset_index(drop=True)


def _require_tables(
    tables: Mapping[str, pd.DataFrame],
    required_tables: tuple[str, ...],
) -> None:
    """Raise a clear error if a required feature source table is missing."""
    missing = sorted(set(required_tables) - set(tables))
    if missing:
        raise ValueError(f"Digital-banking features require missing tables: {missing}")


__all__ = [
    "EARLY_LIFE_ACCOUNT_DAYS",
    "NOVA_BANK_DIGITAL",
    "RISKY_BENEFICIARY_COUNTRIES",
    "build_digital_banking_features",
    "calculate_db_account_age_features",
    "calculate_db_beneficiary_novelty_features",
    "calculate_db_pass_through_features",
    "calculate_db_payment_velocity_features",
    "calculate_db_risky_channel_features",
    "calculate_db_session_risk_features",
    "calculate_db_shared_device_features",
]
