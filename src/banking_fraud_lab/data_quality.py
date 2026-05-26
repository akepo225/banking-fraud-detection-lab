"""Generated dataset quality reporting for foundation data."""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from banking_fraud_lab.generators import (
    SCALE_PROFILES,
    build_learner_facing_views,
    generate_minimal_banking_world,
)
from banking_fraud_lab.generators.minimal_world import DATASET_AS_OF
from banking_fraud_lab.progressive_views import (
    FOUNDATION_PROGRESSIVE_VIEW_SPECS,
    build_foundation_progressive_view,
)
from banking_fraud_lab.schema import (
    COLUMN_NAMES,
    PROTECTED_SCENARIO_ANSWER_KEYS,
    TABLE_NAMES,
    TABLE_SPECS,
)

QUALITY_DIMENSIONS = (
    "row_counts",
    "key_nullability",
    "referential_integrity",
    "temporal_ranges",
    "prevalence_ranges",
    "protected_key_exclusion",
    "progressive_view_health",
)
PROTECTED_KEY_COLUMNS = {"available_to_learners", "label_type", "label_value"}


@dataclass(frozen=True)
class DatasetQualityReport:
    """Deterministic quality summary for one generated dataset."""

    seed: int
    scale: str
    dataset_as_of: str
    row_counts: dict[str, int]
    key_nullability: tuple[dict[str, Any], ...]
    referential_integrity: tuple[dict[str, Any], ...]
    temporal_ranges: tuple[dict[str, Any], ...]
    prevalence_ranges: tuple[dict[str, Any], ...]
    protected_key_exclusion: tuple[dict[str, Any], ...]
    progressive_view_health: tuple[dict[str, Any], ...]
    issues: tuple[str, ...]

    @property
    def passed(self) -> bool:
        """Return whether every quality check passed."""
        return not self.issues

    @property
    def dimensions(self) -> set[str]:
        """Return the report dimensions included in this summary."""
        return set(QUALITY_DIMENSIONS)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable deterministic representation."""
        return {
            "seed": self.seed,
            "scale": self.scale,
            "dataset_as_of": self.dataset_as_of,
            "passed": self.passed,
            "dimensions": list(QUALITY_DIMENSIONS),
            "row_counts": self.row_counts,
            "key_nullability": list(self.key_nullability),
            "referential_integrity": list(self.referential_integrity),
            "temporal_ranges": list(self.temporal_ranges),
            "prevalence_ranges": list(self.prevalence_ranges),
            "protected_key_exclusion": list(self.protected_key_exclusion),
            "progressive_view_health": list(self.progressive_view_health),
            "issues": list(self.issues),
        }

    def to_markdown(self) -> str:
        """Render the quality report as learner-facing Markdown."""
        lines = [
            f"# Dataset Quality Report: {self.scale}",
            "",
            f"- Seed: `{self.seed}`",
            f"- Dataset as of: `{self.dataset_as_of}`",
            f"- Status: `{'PASS' if self.passed else 'FAIL'}`",
            "",
            "## Row Counts",
        ]
        for table_name, row_count in self.row_counts.items():
            lines.append(f"- `{table_name}`: {row_count}")

        lines.extend(
            [
                "",
                "## Quality Dimensions",
            ]
        )
        for dimension in QUALITY_DIMENSIONS:
            if dimension == "row_counts":
                lines.append(f"- `{dimension}`: {len(self.row_counts)} tables counted")
                continue
            checks = getattr(self, dimension)
            passed = sum(1 for check in checks if check["passed"])
            lines.append(f"- `{dimension}`: {passed}/{len(checks)} checks passed")

        lines.extend(["", "## Issues"])
        if self.issues:
            lines.extend(f"- {issue}" for issue in self.issues)
        else:
            lines.append("- None")
        return "\n".join(lines) + "\n"


def generate_dataset_quality_report(
    *,
    seed: int = 42,
    scale: str = "tiny",
) -> DatasetQualityReport:
    """Generate a deterministic quality report for one scale profile."""
    tables = generate_minimal_banking_world(seed=seed, scale=scale)
    scale_name = SCALE_PROFILES[scale].name if scale in SCALE_PROFILES else str(scale)

    report_sections = {
        "row_counts": _row_counts(tables),
        "key_nullability": _key_nullability_checks(tables),
        "referential_integrity": _referential_integrity_checks(tables),
        "temporal_ranges": _temporal_checks(tables),
        "prevalence_ranges": _prevalence_checks(tables),
        "protected_key_exclusion": _protected_key_exclusion_checks(tables),
        "progressive_view_health": _progressive_view_health_checks(tables),
    }
    issues = tuple(
        _issue_for_check(dimension, check)
        for dimension in QUALITY_DIMENSIONS
        if dimension != "row_counts"
        for check in report_sections[dimension]
        if not check["passed"]
    )

    return DatasetQualityReport(
        seed=seed,
        scale=scale_name,
        dataset_as_of=_timestamp_to_iso(DATASET_AS_OF),
        row_counts=report_sections["row_counts"],
        key_nullability=tuple(report_sections["key_nullability"]),
        referential_integrity=tuple(report_sections["referential_integrity"]),
        temporal_ranges=tuple(report_sections["temporal_ranges"]),
        prevalence_ranges=tuple(report_sections["prevalence_ranges"]),
        protected_key_exclusion=tuple(report_sections["protected_key_exclusion"]),
        progressive_view_health=tuple(report_sections["progressive_view_health"]),
        issues=issues,
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Generate dataset quality reports from the command line."""
    parser = argparse.ArgumentParser(
        description="Generate deterministic dataset quality reports for foundation data."
    )
    parser.add_argument("--seed", type=int, default=42, help="Generator seed.")
    parser.add_argument(
        "--scale",
        action="append",
        choices=tuple(SCALE_PROFILES),
        help="Named scale profile. Repeat to generate multiple reports.",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Report output format.",
    )
    parser.add_argument("--output", type=Path, help="Optional output file path.")
    args = parser.parse_args(argv)

    scales = tuple(args.scale or ("tiny",))
    reports = [
        generate_dataset_quality_report(seed=args.seed, scale=scale) for scale in scales
    ]
    output = _render_reports(reports, output_format=args.format)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output, end="")

    return 0 if all(report.passed for report in reports) else 1


