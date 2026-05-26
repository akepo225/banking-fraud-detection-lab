"""Tests for the v0.2 foundation acceptance review document."""

from pathlib import Path


REVIEW_PATH = Path("docs/release/v0.2-foundation-acceptance-review.md")


def test_v02_acceptance_review_has_hitl_boundary_and_evidence() -> None:
    """The v0.2 review must stay explicit about HITL status and command evidence."""
    review = REVIEW_PATH.read_text(encoding="utf-8")

    required_terms = [
        "Status: draft for human review.",
        "<!-- HITL-REVIEW-REQUIRED:",
        "Ready for human v0.2 acceptance review after PR #77 is accepted",
        "uv sync --extra dev",
        "uv run ruff check .",
        "git diff --check",
        "uv run pytest tests/test_sqlite_loader.py tests/test_progressive_views.py tests/test_dataset_quality_report.py tests/test_publication_docs.py",
        "uv run python -m banking_fraud_lab.create_sqlite data/generated/end_user_minimal.sqlite",
        "uv run python -m banking_fraud_lab.run_sql data/sample/minimal_world.sqlite sql/examples/04_progressive_alert_queue.sql",
        "uv run python -m banking_fraud_lab.data_quality --scale tiny --scale small --output data/generated/reports/dataset-quality.md",
        "uv run pytest",
        "174 passed",
        "PR #77 remote checks",
    ]
    for term in required_terms:
        assert term in review


def test_v02_acceptance_review_maps_prs_and_audit_followups() -> None:
    """The review must map implementation slices and PR #77 follow-ups."""
    review = REVIEW_PATH.read_text(encoding="utf-8")

    for issue_number, pr_number in [
        (59, 69),
        (60, 70),
        (61, 71),
        (62, 72),
        (63, 73),
        (64, 74),
        (65, 75),
    ]:
        assert f"Issue #{issue_number} / PR #{pr_number}" in review

    for term in [
        "PR #77 fixed the later-discovered staged-load",
        "PR #77 fixed later-discovered missing-table",
        "cross-platform Python SQL runner",
        "issue #78",
        "No remaining blocking v0.2 defect",
    ]:
        assert term in review


def test_v02_acceptance_review_tracks_deferred_scope_and_label_hygiene() -> None:
    """Deferred work and issue label cleanup must be explicit."""
    review = REVIEW_PATH.read_text(encoding="utf-8")
    normalized_review = " ".join(review.split())

    for follow_up_issue in range(46, 59):
        assert f"#{follow_up_issue}" in review

    required_terms = [
        "#78",
        "Stable Detection pattern identifiers",
        "Issue Tracker Hygiene",
        "stale `needs-triage` / `blocked` labels were removed",
        "ready-for-human",
        "hitl",
    ]
    for term in required_terms:
        assert term in normalized_review


def test_v02_acceptance_review_uses_glossary_and_boundary_terms() -> None:
    """The review should preserve repo vocabulary and source-boundary language."""
    review = REVIEW_PATH.read_text(encoding="utf-8")

    required_terms = [
        "Partner",
        "Client",
        "User",
        "Banking relationship",
        "Progressive data view",
        "Alert lifecycle",
        "Alpine Crest Private Bank",
        "NovaBank Digital",
        "real-bank affiliation",
        "real-client-data",
        "reconstruction",
        "legal-advice",
    ]
    for term in required_terms:
        assert term in review
