"""Private-banking feature calculations over canonical generated tables."""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import pandas as pd

from banking_fraud_lab.schema import (
    ACCOUNTS,
    ALERTS,
    BANKING_RELATIONSHIPS,
    CASES,
    CLIENTS,
    PARTNERS,
    PAYMENT_BENEFICIARIES,
    TRANSACTIONS,
)
from banking_fraud_lab.features.specs import PRIVATE_BANKING_FEATURE_FAMILIES

ALPINE_CREST_PRIVATE_BANK = "Alpine Crest Private Bank"


def calculate_amount_to_aum_features(
    transactions: pd.DataFrame,
    accounts: pd.DataFrame,
    banking_relationships: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate transaction amount as a share of relationship AUM."""
    context = _transaction_relationship_context(
        transactions,
        accounts,
        banking_relationships,
        include_relationship_columns=("aum_chf",),
    )
    amount_chf = _numeric(context["amount_chf"])
    aum_chf = _numeric(context["aum_chf"])

    return pd.DataFrame(
        {
            "transaction_id": context["transaction_id"],
            "amount_to_aum_ratio": _safe_ratio(amount_chf, aum_chf),
        }
    )


def calculate_amount_to_baseline_features(
    transactions: pd.DataFrame,
    accounts: pd.DataFrame,
    banking_relationships: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate current transaction amount relative to prior relationship activity."""
    context = _transaction_relationship_context(transactions, accounts, banking_relationships)
    context = context.sort_values(
        ["banking_relationship_id", "booked_at", "transaction_id"],
        kind="stable",
    ).copy()
    amount_chf = _numeric(context["amount_chf"])
    grouped_amount = amount_chf.groupby(context["banking_relationship_id"])
    prior_count = grouped_amount.cumcount()
    prior_sum = grouped_amount.cumsum() - amount_chf
    baseline = (prior_sum / prior_count.replace(0, np.nan)).where(
        prior_count > 0,
        amount_chf,
    )

    return (
        pd.DataFrame(
            {
                "transaction_id": context["transaction_id"],
                "relationship_amount_baseline_chf": baseline.fillna(0.0),
                "amount_to_relationship_baseline_ratio": _safe_ratio(
                    amount_chf,
                    baseline,
                ),
            }
        )
        .sort_values("transaction_id", kind="stable")
        .reset_index(drop=True)
    )


def calculate_new_counterparty_features(
    transactions: pd.DataFrame,
    payment_beneficiaries: pd.DataFrame,
    *,
    lookback_days: int = 30,
) -> pd.DataFrame:
    """Flag transactions linked to first-observed or recently created counterparties."""
    beneficiary_context = payment_beneficiaries[
        [
            "payment_beneficiary_id",
            "created_at",
            "beneficiary_change_event",
        ]
    ].copy()
    beneficiary_context["beneficiary_created_at"] = pd.to_datetime(
        beneficiary_context["created_at"],
        errors="coerce",
    )
    context = transactions[
        [
            "transaction_id",
            "payment_beneficiary_id",
            "booked_at",
        ]
    ].merge(
        beneficiary_context[
            [
                "payment_beneficiary_id",
                "beneficiary_created_at",
                "beneficiary_change_event",
            ]
        ],
        on="payment_beneficiary_id",
        how="left",
        validate="many_to_one",
    )
    booked_at = pd.to_datetime(context["booked_at"], errors="coerce")
    age_days = (
        (booked_at - context["beneficiary_created_at"]) / pd.Timedelta(days=1)
    ).fillna(-1.0)
    context = context.assign(booked_at=booked_at, counterparty_age_days=age_days)
    context = context.sort_values(
        ["payment_beneficiary_id", "booked_at", "transaction_id"],
        na_position="last",
        kind="stable",
    )
    context["counterparty_use_rank"] = (
        context.groupby("payment_beneficiary_id").cumcount() + 1
    )
    has_counterparty = context["payment_beneficiary_id"].notna()
    is_first_observed = has_counterparty & context["counterparty_use_rank"].eq(1)
    lifecycle_is_new = context["beneficiary_change_event"].eq("new_beneficiary_added")
    is_recently_created = (
        has_counterparty
        & (context["counterparty_age_days"] >= 0)
        & (context["counterparty_age_days"] <= lookback_days)
    )
    is_new = is_first_observed | lifecycle_is_new | is_recently_created

    return (
        pd.DataFrame(
            {
                "transaction_id": context["transaction_id"],
                "counterparty_age_days": context["counterparty_age_days"].round(2),
                "is_new_counterparty": is_new.astype(int),
            }
        )
        .sort_values("transaction_id", kind="stable")
        .reset_index(drop=True)
    )


def calculate_off_hours_features(transactions: pd.DataFrame) -> pd.DataFrame:
    """Extract booking hour and flag transactions outside 08:00-18:00."""
    booked_at = pd.to_datetime(transactions["booked_at"], errors="coerce")
    booked_hour = booked_at.dt.hour.fillna(-1).astype(int)
    is_off_hours = ((booked_hour < 8) | (booked_hour >= 18)).astype(int)

    return pd.DataFrame(
        {
            "transaction_id": transactions["transaction_id"],
            "booked_hour": booked_hour,
            "is_off_hours": is_off_hours,
        }
    )


def calculate_cross_border_features(
    transactions: pd.DataFrame,
    accounts: pd.DataFrame,
    banking_relationships: pd.DataFrame,
    clients: pd.DataFrame,
    partners: pd.DataFrame,
    payment_beneficiaries: pd.DataFrame,
) -> pd.DataFrame:
    """Flag counterparty-linked movement that crosses the Client partner country."""
    account_context = accounts[["account_id", "banking_relationship_id"]]
    relationship_context = banking_relationships[
        ["banking_relationship_id", "primary_client_id"]
    ]
    client_context = clients[["client_id", "partner_id"]]
    partner_context = partners[["partner_id", "country"]].rename(
        columns={"country": "partner_country"}
    )
    beneficiary_context = payment_beneficiaries[
        [
            "payment_beneficiary_id",
            "beneficiary_account_country",
            "beneficiary_bank_country",
        ]
    ]

    context = (
        transactions[["transaction_id", "account_id", "payment_beneficiary_id"]]
        .merge(account_context, on="account_id", how="left", validate="many_to_one")
        .merge(
            relationship_context,
            on="banking_relationship_id",
            how="left",
            validate="many_to_one",
        )
        .merge(
            client_context,
            left_on="primary_client_id",
            right_on="client_id",
            how="left",
            validate="many_to_one",
        )
        .merge(partner_context, on="partner_id", how="left", validate="many_to_one")
        .merge(
            beneficiary_context,
            on="payment_beneficiary_id",
            how="left",
            validate="many_to_one",
        )
    )
    partner_country = context["partner_country"].fillna("")
    account_country = context["beneficiary_account_country"].fillna("")
    bank_country = context["beneficiary_bank_country"].fillna("")
    has_counterparty = context["payment_beneficiary_id"].notna()
    is_cross_border = has_counterparty & (
        ((account_country != "") & (account_country != partner_country))
        | ((bank_country != "") & (bank_country != partner_country))
    )

    return pd.DataFrame(
        {
            "transaction_id": context["transaction_id"],
            "partner_country": partner_country,
            "beneficiary_account_country": account_country,
            "beneficiary_bank_country": bank_country,
            "is_cross_border": is_cross_border.astype(int),
        }
    )


def calculate_velocity_features(
    transactions: pd.DataFrame,
    accounts: pd.DataFrame,
    banking_relationships: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate relationship-level 7-day and 30-day transaction velocity."""
    context = _transaction_relationship_context(transactions, accounts, banking_relationships)
    context = context.sort_values(
        ["banking_relationship_id", "booked_at", "transaction_id"],
        kind="stable",
    ).copy()
    context["booked_at"] = pd.to_datetime(context["booked_at"], errors="coerce")
    context["amount_chf"] = _numeric(context["amount_chf"])

    rows: list[dict[str, float | int | str]] = []
    for _, relationship_transactions in context.groupby(
        "banking_relationship_id",
        sort=False,
    ):
        for row in relationship_transactions.itertuples(index=False):
            booked_at = pd.Timestamp(row.booked_at)
            seven_day_start = booked_at - pd.Timedelta(days=7)
            thirty_day_start = booked_at - pd.Timedelta(days=30)
            window_7d = relationship_transactions[
                (relationship_transactions["booked_at"] >= seven_day_start)
                & (relationship_transactions["booked_at"] <= booked_at)
            ]
            window_30d = relationship_transactions[
                (relationship_transactions["booked_at"] >= thirty_day_start)
                & (relationship_transactions["booked_at"] <= booked_at)
            ]
            count_7d = int(len(window_7d))
            count_30d = int(len(window_30d))
            amount_7d = float(window_7d["amount_chf"].sum())
            amount_30d = float(window_30d["amount_chf"].sum())
            rows.append(
                {
                    "transaction_id": row.transaction_id,
                    "relationship_txn_count_7d": count_7d,
                    "relationship_amount_sum_7d_chf": round(amount_7d, 2),
                    "relationship_txn_count_30d": count_30d,
                    "relationship_amount_sum_30d_chf": round(amount_30d, 2),
                    "txn_count_7d_to_30d_ratio": count_7d / max(count_30d, 1),
                    "amount_7d_to_30d_ratio": amount_7d / amount_30d
                    if amount_30d > 0
                    else 0.0,
                }
            )

    return pd.DataFrame(rows).sort_values("transaction_id", kind="stable").reset_index(drop=True)


def calculate_rm_concentration_features(
    alerts: pd.DataFrame,
    cases: pd.DataFrame,
    banking_relationships: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate alert and case concentration by relationship manager."""
    if "institution_name" in banking_relationships.columns:
        relationship_source = banking_relationships[
            banking_relationships["institution_name"] == ALPINE_CREST_PRIVATE_BANK
        ]
    else:
        relationship_source = banking_relationships
    relationship_context = relationship_source[
        ["banking_relationship_id", "relationship_manager_code"]
    ].copy()
    relationship_alert_counts = _count_by_relationship(alerts, "alert_id", "relationship_alert_count")
    relationship_case_counts = _count_by_relationship(cases, "case_id", "relationship_case_count")
    relationship_counts = (
        relationship_context.merge(
            relationship_alert_counts,
            on="banking_relationship_id",
            how="left",
            validate="one_to_one",
        )
        .merge(
            relationship_case_counts,
            on="banking_relationship_id",
            how="left",
            validate="one_to_one",
        )
        .fillna({"relationship_alert_count": 0, "relationship_case_count": 0})
    )
    rm_totals = (
        relationship_counts.groupby("relationship_manager_code", as_index=False)
        .agg(
            rm_alert_count=("relationship_alert_count", "sum"),
            rm_case_count=("relationship_case_count", "sum"),
        )
    )
    total_alerts = float(rm_totals["rm_alert_count"].sum())
    rm_totals["rm_alert_share"] = (
        rm_totals["rm_alert_count"] / total_alerts if total_alerts > 0 else 0.0
    )

    return relationship_context.merge(
        rm_totals,
        on="relationship_manager_code",
        how="left",
        validate="many_to_one",
    ).fillna({"rm_alert_count": 0, "rm_case_count": 0, "rm_alert_share": 0.0})


def build_private_banking_features(
    tables: Mapping[str, pd.DataFrame],
) -> pd.DataFrame:
    """Build the merged Alpine Crest private-banking transaction feature frame."""
    _require_tables(
        tables,
        (
            TRANSACTIONS,
            ACCOUNTS,
            BANKING_RELATIONSHIPS,
            CLIENTS,
            PARTNERS,
            PAYMENT_BENEFICIARIES,
            ALERTS,
            CASES,
        ),
    )
    base = _transaction_relationship_context(
        tables[TRANSACTIONS],
        tables[ACCOUNTS],
        tables[BANKING_RELATIONSHIPS],
        include_transaction_columns=(
            "transaction_type",
            "channel",
            "direction",
            "payment_beneficiary_id",
        ),
    )
    base = base[base["institution_name"] == ALPINE_CREST_PRIVATE_BANK].copy()
    feature_frame = base[
        [
            "transaction_id",
            "account_id",
            "banking_relationship_id",
            "institution_name",
            "booked_at",
            "transaction_type",
            "channel",
            "direction",
            "amount_chf",
            "payment_beneficiary_id",
        ]
    ].copy()

    transaction_feature_frames = (
        calculate_amount_to_aum_features(
            tables[TRANSACTIONS],
            tables[ACCOUNTS],
            tables[BANKING_RELATIONSHIPS],
        ),
        calculate_amount_to_baseline_features(
            tables[TRANSACTIONS],
            tables[ACCOUNTS],
            tables[BANKING_RELATIONSHIPS],
        ),
        calculate_new_counterparty_features(
            tables[TRANSACTIONS],
            tables[PAYMENT_BENEFICIARIES],
        ),
        calculate_off_hours_features(tables[TRANSACTIONS]),
        calculate_cross_border_features(
            tables[TRANSACTIONS],
            tables[ACCOUNTS],
            tables[BANKING_RELATIONSHIPS],
            tables[CLIENTS],
            tables[PARTNERS],
            tables[PAYMENT_BENEFICIARIES],
        ),
        calculate_velocity_features(
            tables[TRANSACTIONS],
            tables[ACCOUNTS],
            tables[BANKING_RELATIONSHIPS],
        ),
    )
    for frame in transaction_feature_frames:
        feature_frame = feature_frame.merge(
            frame,
            on="transaction_id",
            how="left",
            validate="one_to_one",
        )

    rm_features = calculate_rm_concentration_features(
        tables[ALERTS],
        tables[CASES],
        tables[BANKING_RELATIONSHIPS],
    )
    feature_frame = feature_frame.merge(
        rm_features,
        on="banking_relationship_id",
        how="left",
        validate="many_to_one",
    )

    output_columns = tuple(
        output_column
        for feature in PRIVATE_BANKING_FEATURE_FAMILIES
        for output_column in feature.output_columns
    )
    ordered_columns = (
        "transaction_id",
        "account_id",
        "banking_relationship_id",
        "institution_name",
        "relationship_manager_code",
        "booked_at",
        "transaction_type",
        "channel",
        "direction",
        "amount_chf",
        "payment_beneficiary_id",
        *output_columns,
    )
    return feature_frame.loc[:, ordered_columns].sort_values(
        ["booked_at", "transaction_id"],
        kind="stable",
    ).reset_index(drop=True)


def _transaction_relationship_context(
    transactions: pd.DataFrame,
    accounts: pd.DataFrame,
    banking_relationships: pd.DataFrame,
    *,
    include_transaction_columns: tuple[str, ...] = (),
    include_relationship_columns: tuple[str, ...] = (),
) -> pd.DataFrame:
    """Return transaction rows with account and Banking relationship context."""
    transaction_columns = (
        "transaction_id",
        "account_id",
        "booked_at",
        "amount_chf",
        *include_transaction_columns,
    )
    relationship_columns = (
        "banking_relationship_id",
        "institution_name",
        *include_relationship_columns,
    )
    account_context = accounts[["account_id", "banking_relationship_id"]]
    relationship_context = banking_relationships[list(dict.fromkeys(relationship_columns))]

    return (
        transactions[list(dict.fromkeys(transaction_columns))]
        .merge(account_context, on="account_id", how="left", validate="many_to_one")
        .merge(
            relationship_context,
            on="banking_relationship_id",
            how="left",
            validate="many_to_one",
        )
    )


def _count_by_relationship(
    frame: pd.DataFrame,
    id_column: str,
    output_column: str,
) -> pd.DataFrame:
    """Count rows by Banking relationship for Alert lifecycle tables."""
    if frame.empty:
        return pd.DataFrame(columns=("banking_relationship_id", output_column))
    return (
        frame.groupby("banking_relationship_id", as_index=False)[id_column]
        .nunique()
        .rename(columns={id_column: output_column})
    )


def _numeric(series: pd.Series) -> pd.Series:
    """Return a numeric Series from Decimal/object inputs."""
    return pd.to_numeric(series, errors="coerce").fillna(0.0).astype(float)


def _safe_ratio(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    """Return numerator/denominator with zero and missing denominators set to 0."""
    denominator = pd.to_numeric(denominator, errors="coerce")
    ratio = pd.to_numeric(numerator, errors="coerce") / denominator.where(denominator > 0)
    return ratio.replace([np.inf, -np.inf], np.nan).fillna(0.0).astype(float)


def _require_tables(
    tables: Mapping[str, pd.DataFrame],
    required_tables: tuple[str, ...],
) -> None:
    """Raise a clear error if a required feature source table is missing."""
    missing = sorted(set(required_tables) - set(tables))
    if missing:
        raise ValueError(f"Private-banking features require missing tables: {missing}")


__all__ = [
    "ALPINE_CREST_PRIVATE_BANK",
    "build_private_banking_features",
    "calculate_amount_to_aum_features",
    "calculate_amount_to_baseline_features",
    "calculate_cross_border_features",
    "calculate_new_counterparty_features",
    "calculate_off_hours_features",
    "calculate_rm_concentration_features",
    "calculate_velocity_features",
]