def _row_counts(tables: Mapping[str, pd.DataFrame]) -> dict[str, int]:
    """Return deterministic row counts for every canonical table."""
    return {table_name: int(len(tables[table_name])) for table_name in TABLE_NAMES}


def _key_nullability_checks(tables: Mapping[str, pd.DataFrame]) -> list[dict[str, Any]]:
    """Check primary-key health and required schema-column nullability."""
    checks: list[dict[str, Any]] = []
    for table_name in TABLE_NAMES:
        frame = tables[table_name]
        primary_key = COLUMN_NAMES[table_name][0]
        null_count = int(frame[primary_key].isna().sum())
        duplicate_count = int(frame[primary_key].duplicated().sum())
        checks.append(
            {
                "table": table_name,
                "column": primary_key,
                "check": "primary_key_non_null_unique",
                "null_count": null_count,
                "duplicate_count": duplicate_count,
                "passed": null_count == 0 and duplicate_count == 0,
            }
        )

        for column in TABLE_SPECS[table_name].columns:
            if column.nullable:
                continue
            required_null_count = int(frame[column.name].isna().sum())
            checks.append(
                {
                    "table": table_name,
                    "column": column.name,
                    "check": "required_column_non_null",
                    "null_count": required_null_count,
                    "passed": required_null_count == 0,
                }
            )
    return checks


