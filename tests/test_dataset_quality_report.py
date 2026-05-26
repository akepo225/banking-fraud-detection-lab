"""Tests for the generated dataset quality report."""

from pathlib import Path

import pytest

from banking_fraud_lab import (
    FOUNDATION_PROGRESSIVE_VIEW_SPECS,
    SCALE_PROFILES,
    generate_dataset_quality_report,
)
from banking_fraud_lab.data_quality import main as data_quality_main

REPORT_DOC_PATH = Path("docs/data_quality/dataset_quality_report.md")


def test_dataset_quality_report_covers_required_dimensions_and_is_deterministic() -> None:
    """The report must summarize the core quality dimensions deterministically."""
    first = generate_dataset_quality_report(seed=42, scale="tiny")
    second = generate_dataset_quality_report(seed=42, scale="tiny")

    assert first.to_dict() == second.to_dict()
    assert first.passed
    assert first.scale == "tiny"
    assert first.row_counts["transactions"] == 12

    assert first.dimensions == {
        "row_counts",
        "key_nullability",
        "referential_integrity",
        "temporal_ranges",
        "prevalence_ranges",
        "protected_key_exclusion",
        "progressive_view_health",
    }
    assert not first.issues


@pytest.mark.parametrize("scale", ("tiny", "small"))
def test_dataset_quality_report_is_deterministic_for_fixed_seed(scale: str) -> None:
    """Fixed seeds should produce stable report output at learner-facing scales."""
    first = generate_dataset_quality_report(seed=42, scale=scale)
    second = generate_dataset_quality_report(seed=42, scale=scale)

    assert first.to_dict() == second.to_dict()


@pytest.mark.parametrize("scale", tuple(SCALE_PROFILES))
def test_dataset_quality_report_runs_for_all_supported_scale_profiles(scale: str) -> None:
    """Every scale profile should produce a passing range-based quality report."""
    report = generate_dataset_quality_report(seed=42, scale=scale)

    assert report.passed
    assert report.row_counts["transactions"] >= SCALE_PROFILES[scale].transaction_count
    assert all(check["passed"] for check in report.key_nullability)
    assert all(check["passed"] for check in report.referential_integrity)
    assert all(check["passed"] for check in report.temporal_ranges)
    assert all(check["passed"] for check in report.protected_key_exclusion)
    assert all(check["passed"] for check in report.progressive_view_health)

    prevalence_checks = {check["check"]: check for check in report.prevalence_ranges}
    suspicious_activity_rate = prevalence_checks["suspicious_activity_to_transaction_rate"]
    confirmed_fraud_rate = prevalence_checks["confirmed_fraud_to_transaction_rate"]
    assert suspicious_activity_rate["expected_min"] <= suspicious_activity_rate["rate"]
    assert suspicious_activity_rate["rate"] <= suspicious_activity_rate["expected_max"]
    assert confirmed_fraud_rate["expected_min"] <= confirmed_fraud_rate["rate"]
    assert confirmed_fraud_rate["rate"] <= confirmed_fraud_rate["expected_max"]

    reported_views = {
        check["view"]
        for check in report.progressive_view_health
        if check["check"] == "columns_match_contract"
    }
    assert reported_views == {spec.name for spec in FOUNDATION_PROGRESSIVE_VIEW_SPECS}


def test_dataset_quality_cli_writes_markdown_for_tiny_and_larger_scale(
    tmp_path: Path,
) -> None:
    """The command path should generate learner-facing Markdown locally."""
    output_path = tmp_path / "dataset-quality.md"

    exit_code = data_quality_main(
        [
            "--scale",
            "tiny",
            "--scale",
            "small",
            "--output",
            str(output_path),
        ]
    )

    assert exit_code == 0
    report_text = output_path.read_text(encoding="utf-8")
    assert "# Dataset Quality Report: tiny" in report_text
    assert "# Dataset Quality Report: small" in report_text
    for dimension in (
        "row_counts",
        "key_nullability",
        "referential_integrity",
        "temporal_ranges",
        "prevalence_ranges",
        "protected_key_exclusion",
        "progressive_view_health",
    ):
        assert dimension in report_text


def test_dataset_quality_report_documentation_covers_generation_and_interpretation() -> None:
    """Docs should explain how to generate and read the report."""
    report_doc = REPORT_DOC_PATH.read_text(encoding="utf-8")

    assert "uv run python -m banking_fraud_lab.data_quality" in report_doc
    assert "--scale tiny" in report_doc
    assert "--scale small" in report_doc
    assert "Protected answer keys" in report_doc
    assert "Progressive data views" in report_doc
    assert "No external infrastructure" in report_doc
    for dimension in (
        "row counts",
        "key nullability",
        "referential integrity",
        "temporal ranges",
        "prevalence ranges",
    ):
        assert dimension in report_doc