def _referential_integrity_checks(
    tables: Mapping[str, pd.DataFrame],
) -> list[dict[str, Any]]:
    """Check every documented foreign-key reference against parent tables."""
    checks: list[dict[str, Any]] = []
    for child_table, table_spec in TABLE_SPECS.items():
        for column in table_spec.columns:
            if column.references is None:
                continue
            parent_table, parent_column = column.references.split(".", maxsplit=1)
            child_values = tables[child_table][column.name]
            null_count = int(child_values.isna().sum())
            if column.nullable:
                child_values = child_values.dropna()
            parent_values = set(tables[parent_table][parent_column])
            missing_count = int((~child_values.isin(parent_values)).sum())
            checks.append(
                {
                    "child_table": child_table,
                    "child_column": column.name,
                    "parent_table": parent_table,
                    "parent_column": parent_column,
                    "checked_rows": int(len(child_values)),
                    "null_count": null_count,
                    "missing_reference_count": missing_count,
                    "passed": missing_count == 0 and (column.nullable or null_count == 0),
                }
            )
    return checks


def _temporal_checks(tables: Mapping[str, pd.DataFrame]) -> list[dict[str, Any]]:
    """Summarize datetime ranges and temporal ordering health."""
    checks: list[dict[str, Any]] = []
    for table_name, table_spec in TABLE_SPECS.items():
        frame = tables[table_name]
        for column in table_spec.columns:
            if column.dtype != "datetime64[ns]":
                continue
            values = pd.to_datetime(frame[column.name].dropna())
            after_as_of_count = int((values > DATASET_AS_OF).sum())
            checks.append(
                {
                    "table": table_name,
                    "column": column.name,
                    "check": "datetime_range",
                    "min": _timestamp_to_iso(values.min()) if not values.empty else None,
                    "max": _timestamp_to_iso(values.max()) if not values.empty else None,
                    "after_dataset_as_of_count": after_as_of_count,
                    "passed": after_as_of_count == 0,
                }
            )

    checks.extend(_temporal_ordering_checks(tables))
    return checks


def _temporal_ordering_checks(tables: Mapping[str, pd.DataFrame]) -> list[dict[str, Any]]:
    """Check foundation effective-date and Alert lifecycle ordering."""
    checks = [
        _ordering_check(
            "partners",
            "created_at_before_kyc_review",
            (tables["partners"]["created_at"] <= tables["partners"]["kyc_risk_effective_from"])
            & (
                tables["partners"]["kyc_risk_effective_from"]
                <= tables["partners"]["kyc_risk_reviewed_at"]
            ),
        ),
        _ordering_check(
            "banking_relationships",
            "relationship_manager_assigned_before_opened",
            tables["banking_relationships"]["relationship_manager_assigned_at"]
            <= tables["banking_relationships"]["opened_at"],
        ),
        _nullable_ordering_check(
            tables["partner_roles"],
            "partner_roles",
            "role_effective_from_before_effective_to",
            "effective_from",
            "effective_to",
        ),
        _ordering_check(
            "accounts",
            "opened_before_status_effective_from",
            tables["accounts"]["opened_at"] <= tables["accounts"]["status_effective_from"],
        ),
        _nullable_ordering_check(
            tables["accounts"],
            "accounts",
            "status_effective_from_before_status_effective_to",
            "status_effective_from",
            "status_effective_to",
        ),
        _ordering_check(
            "users",
            "created_before_authorized_from",
            tables["users"]["created_at"] <= tables["users"]["authorized_from"],
        ),
        _nullable_ordering_check(
            tables["users"],
            "users",
            "authorized_from_before_authorized_to",
            "authorized_from",
            "authorized_to",
        ),
    ]

    activities = tables["suspicious_activities"].merge(
        tables["transactions"][["transaction_id", "booked_at"]],
        on="transaction_id",
        how="left",
        validate="many_to_one",
    )
    checks.append(
        _ordering_check(
            "suspicious_activities",
            "transaction_booked_before_activity_detected",
            activities["booked_at"] <= activities["detected_at"],
        )
    )

    alerts = tables["alerts"].merge(
        tables["suspicious_activities"][["suspicious_activity_id", "detected_at"]],
        on="suspicious_activity_id",
        how="left",
        validate="many_to_one",
    )
    checks.extend(
        [
            _ordering_check(
                "alerts",
                "activity_detected_before_alert_generated",
                alerts["detected_at"] <= alerts["generated_at"],
            ),
            _ordering_check(
                "alerts",
                "alert_generated_before_status_updated",
                alerts["generated_at"] <= alerts["status_updated_at"],
            ),
        ]
    )

    cases = tables["cases"].merge(
        tables["alerts"][["alert_id", "generated_at"]],
        on="alert_id",
        how="left",
        validate="many_to_one",
    )
    checks.extend(
        [
            _ordering_check(
                "cases",
                "alert_generated_before_case_opened",
                cases["generated_at"] <= cases["opened_at"],
            ),
            _nullable_ordering_check(
                cases,
                "cases",
                "case_opened_before_closed",
                "opened_at",
                "closed_at",
            ),
        ]
    )

    outcomes = tables["case_outcomes"].merge(
        tables["cases"][["case_id", "opened_at", "closed_at"]],
        on="case_id",
        how="left",
        validate="many_to_one",
    )
    checks.extend(
        [
            _ordering_check(
                "case_outcomes",
                "case_opened_before_decided",
                outcomes["opened_at"] <= outcomes["decided_at"],
            ),
            _ordering_check(
                "case_outcomes",
                "decided_before_recorded",
                outcomes["decided_at"] <= outcomes["recorded_at"],
            ),
            _nullable_ordering_check(
                outcomes,
                "case_outcomes",
                "decided_before_case_closed",
                "decided_at",
                "closed_at",
            ),
        ]
    )
    return checks


def _prevalence_checks(tables: Mapping[str, pd.DataFrame]) -> list[dict[str, Any]]:
    """Return stable rate-band checks for generated lifecycle prevalence."""
    transaction_count = len(tables["transactions"])
    suspicious_count = len(tables["suspicious_activities"])
    alert_count = len(tables["alerts"])
    case_count = len(tables["cases"])
    confirmed_fraud_count = int(tables["case_outcomes"]["confirmed_fraud"].sum())
    protected_key_count = len(tables.get(PROTECTED_SCENARIO_ANSWER_KEYS, ()))

    return [
        _rate_check(
            "suspicious_activity_to_transaction_rate",
            suspicious_count,
            transaction_count,
            lower=0.15,
            upper=0.30,
        ),
        _rate_check(
            "alert_to_suspicious_activity_rate",
            alert_count,
            suspicious_count,
            lower=0.95,
            upper=1.05,
        ),
        _rate_check(
            "case_to_alert_rate",
            case_count,
            alert_count,
            lower=0.60,
            upper=0.75,
        ),
        _rate_check(
            "confirmed_fraud_to_transaction_rate",
            confirmed_fraud_count,
            transaction_count,
            lower=0.02,
            upper=0.10,
        ),
        _rate_check(
            "protected_key_to_transaction_rate",
            protected_key_count,
            transaction_count,
            lower=0.15,
            upper=0.30,
        ),
    ]


def _protected_key_exclusion_checks(
    tables: Mapping[str, pd.DataFrame],
) -> list[dict[str, Any]]:
    """Verify protected answer keys remain outside learner-facing tables."""
    learner_tables = build_learner_facing_views(tables)
    protected = tables.get(
        PROTECTED_SCENARIO_ANSWER_KEYS,
        pd.DataFrame(columns=COLUMN_NAMES[PROTECTED_SCENARIO_ANSWER_KEYS]),
    )
    protected_present_internal = not protected.empty
    protected_columns_in_learner_tables = sorted(
        {
            column
            for frame in learner_tables.values()
            for column in frame.columns
            if column in PROTECTED_KEY_COLUMNS
        }
    )

    return [
        {
            "check": "protected_table_present_internal",
            "passed": PROTECTED_SCENARIO_ANSWER_KEYS in tables
            and protected_present_internal,
        },
        {
            "check": "protected_table_excluded_from_learner_tables",
            "passed": PROTECTED_SCENARIO_ANSWER_KEYS not in learner_tables,
        },
        {
            "check": "protected_answer_keys_not_available_to_learners",
            "false_count": int((~protected["available_to_learners"]).sum()),
            "row_count": int(len(protected)),
            "passed": protected_present_internal
            and bool((~protected["available_to_learners"]).all()),
        },
        {
            "check": "protected_answer_key_columns_absent_from_learner_tables",
            "protected_columns": protected_columns_in_learner_tables,
            "passed": not protected_columns_in_learner_tables,
        },
    ]


def _progressive_view_health_checks(
    tables: Mapping[str, pd.DataFrame],
) -> list[dict[str, Any]]:
    """Check foundation Progressive data views against their contracts."""
    checks: list[dict[str, Any]] = []
    for spec in FOUNDATION_PROGRESSIVE_VIEW_SPECS:
        source_tables_present = set(spec.source_tables) <= set(tables)
        checks.append(
            {
                "view": spec.name,
                "check": "source_tables_present",
                "source_tables": list(spec.source_tables),
                "passed": source_tables_present,
            }
        )
        try:
            view = build_foundation_progressive_view(spec.name, tables)
        except Exception as error:
            checks.append(
                {
                    "view": spec.name,
                    "check": "builds_from_source_tables",
                    "error": f"{type(error).__name__}: {error}",
                    "passed": False,
                }
            )
            continue
        checks.extend(
            [
                {
                    "view": spec.name,
                    "check": "builds_from_source_tables",
                    "passed": True,
                },
                {
                    "view": spec.name,
                    "check": "columns_match_contract",
                    "passed": tuple(view.columns) == spec.columns,
                },
                {
                    "view": spec.name,
                    "check": "non_empty",
                    "row_count": int(len(view)),
                    "passed": not view.empty,
                },
                {
                    "view": spec.name,
                    "check": "protected_key_columns_absent",
                    "protected_columns": sorted(set(view.columns) & PROTECTED_KEY_COLUMNS),
                    "passed": not (set(view.columns) & PROTECTED_KEY_COLUMNS),
                },
            ]
        )
    return checks


def _ordering_check(table: str, check: str, mask: pd.Series) -> dict[str, Any]:
    """Build a standard pass/fail result for a boolean ordering mask."""
    failing_rows = int((~mask).sum())
    return {
        "table": table,
        "check": check,
        "failing_rows": failing_rows,
        "passed": failing_rows == 0,
    }


def _nullable_ordering_check(
    frame: pd.DataFrame,
    table: str,
    check: str,
    start_column: str,
    end_column: str,
) -> dict[str, Any]:
    """Check ordering only where the nullable end timestamp is populated."""
    populated = frame.dropna(subset=[end_column])
    if populated.empty:
        failing_rows = 0
    else:
        failing_rows = int((populated[start_column] > populated[end_column]).sum())
    return {
        "table": table,
        "check": check,
        "failing_rows": failing_rows,
        "passed": failing_rows == 0,
    }


def _rate_check(
    check: str,
    numerator: int,
    denominator: int,
    *,
    lower: float,
    upper: float,
) -> dict[str, Any]:
    """Build a stable prevalence rate check result."""
    rate = numerator / denominator if denominator else 0.0
    return {
        "check": check,
        "numerator": int(numerator),
        "denominator": int(denominator),
        "rate": round(rate, 6),
        "expected_min": lower,
        "expected_max": upper,
        "passed": lower <= rate <= upper,
    }


def _timestamp_to_iso(value: pd.Timestamp) -> str:
    """Normalize timestamps to deterministic ISO-8601 strings."""
    return pd.Timestamp(value).isoformat()


def _issue_for_check(dimension: str, check: Mapping[str, Any]) -> str:
    """Create a compact issue identifier for a failing check."""
    check_name = check.get("check", "unknown_check")
    location = check.get("table") or check.get("view") or check.get("child_table") or "dataset"
    return f"{dimension}:{location}:{check_name}"


def _render_reports(
    reports: Sequence[DatasetQualityReport],
    *,
    output_format: str,
) -> str:
    """Render one or more quality reports in the requested format."""
    if output_format == "json":
        return json.dumps([report.to_dict() for report in reports], indent=2) + "\n"
    return "\n".join(report.to_markdown().rstrip() for report in reports) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
